"""
职位路由
- POST   /jobs              创建职位 (支持 JD 解析)
- POST   /jobs/upload-jd    上传 JD 文件 (PDF/DOC/DOCX) + AI 解析
- GET    /jobs              我的职位列表 (企业)
- GET    /jobs/plaza        职位广场 (公开, 分页)
- GET    /jobs/favorites    我的收藏列表 (求职者)
- GET    /jobs/{id}         职位详情
- DELETE /jobs/{id}         删除职位
- PATCH  /jobs/{id}/status  更新职位状态
- POST   /jobs/{id}/favorite   收藏职位 (求职者)
- DELETE /jobs/{id}/favorite   取消收藏 (求职者)
"""
from fastapi import APIRouter, Depends, Query, UploadFile, File
from sqlalchemy import select, func
from sqlalchemy.orm import Session
import asyncio

from app.core.deps import get_current_user, require_role
from app.db.base import get_db
from app.models.user import SysUser
from app.models.job import Job
from app.models.application import JobApplication
from app.models.favorite import Favorite
from app.schemas.common import success, fail, BizError
from app.schemas.job import JobCreateRequest
from app.services.job_service import job_service
from app.services.file_service import file_service
from app.services.doc_parser import doc_parser

router = APIRouter(prefix="/jobs", tags=["职位"])


@router.post("/upload-jd", summary="上传 JD 文件并 AI 解析", response_model=None)
async def upload_jd(
    file: UploadFile = File(...),
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER")),
):
    """上传 JD 文件 (PDF/DOC/DOCX), 提取文本并用豆包 AI 结构化解析, 返回字段供前端预填表单"""
    try:
        # 1. 保存文件
        file_info = await file_service.save(file, sub_dir="jobs")

        # 2. 提取文本 (放到线程池, 避免阻塞事件循环)
        abs_path = file_info["abs_path"]
        text = await asyncio.to_thread(doc_parser.extract_text, abs_path)
        if not text.strip():
            return fail(BizError.PARSE_FAILED, "无法从文件中提取文本, 请确认文件非扫描件/图片")

        # 3. AI 结构化解析 (放到线程池)
        parsed = await asyncio.to_thread(doc_parser.parse_job, text)

        return success(data={
            "doc_url": file_info["url"],
            "filename": file_info["filename"],
            "raw_text": text[:2000],
            "parsed": {
                "title": parsed.get("title", ""),
                "company": parsed.get("company", ""),
                "department": parsed.get("department", ""),
                "job_type": parsed.get("job_type", ""),
                "work_city": parsed.get("work_city", ""),
                "experience_required": parsed.get("experience_required", ""),
                "education_required": parsed.get("education_required", ""),
                "salary_min": parsed.get("salary_min"),
                "salary_max": parsed.get("salary_max"),
                "headcount": parsed.get("headcount"),
                "description": parsed.get("description", ""),
                "requirements": parsed.get("requirements", []),
            },
        }, message="JD 解析成功")
    except ValueError as e:
        return fail(BizError.VALIDATION_ERROR, str(e))
    except Exception as e:
        return fail(BizError.PARSE_FAILED, f"JD 解析失败: {e}")


