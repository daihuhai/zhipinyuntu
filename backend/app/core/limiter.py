"""
速率限制器 (防暴力登录/注册/匹配/上传)

独立模块, 避免 app.main 与 app.api.v1.* 之间的循环导入
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

# 全局速率限制器单例
limiter = Limiter(key_func=get_remote_address)
