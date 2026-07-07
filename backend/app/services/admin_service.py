"""
平台管理后台服务 (M5)
- 用户管理: 列表/详情/启用禁用/角色修改
- 简历管理: 列表/删除/统计
- 职位管理: 列表/审核/下架/删除
- 日志管理: 操作日志记录与查询
- 数据统计: 用户/简历/职位/匹配数等仪表盘数据
"""
from typing import Any

from sqlalchemy import select, func, desc
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

    def update_user_status(self, user_id: int, new_status: int, db: Session) -> None:
        u = db.get(SysUser, user_id)
        if not u:
            raise ValueError("用户不存在")
        if u.role == "ROLE_ADMIN":
            raise ValueError("不可修改管理员状态")
        u.status = new_status
        db.commit()

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
        admin_id: int,
        action: str,
        target_type: str | None = None,
        target_id: int | None = None,
        detail: str | None = None,
        ip: str | None = None,
    ) -> None:
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


admin_service = AdminService()
