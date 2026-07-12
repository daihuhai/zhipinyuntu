"""数据模型聚合导出 - 导入所有模型以注册到 Base.metadata"""
from app.models.user import SysUser
from app.models.resume import Resume, ResumeSkill
from app.models.job import Job, JobRequirement
from app.models.skill import SkillDict
from app.models.match import MatchRecord
from app.models.application import JobApplication
from app.models.log import AdminLog
from app.models.message import Message
from app.models.favorite import Favorite
from app.models.interview import Interview
from app.models.license import BusinessLicense
from app.models.subscription import JobSubscription

__all__ = [
    "SysUser",
    "Resume", "ResumeSkill",
    "Job", "JobRequirement",
    "SkillDict",
    "MatchRecord",
    "JobApplication",
    "AdminLog",
    "Message",
    "Favorite",
    "Interview",
    "BusinessLicense",
    "JobSubscription",
]
