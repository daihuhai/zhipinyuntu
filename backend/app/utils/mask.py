"""
信息脱敏工具
- 手机号脱敏
- 邮箱脱敏
"""
import re


def mask_phone(phone: str | None) -> str | None:
    """手机号脱敏: 13812345678 -> 138****5678"""
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]


def mask_email(email: str | None) -> str | None:
    """邮箱脱敏: zhangsan@qq.com -> z***@qq.com"""
    if not email or "@" not in email:
        return email
    name, domain = email.split("@", 1)
    if len(name) <= 1:
        return name + "***@" + domain
    return name[0] + "***@" + domain
