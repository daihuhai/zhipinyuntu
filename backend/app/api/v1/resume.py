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
from app.ai.prompts import build_gap_analysis_messages, build_resume_optimize_messages
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
            ark_client.chat_json_lite, messages, temperature=0.2, max_tokens=2048
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


@router.post("/{resume_id}/analyze-form", summary="灵犀分析编辑中的简历(实时)", response_model=None)
async def analyze_resume_form(
    resume_id: int,
    payload: dict,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """接收前端编辑中的表单数据, 实时分析缺失项 (无需先保存)"""
    import asyncio
    try:
        resume = resume_service.get_detail(resume_id, db)
        if resume.user_id != current_user.id:
            return fail(BizError.ROLE_FORBIDDEN, "无权分析他人简历")

        # VIP 配额检查
        _paid_before = current_user.paid_quota
        _free_used_before = current_user.free_quota_used
        try:
            vip_service.check_and_consume_quota(current_user, db, action="gap_analysis")
        except QuotaExceededException as e:
            return fail(BizError.ROLE_FORBIDDEN, e.message, data=e.quota_info)

        # 直接使用前端传来的表单数据构造摘要
        form_data = payload.get("form_data", {})
        resume_summary = {
            "name": form_data.get("name") or "",
            "gender": form_data.get("gender") or "",
            "age": form_data.get("age"),
            "phone": form_data.get("phone") or "",
            "email": form_data.get("email") or "",
            "current_city": form_data.get("current_city") or "",
            "intention_cities": form_data.get("intention_cities") or "",
            "education": form_data.get("education") or "",
            "school": form_data.get("school") or "",
            "major": form_data.get("major") or "",
            "work_years": form_data.get("work_years"),
            "expected_salary_min": form_data.get("expected_salary_min"),
            "expected_salary_max": form_data.get("expected_salary_max"),
            "self_evaluation": form_data.get("self_evaluation") or "",
            "skills": form_data.get("skills") or [],
            "work_experience": _parse_work_experience(resume.raw_parse_json),
            "projects": _parse_projects(resume.raw_parse_json),
        }

        messages = build_gap_analysis_messages(json.dumps(resume_summary, ensure_ascii=False))
        result, gap_usage = await asyncio.to_thread(
            ark_client.chat_json_lite, messages, temperature=0.2, max_tokens=2048
        )

        try:
            from app.services.admin_service import admin_service
            admin_service.write_system_log(
                db,
                action="AI_GAP_ANALYSIS",
                target_type="resume",
                target_id=resume_id,
                detail=f"灵犀分析(实时编辑): {resume.name or '未知'} (ID:{resume_id})",
                tokens_in=gap_usage.get("prompt_tokens", 0),
                tokens_out=gap_usage.get("completion_tokens", 0),
            )
        except Exception:
            pass

        return success(data=result)
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))
    except Exception as e:
        current_user.free_quota_used = _free_used_before
        current_user.paid_quota = _paid_before
        db.commit()
        return fail(BizError.SYSTEM_ERROR, f"分析失败: {e}")


@router.post("/{resume_id}/optimize", summary="灵犀AI简历优化建议", response_model=None)
async def optimize_resume(
    resume_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """调用灵犀大模型对简历进行深度优化评估, 返回评分+改进建议+改写示例 (非 VIP 用户消耗配额)"""
    import asyncio
    try:
        resume = resume_service.get_detail(resume_id, db)
        if resume.user_id != current_user.id:
            return fail(BizError.ROLE_FORBIDDEN, "无权分析他人简历")

        # VIP 配额检查
        _paid_before = current_user.paid_quota
        _free_used_before = current_user.free_quota_used
        try:
            vip_service.check_and_consume_quota(current_user, db, action="gap_analysis")
        except QuotaExceededException as e:
            return fail(BizError.ROLE_FORBIDDEN, e.message, data=e.quota_info)

        # 构造简历摘要 JSON
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

        messages = build_resume_optimize_messages(
            json.dumps(resume_summary, ensure_ascii=False)
        )

        result, opt_usage = await asyncio.to_thread(
            ark_client.chat_json, messages, temperature=0.3, max_tokens=2048
        )

        # 记录操作日志
        try:
            from app.services.admin_service import admin_service
            admin_service.write_system_log(
                db,
                action="AI_RESUME_OPTIMIZE",
                target_type="resume",
                target_id=resume_id,
                detail=f"灵犀AI简历优化建议: {resume.name or '未知'} (ID:{resume_id})",
                tokens_in=opt_usage.get("prompt_tokens", 0),
                tokens_out=opt_usage.get("completion_tokens", 0),
            )
        except Exception:
            pass

        return success(data=result)
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))
    except Exception as e:
        current_user.free_quota_used = _free_used_before
        current_user.paid_quota = _paid_before
        db.commit()
        return fail(BizError.SYSTEM_ERROR, f"优化分析失败: {e}")