@router.post("/parse-jd-text", summary="解析 JD 文本", response_model=None)
async def parse_jd_text(
    payload: dict,
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER")),
):
    """解析 JD 纯文本, 返回结构化字段 + 技能要求 (复用 doc_parser.parse_job)

    注意: AI 调用是同步阻塞操作, 必须放到线程池执行, 否则会阻塞 FastAPI 事件循环
    导致其他请求 (包括健康检查、静态资源) 全部卡住, 表现为前端请求 pending。
    """
    text = (payload.get("text") or "").strip()
    if not text:
        return fail(BizError.VALIDATION_ERROR, "JD 文本不能为空")
    try:
        # AI 调用放到线程池, 避免阻塞事件循环 (与 upload_jd 保持一致)
        parsed = await asyncio.to_thread(doc_parser.parse_job, text)
        return success(data={
            "raw_text": text[:2000],
            "parsed": {
                "title": parsed.get("title", ""),
                "company": parsed.get("company", ""),
                "department": parsed.get("department", ""),
                "job_type": parsed.get("job_type", ""),
                "work_city": parsed.get("work_city", ""),
                "experience_required": parsed.get("experience_required", ""),
                "education_required": parsed.get("education_required", ""),
                "salary_min": parsed.get("salary_min"),
                "salary_max": parsed.get("salary_max"),
                "headcount": parsed.get("headcount"),
                "description": parsed.get("description", ""),
                "requirements": parsed.get("requirements", []),
            },
        }, message="JD 解析成功")
    except ValueError as e:
        return fail(BizError.VALIDATION_ERROR, str(e))
    except Exception as e:
        return fail(BizError.PARSE_FAILED, f"JD 解析失败: {e}")


@router.post("", summary="创建职位 (支持 JD 解析)", response_model=None)
def create_job(
    req: JobCreateRequest,
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER")),
    db: Session = Depends(get_db),
):
    """创建职位, 若提供 parse_text 则用豆包模型解析 JD"""
    try:
        data = req.model_dump(exclude_none=False)
        job = job_service.create(data, current_user.id, db)
        return success(
            data={"job_id": job.id, "title": job.title},
            message="职位创建成功",
        )
    except ValueError as e:
        return fail(BizError.VALIDATION_ERROR, str(e))
    except Exception as e:
        return fail(BizError.SYSTEM_ERROR, f"创建失败: {e}")


@router.get("", summary="我的职位列表", response_model=None)
async def list_my_jobs(
    keyword: str = Query("", description="搜索职位名称"),
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER")),
    db: Session = Depends(get_db),
):
    """企业发布的职位列表 (含投递数统计, 支持关键词搜索)"""
    stmt = select(Job).where(Job.user_id == current_user.id)
    if keyword:
        stmt = stmt.where(Job.title.contains(keyword))
    items = list(db.execute(stmt.order_by(Job.created_at.desc())).scalars())

    if not items:
        return success(data={"items": [], "total": 0})

    # 批量查询各职位投递数
    job_ids = [j.id for j in items]
    app_rows = db.execute(
        select(JobApplication.job_id, func.count()).where(
            JobApplication.job_id.in_(job_ids)
        ).group_by(JobApplication.job_id)
    ).all()
    app_count_map = {jid: cnt for jid, cnt in app_rows}

    data = [
        {
            "id": j.id,
            "title": j.title,
            "company": j.company,
            "work_city": j.work_city,
            "salary_min": j.salary_min,
            "salary_max": j.salary_max,
            "experience_required": j.experience_required,
            "education_required": j.education_required,
            "status": j.status,
            "headcount": j.headcount,
            "application_count": app_count_map.get(j.id, 0),
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }
        for j in items
    ]
    return success(data={"items": data, "total": len(data)})


