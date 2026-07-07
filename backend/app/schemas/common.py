"""
通用 Pydantic 响应模型
统一 { code, message, data, trace_id } 格式
"""
from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应模型"""
    code: int = Field(default=0, description="业务码: 0=成功, 非0=失败")
    message: str = Field(default="success", description="提示信息")
    data: Optional[T] = None
    trace_id: Optional[str] = None


def success(data: Any = None, message: str = "success") -> dict:
    """构造成功响应"""
    return {"code": 0, "message": message, "data": data}


def fail(code: int, message: str, data: Any = None) -> dict:
    """构造失败响应"""
    return {"code": code, "message": message, "data": data}


# ===== 业务错误码 =====
class BizError:
    """业务错误码常量"""
    USER_EXISTS = 1001
    UNAUTHORIZED = 1002
    USER_NOT_FOUND = 1003
    PASSWORD_ERROR = 1004
    USER_DISABLED = 1005
    TOKEN_EXPIRED = 1006
    TOKEN_INVALID = 1007
    ROLE_FORBIDDEN = 1008
    RESOURCE_NOT_FOUND = 1009
    VALIDATION_ERROR = 1010
    PARSE_FAILED = 1011
    FILE_TOO_LARGE = 1012
    SYSTEM_ERROR = 5000
