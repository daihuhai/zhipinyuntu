"""临时: 重置早期账号密码为 123456, 并列出简历"""
from app.db.base import SessionLocal
from app.models.user import SysUser
from app.models.resume import Resume
from app.models.job import Job
from app.core.security import hash_password

db = SessionLocal()
# 重置早期账号密码
for name in ["seeker1", "corp1", "testseeker"]:
    u = db.query(SysUser).filter(SysUser.username == name).first()
    if u:
        u.password_hash = hash_password("123456")
        print(f"reset pwd: {name} -> 123456")
db.commit()

# 列出简历
print("\n=== 简历列表 ===")
resumes = db.query(Resume).all()
for r in resumes:
    print(f"id={r.id} user_id={r.user_id} name={r.name} parse_status={r.parse_status} skills={len(r.skills)}")

# 列出职位
print("\n=== 职位列表 ===")
jobs = db.query(Job).all()
print(f"职位总数: {len(jobs)}, 招聘中: {sum(1 for j in jobs if j.status==1)}")

db.close()
