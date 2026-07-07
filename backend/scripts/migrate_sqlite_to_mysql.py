"""
SQLite → GreatSQL/MySQL 数据迁移脚本
- 从 zhipin.db 读取全部数据
- 在 MySQL zhipin 库中建表并写入
- 同时迁移 education_required 字段值 (大专→专科及以上 等)
- 迁移后验证行数一致性

用法: python -m scripts.migrate_sqlite_to_mysql
"""
import os
import sys
import sqlite3
from datetime import datetime

# 确保能导入 app 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from app.db.base import Base, engine as mysql_engine
# 导入所有模型以注册到 Base.metadata
from app.models import user, resume, job, skill, match, log  # noqa: F401


SQLITE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "zhipin.db")

# 学历字段值映射 (旧 → 新)
EDU_MAP = {
    "大专": "专科及以上",
    "本科": "本科及以上",
    "硕士": "硕士及以上",
    "博士": "博士及以上",
    "": "不限",
}


def migrate_education(val):
    """迁移学历字段值"""
    if val is None:
        return "不限"
    return EDU_MAP.get(val, val)


def main():
    print("=" * 60)
    print("SQLite → GreatSQL/MySQL 数据迁移")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 1. 检查 SQLite 源文件
    if not os.path.exists(SQLITE_PATH):
        print(f"[ERROR] SQLite 文件不存在: {SQLITE_PATH}")
        sys.exit(1)
    print(f"[1/6] SQLite 源文件: {SQLITE_PATH}")

    # 2. 连接 SQLite, 读取所有表
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cur = sqlite_conn.cursor()

    # 获取所有表名
    sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    sqlite_tables = [r[0] for r in sqlite_cur.fetchall()]
    print(f"[2/6] SQLite 表: {sqlite_tables}")

    # 统计各表行数
    print("\n--- SQLite 源数据统计 ---")
    sqlite_counts = {}
    for t in sqlite_tables:
        cnt = sqlite_cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        sqlite_counts[t] = cnt
        print(f"  {t}: {cnt} 行")

    # 3. 在 MySQL 中建表
    print(f"\n[3/6] 在 MySQL 中创建表结构...")
    Base.metadata.drop_all(bind=mysql_engine)  # 清空已有表(如有)
    Base.metadata.create_all(bind=mysql_engine)
    print("  表结构创建完成")

    # 4. 检查 MySQL 表
    mysql_inspector = inspect(mysql_engine)
    mysql_tables = mysql_inspector.get_table_names()
    print(f"[4/6] MySQL 表: {mysql_tables}")

    # 5. 逐表迁移数据
    print(f"\n[5/6] 开始数据迁移...")
    mysql_session = Session(mysql_engine)
    total_migrated = 0

    for table_name in sqlite_tables:
        if table_name not in mysql_tables:
            print(f"  [SKIP] {table_name}: MySQL 中无此表")
            continue

        # 获取 SQLite 数据
        rows = sqlite_cur.execute(f"SELECT * FROM {table_name}").fetchall()
        if not rows:
            print(f"  [SKIP] {table_name}: 无数据")
            continue

        # 获取列名
        columns = rows[0].keys()

        # 获取 MySQL 表的列名
        mysql_columns = [c["name"] for c in mysql_inspector.get_columns(table_name)]

        # 只迁移两边都有的列
        common_cols = [c for c in columns if c in mysql_columns]

        # 构建 INSERT 语句
        col_list = ", ".join(f"`{c}`" for c in common_cols)
        param_list = ", ".join(f":{c}" for c in common_cols)
        insert_sql = text(f"INSERT INTO `{table_name}` ({col_list}) VALUES ({param_list})")

        batch = []
        for row in rows:
            row_dict = {}
            for col in common_cols:
                val = row[col]
                # 学历字段值迁移
                if col == "education_required":
                    val = migrate_education(val)
                # 处理 SQLite 的 1/0 → MySQL 的 True/False (Boolean 字段)
                # SQLAlchemy 会自动处理,无需转换
                row_dict[col] = val
            batch.append(row_dict)

        try:
            mysql_session.execute(insert_sql, batch)
            mysql_session.commit()
            total_migrated += len(batch)
            print(f"  [OK] {table_name}: {len(batch)} 行已迁移")
        except Exception as e:
            mysql_session.rollback()
            print(f"  [FAIL] {table_name}: {e}")
            # 尝试逐行插入,跳过错误行
            ok = 0
            for row_dict in batch:
                try:
                    mysql_session.execute(insert_sql, row_dict)
                    mysql_session.commit()
                    ok += 1
                except Exception:
                    mysql_session.rollback()
            print(f"         逐行插入: {ok}/{len(batch)} 成功")
            total_migrated += ok

    mysql_session.close()
    print(f"\n  总计迁移: {total_migrated} 行")

    # 6. 验证数据完整性
    print(f"\n[6/6] 数据完整性验证...")
    mysql_conn = mysql_engine.raw_connection()
    mysql_cur = mysql_conn.cursor()
    all_ok = True
    for table_name in sqlite_tables:
        if table_name not in mysql_tables:
            continue
        mysql_cur.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        mysql_cnt = mysql_cur.fetchone()[0]
        sqlite_cnt = sqlite_counts[table_name]
        status = "OK" if mysql_cnt == sqlite_cnt else "MISMATCH"
        if mysql_cnt != sqlite_cnt:
            all_ok = False
        print(f"  {table_name}: SQLite={sqlite_cnt} MySQL={mysql_cnt} [{status}]")
    mysql_conn.close()
    sqlite_conn.close()

    print("\n" + "=" * 60)
    if all_ok:
        print("迁移成功! 所有表行数一致")
    else:
        print("警告: 部分表行数不一致, 请检查")
    print("=" * 60)


if __name__ == "__main__":
    main()
