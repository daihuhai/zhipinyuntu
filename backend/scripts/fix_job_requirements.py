"""
修复脚本: 对没有技能要求但有描述的岗位, 调用豆包模型解析 JD 补充 requirements
用法: python scripts/fix_job_requirements.py
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.base import SessionLocal
from app.models.job import Job, JobRequirement
from app.services.doc_parser import doc_parser
from sqlalchemy import select


def main():
    db = SessionLocal()
    jobs = list(db.execute(
        select(Job).where(Job.description.isnot(None), Job.description != "")
    ).scalars())

    fixed = 0
    skipped = 0
    for job in jobs:
        if job.requirements:
            skipped += 1
            continue
        print(f"解析 job_id={job.id} title={job.title}...")
        try:
            parsed = doc_parser.parse_job(job.description)
            reqs = parsed.get("requirements", [])
            if not reqs:
                print(f"  -> 未提取到技能, 跳过")
                continue
            for req in reqs:
                name = req.get("skill_name") or req.get("name")
                if not name:
                    continue
                db.add(JobRequirement(
                    job_id=job.id,
                    skill_name=name.strip(),
                    skill_level=req.get("skill_level"),
                    req_type=req.get("req_type"),
                    weight=1.0 if req.get("req_type") == "必须" else 0.7,
                ))
            db.commit()
            fixed += 1
            print(f"  -> 提取到 {len(reqs)} 个技能要求")
        except Exception as e:
            print(f"  -> 解析失败: {e}")
            db.rollback()

    db.close()
    print(f"\n完成: 修复 {fixed} 个岗位, 跳过 {skipped} 个已有技能要求的岗位")


if __name__ == "__main__":
    main()
