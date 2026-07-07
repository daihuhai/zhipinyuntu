"""检查 embedding 数据"""
from app.db.base import SessionLocal
from app.models.resume import Resume
from app.models.job import Job

db = SessionLocal()
jobs = db.query(Job).all()
jobs_with_emb = sum(1 for j in jobs if j.embedding)
print(f"职位: {len(jobs)} 总, {jobs_with_emb} 有 embedding")

resumes = db.query(Resume).all()
resumes_with_emb = sum(1 for r in resumes if r.embedding)
print(f"简历: {len(resumes)} 总, {resumes_with_emb} 有 embedding")

# 看一个 embedding 的大小
if jobs_with_emb:
    j = next(j for j in jobs if j.embedding)
    print(f"示例 job embedding 字节数: {len(j.embedding)}")

db.close()
