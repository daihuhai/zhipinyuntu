"""
简历业务服务
- 上传 + 解析 (同步调用豆包)
- 列表 / 详情 / 删除
- 向量生成 (用于 M4 匹配)
"""
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.ark_client import ark_client
from app.models.resume import Resume, ResumeSkill
from app.models.user import SysUser
from app.schemas.common import BizError
from app.services.doc_parser import doc_parser
from app.services.file_service import file_service
from app.services.graph_service import graph_service


class ResumeService:
    """简历业务"""

    async def upload_and_parse(self, upload, user_id: int, db: Session) -> dict:
        """上传简历并同步解析"""
        # 1. 保存文件
        file_info = await file_service.save(upload, sub_dir="resumes")

        # 2. 创建简历记录 (待解析)
        resume = Resume(
            user_id=user_id,
            doc_url=file_info["url"],
            doc_hash=file_info["hash"],
            parse_status=1,  # 解析中
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)

        # 3. 提取文本 + 豆包结构化 (同步)
        try:
            abs_path = file_info["abs_path"]
            text = doc_parser.extract_text(abs_path)
            parsed = doc_parser.parse_resume(text)

            # 4. 回填结构化字段
            self._fill_resume_fields(resume, parsed)
            resume.parse_status = 2  # 成功
            resume.raw_parse_json = json.dumps(parsed, ensure_ascii=False)

            # 5. 写入技能关联
            self._save_skills(resume, parsed.get("skills", []))

            db.commit()
            db.refresh(resume)

            # 6. 同步知识图谱 (Neo4j 不可用时静默降级)
            try:
                user = db.get(SysUser, user_id)
                if user:
                    graph_service.upsert_person(resume, user)
            except Exception:
                pass  # 图谱同步失败不影响主流程

            return {
                "resume_id": resume.id,
                "parse_status": resume.parse_status,
                "message": "解析成功",
            }
        except Exception as e:
            resume.parse_status = 3  # 失败
            resume.parse_error = str(e)[:500]
            db.commit()
            raise

    def _fill_resume_fields(self, resume: Resume, parsed: dict[str, Any]) -> None:
        """将解析结果填入 Resume 模型"""
        resume.name = parsed.get("name")
        resume.gender = parsed.get("gender")
        resume.age = parsed.get("age")
        resume.phone = parsed.get("phone")
        resume.email = parsed.get("email")
        resume.current_city = parsed.get("current_city")
        cities = parsed.get("intention_cities")
        if isinstance(cities, list):
            resume.intention_cities = json.dumps(cities, ensure_ascii=False)
        elif isinstance(cities, str):
            resume.intention_cities = cities
        resume.education = parsed.get("education")
        resume.school = parsed.get("school")
        resume.major = parsed.get("major")
        resume.work_years = parsed.get("work_years")
        resume.expected_salary_min = parsed.get("expected_salary_min")
        resume.expected_salary_max = parsed.get("expected_salary_max")
        resume.self_evaluation = parsed.get("self_evaluation")

    def _save_skills(self, resume: Resume, skills: list[dict]) -> None:
        """写入简历技能关联 (通过 relationship 自动关联 resume_id)"""
        level_weight = {"精通": 1.0, "熟练": 0.8, "掌握": 0.6, "了解": 0.4}
        for sk in skills:
            name = sk.get("name") or sk.get("skill_name")
            if not name:
                continue
            level = sk.get("level") or sk.get("skill_level")
            resume.skills.append(
                ResumeSkill(
                    skill_name=name.strip(),
                    skill_level=level,
                    weight=level_weight.get(level, 0.6),
                )
            )

    def list_by_user(self, user_id: int, db: Session) -> list[Resume]:
        """查询用户简历列表"""
        return list(
            db.execute(
                select(Resume)
                .where(Resume.user_id == user_id)
                .order_by(Resume.created_at.desc())
            ).scalars()
        )

    def get_detail(self, resume_id: int, db: Session) -> Resume:
        """获取简历详情 (含技能)"""
        resume = db.get(Resume, resume_id)
        if resume is None:
            raise ValueError("简历不存在")
        # 触发懒加载
        _ = resume.skills
        return resume

    def delete(self, resume_id: int, user_id: int, db: Session) -> None:
        """删除简历 (仅本人)"""
        resume = db.get(Resume, resume_id)
        if resume is None or resume.user_id != user_id:
            raise ValueError("简历不存在或无权删除")
        db.delete(resume)
        db.commit()

    def generate_embedding(self, resume_id: int, db: Session) -> None:
        """生成简历向量 (用于 M4 匹配)"""
        resume = db.get(Resume, resume_id)
        if resume is None:
            return
        # 拼接简历摘要文本
        summary = self._resume_to_text(resume)
        vector = ark_client.embed([summary])[0]
        # 向量序列化为 bytes 存储
        import struct

        resume.embedding = struct.pack(f"{len(vector)}f", *vector)
        db.commit()

    def _resume_to_text(self, resume: Resume) -> str:
        """将简历转为向量化的文本摘要"""
        parts = [
            f"姓名:{resume.name or ''}",
            f"学历:{resume.education or ''}",
            f"专业:{resume.major or ''}",
            f"工作年限:{resume.work_years or 0}年",
            f"当前城市:{resume.current_city or ''}",
            f"自我评价:{resume.self_evaluation or ''}",
        ]
        if resume.skills:
            parts.append("技能:" + ", ".join(s.skill_name for s in resume.skills))
        return " ".join(parts)


resume_service = ResumeService()
