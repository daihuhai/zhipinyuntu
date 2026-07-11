"""
职位业务服务
- 创建 (支持豆包解析 JD)
- 列表 / 详情 / 删除
- 公开职位广场 (分页)
"""
import json
from typing import Any

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.ai.ark_client import ark_client
from app.models.job import Job, JobRequirement
from app.models.user import SysUser
from app.schemas.common import BizError
from app.services.doc_parser import doc_parser
from app.services.graph_service import graph_service


class JobService:
    """职位业务"""

    # 技能等级规范化 (兜底大模型返回的长描述)
    _LEVEL_KEYWORDS = [("精通", "精通"), ("熟练", "熟练"), ("掌握", "掌握"), ("了解", "了解")]
    _VALID_LEVELS = {"精通", "熟练", "掌握", "了解"}

    @classmethod
    def _normalize_level(cls, raw: str | None) -> str:
        """将任意 skill_level 文本归一化为 精通/熟练/掌握/了解 之一"""
        if not raw or not isinstance(raw, str):
            return "掌握"
        raw = raw.strip()
        if raw in cls._VALID_LEVELS:
            return raw
        for kw, std in cls._LEVEL_KEYWORDS:
            if kw in raw:
                return std
        return "掌握"

    def create(self, data: dict[str, Any], user_id: int, db: Session) -> Job:
        """创建职位 (若提供 parse_text 则用豆包解析 JD)"""
        parse_text = data.pop("parse_text", None)

        if parse_text and parse_text.strip():
            # 用豆包解析 JD 文本
            parsed = doc_parser.parse_job(parse_text)
            # 用解析结果填充 (用户显式传入的字段优先)
            field_map = [
                "title", "company", "department", "job_type",
                "work_city", "experience_required", "education_required",
                "description",
            ]
            for f in field_map:
                if not data.get(f) and parsed.get(f):
                    data[f] = parsed[f]
            for f in ["salary_min", "salary_max", "headcount"]:
                if data.get(f) is None and parsed.get(f) is not None:
                    data[f] = parsed[f]
            requirements = parsed.get("requirements", [])
        else:
            requirements = data.pop("requirements", []) if "requirements" in data else []

        job = Job(user_id=user_id, **{k: v for k, v in data.items() if v is not None})
        db.add(job)
        db.commit()
        db.refresh(job)

        # 写入技能要求
        if requirements:
            self._save_requirements(job, requirements, db)

        # 存储原始解析 JSON
        if parse_text:
            job.raw_parse_json = json.dumps(parsed, ensure_ascii=False) if parse_text else None
            db.commit()

        # 同步知识图谱 (Neo4j 不可用时静默降级)
        try:
            user = db.get(SysUser, user_id)
            if user:
                graph_service.upsert_job(job, user)
        except Exception:
            pass

        return job

    def _save_requirements(self, job: Job, requirements: list[dict], db: Session) -> None:
        """写入职位技能要求"""
        for req in requirements:
            name = req.get("skill_name") or req.get("name")
            if not name:
                continue
            level = self._normalize_level(req.get("skill_level"))
            req_type = req.get("req_type") or "必须"
            # req_type 字段也做长度兜底 (String(8))
            if len(req_type) > 8:
                req_type = "必须"
            job.requirements.append(
                JobRequirement(
                    skill_name=name.strip()[:64],
                    skill_level=level,
                    req_type=req_type,
                    weight=1.0 if req_type == "必须" else 0.7,
                )
            )
        db.commit()

    def list_by_user(self, user_id: int, db: Session) -> list[Job]:
        """企业发布的职位列表"""
        return list(
            db.execute(
                select(Job)
                .where(Job.user_id == user_id)
                .order_by(Job.created_at.desc())
            ).scalars()
        )

    def list_public(
        self, db: Session, page: int = 1, size: int = 20, keyword: str = "",
        city: str = "", job_type: str = "", experience: str = "",
        education: str = "", salary_min: int | None = None, salary_max: int | None = None,
    ) -> dict:
        """职位广场 (仅招聘中, 支持多条件筛选)"""
        from sqlalchemy import or_
        # 用 func.count() 替代全表加载, 大幅提升性能
        count_stmt = select(func.count(Job.id)).where(Job.status == 1)
        if keyword:
            count_stmt = count_stmt.where(
                or_(Job.title.contains(keyword), Job.company.contains(keyword), Job.work_city.contains(keyword))
            )
        if city:
            count_stmt = count_stmt.where(Job.work_city.contains(city))
        if job_type:
            count_stmt = count_stmt.where(Job.job_type == job_type)
        if experience:
            count_stmt = count_stmt.where(Job.experience_required == experience)
        if education:
            # "最低学历"匹配: 选"本科及以上"返回 本科/硕士/博士及以上 + 不限/空
            edu_order = ["专科及以上", "本科及以上", "硕士及以上", "博士及以上"]
            if education in edu_order:
                idx = edu_order.index(education)
                valid_levels = edu_order[idx:]
                count_stmt = count_stmt.where(
                    or_(
                        Job.education_required.in_(valid_levels),
                        Job.education_required == "不限",
                        Job.education_required == "",
                        Job.education_required.is_(None),
                    )
                )
            else:
                count_stmt = count_stmt.where(Job.education_required == education)
        if salary_min is not None:
            count_stmt = count_stmt.where(Job.salary_max >= salary_min)
        if salary_max is not None:
            count_stmt = count_stmt.where(Job.salary_min <= salary_max)
        total = db.execute(count_stmt).scalar() or 0

        # 数据查询 (用 limit/offset, 避免加载所有列)
        stmt = select(Job).where(Job.status == 1)
        if keyword:
            stmt = stmt.where(
                or_(Job.title.contains(keyword), Job.company.contains(keyword), Job.work_city.contains(keyword))
            )
        if city:
            stmt = stmt.where(Job.work_city.contains(city))
        if job_type:
            stmt = stmt.where(Job.job_type == job_type)
        if experience:
            stmt = stmt.where(Job.experience_required == experience)
        if education:
            edu_order = ["专科及以上", "本科及以上", "硕士及以上", "博士及以上"]
            if education in edu_order:
                idx = edu_order.index(education)
                valid_levels = edu_order[idx:]
                stmt = stmt.where(
                    or_(
                        Job.education_required.in_(valid_levels),
                        Job.education_required == "不限",
                        Job.education_required == "",
                        Job.education_required.is_(None),
                    )
                )
            else:
                stmt = stmt.where(Job.education_required == education)
        if salary_min is not None:
            stmt = stmt.where(Job.salary_max >= salary_min)
        if salary_max is not None:
            stmt = stmt.where(Job.salary_min <= salary_max)
        stmt = stmt.order_by(Job.created_at.desc())

        offset = (page - 1) * size
        items = list(db.execute(stmt.offset(offset).limit(size)).scalars())
        return {"items": items, "total": total, "page": page, "size": size}

    def get_detail(self, job_id: int, db: Session) -> Job:
        """职位详情 (含要求)"""
        job = db.get(Job, job_id)
        if job is None:
            raise ValueError("职位不存在")
        _ = job.requirements  # 触发懒加载
        return job

    def delete(self, job_id: int, user_id: int, db: Session) -> None:
        """删除职位 (仅本人)"""
        job = db.get(Job, job_id)
        if job is None or job.user_id != user_id:
            raise ValueError("职位不存在或无权删除")
        db.delete(job)
        db.commit()

    def update_status(self, job_id: int, status: int, user_id: int, db: Session) -> Job:
        """更新职位状态 (0=下架 1=招聘中 2=草稿)"""
        job = db.get(Job, job_id)
        if job is None or job.user_id != user_id:
            raise ValueError("职位不存在或无权操作")
        job.status = status
        db.commit()
        db.refresh(job)
        return job


job_service = JobService()
