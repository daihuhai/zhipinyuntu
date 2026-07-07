"""简历相关 Schema"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SkillItem(BaseModel):
    name: str
    level: Optional[str] = None


class ResumeUploadResponse(BaseModel):
    resume_id: int
    parse_status: int
    message: str


class ResumeSkillOut(BaseModel):
    id: int
    skill_name: str
    skill_level: Optional[str] = None
    weight: float = 0.6

    class Config:
        from_attributes = True


class ResumeDetail(BaseModel):
    id: int
    user_id: int
    doc_url: str
    parse_status: int
    parse_error: Optional[str] = None
    name: Optional[str] = None
    gender: Optional[str] = None
    age: Optional[int] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    current_city: Optional[str] = None
    intention_cities: Optional[str] = None
    education: Optional[str] = None
    school: Optional[str] = None
    major: Optional[str] = None
    work_years: Optional[int] = None
    expected_salary_min: Optional[int] = None
    expected_salary_max: Optional[int] = None
    self_evaluation: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ResumeDetailWithSkills(ResumeDetail):
    skills: list[ResumeSkillOut] = []


class ResumeListItem(BaseModel):
    id: int
    name: Optional[str] = None
    parse_status: int
    current_city: Optional[str] = None
    education: Optional[str] = None
    work_years: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True
