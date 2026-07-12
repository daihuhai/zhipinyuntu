"""
平台管理后台服务 (M5)
- 用户管理: 列表/详情/启用禁用/角色修改
- 简历管理: 列表/删除/统计
- 职位管理: 列表/审核/下架/删除
- 日志管理: 操作日志记录与查询
- 数据统计: 用户/简历/职位/匹配数等仪表盘数据
"""
from typing import Any

from sqlalchemy import select, func, desc, delete, update
from sqlalchemy.orm import Session
from loguru import logger

from app.models.job import Job
from app.models.log import AdminLog
from app.models.match import MatchRecord
from app.models.resume import Resume
from app.models.user import SysUser


class AdminService:
    """管理后台业务"""

    # ===== 用户管理 =====
    def list_users(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        role: str | None = None,
        status: int | None = None,
        keyword: str = "",
    ) -> dict[str, Any]:
        stmt = select(SysUser)
        if role:
            stmt = stmt.where(SysUser.role == role)
        if status is not None:
            stmt = stmt.where(SysUser.status == status)
        if keyword:
            stmt = stmt.where(
                (SysUser.username.contains(keyword))
                | (SysUser.nickname.contains(keyword))
                | (SysUser.phone.contains(keyword))
            )
        stmt = stmt.order_by(SysUser.created_at.desc())

        total = len(list(db.execute(stmt).scalars()))
        offset = (page - 1) * size
        items = list(db.execute(stmt.offset(offset).limit(size)).scalars())
        return {
            "items": [self._user_dict(u) for u in items],
            "total": total,
            "page": page,
            "size": size,
        }

    def get_user(self, user_id: int, db: Session) -> dict[str, Any]:
        u = db.get(SysUser, user_id)
        if not u:
            raise ValueError("用户不存在")
        return self._user_dict(u)

    def get_user_detail(self, user_id: int, db: Session) -> dict[str, Any]:
        """用户详情 + 关联统计"""
        from app.models.application import JobApplication
        u = db.get(SysUser, user_id)
        if not u:
            raise ValueError("用户不存在")
        info = self._user_dict(u)
        stats: dict[str, Any] = {}
        if u.role == "ROLE_SEEKER":
            stats["resume_count"] = db.execute(
                select(func.count(Resume.id)).where(Resume.user_id == user_id)
            ).scalar() or 0
            stats["application_count"] = db.execute(
                select(func.count(JobApplication.id)).where(JobApplication.applicant_id == user_id)
            ).scalar() or 0
        elif u.role == "ROLE_EMPLOYER":
            job_ids_rows = db.execute(
                select(Job.id).where(Job.user_id == user_id)
            ).all()
            job_ids = [r[0] for r in job_ids_rows]
            stats["job_count"] = len(job_ids)
            if job_ids:
                stats["received_count"] = db.execute(
                    select(func.count(JobApplication.id)).where(
                        JobApplication.job_id.in_(job_ids)
                    )
                ).scalar() or 0
            else:
                stats["received_count"] = 0
        else:
            stats["resume_count"] = 0
            stats["application_count"] = 0
            stats["job_count"] = 0
            stats["received_count"] = 0
        return {"user": info, "stats": stats}

    def update_user_status(self, user_id: int, new_status: int, db: Session) -> None:
        u = db.get(SysUser, user_id)
        if not u:
            raise ValueError("用户不存在")
        if u.role == "ROLE_ADMIN":
            raise ValueError("不可修改管理员状态")
        u.status = new_status
        db.commit()

    def batch_update_user_status(self, user_ids: list[int], status: int, db: Session) -> int:
        """批量更新用户状态 (跳过管理员), 返回更新数量"""
        if not user_ids:
            return 0
        if status not in (0, 1):
            raise ValueError("状态非法")
        result = db.execute(
            update(SysUser)
            .where(SysUser.id.in_(user_ids), SysUser.role != "ROLE_ADMIN")
            .values(status=status)
        )
        db.commit()
        return result.rowcount or 0

    def update_user_role(self, user_id: int, new_role: str, db: Session) -> None:
        u = db.get(SysUser, user_id)
        if not u:
            raise ValueError("用户不存在")
        if u.role == "ROLE_ADMIN":
            raise ValueError("不可修改管理员角色")
        if new_role not in ("ROLE_SEEKER", "ROLE_EMPLOYER"):
            raise ValueError("角色非法")
        u.role = new_role
        db.commit()

    def delete_user(self, user_id: int, db: Session) -> None:
        u = db.get(SysUser, user_id)
        if not u:
            raise ValueError("用户不存在")
        if u.role == "ROLE_ADMIN":
            raise ValueError("不可删除管理员")
        db.delete(u)
        db.commit()

    def _user_dict(self, u: SysUser) -> dict[str, Any]:
        return {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "phone": u.phone,
            "email": u.email,
            "nickname": u.nickname,
            "avatar_url": u.avatar_url,
            "company_name": u.company_name,
            "real_name": u.real_name,
            "gender": u.gender,
            "status": u.status,
            "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
            "created_at": u.created_at.isoformat() if u.created_at else None,
        }

    # ===== 简历管理 =====
    def list_resumes(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        keyword: str = "",
        parse_status: int | None = None,
    ) -> dict[str, Any]:
        stmt = select(Resume)
        if parse_status is not None:
            stmt = stmt.where(Resume.parse_status == parse_status)
        if keyword:
            stmt = stmt.where(
                (Resume.name.contains(keyword)) | (Resume.school.contains(keyword))
            )
        stmt = stmt.order_by(Resume.created_at.desc())

        total = len(list(db.execute(stmt).scalars()))
        offset = (page - 1) * size
        items = list(db.execute(stmt.offset(offset).limit(size)).scalars())
        return {
            "items": [self._resume_dict(r) for r in items],
            "total": total,
            "page": page,
            "size": size,
        }

    def delete_resume(self, resume_id: int, db: Session) -> None:
        r = db.get(Resume, resume_id)
        if not r:
            raise ValueError("简历不存在")
        db.delete(r)
        db.commit()

    def batch_delete_resumes(self, resume_ids: list[int], db: Session) -> int:
        """批量删除简历, 返回删除数量"""
        if not resume_ids:
            return 0
        result = db.execute(
            delete(Resume).where(Resume.id.in_(resume_ids))
        )
        db.commit()
        return result.rowcount or 0

    def _resume_dict(self, r: Resume) -> dict[str, Any]:
        return {
            "id": r.id,
            "user_id": r.user_id,
            "name": r.name,
            "gender": r.gender,
            "age": r.age,
            "education": r.education,
            "school": r.school,
            "major": r.major,
            "work_years": r.work_years,
            "current_city": r.current_city,
            "parse_status": r.parse_status,
            "doc_url": r.doc_url,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }

    # ===== 职位管理 =====
    def list_jobs(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        keyword: str = "",
        status: int | None = None,
    ) -> dict[str, Any]:
        stmt = select(Job)
        if status is not None:
            stmt = stmt.where(Job.status == status)
        if keyword:
            stmt = stmt.where(
                (Job.title.contains(keyword)) | (Job.company.contains(keyword))
            )
        stmt = stmt.order_by(Job.created_at.desc())

        total = len(list(db.execute(stmt).scalars()))
        offset = (page - 1) * size
        items = list(db.execute(stmt.offset(offset).limit(size)).scalars())
        return {
            "items": [self._job_dict(j) for j in items],
            "total": total,
            "page": page,
            "size": size,
        }

    def update_job_status(self, job_id: int, new_status: int, db: Session) -> None:
        j = db.get(Job, job_id)
        if not j:
            raise ValueError("职位不存在")
        if new_status not in (0, 1, 2):
            raise ValueError("状态非法")
        j.status = new_status
        db.commit()

    def batch_update_job_status(self, job_ids: list[int], status: int, db: Session) -> int:
        """批量更新职位状态, 返回更新数量"""
        if not job_ids:
            return 0
        if status not in (0, 1, 2):
            raise ValueError("状态非法")
        result = db.execute(
            update(Job).where(Job.id.in_(job_ids)).values(status=status)
        )
        db.commit()
        return result.rowcount or 0

    def delete_job(self, job_id: int, db: Session) -> None:
        j = db.get(Job, job_id)
        if not j:
            raise ValueError("职位不存在")
        db.delete(j)
        db.commit()

    def _job_dict(self, j: Job) -> dict[str, Any]:
        return {
            "id": j.id,
            "user_id": j.user_id,
            "title": j.title,
            "company": j.company,
            "work_city": j.work_city,
            "salary_min": j.salary_min,
            "salary_max": j.salary_max,
            "experience_required": j.experience_required,
            "education_required": j.education_required,
            "headcount": j.headcount,
            "status": j.status,
            "created_at": j.created_at.isoformat() if j.created_at else None,
        }

    # ===== 操作日志 =====
    def list_logs(
        self,
        db: Session,
        page: int = 1,
        size: int = 20,
        admin_id: int | None = None,
        action: str | None = None,
    ) -> dict[str, Any]:
        stmt = select(AdminLog)
        if admin_id:
            stmt = stmt.where(AdminLog.admin_id == admin_id)
        if action:
            stmt = stmt.where(AdminLog.action == action)
        stmt = stmt.order_by(AdminLog.created_at.desc())

        total = len(list(db.execute(stmt).scalars()))
        offset = (page - 1) * size
        items = list(db.execute(stmt.offset(offset).limit(size)).scalars())
        return {
            "items": [
                {
                    "id": l.id,
                    "admin_id": l.admin_id,
                    "action": l.action,
                    "target_type": l.target_type,
                    "target_id": l.target_id,
                    "detail": l.detail,
                    "ip": l.ip,
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                }
                for l in items
            ],
            "total": total,
            "page": page,
            "size": size,
        }

    def write_log(
        self,
        db: Session,
        admin_id: int | None,
        action: str,
        target_type: str | None = None,
        target_id: int | None = None,
        detail: str | None = None,
        ip: str | None = None,
    ) -> None:
        """写入操作日志 (admin_id 可空, 用于系统自动操作如 AI 调用)"""
        log = AdminLog(
            admin_id=admin_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip=ip,
        )
        db.add(log)
        db.commit()

    def write_system_log(
        self,
        db: Session,
        action: str,
        detail: str,
        target_type: str | None = None,
        target_id: int | None = None,
    ) -> None:
        """记录系统级操作 (AI 调用/数据导出等, 无需管理员发起)"""
        log = AdminLog(
            admin_id=None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            ip="system",
        )
        db.add(log)
        db.commit()

    # ===== 数据统计 (仪表盘) =====
    def get_dashboard_stats(self, db: Session) -> dict[str, Any]:
        """管理后台仪表盘统计数据"""
        # 用户统计
        total_users = db.execute(select(func.count(SysUser.id))).scalar() or 0
        seeker_count = db.execute(
            select(func.count(SysUser.id)).where(SysUser.role == "ROLE_SEEKER")
        ).scalar() or 0
        employer_count = db.execute(
            select(func.count(SysUser.id)).where(SysUser.role == "ROLE_EMPLOYER")
        ).scalar() or 0

        # 简历统计
        total_resumes = db.execute(select(func.count(Resume.id))).scalar() or 0
        parsed_ok = db.execute(
            select(func.count(Resume.id)).where(Resume.parse_status == 2)
        ).scalar() or 0

        # 职位统计
        total_jobs = db.execute(select(func.count(Job.id))).scalar() or 0
        active_jobs = db.execute(
            select(func.count(Job.id)).where(Job.status == 1)
        ).scalar() or 0

        # 匹配统计
        total_matches = db.execute(select(func.count(MatchRecord.id))).scalar() or 0
        avg_score = db.execute(
            select(func.avg(MatchRecord.total_score))
        ).scalar() or 0.0

        # 近 7 日新增用户 (简化为总数趋势)
        recent_users = list(
            db.execute(
                select(SysUser)
                .order_by(SysUser.created_at.desc())
                .limit(5)
            ).scalars()
        )
        recent_jobs = list(
            db.execute(
                select(Job).order_by(Job.created_at.desc()).limit(5)
            ).scalars()
        )

        return {
            "users": {
                "total": total_users,
                "seeker": seeker_count,
                "employer": employer_count,
                "admin": total_users - seeker_count - employer_count,
            },
            "resumes": {
                "total": total_resumes,
                "parsed": parsed_ok,
                "pending": total_resumes - parsed_ok,
            },
            "jobs": {
                "total": total_jobs,
                "active": active_jobs,
                "inactive": total_jobs - active_jobs,
            },
            "matches": {
                "total": total_matches,
                "avg_score": round(float(avg_score), 2),
            },
            "recent_users": [self._user_dict(u) for u in recent_users],
            "recent_jobs": [self._job_dict(j) for j in recent_jobs],
        }

    def get_dashboard_trend(self, db: Session) -> dict[str, Any]:
        """仪表盘图表数据: 用户增长趋势 + 简历状态分布 + 职位状态分布 + 热门技能 Top10"""
        from datetime import datetime, timedelta
        from app.models.resume import ResumeSkill
        from app.models.job import JobRequirement

        # 1. 用户增长趋势 (近 14 天)
        today = datetime.utcnow().date()
        days = [(today - timedelta(days=i)) for i in range(13, -1, -1)]
        day_labels = [d.strftime("%m-%d") for d in days]
        day_counts = {d.strftime("%Y-%m-%d"): 0 for d in days}
        users = list(db.execute(select(SysUser.created_at)).all())
        for (ts,) in users:
            if ts:
                key = ts.strftime("%Y-%m-%d")
                if key in day_counts:
                    day_counts[key] += 1
        # 累计增长
        cumulative = []
        running = 0
        for d in days:
            running += day_counts[d.strftime("%Y-%m-%d")]
            cumulative.append(running)

        # 2. 简历解析状态分布
        resume_status_rows = db.execute(
            select(Resume.parse_status, func.count(Resume.id)).group_by(Resume.parse_status)
        ).all()
        resume_status = {"0": 0, "1": 0, "2": 0, "3": 0}
        status_names = {"0": "待解析", "1": "解析中", "2": "成功", "3": "失败"}
        for status, cnt in resume_status_rows:
            resume_status[str(status)] = cnt

        # 3. 职位状态分布
        job_status_rows = db.execute(
            select(Job.status, func.count(Job.id)).group_by(Job.status)
        ).all()
        job_status = {"0": 0, "1": 0, "2": 0}
        job_status_names = {"0": "草稿", "1": "招聘中", "2": "已下架"}
        for status, cnt in job_status_rows:
            job_status[str(status)] = cnt

        # 4. 热门技能 Top10 (简历技能出现频次)
        hot_skills_rows = db.execute(
            select(ResumeSkill.skill_name, func.count(ResumeSkill.id).label("cnt"))
            .group_by(ResumeSkill.skill_name)
            .order_by(desc("cnt"))
            .limit(10)
        ).all()
        hot_skills = [{"name": name, "count": cnt} for name, cnt in hot_skills_rows]

        # 5. 简历解析次数趋势 (近 14 天, 从 admin_log 统计 AI_RESUME_PARSE)
        from app.models.log import AdminLog
        parse_logs = db.execute(
            select(AdminLog.created_at, AdminLog.action)
            .where(AdminLog.action.in_([
                "AI_RESUME_PARSE", "AI_RESUME_PARSE_FAILED",
                "AI_GAP_ANALYSIS", "AI_MATCH_RECOMMEND"
            ]))
        ).all()
        parse_daily = {d.strftime("%Y-%m-%d"): 0 for d in days}
        ai_call_counts = {"AI_RESUME_PARSE": 0, "AI_RESUME_PARSE_FAILED": 0,
                          "AI_GAP_ANALYSIS": 0, "AI_MATCH_RECOMMEND": 0}
        for log_ts, log_action in parse_logs:
            if log_ts:
                key = log_ts.strftime("%Y-%m-%d")
                if key in parse_daily and log_action == "AI_RESUME_PARSE":
                    parse_daily[key] += 1
                if log_action in ai_call_counts:
                    ai_call_counts[log_action] += 1

        # 6. AI Token 消耗估算 (基于操作次数 × 单次估算 token)
        TOKEN_ESTIMATE = {
            "AI_RESUME_PARSE": 3500,       # 简历解析: 输入简历文本 + 输出结构化 JSON
            "AI_RESUME_PARSE_FAILED": 800,  # 失败也消耗了部分 token
            "AI_GAP_ANALYSIS": 2500,        # 缺失分析: 输入简历 + 输出建议
            "AI_MATCH_RECOMMEND": 1500,     # 匹配推荐: 输入简历+岗位 + 输出评分
        }
        ai_token_total = sum(ai_call_counts[k] * TOKEN_ESTIMATE[k] for k in ai_call_counts)
        ai_call_total = sum(ai_call_counts.values())

        return {
            "user_growth": {
                "days": day_labels,
                "daily": [day_counts[d.strftime("%Y-%m-%d")] for d in days],
                "cumulative": cumulative,
            },
            "resume_status": {
                "names": [status_names[k] for k in ["0", "1", "2", "3"]],
                "values": [resume_status[k] for k in ["0", "1", "2", "3"]],
            },
            "job_status": {
                "names": [job_status_names[k] for k in ["0", "1", "2"]],
                "values": [job_status[k] for k in ["0", "1", "2"]],
            },
            "hot_skills": hot_skills,
            "resume_parse_trend": {
                "days": day_labels,
                "values": [parse_daily[d.strftime("%Y-%m-%d")] for d in days],
            },
            "ai_usage": {
                "total_calls": ai_call_total,
                "total_tokens": ai_token_total,
                "breakdown": [
                    {"label": "简历解析", "count": ai_call_counts["AI_RESUME_PARSE"],
                     "tokens": ai_call_counts["AI_RESUME_PARSE"] * TOKEN_ESTIMATE["AI_RESUME_PARSE"]},
                    {"label": "解析失败", "count": ai_call_counts["AI_RESUME_PARSE_FAILED"],
                     "tokens": ai_call_counts["AI_RESUME_PARSE_FAILED"] * TOKEN_ESTIMATE["AI_RESUME_PARSE_FAILED"]},
                    {"label": "缺失分析", "count": ai_call_counts["AI_GAP_ANALYSIS"],
                     "tokens": ai_call_counts["AI_GAP_ANALYSIS"] * TOKEN_ESTIMATE["AI_GAP_ANALYSIS"]},
                    {"label": "智能匹配", "count": ai_call_counts["AI_MATCH_RECOMMEND"],
                     "tokens": ai_call_counts["AI_MATCH_RECOMMEND"] * TOKEN_ESTIMATE["AI_MATCH_RECOMMEND"]},
                ],
            },
        }

    # ===== 大数据中心扩展接口 =====
    def get_dashboard_overview(self, db: Session) -> dict[str, Any]:
        """大数据中心总览: 6 KPI + 环比 + 3 Gauge"""
        from datetime import datetime, timedelta
        from app.models.application import JobApplication

        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)

        def _count_since(model, date_field, target_date):
            """统计 target_date 当天 00:00 ~ 次日 00:00 的记录数"""
            start = datetime.combine(target_date, datetime.min.time())
            end = start + timedelta(days=1)
            return db.execute(
                select(func.count(model.id)).where(
                    date_field >= start, date_field < end
                )
            ).scalar() or 0

        def _count_before(model, date_field, target_date):
            """统计 target_date 之前(不含)的累计记录数"""
            start = datetime.combine(target_date, datetime.min.time())
            return db.execute(
                select(func.count(model.id)).where(date_field < start)
            ).scalar() or 0

        # KPI 总量
        total_users = db.execute(select(func.count(SysUser.id))).scalar() or 0
        total_resumes = db.execute(select(func.count(Resume.id))).scalar() or 0
        total_jobs = db.execute(select(func.count(Job.id))).scalar() or 0
        total_apps = db.execute(select(func.count(JobApplication.id))).scalar() or 0
        total_matches = db.execute(select(func.count(MatchRecord.id))).scalar() or 0
        avg_score = db.execute(select(func.avg(MatchRecord.total_score))).scalar() or 0.0

        # 昨日新增 (环比)
        y_users = _count_since(SysUser, SysUser.created_at, yesterday)
        y_resumes = _count_since(Resume, Resume.created_at, yesterday)
        y_jobs = _count_since(Job, Job.created_at, yesterday)
        y_apps = _count_since(JobApplication, JobApplication.created_at, yesterday)
        y_matches = _count_since(MatchRecord, MatchRecord.created_at, yesterday)

        # 上周平均匹配分 (环比)
        week_ago = today - timedelta(days=7)
        week_start = datetime.combine(week_ago, datetime.min.time())
        last_week_avg = db.execute(
            select(func.avg(MatchRecord.total_score)).where(
                MatchRecord.created_at < week_start
            )
        ).scalar() or float(avg_score)

        def _pct(cur, prev):
            if prev == 0:
                return 0.0
            return round((cur - prev) / prev * 100, 2)

        # Gauge 指标
        parsed_ok = db.execute(
            select(func.count(Resume.id)).where(Resume.parse_status == 2)
        ).scalar() or 0
        active_jobs = db.execute(
            select(func.count(Job.id)).where(Job.status == 1)
        ).scalar() or 0
        parse_rate = round(parsed_ok / total_resumes * 100, 1) if total_resumes else 0.0
        job_active_rate = round(active_jobs / total_jobs * 100, 1) if total_jobs else 0.0

        return {
            "kpi": {
                "users": {"total": total_users, "delta": y_users, "delta_pct": _pct(y_users, total_users - y_users if total_users - y_users > 0 else 1)},
                "resumes": {"total": total_resumes, "delta": y_resumes, "delta_pct": _pct(y_resumes, total_resumes - y_resumes if total_resumes - y_resumes > 0 else 1)},
                "jobs": {"total": total_jobs, "delta": y_jobs, "delta_pct": _pct(y_jobs, total_jobs - y_jobs if total_jobs - y_jobs > 0 else 1)},
                "applications": {"total": total_apps, "delta": y_apps, "delta_pct": _pct(y_apps, total_apps - y_apps if total_apps - y_apps > 0 else 1)},
                "matches": {"total": total_matches, "delta": y_matches, "delta_pct": _pct(y_matches, total_matches - y_matches if total_matches - y_matches > 0 else 1)},
                "avg_score": {"total": round(float(avg_score), 1), "delta": round(float(avg_score) - float(last_week_avg), 1), "delta_pct": _pct(float(avg_score), float(last_week_avg))},
            },
            "gauges": {
                "parse_rate": parse_rate,
                "job_active_rate": job_active_rate,
                "avg_match_score": round(float(avg_score), 1),
            },
            "backend_status": "ok",
        }

    def get_application_stats(self, db: Session) -> dict[str, Any]:
        """投递统计: 总数 + 状态分布"""
        from app.models.application import JobApplication

        status_map = {0: "已投递", 1: "已查看", 2: "面试邀请", 3: "不合适", 4: "已录用"}
        rows = db.execute(
            select(JobApplication.status, func.count(JobApplication.id))
            .group_by(JobApplication.status)
        ).all()
        distribution = {str(k): 0 for k in status_map}
        for status, cnt in rows:
            distribution[str(status)] = cnt

        total = sum(distribution.values())
        return {
            "total": total,
            "names": [status_map[int(k)] for k in ["0", "1", "2", "3", "4"]],
            "values": [distribution[k] for k in ["0", "1", "2", "3", "4"]],
        }

    def get_match_distribution(self, db: Session) -> dict[str, Any]:
        """匹配分直方图分桶统计"""
        buckets = ["0-20", "20-40", "40-60", "60-80", "80-100"]
        ranges = [(0, 20), (20, 40), (40, 60), (60, 80), (80, 101)]
        counts = []
        for lo, hi in ranges:
            cnt = db.execute(
                select(func.count(MatchRecord.id)).where(
                    MatchRecord.total_score >= lo,
                    MatchRecord.total_score < hi,
                )
            ).scalar() or 0
            counts.append(cnt)

        avg_score = db.execute(select(func.avg(MatchRecord.total_score))).scalar() or 0.0
        # 中位数 (简化: 取排序后中间值)
        all_scores = [r[0] for r in db.execute(
            select(MatchRecord.total_score).order_by(MatchRecord.total_score)
        ).all()]
        median = 0.0
        if all_scores:
            mid = len(all_scores) // 2
            median = float(all_scores[mid]) if len(all_scores) % 2 else float(
                (all_scores[mid - 1] + all_scores[mid]) / 2
            )

        return {
            "buckets": buckets,
            "counts": counts,
            "avg_score": round(float(avg_score), 1),
            "median_score": round(median, 1),
        }

    def get_city_distribution(self, db: Session) -> dict[str, Any]:
        """职位城市分布 TOP10"""
        rows = db.execute(
            select(Job.work_city, func.count(Job.id).label("cnt"))
            .where(Job.work_city.isnot(None), Job.work_city != "")
            .group_by(Job.work_city)
            .order_by(desc("cnt"))
            .limit(10)
        ).all()
        return {
            "names": [r[0] for r in rows],
            "values": [r[1] for r in rows],
        }

    def get_school_rank(self, db: Session) -> dict[str, Any]:
        """院校 TOP10"""
        rows = db.execute(
            select(Resume.school, func.count(Resume.id).label("cnt"))
            .where(Resume.school.isnot(None), Resume.school != "")
            .group_by(Resume.school)
            .order_by(desc("cnt"))
            .limit(10)
        ).all()
        return [
            {"name": r[0], "count": r[1]}
            for r in rows
        ]

    def get_realtime_logs(self, db: Session, limit: int = 20) -> dict[str, Any]:
        """最近 N 条操作日志 (供滚动流)"""
        rows = list(db.execute(
            select(AdminLog).order_by(AdminLog.created_at.desc()).limit(limit)
        ).scalars())
        return {
            "items": [
                {
                    "id": l.id,
                    "admin_id": l.admin_id,
                    "action": l.action,
                    "target_type": l.target_type,
                    "target_id": l.target_id,
                    "detail": l.detail,
                    "ip": l.ip,
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                }
                for l in rows
            ]
        }


admin_service = AdminService()
