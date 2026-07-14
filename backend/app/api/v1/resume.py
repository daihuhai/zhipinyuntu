"""
简历路由
- POST   /resumes/upload   上传简历 (DOC/PDF) + 灵犀解析
- GET    /resumes           我的简历列表
- GET    /resumes/{id}      简历详情 (含技能 + 工作经历 + 项目经历)
- PUT    /resumes/{id}      在线编辑简历
- GET    /resumes/{id}/file 获取简历原文件 URL (企业可查看投递者简历)
- DELETE /resumes/{id}      删除简历
- POST   /resumes/{id}/embed  生成简历向量
"""
import json
from fastapi import APIRouter, Depends, UploadFile, File, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.core.limiter import limiter
from app.db.base import get_db
from app.models.user import SysUser
from app.models.resume import Resume, ResumeSkill
from app.models.job import Job
from app.models.application import JobApplication
from app.schemas.common import success, fail, BizError
from app.services.resume_service import resume_service
from app.services.vip_service import vip_service, QuotaExceededException
from app.ai.ark_client import ark_client
from app.ai.prompts import build_gap_analysis_messages
from app.utils.mask import mask_phone, mask_email

router = APIRouter(prefix="/resumes", tags=["简历"])


class ResumeEditRequest(BaseModel):
    """在线编辑简历请求体"""
    name: str | None = Field(None, max_length=64)
    gender: str | None = Field(None, max_length=8)
    age: int | None = Field(None, ge=16, le=80)
    phone: str | None = Field(None, max_length=20)
    email: str | None = Field(None, max_length=128)
    current_city: str | None = Field(None, max_length=32)
    intention_cities: str | None = None  # JSON 数组字符串
    education: str | None = Field(None, max_length=16)
    school: str | None = Field(None, max_length=64)
    major: str | None = Field(None, max_length=64)
    work_years: int | None = Field(None, ge=0, le=50)
    expected_salary_min: int | None = Field(None, ge=0)
    expected_salary_max: int | None = Field(None, ge=0)
    self_evaluation: str | None = Field(None, max_length=2000)
    skills: list[dict] | None = None  # [{"skill_name": "Java", "skill_level": "熟练"}]


@router.post("/upload", summary="上传简历并灵犀解析", response_model=None)
@limiter.limit("5/minute")
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """上传 DOC/PDF 简历, 同步调用灵犀大模型解析结构化 (非 VIP 用户消耗配额)"""
    # VIP 配额检查 (保存消耗前状态, 失败时精确退还)
    _paid_before = current_user.paid_quota
    _free_used_before = current_user.free_quota_used
    try:
        vip_service.check_and_consume_quota(current_user, db, action="resume_parse")
    except QuotaExceededException as e:
        return fail(BizError.ROLE_FORBIDDEN, e.message, data=e.quota_info)

    try:
        result = await resume_service.upload_and_parse(file, current_user.id, db)
        return success(data=result, message="简历上传并解析成功")
    except ValueError as e:
        return fail(BizError.VALIDATION_ERROR, str(e))
    except Exception as e:
        # 解析失败, 精确退还消耗的配额
        current_user.free_quota_used = _free_used_before
        current_user.paid_quota = _paid_before
        db.commit()
        return fail(BizError.PARSE_FAILED, f"解析失败: {e}")


