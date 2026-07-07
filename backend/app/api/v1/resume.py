"""
简历路由
- POST   /resumes/upload   上传简历 (DOC/PDF) + AI 解析
- GET    /resumes           我的简历列表
- GET    /resumes/{id}      简历详情 (含技能)
- DELETE /resumes/{id}      删除简历
- POST   /resumes/{id}/embed  生成简历向量
"""
from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.user import SysUser
from app.schemas.common import success, fail, BizError
from app.services.resume_service import resume_service

router = APIRouter(prefix="/resumes", tags=["简历"])


@router.post("/upload", summary="上传简历并 AI 解析", response_model=None)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """上传 DOC/PDF 简历, 同步调用豆包模型解析结构化"""
    try:
        result = await resume_service.upload_and_parse(file, current_user.id, db)
        return success(data=result, message="简历上传并解析成功")
    except ValueError as e:
        return fail(BizError.VALIDATION_ERROR, str(e))
    except Exception as e:
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


@router.get("/{resume_id}", summary="简历详情", response_model=None)
async def get_resume(
    resume_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """获取简历详情 (含技能列表)"""
    try:
        resume = resume_service.get_detail(resume_id, db)
        # 权限: 求职者只能看自己的, 管理员可看所有
        if current_user.role == "ROLE_SEEKER" and resume.user_id != current_user.id:
            return fail(BizError.ROLE_FORBIDDEN, "无权查看他人简历")
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
            "created_at": resume.created_at.isoformat() if resume.created_at else None,
        }
        return success(data=data)
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
async def embed_resume(
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
