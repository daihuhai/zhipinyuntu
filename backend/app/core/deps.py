"""
FastAPI 依赖注入
- get_current_user: 从 JWT 解析当前用户
- require_role: 角色权限校验
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_token
from app.db.base import get_db
from app.models.user import SysUser
from app.schemas.common import BizError


# Bearer Token 提取器
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> SysUser:
    """从请求头解析 JWT 并返回当前用户"""
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": BizError.UNAUTHORIZED, "message": "未提供认证令牌"},
        )

    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": BizError.TOKEN_INVALID, "message": "令牌无效或已过期"},
        )

    # 校验令牌类型
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": BizError.TOKEN_INVALID, "message": "令牌类型错误"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": BizError.TOKEN_INVALID, "message": "令牌载荷缺失"},
        )

    user = db.get(SysUser, int(user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": BizError.USER_NOT_FOUND, "message": "用户不存在"},
        )

    if user.status != 1:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": BizError.USER_DISABLED, "message": "账号已被禁用"},
        )

    return user


def require_admin(current_user: SysUser = Depends(get_current_user)) -> SysUser:
    """要求管理员角色"""
    if current_user.role != "ROLE_ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": BizError.ROLE_FORBIDDEN, "message": "仅管理员可访问此资源"},
        )
    return current_user


def require_role(*allowed_roles: str):
    """角色权限校验依赖工厂

    用法:
        @router.get("/x", dependencies=[Depends(require_role("ROLE_ADMIN"))])
    """
    def _check(current_user: SysUser = Depends(get_current_user)) -> SysUser:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": BizError.ROLE_FORBIDDEN, "message": "无权访问此资源"},
            )
        return current_user
    return _check