# ===== 学历排序映射 =====
_EDU_RANK = {"高中": 1, "大专": 2, "本科": 3, "硕士": 4, "博士": 5}


@router.get("/{resume_id}/competitiveness", summary="求职者竞争力分析", response_model=None)
async def get_competitiveness(
    resume_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """竞争力分析: 统计同岗位候选人数据, 返回五维百分位 + 雷达图数据 + 提升建议"""
    try:
        resume = resume_service.get_detail(resume_id, db)
        if resume.user_id != current_user.id:
            return fail(BizError.ROLE_FORBIDDEN, "无权分析他人简历")

        # 1. 找到该简历投递过的所有职位, 获取同岗位候选人
        from app.models.application import JobApplication
        from app.models.match import MatchRecord

        job_ids_subq = (
            select(JobApplication.job_id)
            .where(JobApplication.resume_id == resume_id)
            .subquery()
        )

        # 查询投递了相同职位的其他简历 (同岗位候选人)
        peer_resume_ids_q = (
            select(JobApplication.resume_id)
            .where(JobApplication.job_id.in_(select(job_ids_subq.c.job_id)))
            .where(JobApplication.resume_id != resume_id)
            .distinct()
        )
        peer_resume_ids = [row[0] for row in db.execute(peer_resume_ids_q).all()]

        # 如果同岗位候选人不足, 用全部简历作为参考池
        if len(peer_resume_ids) < 3:
            peer_resume_ids_q = (
                select(Resume.id)
                .where(Resume.id != resume_id)
                .where(Resume.parse_status == 2)
                .limit(200)
            )
            peer_resume_ids = [row[0] for row in db.execute(peer_resume_ids_q).all()]

        # 2. 查询全体候选人数据 (含自己)
        all_ids = list(set(peer_resume_ids + [resume_id]))
        all_resumes_q = (
            select(Resume, ResumeSkill)
            .outerjoin(ResumeSkill, ResumeSkill.resume_id == Resume.id)
            .where(Resume.id.in_(all_ids))
        )
        rows = db.execute(all_resumes_q).all()

        # 聚合每份简历的技能数
        skill_count_map: dict[int, int] = {}
        resume_map: dict[int, Resume] = {}
        for r, s in rows:
            if r.id not in resume_map:
                resume_map[r.id] = r
                skill_count_map[r.id] = 0
            if s is not None:
                skill_count_map[r.id] += 1

        # 3. 查询匹配得分 (该简历被推荐时的平均匹配分)
        match_scores_q = (
            select(MatchRecord.total_score)
            .where(MatchRecord.resume_id == resume_id)
        )
        my_match_scores = [row[0] for row in db.execute(match_scores_q).all()]

        # 同岗位候选人的匹配得分
        if peer_resume_ids:
            peer_match_scores_q = (
                select(MatchRecord.total_score)
                .where(MatchRecord.resume_id.in_(peer_resume_ids))
            )
            peer_match_scores = [row[0] for row in db.execute(peer_match_scores_q).all()]
        else:
            peer_match_scores = []

        # 4. 计算百分位函数
        def percentile(value: float, pool: list[float]) -> float:
            """计算 value 在 pool 中的百分位 (0-100)"""
            if not pool:
                return 50.0
            below = sum(1 for v in pool if v <= value)
            return round(below / len(pool) * 100, 1)

        # 5. 五维数据
        my_skills = skill_count_map.get(resume_id, 0)
        peer_skill_counts = [skill_count_map.get(rid, 0) for rid in peer_resume_ids]

        my_work_years = float(resume.work_years or 0)
        peer_work_years = [float(r.work_years or 0) for r in resume_map.values() if r.id != resume_id]

        my_edu_rank = _EDU_RANK.get(resume.education or "", 0)
        peer_edu_ranks = [_EDU_RANK.get(r.education or "", 0) for r in resume_map.values() if r.id != resume_id]

        my_avg_match = sum(my_match_scores) / len(my_match_scores) if my_match_scores else 0
        peer_avg_match = peer_match_scores if peer_match_scores else []

        # 技能覆盖度百分位
        skill_pct = percentile(float(my_skills), [float(c) for c in peer_skill_counts])
        # 经验年限百分位
        exp_pct = percentile(my_work_years, peer_work_years)
        # 学历水平百分位
        edu_pct = percentile(float(my_edu_rank), [float(r) for r in peer_edu_ranks])
        # 匹配得分百分位
        match_pct = percentile(my_avg_match, peer_avg_match) if peer_avg_match else 50.0
        # 简历完整度 (根据填写字段比例)
        my_fields = [resume.name, resume.gender, resume.age, resume.phone, resume.email,
                     resume.current_city, resume.education, resume.school, resume.major,
                     resume.work_years, resume.self_evaluation]
        filled = sum(1 for f in my_fields if f is not None and str(f).strip())
        completeness = round(filled / len(my_fields) * 100, 1)

        # 6. 雷达图数据
        radar_indicators = [
            {"name": "技能覆盖度", "max": 100},
            {"name": "经验年限", "max": 100},
            {"name": "学历水平", "max": 100},
            {"name": "匹配得分", "max": 100},
            {"name": "简历完整度", "max": 100},
        ]
        radar_values = [skill_pct, exp_pct, edu_pct, match_pct, completeness]

        # 7. 同岗位统计概要
        peer_count = len(peer_resume_ids)
        skill_median = sorted(peer_skill_counts)[len(peer_skill_counts) // 2] if peer_skill_counts else 0
        exp_median = sorted(peer_work_years)[len(peer_work_years) // 2] if peer_work_years else 0

        # 8. 提升建议
        suggestions = []
        if skill_pct < 50:
            suggestions.append(f"你的技能数量({my_skills}项)低于同岗位中位数({skill_median}项), 建议补充更多技能以提升竞争力")
        if exp_pct < 50:
            suggestions.append(f"你的工作年限({int(my_work_years)}年)低于同岗位中位数({int(exp_median)}年), 建议突出项目经验弥补年限不足")
        if edu_pct < 50:
            suggestions.append("你的学历在同岗位候选人中偏低, 建议通过证书或项目成果展示实力")
        if match_pct < 50:
            suggestions.append(f"你的平均匹配得分({my_avg_match:.1f})低于同岗位平均水平, 建议优化简历关键词以提高匹配度")
        if completeness < 80:
            suggestions.append(f"简历完整度仅{completeness}%, 建议补全个人信息以提升简历质量")
        if not suggestions:
            suggestions.append("你的各项指标在同岗位候选人中表现优秀, 继续保持!")

        # 9. TOP 技能分析
        my_skill_names = set()
        for r, s in rows:
            if r.id == resume_id and s is not None:
                my_skill_names.add(s.skill_name)

        peer_skill_freq: dict[str, int] = {}
        for r, s in rows:
            if r.id != resume_id and s is not None:
                peer_skill_freq[s.skill_name] = peer_skill_freq.get(s.skill_name, 0) + 1

        # 同岗位热门技能 TOP5 中你缺失的
        top_peer_skills = sorted(peer_skill_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        missing_hot_skills = [name for name, cnt in top_peer_skills if name not in my_skill_names]
        if missing_hot_skills:
            suggestions.append(f"同岗位热门技能中你还缺少: {', '.join(missing_hot_skills)}, 建议学习补充")

        return success(data={
            "radar": {
                "indicators": radar_indicators,
                "values": radar_values,
            },
            "dimensions": [
                {"name": "技能覆盖度", "percentile": skill_pct, "value": my_skills, "median": skill_median,
                 "unit": "项", "desc": f"你的技能数 {my_skills} 项, 同岗位中位数 {skill_median} 项"},
                {"name": "经验年限", "percentile": exp_pct, "value": int(my_work_years), "median": int(exp_median),
                 "unit": "年", "desc": f"你的工作年限 {int(my_work_years)} 年, 同岗位中位数 {int(exp_median)} 年"},
                {"name": "学历水平", "percentile": edu_pct,
                 "value": resume.education or "未填写",
                 "median": _median_education(peer_edu_ranks),
                 "unit": "", "desc": f"你的学历 {resume.education or '未填写'}, 同岗位中位数 {_median_education(peer_edu_ranks)}"},
                {"name": "匹配得分", "percentile": match_pct,
                 "value": round(my_avg_match, 1), "median": _median_float(peer_avg_match),
                 "unit": "分", "desc": f"你的平均匹配分 {my_avg_match:.1f}, 同岗位平均 {_median_float(peer_avg_match):.1f}"},
                {"name": "简历完整度", "percentile": completeness,
                 "value": completeness, "median": None,
                 "unit": "%", "desc": f"简历信息填写完整度 {completeness}%"},
            ],
            "peer_count": peer_count,
            "suggestions": suggestions,
        })
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))
    except Exception as e:
        return fail(BizError.SYSTEM_ERROR, f"竞争力分析失败: {e}")


def _median_float(values: list[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    return s[len(s) // 2]


def _median_education(ranks: list[float]) -> str:
    if not ranks:
        return "未知"
    s = sorted(ranks)
    median_rank = s[len(s) // 2]
    reverse_map = {v: k for k, v in _EDU_RANK.items()}
    return reverse_map.get(median_rank, "未知")