@router.get("", summary="我的简历列表", response_model=None)
async def list_resumes(
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """查询当前用户的简历列表"""
    items = resume_service.list_by_user(current_user.id, db)
    data = [
        {
            "id": r.id,
            "name": r.name,
            "parse_status": r.parse_status,
            "current_city": r.current_city,
            "education": r.education,
            "school": r.school,
            "major": r.major,
            "work_years": r.work_years,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in items
    ]
    return success(data={"items": data, "total": len(data)})


def _parse_work_experience(raw_json: str | None) -> list[dict]:
    """从 raw_parse_json 中解析工作经历"""
    if not raw_json:
        return []
    try:
        data = json.loads(raw_json)
        return data.get("work_experience", []) or []
    except (json.JSONDecodeError, TypeError):
        return []


def _parse_projects(raw_json: str | None) -> list[dict]:
    """从 raw_parse_json 中解析项目经历"""
    if not raw_json:
        return []
    try:
        data = json.loads(raw_json)
        return data.get("projects", []) or []
    except (json.JSONDecodeError, TypeError):
        return []


def _check_employer_can_view(resume_id: int, employer_id: int, db: Session) -> bool:
    """校验企业是否有权查看该简历 (该求职者投递了该企业的职位)"""
    # 查询该简历投递的职位, 是否属于该企业
    rows = db.execute(
        select(JobApplication.job_id).join(
            Job, JobApplication.job_id == Job.id
        ).where(
            JobApplication.resume_id == resume_id,
            Job.user_id == employer_id,
        )
    ).all()
    return len(rows) > 0


@router.get("/{resume_id}", summary="简历详情", response_model=None)
async def get_resume(
    resume_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """获取简历详情 (含技能 + 工作经历 + 项目经历)
    权限: 求职者仅本人, 企业仅投递者, 管理员全部
    """
    try:
        resume = resume_service.get_detail(resume_id, db)
        # 权限校验
        if current_user.role == "ROLE_SEEKER" and resume.user_id != current_user.id:
            return fail(BizError.ROLE_FORBIDDEN, "无权查看他人简历")
        if current_user.role == "ROLE_EMPLOYER":
            if not _check_employer_can_view(resume_id, current_user.id, db):
                return fail(BizError.ROLE_FORBIDDEN, "无权查看未投递本企业的简历")
        data = {
            "id": resume.id,
            "user_id": resume.user_id,
            "doc_url": resume.doc_url,
            "parse_status": resume.parse_status,
            "parse_error": resume.parse_error,
            "name": resume.name,
            "gender": resume.gender,
            "age": resume.age,
            "phone": resume.phone,
            "email": resume.email,
            "current_city": resume.current_city,
            "intention_cities": resume.intention_cities,
            "education": resume.education,
            "school": resume.school,
            "major": resume.major,
            "work_years": resume.work_years,
            "expected_salary_min": resume.expected_salary_min,
            "expected_salary_max": resume.expected_salary_max,
            "self_evaluation": resume.self_evaluation,
            "skills": [
                {
                    "id": s.id,
                    "skill_name": s.skill_name,
                    "skill_level": s.skill_level,
                    "weight": s.weight,
                }
                for s in resume.skills
            ],
            "work_experience": _parse_work_experience(resume.raw_parse_json),
            "projects": _parse_projects(resume.raw_parse_json),
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
        }
        # 企业查看简历时对手机号/邮箱脱敏 (本人/管理员不脱敏)
        if current_user.role == "ROLE_EMPLOYER":
            data["phone"] = mask_phone(data["phone"])
            data["email"] = mask_email(data["email"])
        return success(data=data)
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))


@router.put("/{resume_id}", summary="在线编辑简历", response_model=None)
async def update_resume(
    resume_id: int,
    req: ResumeEditRequest,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """在线编辑简历基本信息和技能 (仅本人可编辑)"""
    try:
        resume = resume_service.get_detail(resume_id, db)
        # 权限校验: 仅本人可编辑
        if resume.user_id != current_user.id:
            return fail(BizError.ROLE_FORBIDDEN, "无权编辑他人简历")

        # 更新基本信息 (只更新非 None 字段)
        update_data = req.model_dump(exclude_none=True)
        skills_data = update_data.pop("skills", None)

        for field, value in update_data.items():
            if hasattr(resume, field):
                setattr(resume, field, value)

        db.commit()
        db.refresh(resume)

        # 更新技能 (如果提供了)
        if skills_data is not None:
            # 删除旧技能
            db.execute(delete(ResumeSkill).where(ResumeSkill.resume_id == resume_id))
            # 插入新技能
            for skill_item in skills_data:
                skill = ResumeSkill(
                    resume_id=resume_id,
                    skill_name=skill_item.get("skill_name", ""),
                    skill_level=skill_item.get("skill_level", "了解"),
                    weight=skill_item.get("weight", 0.5),
                )
                db.add(skill)
            db.commit()

        return success(message="简历更新成功")
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"更新失败: {e}")


@router.get("/{resume_id}/file", summary="获取简历原文件 URL", response_model=None)
async def get_resume_file(
    resume_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """获取简历原文件 URL (企业仅可查看投递本企业的简历)"""
    try:
        resume = resume_service.get_detail(resume_id, db)
        # 权限校验
        if current_user.role == "ROLE_SEEKER" and resume.user_id != current_user.id:
            return fail(BizError.ROLE_FORBIDDEN, "无权查看他人简历")
        if current_user.role == "ROLE_EMPLOYER":
            if not _check_employer_can_view(resume_id, current_user.id, db):
                return fail(BizError.ROLE_FORBIDDEN, "无权查看未投递本企业的简历")
        # 规范化 doc_url: 确保以 /uploads/ 开头 (兼容历史数据缺前导斜杠)
        import os
        doc_url = resume.doc_url or ""
        if doc_url and not doc_url.startswith("/uploads/"):
            if doc_url.startswith("uploads/"):
                doc_url = "/" + doc_url
            elif doc_url.startswith("/"):
                doc_url = "/uploads" + doc_url
            else:
                doc_url = "/uploads/" + doc_url
        filename = os.path.basename(doc_url) if doc_url else f"resume_{resume_id}"
        return success(data={
            "doc_url": doc_url,
            "filename": filename,
        })
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))


