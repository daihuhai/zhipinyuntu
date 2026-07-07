"""职位相关 Schema"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobRequirementOut(BaseModel):
    id: int
    skill_name: str
    skill_level: Optional[str] = None
    req_type: Optional[str] = None
    weight: float = 1.0

    class Config:
        from_attributes = True


class JobCreateRequest(BaseModel):
    """职位创建请求 (支持手动填写或粘贴 JD 让 AI 解析)"""
    title: str
    company: Optional[str] = None
    department: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_unit: Optional[str] = "K"
    work_city: Optional[str] = None
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    headcount: int = 1
    description: Optional[str] = None
    # 若提供 parse_text, 则用豆包解析 JD 填充以上字段
    parse_text: Optional[str] = None


class JobDetail(BaseModel):
    id: int
    user_id: int
    title: str
    company: Optional[str] = None
    department: Optional[str] = None
    job_type: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_unit: Optional[str] = None
    work_city: Optional[str] = None
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    headcount: int = 1
    status: int = 1
    description: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobDetailWithRequirements(JobDetail):
    requirements: list[JobRequirementOut] = []


class JobListItem(BaseModel):
    id: int
    title: str
    company: Optional[str] = None
    work_city: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    experience_required: Optional[str] = None
    education_required: Optional[str] = None
    status: int = 1
    created_at: datetime

    class Config:
        from_attributes = True
