"""
知识图谱路由
- GET /graph/resume/{id}  简历能力图谱
- GET /graph/skill/{name} 技能关联图谱
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.base import get_db
from app.models.user import SysUser
from app.schemas.common import success
from app.services.graph_service import graph_service

router = APIRouter(prefix="/graph", tags=["知识图谱"])


@router.get("/resume/{resume_id}", summary="简历能力图谱", response_model=None)
async def resume_graph(
    resume_id: int,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取简历能力图谱 (Person-Skill 节点与边)"""
    # 优先用 Neo4j, 不可用时降级到关系数据库
    data = graph_service.get_resume_graph(resume_id)
    if data.get("degraded"):
        data = graph_service.get_resume_graph_fallback(resume_id, db)
    return success(data=data)


@router.get("/skill/{skill_name}", summary="技能关联图谱", response_model=None)
async def skill_graph(
    skill_name: str,
    current_user: SysUser = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """获取技能关联图谱 (涉及该技能的人/职位)"""
    data = graph_service.get_skill_graph(skill_name)
    return success(data=data)
