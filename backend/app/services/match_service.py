"""
智能匹配服务 (M4)
- 召回: Embedding 余弦相似度 Top-N
- 粗排: 多维度规则加权评分 (技能/经验/学历/城市/薪资/项目)
- 精排: 豆包大模型 RERANK 重排 + 生成自然语言依据
- 匹配记录写入 match_record 表 + 同步知识图谱 MATCHED 边

性能优化 (2026-07-07):
- 精排: ThreadPoolExecutor 并发调用 LLM, 10 候选从串行 ~30s 降到并发 ~3s
- 召回: 批量 embed 调用, 缺失向量一次性生成
- 查询: selectinload 预加载 requirements/skills, 消除 N+1
"""
import json
import math
import struct
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from loguru import logger

from app.ai.ark_client import ark_client
from app.ai.prompts import build_rerank_messages, build_batch_rerank_messages
from app.models.job import Job, JobRequirement
from app.models.match import MatchRecord
from app.models.resume import Resume, ResumeSkill
from app.models.application import JobApplication
from app.services.graph_service import graph_service


# 学历权重映射 (学历越高分数越高)
EDU_WEIGHT = {"博士": 5, "硕士": 4, "本科": 3, "大专": 2, "高中": 1, "其他": 0}

# 技能等级权重
LEVEL_WEIGHT = {"精通": 1.0, "熟练": 0.8, "掌握": 0.6, "了解": 0.4}

# 精排并发数 (豆包 LLM)
RERANK_MAX_WORKERS = 8
# 精排候选数 (调用 LLM 的数量, 配合 ARK 并发限流与模型延迟)
RERANK_TOP_N = 4


