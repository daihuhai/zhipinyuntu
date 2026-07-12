"""企业资质认证路由"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.core.deps import require_role
from app.db.base import get_db
from app.models.user import SysUser
from app.models.license import BusinessLicense
from app.schemas.common import success, fail, BizError

router = APIRouter(prefix="/licenses", tags=["企业资质认证"])
admin_router = APIRouter(prefix="/admin/licenses", tags=["资质审核"], dependencies=[Depends(require_role("ROLE_ADMIN"))])


class LicenseApplyRequest(BaseModel):
    company_name: str
    credit_code: str
    license_image: str


class LicenseAuditRequest(BaseModel):
    status: int  # 1=通过 2=拒绝
    audit_remark: str | None = None


@router.post("/apply", summary="企业提交认证申请", response_model=None)
async def apply_license(
    req: LicenseApplyRequest,
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """企业提交营业执照认证申请"""
    # 校验是否已申请
    existing = db.execute(
        select(BusinessLicense).where(BusinessLicense.user_id == current_user.id)
    ).scalar_one_or_none()
    if existing:
        return fail(BizError.VALIDATION_ERROR, "已提交过认证申请, 请等待审核")

    if not req.company_name.strip():
        return fail(BizError.VALIDATION_ERROR, "企业名称不能为空")
    if not req.credit_code.strip():
        return fail(BizError.VALIDATION_ERROR, "信用代码不能为空")
    if not req.license_image.strip():
        return fail(BizError.VALIDATION_ERROR, "营业执照图片不能为空")

    try:
        license = BusinessLicense(
            user_id=current_user.id,
            company_name=req.company_name.strip(),
            credit_code=req.credit_code.strip(),
            license_image=req.license_image.strip(),
            status=0,
        )
        db.add(license)
        db.commit()
        db.refresh(license)
        return success(data={"id": license.id}, message="认证申请已提交, 请等待审核")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"提交失败: {e}")


@router.get("/status", summary="企业查看认证状态", response_model=None)
async def license_status(
    current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """企业查看资质认证状态"""
    lic = db.execute(
        select(BusinessLicense).where(BusinessLicense.user_id == current_user.id)
    ).scalar_one_or_none()
    if not lic:
        return success(data=None, message="暂未提交认证")
    return success(data={
        "id": lic.id,
        "company_name": lic.company_name,
        "credit_code": lic.credit_code,
        "license_image": lic.license_image,
        "status": lic.status,
        "audit_remark": lic.audit_remark,
        "created_at": lic.created_at.isoformat() if lic.created_at else None,
    })


@admin_router.get("", summary="管理员查看认证列表", response_model=None)
async def admin_license_list(
    status: int | None = Query(None, description="按状态筛选 0=待审核 1=通过 2=拒绝"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """管理员查看所有企业认证申请"""
    stmt = select(BusinessLicense)
    if status is not None:
        stmt = stmt.where(BusinessLicense.status == status)
    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()
    rows = db.execute(stmt.order_by(BusinessLicense.created_at.desc()).offset((page - 1) * size).limit(size)).scalars().all()

    items = []
    for lic in rows:
        user = db.get(SysUser, lic.user_id)
        items.append({
            "id": lic.id,
            "user_id": lic.user_id,
            "username": user.username if user else None,
            "company_name": lic.company_name,
            "credit_code": lic.credit_code,
            "license_image": lic.license_image,
            "status": lic.status,
            "audit_remark": lic.audit_remark,
            "created_at": lic.created_at.isoformat() if lic.created_at else None,
        })
    return success(data={"items": items, "total": total, "page": page, "size": size})


@admin_router.post("/{license_id}/audit", summary="管理员审核认证", response_model=None)
async def audit_license(
    license_id: int,
    req: LicenseAuditRequest,
    current_user: SysUser = Depends(require_role("ROLE_ADMIN")),
    db: Session = Depends(get_db),
):
    """管理员审核企业资质认证 (通过/拒绝)"""
    if req.status not in (1, 2):
        return fail(BizError.VALIDATION_ERROR, "审核状态只能为 1=通过 或 2=拒绝")

    lic = db.get(BusinessLicense, license_id)
    if not lic:
        return fail(BizError.RESOURCE_NOT_FOUND, "认证申请不存在")
    if lic.status != 0:
        return fail(BizError.VALIDATION_ERROR, "该申请已审核")

    try:
        lic.status = req.status
        lic.audit_remark = req.audit_remark
        db.commit()
        return success(message="审核完成")
    except Exception as e:
        db.rollback()
        return fail(BizError.SYSTEM_ERROR, f"审核失败: {e}")