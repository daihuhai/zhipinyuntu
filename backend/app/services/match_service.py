"""
智能匹配服务 (M4)
- 召回: Embedding 余弦相似度 Top-N
- 粗排: 多维度规则加权评分 (技能/经验/学历/城市/薪资/项目)
- 精排: 灵犀大模型 RERANK 重排 + 生成自然语言依据
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
EDU_WEIGHT = {"博士": 5, "硕士": 4, "本科": 3, "大专": 2, "专科": 2, "高中": 1, "其他": 0}

# 技能等级权重
LEVEL_WEIGHT = {"精通": 1.0, "熟练": 0.8, "掌握": 0.6, "熟悉": 0.5, "了解": 0.4}

# 主要城市经纬度 (用于城市距离打分)
CITY_COORDS = {
    "北京": (39.90, 116.40), "天津": (39.13, 117.20), "上海": (31.23, 121.47),
    "重庆": (29.56, 106.55), "广州": (23.13, 113.26), "深圳": (22.54, 114.06),
    "成都": (30.57, 104.07), "杭州": (30.27, 120.16), "南京": (32.06, 118.80),
    "武汉": (30.59, 114.31), "西安": (34.34, 108.94), "苏州": (31.30, 120.62),
    "郑州": (34.75, 113.63), "长沙": (28.23, 112.94), "青岛": (36.07, 120.38),
    "大连": (38.91, 121.61), "宁波": (29.87, 121.55), "厦门": (24.48, 118.09),
    "福州": (26.07, 119.30), "无锡": (31.49, 120.31), "合肥": (31.82, 117.23),
    "济南": (36.65, 117.00), "沈阳": (41.80, 123.43), "哈尔滨": (45.80, 126.53),
    "长春": (43.88, 125.32), "石家庄": (38.04, 114.51), "太原": (37.87, 112.55),
    "南昌": (28.68, 115.86), "贵阳": (26.65, 106.63), "昆明": (25.04, 102.71),
    "兰州": (36.06, 103.83), "南宁": (22.82, 108.32), "海口": (20.04, 110.35),
    "珠海": (22.27, 113.58), "佛山": (23.02, 113.12), "东莞": (23.02, 113.75),
    "常州": (31.81, 119.97), "烟台": (37.46, 121.44), "温州": (28.00, 120.67),
    "绍兴": (30.03, 120.58), "嘉兴": (30.75, 120.76), "徐州": (34.26, 117.19),
    "洛阳": (34.62, 112.45), "襄阳": (32.04, 112.14), "宜昌": (30.69, 111.29),
    "绵阳": (31.47, 104.68), "镇江": (32.19, 119.45), "扬州": (32.39, 119.41),
    "南通": (31.98, 120.89), "湖州": (30.89, 120.09), "金华": (29.08, 119.65),
    "台州": (28.66, 121.42), "泉州": (24.87, 118.68), "中山": (22.52, 113.39),
    "惠州": (23.11, 114.42), "唐山": (39.63, 118.18), "保定": (38.87, 115.47),
    "廊坊": (39.54, 116.68), "潍坊": (36.71, 119.16), "淄博": (36.81, 118.05),
    "威海": (37.51, 122.12), "临沂": (35.10, 118.36), "咸阳": (34.33, 108.71),
    "株洲": (27.83, 113.13), "桂林": (25.28, 110.29), "三亚": (18.25, 109.51),
    "乌鲁木齐": (43.83, 87.62), "银川": (38.49, 106.23), "西宁": (36.62, 101.78),
    "拉萨": (29.65, 91.14), "呼和浩特": (40.84, 111.75), "包头": (40.66, 109.84),
}


def _norm_city(name: str) -> str:
    """去掉 市/省 等后缀, 便于匹配坐标表"""
    if not name:
        return ""
    s = str(name).strip()
    for suffix in ("特别行政区", "自治区", "市", "省"):
        if s.endswith(suffix) and len(s) > len(suffix):
            s = s[: -len(suffix)]
    return s


def _haversine_km(a: tuple, b: tuple) -> float:
    """两经纬度点之间的球面距离 (km)"""
    lat1, lon1 = a
    lat2, lon2 = b
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def _city_distance_score(city_a: str, city_b: str) -> float:
    """按两城市距离打分: 同城 1.0, 隔壁市(<=150km) 0.9, 越远越低"""
    ca, cb = _norm_city(city_a), _norm_city(city_b)
    if not ca or not cb:
        return 0.0
    if ca == cb or ca in cb or cb in ca:
        return 1.0
    pa = CITY_COORDS.get(ca)
    pb = CITY_COORDS.get(cb)
    if not pa or not pb:
        return 0.5  # 坐标表未收录的城市给中间分
    d = _haversine_km(pa, pb)
    if d <= 50:
        return 1.0
    if d <= 150:
        return 0.9
    if d <= 300:
        return 0.8
    if d <= 500:
        return 0.7
    if d <= 800:
        return 0.6
    if d <= 1200:
        return 0.5
    return 0.4

# 精排并发数 (灵犀大模型)
RERANK_MAX_WORKERS = 8
# 精排候选数 (调用 LLM 的数量, 配合 ARK 并发限流与模型延迟)
RERANK_TOP_N = 3


class MatchService:
    """智能匹配引擎"""

    # embedding 可用性标记 (失败后缓存, 避免重复重试浪费时间)
    _embedding_disabled: bool = False

    def __init__(self):
        self._rerank_tokens: dict[str, int] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def _add_usage(self, usage: dict[str, int]):
        """累积 token 消耗"""
        for k in self._rerank_tokens:
            self._rerank_tokens[k] += usage.get(k, 0)

    def _reset_usage(self):
        """重置 token 累积器"""
        self._rerank_tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    def get_rerank_usage(self) -> dict[str, int]:
        """获取当前累积的 token 消耗"""
        return dict(self._rerank_tokens)

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
        - 候选人技能等级权重 (精通=1.0, 熟练=0.8, 掌握=0.6, 熟悉=0.5, 了解=0.4)
        - 支持模糊匹配 (包含关系) 和别名归一化
        """
        reqs: list[JobRequirement] = list(job.requirements)
        if not reqs:
            return 0.5  # 无明确技能要求, 给中等分
        resume_skills = {s.skill_name.lower(): s for s in resume.skills}

        # 技能别名归一化映射
        alias_map = {
            "office": ["office办公软件", "office套件", "office", "msoffice", "ms office"],
            "python": ["python", "python3", "py"],
            "java": ["java", "java语言", "jdk"],
            "mysql": ["mysql", "sql", "数据库"],
            "linux": ["linux", "linux系统", "unix"],
            "vue": ["vue", "vue.js", "vuejs"],
            "react": ["react", "react.js", "reactjs"],
            "docker": ["docker", "容器", "容器化"],
            "kubernetes": ["kubernetes", "k8s"],
        }
        # 反向索引: 小写技能名 -> 标准名
        normalize_map = {}
        for std, aliases in alias_map.items():
            for a in aliases:
                normalize_map[a] = std

        def normalize(name: str) -> str:
            n = (name or "").lower().strip()
            return normalize_map.get(n, n)

        total_weight = 0.0
        matched_weight = 0.0
        for req in reqs:
            req_w = req.weight or (1.0 if req.req_type == "必须" else 0.7)
            total_weight += req_w
            req_std = normalize(req.skill_name)

            # 1. 精确匹配
            rs = resume_skills.get((req.skill_name or "").lower())
            # 2. 归一化匹配
            if not rs:
                for sk_name, sk in resume_skills.items():
                    if normalize(sk_name) == req_std:
                        rs = sk
                        break
            # 3. 模糊匹配 (包含关系)
            if not rs:
                req_lower = (req.skill_name or "").lower()
                for sk_name, sk in resume_skills.items():
                    if req_lower in sk_name or sk_name in req_lower:
                        rs = sk
                        break
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
            # 经验越多越好: 达到下限即满分 (含超出上限)
            if years >= lower:
                return 1.0
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
        """城市匹配度 [0,1]

        - 职位未填城市: 1.0 (无城市限制, 视为完全匹配)
        - 简历当前城市/意向城市包含职位城市: 1.0
        - 其他城市: 按与职位城市的地理距离衰减打分 (隔壁市 0.9)
        """
        if not job.work_city:
            return 1.0

        scores = []
        # 当前城市 vs 职位城市
        if resume.current_city:
            scores.append(_city_distance_score(resume.current_city, job.work_city))
        # 意向城市 vs 职位城市
        try:
            intentions = json.loads(resume.intention_cities or "[]")
            if isinstance(intentions, list):
                for c in intentions:
                    scores.append(_city_distance_score(str(c), job.work_city))
        except Exception:
            pass

        if not scores:
            return 0.5  # 简历无城市信息, 给中间分
        return max(scores)

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

    # ============ 3. 精排阶段 (灵犀大模型重排, 批量优化) ============
    def _rerank_with_cache(
        self,
        resume: Resume,
        resume_id: int,
        candidates: list[tuple[Job, dict]],
        db: Session,
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """精排 (带缓存): 先查 match_record 近期记录, 命中则复用, 未命中才调 LLM
        策略: 仅对 Top RERANK_TOP_N 调 LLM 精排 (保速度), 其余用粗排分数填充 (保数量)
        """
        if not candidates:
            return []

        # 取 Top N 候选进行精排 (RERANK_TOP_N=3, 控制 LLM 调用量)
        rerank_candidates = candidates[:RERANK_TOP_N]
        # 保留 Top K 候选 (top_k=10, 保证返回数量)
        display_candidates = candidates[:top_k]
        rerank_job_ids = {job.id for job, _ in rerank_candidates}

        # 查询近期缓存 (2 小时内的匹配记录)
        # 注意: GreatSQL/MySQL func.now() 返回 UTC 时间, 故用 utcnow() 对齐
        from datetime import datetime, timedelta
        cache_threshold = datetime.utcnow() - timedelta(hours=2)
        cached = db.execute(
            select(MatchRecord).where(
                MatchRecord.resume_id == resume_id,
                MatchRecord.job_id.in_(list(rerank_job_ids)),
                MatchRecord.direction == "RESUME_TO_JOB",
                MatchRecord.created_at >= cache_threshold,
            ).order_by(MatchRecord.created_at.desc())
        ).scalars().all()
        # 每个 job_id 取最新一条
        cache_map: dict[int, MatchRecord] = {}
        for rec in cached:
            if rec.job_id not in cache_map:
                cache_map[rec.job_id] = rec

        # 精排结果 (仅 Top RERANK_TOP_N)
        cached_results: list[dict[str, Any]] = []
        uncached: list[tuple[Job, dict]] = []
        for job, dims in rerank_candidates:
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
                    "match_reason": rec.match_reason or "灵犀精排缓存",
                })
            else:
                uncached.append((job, dims))

        if cached_results:
            logger.info(f"精排缓存命中 {len(cached_results)}/{len(rerank_candidates)}, 调 LLM {len(uncached)} 个")

        # 未命中的调 LLM 精排
        if uncached:
            llm_results = self.fine_rerank(resume, uncached, top_k=len(uncached))
            cached_results.extend(llm_results)

        # 构建精排结果索引 (仅 Top RERANK_TOP_N 有精排分数)
        rerank_result_map: dict[int, dict[str, Any]] = {}
        for item in cached_results:
            rerank_result_map[item["job"].id] = item

        # 组装最终结果: 精排候选用精排分数, 其余用粗排分数填充
        final_results: list[dict[str, Any]] = []
        for job, dims in display_candidates:
            if job.id in rerank_result_map:
                final_results.append(rerank_result_map[job.id])
            else:
                # 粗排候选: 使用粗排分数, 标记为规则匹配
                final_results.append({
                    "job": job,
                    "total_score": round(dims["total"], 2),
                    "skill_score": dims["skill"],
                    "exp_score": dims["experience"],
                    "edu_score": dims["education"],
                    "city_score": dims["city"],
                    "salary_score": dims["salary"],
                    "proj_score": dims["project"],
                    "match_reason": "规则匹配 (粗排)",
                })

        final_results.sort(key=lambda x: x["total_score"], reverse=True)
        return final_results[:top_k]

    def fine_rerank(
        self,
        resume: Resume,
        candidates: list[tuple[Job, dict]],
        top_k: int = 10,
    ) -> list[dict[str, Any]]:
        """豆包模型精排 (批量调用 LLM, 6 候选合 1 次), 返回 [{job, score, reason, dimensions}, ...]"""
        if not candidates:
            return []

        # 仅对 Top6 调用灵犀大模型
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
            arr, usage = ark_client.chat_json_array_lite(messages, temperature=0.1, max_tokens=1024)
            self._add_usage(usage)
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
            llm_score, reason = llm_scores.get(idx, (dims["total"], "灵犀精排不可用, 使用规则评分"))
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
                llm_result, usage = ark_client.chat_json_lite(messages, temperature=0.1, max_tokens=256)
                self._add_usage(usage)
                return idx, float(llm_result.get("score", dims["total"])), llm_result.get("reason", "")
            except Exception as e:
                logger.warning(f"单次精排失败 job_id={job.id}: {e}, 使用粗排分数")
                return idx, dims["total"], "灵犀精排不可用, 使用规则评分"

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
                    out[idx] = (dims["total"], "灵犀精排超时, 使用规则评分")
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
        self._reset_usage()
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

    # ============ 4b. 冷启动推荐 (无简历时) ============
    def recommend_jobs_cold_start(
        self, user_id: int, db: Session, top_k: int = 10
    ) -> list[dict[str, Any]]:
        """冷启动推荐: 无简历时按求职者意向城市+职位类别推荐热门职位"""
        self._reset_usage()
        from app.models.user import SysUser
        from sqlalchemy import func

        user = db.get(SysUser, user_id)
        if not user:
            return []

        # 查询所有招聘中的职位
        jobs = list(db.execute(
            select(Job)
            .options(selectinload(Job.requirements))
            .where(Job.status == 1)
        ).scalars())

        if not jobs:
            return []

        # 按投递数排序 (热门度)
        job_app_counts = {}
        app_rows = db.execute(
            select(JobApplication.job_id, func.count())
            .where(JobApplication.job_id.in_([j.id for j in jobs]))
            .group_by(JobApplication.job_id)
        ).all()
        for jid, cnt in app_rows:
            job_app_counts[jid] = cnt

        # 简单排序: 投递数多的优先
        sorted_jobs = sorted(jobs, key=lambda j: job_app_counts.get(j.id, 0), reverse=True)

        results = []
        for job in sorted_jobs[:top_k]:
            results.append({
                "job": job,
                "total_score": 50.0,  # 冷启动默认中等分
                "skill_score": 0.5,
                "exp_score": 0.5,
                "edu_score": 0.5,
                "city_score": 0.5,
                "salary_score": 0.5,
                "proj_score": 0.5,
                "match_reason": "热门推荐 (完善简历后获得精准匹配)",
            })
        return results

    # ============ 5. 主入口: 职位推荐候选人 ============
    def recommend_resumes_for_job(
        self, job_id: int, db: Session, top_k: int = 10
    ) -> list[dict[str, Any]]:
        """为企业推荐候选人 (优先从已投递者中选取; 无投递时全量搜索, 召回→粗排→精排, 带缓存)"""
        self._reset_usage()
        job = db.execute(
            select(Job)
            .options(selectinload(Job.requirements))
            .where(Job.id == job_id)
        ).scalar_one_or_none()
        if not job:
            raise ValueError("职位不存在")

        # 候选简历: 优先从已投递该职位的求职者中选取
        resumes = list(db.execute(
            select(Resume)
            .options(selectinload(Resume.skills))
            .join(JobApplication, JobApplication.resume_id == Resume.id)
            .where(
                JobApplication.job_id == job_id,
                Resume.parse_status == 2,
            )
        ).scalars())

        # 无投递记录时, 全量搜索已解析简历 (回退策略, 确保企业端始终有推荐结果)
        if not resumes:
            resumes = list(db.execute(
                select(Resume)
                .options(selectinload(Resume.skills))
                .where(Resume.parse_status == 2)
                .order_by(Resume.created_at.desc())
                .limit(100)
            ).scalars())
        if not resumes:
            return []

        # 查询这些简历对该职位的投递记录 (用于返回投递状态 + application_id, 供前端更新状态)
        resume_ids = [r.id for r in resumes]
        app_rows = db.execute(
            select(JobApplication.id, JobApplication.resume_id, JobApplication.status).where(
                JobApplication.job_id == job_id,
                JobApplication.resume_id.in_(resume_ids),
            )
        ).all()
        # resume_id -> (application_id, application_status)
        app_map: dict[int, tuple[int | None, int | None]] = {
            rid: (aid, status) for aid, rid, status in app_rows
        }

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

        # 附加投递状态 (application_id + application_status), 供前端展示与更新
        for item in results:
            app_info = app_map.get(item["resume"].id)
            if app_info:
                item["application_id"] = app_info[0]
                item["application_status"] = app_info[1]
            else:
                item["application_id"] = None
                item["application_status"] = None

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
                    "match_reason": rec.match_reason or "灵犀精排缓存",
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
                llm_result, usage = ark_client.chat_json_lite(messages, temperature=0.1)
                self._add_usage(usage)
                llm_score = float(llm_result.get("score", dims["total"]))
                reason = llm_result.get("reason", "")
                final = dims["total"] * 0.7 + llm_score * 0.3
            except Exception as e:
                logger.warning(f"精排失败 resume_id={resume.id}: {e}")
                final = dims["total"]
                reason = "灵犀精排不可用, 使用规则评分"
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
                        "match_reason": "灵犀精排超时, 使用规则评分",
                    })
        results.sort(key=lambda x: x["total_score"], reverse=True)
        return results

    def _batch_fill_embeddings(self, objs: list[Any], kind: str, db: Session) -> None:
        """批量生成缺失的 embedding (一次 API 调用, 带超时保护)"""
        if self._embedding_disabled:
            return
        missing = [o for o in objs if not o.embedding]
        if not missing:
            return
        # 限制单次批量生成的数量, 避免大量缺失向量导致长时间阻塞
        if len(missing) > 50:
            logger.info(f"有 {len(missing)} 条 {kind} 缺失向量, 本次仅生成前 50 条, 其余下次补充")
            missing = missing[:50]
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
