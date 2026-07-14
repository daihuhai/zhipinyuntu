"""
知识图谱服务 (NebulaGraph)
- 构建人才能力图谱: Person -[HAS_SKILL]-> Skill
- 构建职位图谱: Job -[REQUIRES]-> Skill
- 构建匹配关系: Person -[MATCHED]-> Job
- 图谱查询: 邻居/路径/中心度
- 无 NebulaGraph 时优雅降级, 返回结构化数据供前端展示
"""
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.nebula_client import nebula_client
from app.models.job import Job, JobRequirement
from app.models.resume import Resume, ResumeSkill
from app.models.skill import SkillDict
from app.models.user import SysUser


def _escape(s: str) -> str:
    """转义 nGQL 字符串中的特殊字符"""
    return (s or "").replace("\\", "\\\\").replace('"', '\\"')


class GraphService:
    """知识图谱服务"""

    # ===== 图谱构建 (nGQL DML) =====
    def upsert_person(self, resume: Resume, user: SysUser) -> None:
        """创建/更新 Person 节点 + HAS_SKILL 关系"""
        if not nebula_client.available:
            return
        vid = f"person_{resume.id}"
        name = _escape(resume.name or user.nickname or user.username)
        role = _escape(user.role or "")
        education = _escape(resume.education or "")
        work_years = resume.work_years or 0
        city = _escape(resume.current_city or "")

        # UPSERT Person 顶点
        ngql = (
            f'INSERT VERTEX IF NOT EXISTS Person(name, role, education, work_years, city) '
            f'VALUES "{vid}":("{name}", "{role}", "{education}", {work_years}, "{city}");'
        )
        nebula_client.execute(ngql)

        # 逐条 UPSERT Skill 顶点 + HAS_SKILL 边
        for sk in resume.skills:
            sk_name = _escape(sk.skill_name)
            sk_vid = f"skill_{sk_name}"
            sk_level = _escape(sk.skill_level or "")
            sk_weight = sk.weight or 0.6

            nebula_client.execute(
                f'INSERT VERTEX IF NOT EXISTS Skill(name, category) '
                f'VALUES "{sk_vid}":("{sk_name}", "");'
            )
            nebula_client.execute(
                f'INSERT EDGE IF NOT EXISTS HAS_SKILL(level, weight) '
                f'VALUES "{vid}" -> "{sk_vid}":("{sk_level}", {sk_weight});'
            )

    def upsert_job(self, job: Job, user: SysUser) -> None:
        """创建/更新 Job 节点 + REQUIRES 关系"""
        if not nebula_client.available:
            return
        vid = f"job_{job.id}"
        title = _escape(job.title or "")
        company = _escape(job.company or user.nickname or "")
        city = _escape(job.work_city or "")
        salary_min = job.salary_min or 0
        salary_max = job.salary_max or 0

        # UPSERT Job 顶点
        ngql = (
            f'INSERT VERTEX IF NOT EXISTS Job(title, company, city, salary_min, salary_max) '
            f'VALUES "{vid}":("{title}", "{company}", "{city}", {salary_min}, {salary_max});'
        )
        nebula_client.execute(ngql)

        # 逐条 UPSERT Skill + REQUIRES 边
        for req in job.requirements:
            req_name = _escape(req.skill_name)
            sk_vid = f"skill_{req_name}"
            req_level = _escape(req.skill_level or "")
            req_type = _escape(req.req_type or "")
            req_weight = req.weight or 0.6

            nebula_client.execute(
                f'INSERT VERTEX IF NOT EXISTS Skill(name, category) '
                f'VALUES "{sk_vid}":("{req_name}", "");'
            )
            nebula_client.execute(
                f'INSERT EDGE IF NOT EXISTS REQUIRES(level, req_type, weight) '
                f'VALUES "{vid}" -> "{sk_vid}":("{req_level}", "{req_type}", {req_weight});'
            )

    def add_match_edge(self, resume_id: int, job_id: int, score: float) -> None:
        """创建 Person -[MATCHED]-> Job 关系"""
        if not nebula_client.available:
            return
        src = f"person_{resume_id}"
        dst = f"job_{job_id}"
        nebula_client.execute(
            f'INSERT EDGE IF NOT EXISTS MATCHED(score) '
            f'VALUES "{src}" -> "{dst}":({score});'
        )

    # ===== 图谱查询 (供前端可视化) =====
    def get_resume_graph(self, resume_id: int) -> dict[str, Any]:
        """获取简历能力图谱 (中心=Person, 邻居=Skill)"""
        if nebula_client.available:
            vid = f"person_{resume_id}"
            ngql = (
                f'MATCH (v:Person)-[e:HAS_SKILL]->(v2:Skill) '
                f'WHERE id(v) == "{vid}" '
                f'RETURN v, e, v2;'
            )
            result = nebula_client.execute(ngql)
            rows = result.to_dicts()
            if rows:
                return self._format_graph(rows)
        return {"nodes": [], "edges": [], "degraded": True}

    def get_job_graph(self, job_id: int) -> dict[str, Any]:
        """获取职位能力图谱 (中心=Job, 邻居=Skill)"""
        if nebula_client.available:
            vid = f"job_{job_id}"
            ngql = (
                f'MATCH (v:Job)-[e:REQUIRES]->(v2:Skill) '
                f'WHERE id(v) == "{vid}" '
                f'RETURN v, e, v2;'
            )
            result = nebula_client.execute(ngql)
            rows = result.to_dicts()
            if rows:
                return self._format_graph(rows)
        return {"nodes": [], "edges": [], "degraded": True}

    def get_skill_graph(self, skill_name: str) -> dict[str, Any]:
        """获取技能关联图谱 (哪些人/职位涉及该技能)"""
        if nebula_client.available:
            sk_vid = f"skill_{_escape(skill_name)}"
            # 查询与该技能相关的所有关系和节点
            ngql = (
                f'MATCH (v)-[e]-(v2:Skill) '
                f'WHERE id(v2) == "{sk_vid}" '
                f'RETURN v, e, v2 '
                f'LIMIT 50;'
            )
            result = nebula_client.execute(ngql)
            rows = result.to_dicts()
            if rows:
                return self._format_graph(rows)
        return {"nodes": [], "edges": [], "degraded": True}

    def _format_graph(self, rows: list[dict]) -> dict[str, Any]:
        """格式化 NebulaGraph 查询结果为 {nodes, edges}"""
        nodes: dict[str, dict] = {}
        edges: list[dict] = []

        for row in rows:
            for key in ("v", "v2"):
                vertex = row.get(key)
                if vertex and isinstance(vertex, dict) and vertex.get("vid"):
                    vid = vertex["vid"]
                    if vid not in nodes:
                        tags = vertex.get("tags", [])
                        node_type = tags[0] if tags else "Unknown"
                        props = vertex.get("props", {})

                        if node_type == "Job":
                            label = props.get("title") or f"职位#{vid}"
                        elif node_type == "Person":
                            label = props.get("name") or f"求职者#{vid}"
                        elif node_type == "Skill":
                            label = props.get("name") or vid
                        else:
                            label = props.get("name") or vid

                        nodes[vid] = {
                            "id": vid,
                            "label": label,
                            "type": node_type,
                            "properties": props,
                        }

            edge = row.get("e")
            if edge and isinstance(edge, dict):
                src = edge.get("src", "")
                dst = edge.get("dst", "")
                etype = edge.get("edge_name", "")
                eprops = edge.get("props", {})
                edges.append({
                    "source": src,
                    "target": dst,
                    "label": etype,
                    **eprops,
                })

        return {"nodes": list(nodes.values()), "edges": edges, "degraded": False}

    # ===== 降级模式: 从关系数据库构建图谱数据 =====
    def get_resume_graph_fallback(self, resume_id: int, db: Session) -> dict[str, Any]:
        """从关系数据库构建简历能力图谱 (NebulaGraph 不可用时), 带技能分类层级"""
        resume = db.get(Resume, resume_id)
        if not resume:
            return {"nodes": [], "edges": []}
        nodes = [{
            "id": f"resume_{resume.id}",
            "label": resume.name or f"简历#{resume.id}",
            "type": "Person",
            "properties": {
                "education": resume.education,
                "work_years": resume.work_years,
                "city": resume.current_city,
            },
        }]
        edges = []
        # 预加载技能词典分类
        skill_names = [sk.skill_name for sk in resume.skills]
        skill_cats = {}
        if skill_names:
            rows = db.execute(
                select(SkillDict.name, SkillDict.category).where(SkillDict.name.in_(skill_names))
            ).all()
            skill_cats = {r[0]: r[1] for r in rows}
        # 默认分类
        default_cats = {
            "Java": "编程语言", "Python": "编程语言", "C++": "编程语言", "Go": "编程语言",
            "JavaScript": "编程语言", "TypeScript": "编程语言",
            "Spring Boot": "框架", "Django": "框架", "Vue": "框架", "React": "框架",
            "MySQL": "数据库", "PostgreSQL": "数据库", "Redis": "数据库", "MongoDB": "数据库",
            "Kubernetes": "工具", "Docker": "工具", "Git": "工具", "Linux": "工具",
        }
        cat_nodes: dict[str, dict] = {}
        cat_edges_added: set[str] = set()
        for sk in resume.skills:
            cat = skill_cats.get(sk.skill_name) or default_cats.get(sk.skill_name, "其他技能")
            cat_id = f"cat_{cat}"
            if cat_id not in cat_nodes:
                cat_nodes[cat_id] = {"id": cat_id, "label": cat, "type": "Category", "properties": {}}
            sk_id = f"skill_{sk.skill_name}"
            nodes.append({
                "id": sk_id,
                "label": sk.skill_name,
                "type": "Skill",
                "properties": {"level": sk.skill_level},
            })
            if cat_id not in cat_edges_added:
                edges.append({
                    "source": f"resume_{resume.id}",
                    "target": cat_id,
                    "label": "HAS_CATEGORY",
                    "weight": 1.0,
                })
                cat_edges_added.add(cat_id)
            edges.append({
                "source": cat_id,
                "target": sk_id,
                "label": "INCLUDES",
                "weight": sk.weight or 0.6,
            })
        nodes.extend(cat_nodes.values())
        return {"nodes": nodes, "edges": edges, "degraded": True}

    def get_job_graph_fallback(self, job_id: int, db: Session) -> dict[str, Any]:
        """从关系数据库构建职位能力图谱 (中心=Job, 邻居=Skill, 区分必须/优先)"""
        job = db.get(Job, job_id)
        if not job:
            return {"nodes": [], "edges": []}
        nodes = [{
            "id": f"job_{job.id}",
            "label": job.title or f"职位#{job.id}",
            "type": "Job",
            "properties": {
                "company": job.company,
                "city": job.work_city,
                "salary_min": job.salary_min,
                "salary_max": job.salary_max,
            },
        }]
        edges = []
        for req in job.requirements:
            sk_id = f"skill_{req.skill_name}"
            nodes.append({
                "id": sk_id,
                "label": req.skill_name,
                "type": "Skill",
                "properties": {
                    "category": req.req_type,
                    "level": req.skill_level,
                },
            })
            edges.append({
                "source": f"job_{job.id}",
                "target": sk_id,
                "label": "REQUIRES",
                "req_type": req.req_type,
                "weight": req.weight,
            })
        return {"nodes": nodes, "edges": edges, "degraded": True}


graph_service = GraphService()