@router.delete("/{resume_id}", summary="删除简历", response_model=None)
async def delete_resume(
    resume_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """删除简历 (仅本人)"""
    try:
        resume_service.delete(resume_id, current_user.id, db)
        return success(message="删除成功")
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))


@router.post("/{resume_id}/embed", summary="生成简历向量", response_model=None)
def embed_resume(
    resume_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """生成简历向量 (用于 M4 智能匹配)"""
    try:
        resume_service.generate_embedding(resume_id, db)
        return success(message="向量生成成功")
    except Exception as e:
        return fail(BizError.SYSTEM_ERROR, f"向量生成失败: {e}")


@router.post("/{resume_id}/gap-analysis", summary="灵犀分析简历缺失项", response_model=None)
async def analyze_resume_gaps(
    resume_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """调用灵犀大模型分析简历中缺失或可改进的部分, 返回具体建议 (非 VIP 用户消耗配额)"""
    import asyncio
    try:
        resume = resume_service.get_detail(resume_id, db)
        if resume.user_id != current_user.id:
            return fail(BizError.ROLE_FORBIDDEN, "无权分析他人简历")

        # VIP 配额检查 (保存消耗前状态, 失败时精确退还)
        _paid_before = current_user.paid_quota
        _free_used_before = current_user.free_quota_used
        try:
            vip_service.check_and_consume_quota(current_user, db, action="gap_analysis")
        except QuotaExceededException as e:
            return fail(BizError.ROLE_FORBIDDEN, e.message, data=e.quota_info)

        # 构造简历摘要 JSON 发送给灵犀大模型
        resume_summary = {
            "name": resume.name or "",
            "gender": resume.gender or "",
            "age": resume.age,
            "phone": resume.phone or "",
            "email": resume.email or "",
            "current_city": resume.current_city or "",
            "intention_cities": resume.intention_cities or "",
            "education": resume.education or "",
            "school": resume.school or "",
            "major": resume.major or "",
            "work_years": resume.work_years,
            "expected_salary_min": resume.expected_salary_min,
            "expected_salary_max": resume.expected_salary_max,
            "self_evaluation": resume.self_evaluation or "",
            "skills": [
                {"skill_name": s.skill_name, "skill_level": s.skill_level}
                for s in resume.skills
            ],
            "work_experience": _parse_work_experience(resume.raw_parse_json),
            "projects": _parse_projects(resume.raw_parse_json),
        }

        messages = build_gap_analysis_messages(json.dumps(resume_summary, ensure_ascii=False))

        # 在线程池中调用 LLM, 避免阻塞事件循环
        result, gap_usage = await asyncio.to_thread(
            ark_client.chat_json, messages, temperature=0.2, max_tokens=2048
        )

        # 记录灵犀分析操作日志
        try:
            from app.services.admin_service import admin_service
            admin_service.write_system_log(
                db,
                action="AI_GAP_ANALYSIS",
                target_type="resume",
                target_id=resume_id,
                detail=f"灵犀大模型分析简历缺失项: {resume.name or '未知'} (ID:{resume_id})",
                tokens_in=gap_usage.get("prompt_tokens", 0),
                tokens_out=gap_usage.get("completion_tokens", 0),
            )
        except Exception:
            pass

        return success(data=result)
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))
    except Exception as e:
        # 分析失败, 退还配额
        current_user.free_quota_used = _free_used_before
        current_user.paid_quota = _paid_before
        db.commit()
        return fail(BizError.SYSTEM_ERROR, f"分析失败: {e}")