@router.get("/plaza", summary="职位广场 (公开)", response_model=None)
async def job_plaza(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    keyword: str = Query(""),
    city: str = Query(""),
    job_type: str = Query(""),
    experience: str = Query(""),
    education: str = Query(""),
    salary_min: int | None = Query(None, ge=0),
    salary_max: int | None = Query(None, ge=0),
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """职位广场 (所有招聘中职位, 分页, 支持多条件筛选)"""
    result = job_service.list_public(
        db, page=page, size=size, keyword=keyword,
        city=city, job_type=job_type, experience=experience,
        education=education, salary_min=salary_min, salary_max=salary_max,
    )
    data = {
        "items": [
            {
                "id": j.id,
                "title": j.title,
                "company": j.company,
                "work_city": j.work_city,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "job_type": j.job_type,
                "experience_required": j.experience_required,
                "education_required": j.education_required,
                "description": (j.description or "")[:200],
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in result["items"]
        ],
        "total": result["total"],
        "page": result["page"],
        "size": result["size"],
    }
    return success(data=data)


@router.get("/favorites", summary="我的收藏列表", response_model=None)
async def list_favorites(
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """查询当前用户收藏的职位列表"""
    rows = db.execute(
        select(Favorite, Job)
        .join(Job, Favorite.job_id == Job.id)
        .where(Favorite.user_id == current_user.id)
        .order_by(Favorite.created_at.desc())
    ).all()
    items = [
        {
            "id": fav.id,
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "work_city": job.work_city,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "job_type": job.job_type,
            "experience_required": job.experience_required,
            "education_required": job.education_required,
            "status": job.status,
            "created_at": fav.created_at.isoformat() if fav.created_at else None,
        }
        for fav, job in rows
    ]
    return success(data={"items": items, "total": len(items)})


@router.get("/{job_id}", summary="职位详情", response_model=None)
async def get_job(
    job_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """职位详情 (含技能要求)"""
    try:
        job = job_service.get_detail(job_id, db)
        data = {
            "id": job.id,
            "user_id": job.user_id,
            "title": job.title,
            "company": job.company,
            "department": job.department,
            "job_type": job.job_type,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "salary_unit": job.salary_unit,
            "work_city": job.work_city,
            "experience_required": job.experience_required,
            "education_required": job.education_required,
            "headcount": job.headcount,
            "status": job.status,
            "description": job.description,
            "requirements": [
                {
                    "id": r.id,
                    "skill_name": r.skill_name,
                    "skill_level": r.skill_level,
                    "req_type": r.req_type,
                    "weight": r.weight,
                }
                for r in job.requirements
            ],
            "created_at": job.created_at.isoformat() if job.created_at else None,
        }
        return success(data=data)
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))


@router.delete("/{job_id}", summary="删除职位", response_model=None)
async def delete_job(
    job_id: int,
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER")),
    db: Session = Depends(get_db),
):
    """删除职位 (仅本人)"""
    try:
        job_service.delete(job_id, current_user.id, db)
        return success(message="删除成功")
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))


@router.patch("/{job_id}/status", summary="更新职位状态", response_model=None)
async def update_job_status(
    job_id: int,
    status: int = Query(..., ge=0, le=2, description="0=下架 1=招聘中 2=草稿"),
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER")),
    db: Session = Depends(get_db),
):
    """更新职位状态"""
    try:
        job = job_service.update_status(job_id, status, current_user.id, db)
        return success(data={"job_id": job.id, "status": job.status}, message="状态更新成功")
    except ValueError as e:
        return fail(BizError.RESOURCE_NOT_FOUND, str(e))


@router.post("/{job_id}/favorite", summary="收藏职位", response_model=None)
async def add_favorite(
    job_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """收藏职位 (已收藏则直接返回成功)"""
    job = db.get(Job, job_id)
    if job is None:
        return fail(BizError.RESOURCE_NOT_FOUND, "职位不存在")
    existing = db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.job_id == job_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        return success(message="已收藏")
    try:
        fav = Favorite(user_id=current_user.id, job_id=job_id)
        db.add(fav)
        db.commit()
        db.refresh(fav)
        return success(data={"id": fav.id, "job_id": job_id}, message="收藏成功")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"收藏失败: {e}")


@router.delete("/{job_id}/favorite", summary="取消收藏", response_model=None)
async def remove_favorite(
    job_id: int,
    current_user: SysUser = Depends(require_role("ROLE_SEEKER")),
    db: Session = Depends(get_db),
):
    """取消收藏 (不存在也算成功)"""
    fav = db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.job_id == job_id,
        )
    ).scalar_one_or_none()
    if fav is not None:
        db.delete(fav)
        db.commit()
    return success(message="已取消收藏")
