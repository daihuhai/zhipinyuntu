"""反馈相关 Schema"""
from typing import Optional
from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    """提交反馈"""
    type: str = Field(default="feature", description="反馈类型: bug/feature/other")
    title: str = Field(..., min_length=2, max_length=128, description="反馈标题")
    content: str = Field(..., min_length=5, max_length=2000, description="反馈内容")


class FeedbackReply(BaseModel):
    """管理员回复"""
    status: str = Field(..., description="处理状态: processing/resolved")
    reply: Optional[str] = Field(None, max_length=2000, description="回复内容")