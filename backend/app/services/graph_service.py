"""
知识图谱服务 (Neo4j)
- 构建人才能力图谱: Person -[HAS_SKILL]-> Skill
- 构建职位图谱: Job -[REQUIRES]-> Skill
- 构建匹配关系: Person -[MATCHED]-> Job
- 图谱查询: 邻居/路径/中心度
- 无 Neo4j 时优雅降级, 返回结构化数据供前端展示
"""
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.neo4j_client import neo4j_client
from app.models.job import Job, JobRequirement
from app.models.resume import Resume, ResumeSkill
from app.models.skill import SkillDict
from app.models.user import SysUser


class GraphService:
    """知识图谱服务"""

    # ===== 图谱构建 (Cyper 写入) =====
    def upsert_person(self, resume: Resume, user: SysUser) -> None:
        """创建/更新 Person 节点 + HAS_SKILL 关系"""
        if not neo4j_client.available:
            return
        cypher = """
        MERGE (p:Person {id: $id})
        SET p.name = $name, p.role = $role,
            p.education = $education, p.work_years = $work_years,
            p.city = $city
        WITH p
        UNWIND $skills AS sk
        MERGE (s:Skill {name: sk.name})
        SET s.category = sk.category
        MERGE (p)-[r:HAS_SKILL]->(s)
        SET r.level = sk.level, r.weight = sk.weight
        """
        skills = [{"name": s.skill_name, "level": s.skill_level, "weight": s.weight, "category": None} for s in resume.skills]
        neo4j_client.run(cypher, {
            "id": resume.id,
            "name": resume.name or user.nickname or user.username,
            "role": user.role,
            "education": resume.education,
            "work_years": resume.work_years,
            "city": resume.current_city,
            "skills": skills,
        })

    def upsert_job(self, job: Job, user: SysUser) -> None:
        """创建/更新 Job 节点 + REQUIRES 关系"""
        if not neo4j_client.available:
            return
        cypher = """
        MERGE (j:Job {id: $id})
        SET j.title = $title, j.company = $company,
            j.city = $city, j.salary_min = $salary_min, j.salary_max = $salary_max
        WITH j
        UNWIND $reqs AS rq
        MERGE (s:Skill {name: rq.name})
        MERGE (j)-[r:REQUIRES]->(s)
        SET r.level = rq.level, r.req_type = rq.req_type, r.weight = rq.weight
        """
        reqs = [{"name": r.skill_name, "level": r.skill_level, "req_type": r.req_type, "weight": r.weight} for r in job.requirements]
        neo4j_client.run(cypher, {
            "id": job.id,
            "title": job.title,
            "company": job.company or user.nickname,
            "city": job.work_city,
            "salary_min": job.salary_min,
            "salary_max": job.salary_max,
            "reqs": reqs,
        })

    def add_match_edge(self, resume_id: int, job_id: int, score: float) -> None:
        """创建 Person -[MATCHED]-> Job 关系"""
        if not neo4j_client.available:
            return
        cypher = """
        MATCH (p:Person {id: $rid}), (j:Job {id: $jid})
        MERGE (p)-[m:MATCHED]->(j)
        SET m.score = $score
        """
        neo4j_client.run(cypher, {"rid": resume_id, "jid": job_id, "score": score})

    # ===== 图谱查询 (供前端可视化) =====
    def get_resume_graph(self, resume_id: int) -> dict[str, Any]:
        """获取简历能力图谱 (中心=Person, 邻居=Skill)"""
        if neo4j_client.available:
            cypher = """
            MATCH (p:Person {id: $id})-[r:HAS_SKILL]->(s:Skill)
            RETURN p, r, s
            """
            rows = neo4j_client.run(cypher, {"id": resume_id})
            if rows:
                return self._format_graph(rows, center_type="Person")
        # 降级: 从关系数据库读取
        return {"nodes": [], "edges": [], "degraded": True}

    def get_job_graph(self, job_id: int) -> dict[str, Any]:
        """获取职位能力图谱 (中心=Job, 邻居=Skill)"""
        if neo4j_client.available:
            cypher = """
            MATCH (j:Job {id: $id})-[r:REQUIRES]->(s:Skill)
            RETURN j, r, s
            """
            rows = neo4j_client.run(cypher, {"id": job_id})
            if rows:
                return self._format_graph(rows, center_type="Job")
        # 降级: 从关系数据库读取
        return {"nodes": [], "edges": [], "degraded": True}

    def get_skill_graph(self, skill_name: str) -> dict[str, Any]:
        """获取技能关联图谱 (哪些人/职位涉及该技能)"""
        if neo4j_client.available:
            cypher = """
            MATCH (n)-[r]-(s:Skill {name: $name})
            RETURN n, r, s, labels(n) AS labels
            LIMIT 50
            """
            rows = neo4j_client.run(cypher, {"name": skill_name})
            if rows:
                return self._format_graph(rows, center_type="Skill")
        return {"nodes": [], "edges": [], "degraded": True}

    def _format_graph(self, rows: list[dict], center_type: str) -> dict[str, Any]:
        """格式化图谱查询结果为 {nodes, edges}"""
        nodes: dict[str, dict] = {}
        edges: list[dict] = []
        for row in rows:
            for key in ["p", "j", "s", "n"]:
                node = row.get(key)
                if node and "id" in node:
                    node_id = f"{node.element_id}"
                    if node_id not in nodes:
                        labels = list(node.labels) if hasattr(node, "labels") else [key.upper()]
                        node_type = labels[0] if labels else key
                        # 根据节点类型提取可读标签 (避免显示 job_56 等内部ID)
                        props = dict(node)
                        if node_type == "Job":
                            label = props.get("title") or props.get("name") or f"职位#{props.get('id', '')}"
                        elif node_type == "Person":
                            label = props.get("name") or props.get("title") or f"求职者#{props.get('id', '')}"
                        elif node_type == "Skill":
                            label = props.get("name") or f"技能#{props.get('id', '')}"
                        elif node_type == "Category":
                            label = props.get("name") or f"分类#{props.get('id', '')}"
                        else:
                            label = props.get("name") or props.get("title") or str(props.get("id", ""))
                        nodes[node_id] = {
                            "id": node_id,
                            "label": label,
                            "type": node_type,
                            "properties": props,
                        }
        return {"nodes": list(nodes.values()), "edges": edges, "degraded": False}

    # ===== 降级模式: 从关系数据库构建图谱数据 =====
    def get_resume_graph_fallback(self, resume_id: int, db: Session) -> dict[str, Any]:
        """从关系数据库构建简历能力图谱 (Neo4j 不可用时), 带技能分类层级"""
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
        # 收集分类节点 (避免重复)
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
            # Person → Category (去重)
            if cat_id not in cat_edges_added:
                edges.append({
                    "source": f"resume_{resume.id}",
                    "target": cat_id,
                    "label": "HAS_CATEGORY",
                    "weight": 1.0,
                })
                cat_edges_added.add(cat_id)
            # Category → Skill
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