class MatchService:
    """智能匹配引擎"""

    # embedding 可用性标记 (失败后缓存, 避免重复重试浪费时间)
    _embedding_disabled: bool = False

    # ============ 1. 召回阶段 (Embedding 余弦相似度) ============
    def recall_by_embedding(
        self,
        query_vec: list[float],
        candidates: list[tuple[int, list[float]]],
        top_n: int = 200,
    ) -> list[tuple[int, float]]:
        """基于向量余弦相似度召回 Top-N
        candidates: [(id, vector), ...]
        返回: [(id, similarity), ...] 按相似度降序
        """
        if not query_vec or not candidates:
            return []
        q_norm = math.sqrt(sum(x * x for x in query_vec)) or 1.0
        scored = []
        for cid, vec in candidates:
            if not vec:
                continue
            c_norm = math.sqrt(sum(x * x for x in vec)) or 1.0
            dot = sum(a * b for a, b in zip(query_vec, vec))
            sim = dot / (q_norm * c_norm)
            scored.append((cid, sim))
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    # ============ 2. 粗排阶段 (规则加权多维评分) ============
    def coarse_rank(self, resume: Resume, job: Job) -> dict[str, float]:
        """多维度规则加权评分, 返回各维度分数"""
        skill_score = self._score_skill(resume, job)
        exp_score = self._score_experience(resume, job)
        edu_score = self._score_education(resume, job)
        city_score = self._score_city(resume, job)
        salary_score = self._score_salary(resume, job)
        proj_score = self._score_project(resume)

        # 加权总分 (0-100)
        total = (
            skill_score * 0.35
            + exp_score * 0.20
            + edu_score * 0.10
            + city_score * 0.10
            + salary_score * 0.10
            + proj_score * 0.15
        ) * 100
        return {
            "total": round(total, 2),
            "skill": round(skill_score, 4),
            "experience": round(exp_score, 4),
            "education": round(edu_score, 4),
            "city": round(city_score, 4),
            "salary": round(salary_score, 4),
            "project": round(proj_score, 4),
        }

    def _score_skill(self, resume: Resume, job: Job) -> float:
        """技能匹配度 [0,1]
        - 必须技能命中权重 1.0, 优先技能命中权重 0.7
        - 候选人技能等级权重 (精通=1.0, 熟练=0.8, 掌握=0.6, 了解=0.4)
        """
        reqs: list[JobRequirement] = list(job.requirements)
        if not reqs:
            return 0.5  # 无明确技能要求, 给中等分
        resume_skills = {s.skill_name.lower(): s for s in resume.skills}
        total_weight = 0.0
        matched_weight = 0.0
        for req in reqs:
            req_w = req.weight or (1.0 if req.req_type == "必须" else 0.7)
            total_weight += req_w
            rs = resume_skills.get((req.skill_name or "").lower())
            if rs:
                level_w = LEVEL_WEIGHT.get(rs.skill_level or "掌握", 0.6)
                matched_weight += req_w * level_w
        return matched_weight / total_weight if total_weight > 0 else 0.0

    def _score_experience(self, resume: Resume, job: Job) -> float:
        """经验匹配度 [0,1]"""
        years = resume.work_years or 0
        req = job.experience_required or ""
        # 解析 "3-5年" / "3年以上" / "应届"
        try:
            if "应届" in req:
                return 1.0 if years <= 1 else 0.7
            nums = [int(s) for s in req.replace("年", "").split("-") if s.strip().isdigit()]
            if not nums:
                return min(years / 5, 1.0)
            if len(nums) == 1:
                lower = nums[0]
                return 1.0 if years >= lower else max(years / lower, 0.0)
            lower, upper = nums[0], nums[1]
            if lower <= years <= upper:
                return 1.0
            if years > upper:
                return max(1.0 - (years - upper) * 0.1, 0.5)
            return max(years / lower, 0.0)
        except Exception:
            return 0.5

    def _score_education(self, resume: Resume, job: Job) -> float:
        """学历匹配度 [0,1]"""
        req_edu = job.education_required or ""
        if not req_edu:
            return 0.8
        req_score = 0
        for k, v in EDU_WEIGHT.items():
            if k in req_edu:
                req_score = v
                break
        cand_score = EDU_WEIGHT.get(resume.education or "其他", 0)
        if req_score == 0:
            return 0.8
        return 1.0 if cand_score >= req_score else cand_score / req_score

    def _score_city(self, resume: Resume, job: Job) -> float:
        """城市匹配度 [0,1]"""
        if not job.work_city:
            return 0.8
        if resume.current_city and job.work_city in resume.current_city:
            return 1.0
        # 检查意向城市
        try:
            intentions = json.loads(resume.intention_cities or "[]")
            if isinstance(intentions, list):
                for c in intentions:
                    if job.work_city in str(c):
                        return 1.0
        except Exception:
            pass
        return 0.3

    def _score_salary(self, resume: Resume, job: Job) -> float:
        """薪资匹配度 [0,1]"""
        if not (job.salary_min and job.salary_max):
            return 0.6
        if not (resume.expected_salary_min and resume.expected_salary_max):
            return 0.6
        # 区间重叠度
        overlap = max(0, min(job.salary_max, resume.expected_salary_max) - max(job.salary_min, resume.expected_salary_min))
        union = max(job.salary_max, resume.expected_salary_max) - min(job.salary_min, resume.expected_salary_min)
        return overlap / union if union > 0 else 0.0

    def _score_project(self, resume: Resume) -> float:
        """项目经验丰富度 [0,1]"""
        try:
            raw = json.loads(resume.raw_parse_json or "{}")
            projects = raw.get("projects", [])
            return min(len(projects) / 3, 1.0)
        except Exception:
            return 0.5

    # ============ 3. 精排阶段 (豆包大模型重排, 批量优化) ============
    def _rerank_with_cache(
        self,
        resume: Resume,
        resume_id: int,
        candidates: list[tuple[Job, dict]],
        db: Session,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """精排 (带缓存): 先查 match_record 近期记录, 命中则复用, 未命中才调 LLM"""
        if not candidates:
            return []

        # 取 Top N 候选
        top_candidates = candidates[:RERANK_TOP_N]
        job_ids = [job.id for job, _ in top_candidates]

        # 查询近期缓存 (2 小时内的匹配记录)
        # 注意: SQLite func.now() 返回 UTC 时间, 故用 utcnow() 对齐
        from datetime import datetime, timedelta
        cache_threshold = datetime.utcnow() - timedelta(hours=2)
        cached = db.execute(
            select(MatchRecord).where(
                MatchRecord.resume_id == resume_id,
                MatchRecord.job_id.in_(job_ids),
                MatchRecord.direction == "RESUME_TO_JOB",
                MatchRecord.created_at >= cache_threshold,
            ).order_by(MatchRecord.created_at.desc())
        ).scalars().all()
        # 每个 job_id 取最新一条
        cache_map: dict[int, MatchRecord] = {}
        for rec in cached:
            if rec.job_id not in cache_map:
                cache_map[rec.job_id] = rec

        cached_results: list[dict[str, Any]] = []
        uncached: list[tuple[Job, dict]] = []
        for job, dims in top_candidates:
            rec = cache_map.get(job.id)
            if rec:
                cached_results.append({
                    "job": job,
                    "total_score": rec.total_score,
                    "skill_score": rec.skill_score or 0,
                    "exp_score": rec.exp_score or 0,
                    "edu_score": rec.edu_score or 0,
                    "city_score": rec.city_score or 0,
                    "salary_score": rec.salary_score or 0,
                    "proj_score": rec.proj_score or 0,
                    "match_reason": rec.match_reason or "AI 精排缓存",
                })
            else:
                uncached.append((job, dims))

        if cached_results:
            logger.info(f"精排缓存命中 {len(cached_results)}/{len(top_candidates)}, 调 LLM {len(uncached)} 个")

        # 未命中的调 LLM 精排
        if uncached:
            llm_results = self.fine_rerank(resume, uncached, top_k=top_k)
            cached_results.extend(llm_results)

        cached_results.sort(key=lambda x: x["total_score"], reverse=True)
        return cached_results[:top_k]

    def fine_rerank(
        self,
        resume: Resume,
        candidates: list[tuple[Job, dict]],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """豆包模型精排 (批量调用 LLM, 6 候选合 1 次), 返回 [{job, score, reason, dimensions}, ...]"""
        if not candidates:
            return []

        # 仅对 Top6 调用大模型
        top_candidates = candidates[:RERANK_TOP_N]
        resume_brief = self._resume_brief(resume)
        resume_json = json.dumps(resume_brief, ensure_ascii=False)

        # 尝试批量精排 (1 次 LLM 调用评估所有候选)
        llm_scores: dict[int, tuple[float, str]] = {}
        try:
            jobs_brief = [self._job_brief(job) for job, _ in top_candidates]
            messages = build_batch_rerank_messages(
                resume_json=resume_json,
                jobs_json=json.dumps(jobs_brief, ensure_ascii=False),
            )
            # max_tokens=1024: 6 个候选各 1 句 reason, 约 600 token
            arr = ark_client.chat_json_array(messages, temperature=0.1, max_tokens=1024)
            for item in arr:
                idx = int(item.get("idx", -1))
                if 0 <= idx < len(top_candidates):
                    score = float(item.get("score", top_candidates[idx][1]["total"]))
                    reason = item.get("reason", "")
                    llm_scores[idx] = (score, reason)
            logger.info(f"批量精排成功, {len(llm_scores)}/{len(top_candidates)} 候选已评分")
        except Exception as e:
            logger.warning(f"批量精排失败: {e}, 降级到并发单次精排")

        # 批量结果不完整时, 对缺失的候选用并发单次精排兜底
        missing_idx = [i for i in range(len(top_candidates)) if i not in llm_scores]
        if missing_idx:
            llm_scores.update(self._rerank_concurrent(resume_json, top_candidates, missing_idx))

        # 组装结果 (粗排 0.7 + LLM 0.3)
        results: list[dict[str, Any]] = []
        for idx, (job, dims) in enumerate(top_candidates):
            llm_score, reason = llm_scores.get(idx, (dims["total"], "AI 精排不可用, 使用规则评分"))
            final = dims["total"] * 0.7 + llm_score * 0.3
            results.append({
                "job": job,
                "total_score": round(final, 2),
                "skill_score": dims["skill"],
                "exp_score": dims["experience"],
                "edu_score": dims["education"],
                "city_score": dims["city"],
                "salary_score": dims["salary"],
                "proj_score": dims["project"],
                "match_reason": reason,
            })

        results.sort(key=lambda x: x["total_score"], reverse=True)
        return results[:top_k]

    def _rerank_concurrent(
        self,
        resume_json: str,
        top_candidates: list[tuple[Job, dict]],
        idx_list: list[int],
    ) -> dict[int, tuple[float, str]]:
        """并发单次精排兜底 (批量失败时使用)"""
        def _rerank_one(idx: int) -> tuple[int, float, str]:
            job, dims = top_candidates[idx]
            try:
                job_brief = self._job_brief(job)
                messages = build_rerank_messages(
                    resume_json=resume_json,
                    job_json=json.dumps(job_brief, ensure_ascii=False),
                )
                llm_result = ark_client.chat_json(messages, temperature=0.1, max_tokens=256)
                return idx, float(llm_result.get("score", dims["total"])), llm_result.get("reason", "")
            except Exception as e:
                logger.warning(f"单次精排失败 job_id={job.id}: {e}, 使用粗排分数")
                return idx, dims["total"], "AI 精排不可用, 使用规则评分"

        out: dict[int, tuple[float, str]] = {}
        with ThreadPoolExecutor(max_workers=min(RERANK_MAX_WORKERS, len(idx_list))) as ex:
            futures = {ex.submit(_rerank_one, i): i for i in idx_list}
            for f in as_completed(futures):
                try:
                    idx, score, reason = f.result(timeout=25)
                    out[idx] = (score, reason)
                except Exception as e:
                    idx = futures[f]
                    dims = top_candidates[idx][1]
                    logger.warning(f"单次精排超时 idx={idx}: {e}")
                    out[idx] = (dims["total"], "AI 精排超时, 使用规则评分")
        return out

    def _resume_brief(self, resume: Resume) -> dict:
        return {
            "name": resume.name,
            "education": resume.education,
            "school": resume.school,
            "major": resume.major,
            "work_years": resume.work_years,
            "city": resume.current_city,
            "expected_salary": [resume.expected_salary_min, resume.expected_salary_max],
            "skills": [{"name": s.skill_name, "level": s.skill_level} for s in resume.skills],
            "self_evaluation": (resume.self_evaluation or "")[:200],
        }

    def _job_brief(self, job: Job) -> dict:
        return {
            "title": job.title,
            "company": job.company,
            "city": job.work_city,
            "salary": [job.salary_min, job.salary_max],
            "experience_required": job.experience_required,
            "education_required": job.education_required,
            "requirements": [{"name": r.skill_name, "type": r.req_type} for r in job.requirements],
            "description": (job.description or "")[:200],
        }

    # ============ 4. 主入口: 简历推荐职位 ============
    def recommend_jobs_for_resume(
        self, resume_id: int, db: Session, top_k: int = 10
    ) -> list[dict[str, Any]]:
        """为求职者推荐职位 (召回→粗排→精排)"""
        # selectinload 预加载 skills/requirements, 消除 N+1
        resume = db.execute(
            select(Resume)
            .options(selectinload(Resume.skills))
            .where(Resume.id == resume_id)
        ).scalar_one_or_none()
        if not resume:
            raise ValueError("简历不存在")

        # 1. 获取候选职位 (招聘中, 预加载 requirements)
        jobs = list(db.execute(
            select(Job)
            .options(selectinload(Job.requirements))
            .where(Job.status == 1)
        ).scalars())
        if not jobs:
            return []

        # 2. 召回 (Embedding 相似度 Top200)
        query_vec = self._get_resume_embedding(resume, db)
        candidates_raw = []
        if query_vec:
            # 批量生成缺失的 job embedding
            self._batch_fill_embeddings(jobs, "job", db)
            job_vecs = [(j.id, self._bytes_to_vec(j.embedding) if j.embedding else []) for j in jobs]
            recalled = self.recall_by_embedding(query_vec, job_vecs, top_n=200)
            id_to_job = {j.id: j for j in jobs}
            for jid, sim in recalled:
                if jid in id_to_job:
                    candidates_raw.append((id_to_job[jid], sim))
        else:
            # 无向量, 全量进入粗排
            candidates_raw = [(j, 0.5) for j in jobs]

        # 3. 粗排 (规则加权)
        coarse_results: list[tuple[Job, dict]] = []
        for job, sim in candidates_raw[:200]:
            dims = self.coarse_rank(resume, job)
            dims["semantic"] = sim
            coarse_results.append((job, dims))
        coarse_results.sort(key=lambda x: x[1]["total"], reverse=True)

        # 4. 精排 (先查缓存, 未命中才调 LLM)
        ranked = self._rerank_with_cache(resume, resume_id, coarse_results[:20], db, top_k=top_k)

        # 5. 写入匹配记录 + 同步图谱
        for item in ranked:
            self._save_match_record(
                db, resume_id, item["job"].id, item, direction="RESUME_TO_JOB"
            )
        db.commit()

        return ranked

    # ============ 5. 主入口: 职位推荐候选人 ============
    def recommend_resumes_for_job(
        self, job_id: int, db: Session, top_k: int = 10
    ) -> list[dict[str, Any]]:
        """为企业推荐候选人 (仅从已投递该职位的求职者中选取: 召回→粗排→精排, 带缓存)"""
        job = db.execute(
            select(Job)
            .options(selectinload(Job.requirements))
            .where(Job.id == job_id)
        ).scalar_one_or_none()
        if not job:
            raise ValueError("职位不存在")

        # 候选简历: 仅从已投递该职位的求职者中选取 (关联 resume + 预加载 skills)
        resumes = list(db.execute(
            select(Resume)
            .options(selectinload(Resume.skills))
            .join(JobApplication, JobApplication.resume_id == Resume.id)
            .where(
                JobApplication.job_id == job_id,
                Resume.parse_status == 2,
            )
        ).scalars())
        if not resumes:
            return []

        # 召回 (Embedding 相似度, 仅在有向量时启用; 投递量通常较少, 直接全量进入粗排)
        query_vec = self._get_job_embedding(job, db)
        candidates_raw = []
        if query_vec:
            self._batch_fill_embeddings(resumes, "resume", db)
            r_vecs = [(r.id, self._bytes_to_vec(r.embedding) if r.embedding else []) for r in resumes]
            recalled = self.recall_by_embedding(query_vec, r_vecs, top_n=200)
            id_to_r = {r.id: r for r in resumes}
            for rid, sim in recalled:
                if rid in id_to_r:
                    candidates_raw.append((id_to_r[rid], sim))
        else:
            candidates_raw = [(r, 0.5) for r in resumes]

        # 粗排
        coarse_results: list[tuple[Resume, dict]] = []
        for resume, sim in candidates_raw[:200]:
            dims = self.coarse_rank(resume, job)
            dims["semantic"] = sim
            coarse_results.append((resume, dims))
        coarse_results.sort(key=lambda x: x[1]["total"], reverse=True)

        # 精排 (先查缓存, 未命中才调 LLM)
        results = self._rerank_resumes_with_cache(job, job_id, coarse_results[:10], db, top_k=top_k)

        # 写入记录
        for item in results:
            self._save_match_record(
                db, item["resume"].id, job_id, item, direction="JOB_TO_RESUME"
            )
        db.commit()

        return results

    def _rerank_resumes_with_cache(
        self,
        job: Job,
        job_id: int,
        candidates: list[tuple[Resume, dict]],
        db: Session,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """候选人精排 (带缓存): 先查 match_record 近期记录, 命中则复用, 未命中才调 LLM"""
        if not candidates:
            return []

        top_candidates = candidates[:RERANK_TOP_N]
        resume_ids = [r.id for r, _ in top_candidates]

        # 查询近期缓存 (2 小时内的 JOB_TO_RESUME 记录)
        from datetime import datetime, timedelta
        cache_threshold = datetime.utcnow() - timedelta(hours=2)
        cached = db.execute(
            select(MatchRecord).where(
                MatchRecord.job_id == job_id,
                MatchRecord.resume_id.in_(resume_ids),
                MatchRecord.direction == "JOB_TO_RESUME",
                MatchRecord.created_at >= cache_threshold,
            ).order_by(MatchRecord.created_at.desc())
        ).scalars().all()
        cache_map: dict[int, MatchRecord] = {}
        for rec in cached:
            if rec.resume_id not in cache_map:
                cache_map[rec.resume_id] = rec

        cached_results: list[dict[str, Any]] = []
        uncached: list[tuple[Resume, dict]] = []
        for resume, dims in top_candidates:
            rec = cache_map.get(resume.id)
            if rec:
                cached_results.append({
                    "resume": resume,
                    "total_score": rec.total_score,
                    "skill_score": rec.skill_score or 0,
                    "exp_score": rec.exp_score or 0,
                    "edu_score": rec.edu_score or 0,
                    "city_score": rec.city_score or 0,
                    "salary_score": rec.salary_score or 0,
                    "proj_score": rec.proj_score or 0,
                    "match_reason": rec.match_reason or "AI 精排缓存",
                })
            else:
                uncached.append((resume, dims))

        if cached_results:
            logger.info(f"候选人精排缓存命中 {len(cached_results)}/{len(top_candidates)}, 调 LLM {len(uncached)} 个")

        # 未命中的调 LLM 精排 (带超时控制)
        if uncached:
            llm_results = self._rerank_resumes_concurrent(job, uncached)
            cached_results.extend(llm_results)

        cached_results.sort(key=lambda x: x["total_score"], reverse=True)
        return cached_results[:top_k]

    def _rerank_resumes_concurrent(
        self, job: Job, candidates: list[tuple[Resume, dict]]
    ) -> list[dict[str, Any]]:
        """并发精排候选人 (Top10 同时调用 LLM)"""
        if not candidates:
            return []
        job_brief = self._job_brief(job)
        job_json = json.dumps(job_brief, ensure_ascii=False)

        def _rerank_one(idx: int) -> dict[str, Any]:
            resume, dims = candidates[idx]
            try:
                messages = build_rerank_messages(
                    resume_json=json.dumps(self._resume_brief(resume), ensure_ascii=False),
                    job_json=job_json,
                )
                llm_result = ark_client.chat_json(messages, temperature=0.1)
                llm_score = float(llm_result.get("score", dims["total"]))
                reason = llm_result.get("reason", "")
                final = dims["total"] * 0.7 + llm_score * 0.3
            except Exception as e:
                logger.warning(f"精排失败 resume_id={resume.id}: {e}")
                final = dims["total"]
                reason = "AI 精排不可用, 使用规则评分"
            return {
                "resume": resume,
                "total_score": round(final, 2),
                "skill_score": dims["skill"],
                "exp_score": dims["experience"],
                "edu_score": dims["education"],
                "city_score": dims["city"],
                "salary_score": dims["salary"],
                "proj_score": dims["project"],
                "match_reason": reason,
            }

        results: list[dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=min(RERANK_MAX_WORKERS, len(candidates))) as ex:
            futures = {ex.submit(_rerank_one, i): i for i in range(len(candidates))}
            for f in as_completed(futures):
                try:
                    # 单候选 LLM 调用最多等 25 秒, 避免无限等待导致前端"一直加载"
                    results.append(f.result(timeout=25))
                except Exception as e:
                    idx = futures[f]
                    dims = candidates[idx][1]
                    logger.warning(f"候选人精排超时/失败 idx={idx}: {e}, 使用粗排分数")
                    results.append({
                        "resume": candidates[idx][0],
                        "total_score": round(dims["total"], 2),
                        "skill_score": dims["skill"],
                        "exp_score": dims["experience"],
                        "edu_score": dims["education"],
                        "city_score": dims["city"],
                        "salary_score": dims["salary"],
                        "proj_score": dims["project"],
                        "match_reason": "AI 精排超时, 使用规则评分",
                    })
        results.sort(key=lambda x: x["total_score"], reverse=True)
        return results

    def _batch_fill_embeddings(self, objs: list[Any], kind: str, db: Session) -> None:
        """批量生成缺失的 embedding (一次 API 调用)"""
        if self._embedding_disabled:
            return
        missing = [o for o in objs if not o.embedding]
        if not missing:
            return
        try:
            texts = [self._job_summary(o) if kind == "job" else self._resume_summary(o) for o in missing]
            vectors = ark_client.embed(texts)
            for obj, vec in zip(missing, vectors):
                obj.embedding = self._vec_to_bytes(vec)
            db.commit()
        except Exception as e:
            logger.warning(f"批量生成 {kind} 向量失败 ({len(missing)} 条): {e}, 后续将跳过 embedding 召回")
            self._embedding_disabled = True

    # ============ 辅助方法 ============
    def _get_resume_embedding(self, resume: Resume, db: Session) -> list[float]:
        """获取简历向量, 不存在则生成"""
        if self._embedding_disabled:
            return []
        if resume.embedding:
            return self._bytes_to_vec(resume.embedding)
        try:
            summary = self._resume_summary(resume)
            vec = ark_client.embed([summary])[0]
            resume.embedding = self._vec_to_bytes(vec)
            db.commit()
            return vec
        except Exception as e:
            logger.warning(f"生成简历向量失败: {e}, 后续将跳过 embedding 召回")
            self._embedding_disabled = True
            return []

    def _get_job_embedding(self, job: Job, db: Session) -> list[float]:
        """获取职位向量"""
        if self._embedding_disabled:
            return []
        if job.embedding:
            return self._bytes_to_vec(job.embedding)
        try:
            summary = self._job_summary(job)
            vec = ark_client.embed([summary])[0]
            job.embedding = self._vec_to_bytes(vec)
            db.commit()
            return vec
        except Exception as e:
            logger.warning(f"生成职位向量失败: {e}, 后续将跳过 embedding 召回")
            self._embedding_disabled = True
            return []

    def _resume_summary(self, resume: Resume) -> str:
        parts = [
            f"姓名:{resume.name or ''}",
            f"学历:{resume.education or ''}",
            f"专业:{resume.major or ''}",
            f"工作年限:{resume.work_years or 0}年",
            f"城市:{resume.current_city or ''}",
            f"自我评价:{resume.self_evaluation or ''}",
        ]
        if resume.skills:
            parts.append("技能:" + ", ".join(s.skill_name for s in resume.skills))
        return " ".join(parts)

    def _job_summary(self, job: Job) -> str:
        parts = [
            f"职位:{job.title}",
            f"城市:{job.work_city or ''}",
            f"经验:{job.experience_required or ''}",
            f"学历:{job.education_required or ''}",
            f"薪资:{job.salary_min}-{job.salary_max}K",
            f"描述:{job.description or ''}",
        ]
        if job.requirements:
            parts.append("要求:" + ", ".join(r.skill_name for r in job.requirements))
        return " ".join(parts)

    def _vec_to_bytes(self, vec: list[float]) -> bytes:
        return struct.pack(f"{len(vec)}f", *vec)

    def _bytes_to_vec(self, data: bytes) -> list[float]:
        n = len(data) // 4
        return list(struct.unpack(f"{n}f", data))

    def _save_match_record(
        self,
        db: Session,
        resume_id: int,
        job_id: int,
        item: dict,
        direction: str,
    ) -> None:
        """写入匹配记录 + 同步图谱 MATCHED 边"""
        record = MatchRecord(
            resume_id=resume_id,
            job_id=job_id,
            total_score=item["total_score"],
            skill_score=item.get("skill_score"),
            exp_score=item.get("exp_score"),
            edu_score=item.get("edu_score"),
            city_score=item.get("city_score"),
            proj_score=item.get("proj_score"),
            salary_score=item.get("salary_score"),
            match_reason=item.get("match_reason"),
            direction=direction,
        )
        db.add(record)
        # 同步知识图谱
        try:
            graph_service.add_match_edge(resume_id, job_id, item["total_score"])
        except Exception:
            pass


match_service = MatchService()
