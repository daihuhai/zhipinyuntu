#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智聘云图招聘平台 - 演示数据填充脚本

参考中国科学技术大学 Job-SDF 数据集精神, 生成覆盖多种技能/公司/地区的丰富测试数据。

用法:
    cd d:\\智聘云图\\backend
    .\\venv\\Scripts\\python.exe scripts\\seed_demo_data.py            # 追加模式
    .\\venv\\Scripts\\python.exe scripts\\seed_demo_data.py --reset    # 清空模式

数据规模:
    - 企业用户: 复用已有 corp1 (不新增)
    - 求职者:   新增 seeker2~seeker9 (8 个)
    - 简历:     ~20 份 (每求职者 2-3 份, 覆盖多学历/经验/技能栈/城市)
    - 职位:     25 个 (覆盖后端/前端/算法/数据/测试运维/产品设计/全栈)
    - 不调用 AI, 不生成 embedding (由 match_service 首次匹配时批量生成)
"""

import argparse
import json
import sys
from pathlib import Path

# 将 backend 目录加入 sys.path, 使 app.* 可导入
_BACKEND_DIR = str(Path(__file__).resolve().parent.parent)
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

from sqlalchemy import text

from app.db.base import SessionLocal
from app.core.security import hash_password
from app.models.user import SysUser
from app.models.resume import Resume, ResumeSkill
from app.models.job import Job, JobRequirement
from app.models.match import MatchRecord
from app.models.application import JobApplication

ROLE_SEEKER = "ROLE_SEEKER"
DEFAULT_PASSWORD = "123456"


# ============================================================
# 求职者用户数据 (seeker2 ~ seeker9)
# ============================================================
SEEKERS = [
    {
        "username": "seeker2",
        "nickname": "张明",
        "real_name": "张明",
        "gender": "男",
        "phone": "13800000002",
        "email": "zhangming@example.com",
    },
    {
        "username": "seeker3",
        "nickname": "李芳",
        "real_name": "李芳",
        "gender": "女",
        "phone": "13800000003",
        "email": "lifang@example.com",
    },
    {
        "username": "seeker4",
        "nickname": "王强",
        "real_name": "王强",
        "gender": "男",
        "phone": "13800000004",
        "email": "wangqiang@example.com",
    },
    {
        "username": "seeker5",
        "nickname": "赵敏",
        "real_name": "赵敏",
        "gender": "女",
        "phone": "13800000005",
        "email": "zhaomin@example.com",
    },
    {
        "username": "seeker6",
        "nickname": "陈杰",
        "real_name": "陈杰",
        "gender": "男",
        "phone": "13800000006",
        "email": "chenjie@example.com",
    },
    {
        "username": "seeker7",
        "nickname": "刘洋",
        "real_name": "刘洋",
        "gender": "男",
        "phone": "13800000007",
        "email": "liuyang@example.com",
    },
    {
        "username": "seeker8",
        "nickname": "周婷",
        "real_name": "周婷",
        "gender": "女",
        "phone": "13800000008",
        "email": "zhouting@example.com",
    },
    {
        "username": "seeker9",
        "nickname": "吴磊",
        "real_name": "吴磊",
        "gender": "男",
        "phone": "13800000009",
        "email": "wulei@example.com",
    },
]


# ============================================================
# 职位数据 (25 个, 覆盖全岗位类型)
# ============================================================
JOBS = [
    # ---- 后端开发 (5) ----
    {
        "title": "Java高级开发工程师",
        "company": "字节跳动",
        "department": "基础架构部",
        "work_city": "北京",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 3,
        "description": "负责字节跳动核心业务系统的后端架构设计与开发, 构建高并发、高可用的分布式服务。参与技术方案评审, 指导初中级工程师。",
        "requirements": [
            {"skill_name": "Java", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Spring Boot", "req_type": "必须", "weight": 1.0},
            {"skill_name": "MySQL", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Redis", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Spring Cloud", "req_type": "优先", "weight": 0.7},
            {"skill_name": "Kafka", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Docker", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "Python后端工程师",
        "company": "知乎",
        "department": "内容平台",
        "work_city": "北京",
        "salary_min": 20,
        "salary_max": 40,
        "experience_required": "1-3年",
        "education_required": "本科",
        "headcount": 2,
        "description": "使用 Python 开发知乎内容推荐与分发系统后端, 优化接口性能, 保障系统稳定性。",
        "requirements": [
            {"skill_name": "Python", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Django", "req_type": "必须", "weight": 0.9},
            {"skill_name": "MySQL", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Redis", "req_type": "必须", "weight": 0.8},
            {"skill_name": "FastAPI", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Docker", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "Go开发工程师",
        "company": "腾讯",
        "department": "云平台部",
        "work_city": "深圳",
        "salary_min": 22,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责腾讯云核心组件的 Go 语言开发, 设计高性能微服务架构, 参与开源社区贡献。",
        "requirements": [
            {"skill_name": "Go", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Gin", "req_type": "必须", "weight": 0.8},
            {"skill_name": "MySQL", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Kubernetes", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Docker", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Redis", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "C++开发工程师",
        "company": "华为",
        "department": "2012实验室",
        "work_city": "深圳",
        "salary_min": 20,
        "salary_max": 42,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 3,
        "description": "负责华为底层系统软件 C++ 开发, 涉及操作系统、数据库内核、高性能计算等方向。",
        "requirements": [
            {"skill_name": "C++", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Linux", "req_type": "必须", "weight": 0.8},
            {"skill_name": "MySQL", "req_type": "优先", "weight": 0.5},
            {"skill_name": "Docker", "req_type": "优先", "weight": 0.4},
        ],
    },
    {
        "title": "Node.js开发工程师",
        "company": "网易",
        "department": "云音乐",
        "work_city": "杭州",
        "salary_min": 18,
        "salary_max": 35,
        "experience_required": "1-3年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责网易云音乐 Node.js 后端服务开发, 包括 API 网关、实时消息推送等模块。",
        "requirements": [
            {"skill_name": "Node.js", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Express", "req_type": "必须", "weight": 0.8},
            {"skill_name": "MySQL", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Redis", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Docker", "req_type": "优先", "weight": 0.5},
        ],
    },
    # ---- 前端开发 (4) ----
    {
        "title": "Vue3前端工程师",
        "company": "阿里巴巴",
        "department": "前端技术部",
        "work_city": "杭州",
        "salary_min": 18,
        "salary_max": 35,
        "experience_required": "1-3年",
        "education_required": "本科",
        "headcount": 3,
        "description": "负责阿里电商平台 Vue3 前端开发, 持续优化页面性能与用户体验, 参与前端工程化建设。",
        "requirements": [
            {"skill_name": "Vue3", "req_type": "必须", "weight": 1.0},
            {"skill_name": "JavaScript", "req_type": "必须", "weight": 1.0},
            {"skill_name": "TypeScript", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Vite", "req_type": "优先", "weight": 0.7},
            {"skill_name": "Element Plus", "req_type": "优先", "weight": 0.6},
            {"skill_name": "CSS3", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "React前端工程师",
        "company": "美团",
        "department": "到店事业群",
        "work_city": "北京",
        "salary_min": 20,
        "salary_max": 40,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责美团到店业务 React 前端架构, 搭建组件库与工具链, 推动前端标准化建设。",
        "requirements": [
            {"skill_name": "React", "req_type": "必须", "weight": 1.0},
            {"skill_name": "React Hooks", "req_type": "必须", "weight": 0.9},
            {"skill_name": "TypeScript", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Webpack", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Ant Design", "req_type": "优先", "weight": 0.6},
            {"skill_name": "JavaScript", "req_type": "必须", "weight": 0.8},
        ],
    },
    {
        "title": "小程序开发工程师",
        "company": "拼多多",
        "department": "用户增长",
        "work_city": "上海",
        "salary_min": 15,
        "salary_max": 30,
        "experience_required": "1-3年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责拼多多微信小程序及多端应用开发, 使用 Uni-app 框架实现一套代码多端运行。",
        "requirements": [
            {"skill_name": "小程序", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Uni-app", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Vue3", "req_type": "必须", "weight": 0.8},
            {"skill_name": "JavaScript", "req_type": "必须", "weight": 0.8},
            {"skill_name": "CSS3", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "Web前端初级工程师",
        "company": "小米",
        "department": "MIUI部门",
        "work_city": "北京",
        "salary_min": 10,
        "salary_max": 18,
        "experience_required": "应届/1年",
        "education_required": "本科",
        "headcount": 3,
        "description": "参与 MIUI 生态 Web 端页面开发, 在导师指导下完成需求迭代, 学习前端工程化最佳实践。",
        "requirements": [
            {"skill_name": "JavaScript", "req_type": "必须", "weight": 1.0},
            {"skill_name": "HTML5", "req_type": "必须", "weight": 0.9},
            {"skill_name": "CSS3", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Vue3", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Webpack", "req_type": "优先", "weight": 0.4},
        ],
    },
    # ---- 算法/AI (4) ----
    {
        "title": "算法工程师(推荐系统)",
        "company": "字节跳动",
        "department": "推荐架构",
        "work_city": "北京",
        "salary_min": 30,
        "salary_max": 60,
        "experience_required": "3-5年",
        "education_required": "硕士",
        "headcount": 2,
        "description": "负责抖音/今日头条推荐系统核心算法研发, 优化召回与排序模型, 提升用户内容消费体验。",
        "requirements": [
            {"skill_name": "推荐系统", "req_type": "必须", "weight": 1.0},
            {"skill_name": "机器学习", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.9},
            {"skill_name": "PyTorch", "req_type": "必须", "weight": 0.8},
            {"skill_name": "深度学习", "req_type": "优先", "weight": 0.7},
            {"skill_name": "Spark", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "NLP工程师",
        "company": "百度",
        "department": "自然语言处理部",
        "work_city": "北京",
        "salary_min": 25,
        "salary_max": 55,
        "experience_required": "1-3年",
        "education_required": "硕士",
        "headcount": 2,
        "description": "负责百度搜索与文心一言 NLP 核心能力研发, 涵盖文本理解、信息抽取、语义匹配等方向。",
        "requirements": [
            {"skill_name": "NLP", "req_type": "必须", "weight": 1.0},
            {"skill_name": "深度学习", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.9},
            {"skill_name": "PyTorch", "req_type": "必须", "weight": 0.8},
            {"skill_name": "TensorFlow", "req_type": "优先", "weight": 0.6},
            {"skill_name": "机器学习", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "计算机视觉工程师",
        "company": "商汤科技",
        "department": "研究院",
        "work_city": "上海",
        "salary_min": 25,
        "salary_max": 55,
        "experience_required": "1-3年",
        "education_required": "硕士",
        "headcount": 2,
        "description": "负责计算机视觉前沿算法研发与落地, 涵盖目标检测、图像分割、人脸识别等方向。",
        "requirements": [
            {"skill_name": "计算机视觉", "req_type": "必须", "weight": 1.0},
            {"skill_name": "深度学习", "req_type": "必须", "weight": 0.9},
            {"skill_name": "PyTorch", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.8},
            {"skill_name": "TensorFlow", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "大模型算法工程师",
        "company": "智谱AI",
        "department": "GLM团队",
        "work_city": "北京",
        "salary_min": 35,
        "salary_max": 70,
        "experience_required": "3-5年",
        "education_required": "博士",
        "headcount": 2,
        "description": "参与 GLM 大语言模型预训练与微调, 研究对齐技术、RLHF、高效推理等前沿课题。",
        "requirements": [
            {"skill_name": "深度学习", "req_type": "必须", "weight": 1.0},
            {"skill_name": "NLP", "req_type": "必须", "weight": 1.0},
            {"skill_name": "PyTorch", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.8},
            {"skill_name": "机器学习", "req_type": "优先", "weight": 0.7},
        ],
    },
    # ---- 数据 (4) ----
    {
        "title": "数据分析师",
        "company": "京东",
        "department": "数据智能部",
        "work_city": "北京",
        "salary_min": 15,
        "salary_max": 30,
        "experience_required": "1-3年",
        "education_required": "本科",
        "headcount": 3,
        "description": "负责京东零售业务数据分析, 搭建指标体系, 输出业务洞察报告, 驱动数据化运营。",
        "requirements": [
            {"skill_name": "数据分析", "req_type": "必须", "weight": 1.0},
            {"skill_name": "SQL", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Pandas", "req_type": "必须", "weight": 0.8},
            {"skill_name": "NumPy", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Python", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "数据挖掘工程师",
        "company": "滴滴出行",
        "department": "智能出行",
        "work_city": "北京",
        "salary_min": 22,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "硕士",
        "headcount": 2,
        "description": "负责滴滴出行供需预测、定价策略、司机调度等场景的数据挖掘与建模工作。",
        "requirements": [
            {"skill_name": "数据挖掘", "req_type": "必须", "weight": 1.0},
            {"skill_name": "机器学习", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Spark", "req_type": "优先", "weight": 0.6},
            {"skill_name": "SQL", "req_type": "必须", "weight": 0.7},
        ],
    },
    {
        "title": "大数据开发工程师",
        "company": "快手",
        "department": "数据平台",
        "work_city": "北京",
        "salary_min": 22,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责快手数据仓库与离线/实时计算平台开发, 构建 PB 级数据处理流水线。",
        "requirements": [
            {"skill_name": "Spark", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Hadoop", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Hive", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Flink", "req_type": "优先", "weight": 0.7},
            {"skill_name": "Java", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "ETL工程师",
        "company": "携程",
        "department": "数据治理",
        "work_city": "上海",
        "salary_min": 15,
        "salary_max": 28,
        "experience_required": "1-3年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责携程数据仓库 ETL 流程开发与维护, 保障数据质量, 优化数据加工性能。",
        "requirements": [
            {"skill_name": "SQL", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Hive", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Spark", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Python", "req_type": "优先", "weight": 0.5},
            {"skill_name": "Shell", "req_type": "优先", "weight": 0.4},
        ],
    },
    # ---- 测试/运维 (4) ----
    {
        "title": "测试开发工程师",
        "company": "哔哩哔哩",
        "department": "质量保障",
        "work_city": "上海",
        "salary_min": 18,
        "salary_max": 35,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责 B 站核心业务测试平台开发与自动化测试体系建设, 提升研发效能与交付质量。",
        "requirements": [
            {"skill_name": "Python", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Selenium", "req_type": "必须", "weight": 0.8},
            {"skill_name": "JMeter", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Postman", "req_type": "优先", "weight": 0.5},
            {"skill_name": "Jenkins", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "DevOps工程师",
        "company": "蚂蚁集团",
        "department": "基础设施",
        "work_city": "杭州",
        "salary_min": 22,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责蚂蚁集团 DevOps 平台建设, 推进 CI/CD 流水线自动化, 构建云原生基础设施。",
        "requirements": [
            {"skill_name": "Docker", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Kubernetes", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Jenkins", "req_type": "必须", "weight": 0.8},
            {"skill_name": "GitLab CI", "req_type": "优先", "weight": 0.7},
            {"skill_name": "Linux", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Shell", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "SRE工程师",
        "company": "字节跳动",
        "department": "稳定性保障",
        "work_city": "深圳",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责字节跳动核心业务稳定性保障, 建设监控告警与自动化运维体系, 推动故障自愈。",
        "requirements": [
            {"skill_name": "Linux", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Kubernetes", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Prometheus", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Grafana", "req_type": "优先", "weight": 0.7},
            {"skill_name": "Ansible", "req_type": "优先", "weight": 0.5},
            {"skill_name": "Python", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "自动化测试工程师",
        "company": "美团",
        "department": "测试部",
        "work_city": "北京",
        "salary_min": 15,
        "salary_max": 28,
        "experience_required": "1-3年",
        "education_required": "本科",
        "headcount": 3,
        "description": "负责美团业务线自动化测试用例编写与维护, 搭建持续集成测试体系。",
        "requirements": [
            {"skill_name": "Selenium", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Postman", "req_type": "优先", "weight": 0.6},
            {"skill_name": "JMeter", "req_type": "优先", "weight": 0.5},
            {"skill_name": "Jenkins", "req_type": "优先", "weight": 0.5},
        ],
    },
    # ---- 产品/设计 (3) ----
    {
        "title": "产品经理",
        "company": "腾讯",
        "department": "产品部",
        "work_city": "深圳",
        "salary_min": 20,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责腾讯核心社交产品规划与迭代, 主导需求分析、原型设计与项目推进, 对产品体验负责。",
        "requirements": [
            {"skill_name": "Axure", "req_type": "必须", "weight": 0.9},
            {"skill_name": "用户研究", "req_type": "必须", "weight": 0.8},
            {"skill_name": "原型设计", "req_type": "必须", "weight": 0.8},
            {"skill_name": "交互设计", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "UI设计师",
        "company": "网易",
        "department": "设计中心",
        "work_city": "杭州",
        "salary_min": 15,
        "salary_max": 30,
        "experience_required": "1-3年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责网易产品视觉设计, 包括界面视觉、图标体系、运营设计等, 维护设计规范一致性。",
        "requirements": [
            {"skill_name": "Figma", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Photoshop", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Illustrator", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Sketch", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "UX设计师",
        "company": "阿里巴巴",
        "department": "用户体验部",
        "work_city": "杭州",
        "salary_min": 18,
        "salary_max": 35,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 1,
        "description": "负责阿里核心产品交互设计与用户研究, 通过数据驱动设计决策, 提升产品可用性。",
        "requirements": [
            {"skill_name": "交互设计", "req_type": "必须", "weight": 1.0},
            {"skill_name": "用户研究", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Axure", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Figma", "req_type": "优先", "weight": 0.6},
        ],
    },
    # ---- 全栈 (1) ----
    {
        "title": "全栈工程师",
        "company": "菜鸟网络",
        "department": "物流科技",
        "work_city": "杭州",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责菜鸟物流科技产品全栈开发, 涵盖前端可视化、后端服务、数据 pipeline 全链路。",
        "requirements": [
            {"skill_name": "Vue3", "req_type": "必须", "weight": 0.8},
            {"skill_name": "React", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Go", "req_type": "优先", "weight": 0.6},
            {"skill_name": "MySQL", "req_type": "必须", "weight": 0.7},
            {"skill_name": "Docker", "req_type": "优先", "weight": 0.5},
        ],
    },
]


# ============================================================
# 简历数据 (~20 份, 每求职者 2-3 份)
# ============================================================
RESUMES = [
    # ===== seeker2: 后端方向 (Java + Python), 硕士, 5年 =====
    {
        "seeker_username": "seeker2",
        "name": "张明",
        "gender": "男",
        "age": 28,
        "phone": "13800000002",
        "email": "zhangming@example.com",
        "current_city": "北京",
        "intention_cities": ["北京", "上海"],
        "education": "硕士",
        "school": "中国科学技术大学",
        "major": "计算机科学与技术",
        "work_years": 5,
        "expected_salary_min": 25,
        "expected_salary_max": 45,
        "self_evaluation": "5 年 Java 后端开发经验, 熟悉高并发系统设计, 曾主导百万级 QPS 服务架构升级, 具备良好的工程素养与团队协作能力。",
        "skills": [
            {"skill_name": "Java", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "Spring Boot", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Spring Cloud", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "MyBatis", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "MySQL", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Redis", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Kafka", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Docker", "skill_level": "掌握", "weight": 0.65},
        ],
        "projects": [
            {"name": "电商订单系统重构", "description": "主导订单系统从单体到微服务架构迁移, QPS 从 5k 提升至 50k, 使用 Spring Cloud + Kafka 实现最终一致性。", "role": "技术负责人"},
            {"name": "秒杀系统设计", "description": "设计并实现高并发秒杀系统, 采用 Redis 预扣库存 + 异步下单方案, 峰值 QPS 达 10 万。", "role": "核心开发"},
        ],
        "work_experience": [
            {"company": "字节跳动", "position": "后端开发工程师", "duration": "2021.07 - 至今"},
            {"company": "美团", "position": "Java开发工程师", "duration": "2019.07 - 2021.06"},
        ],
    },
    {
        "seeker_username": "seeker2",
        "name": "张明",
        "gender": "男",
        "age": 28,
        "phone": "13800000002",
        "email": "zhangming@example.com",
        "current_city": "北京",
        "intention_cities": ["北京", "深圳"],
        "education": "硕士",
        "school": "中国科学技术大学",
        "major": "计算机科学与技术",
        "work_years": 5,
        "expected_salary_min": 25,
        "expected_salary_max": 45,
        "self_evaluation": "同时具备 Java 与 Python 后端开发能力, 熟悉 Django/FastAPI 框架, 对微服务架构有深入实践。",
        "skills": [
            {"skill_name": "Python", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Django", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "FastAPI", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Flask", "skill_level": "掌握", "weight": 0.6},
            {"skill_name": "MySQL", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Redis", "skill_level": "熟练", "weight": 0.75},
            {"skill_name": "Docker", "skill_level": "掌握", "weight": 0.65},
            {"skill_name": "Java", "skill_level": "精通", "weight": 0.9},
        ],
        "projects": [
            {"name": "Python 数据服务平台", "description": "使用 FastAPI 搭建数据查询 API 服务, 支持千万级数据实时检索, 接入 Elasticsearch。", "role": "主力开发"},
        ],
        "work_experience": [
            {"company": "字节跳动", "position": "后端开发工程师", "duration": "2021.07 - 至今"},
        ],
    },
    # ===== seeker3: 前端方向 (Vue + React + 小程序), 本科, 3年 =====
    {
        "seeker_username": "seeker3",
        "name": "李芳",
        "gender": "女",
        "age": 26,
        "phone": "13800000003",
        "email": "lifang@example.com",
        "current_city": "上海",
        "intention_cities": ["上海", "杭州", "北京"],
        "education": "本科",
        "school": "浙江大学",
        "major": "软件工程",
        "work_years": 3,
        "expected_salary_min": 18,
        "expected_salary_max": 30,
        "self_evaluation": "3 年前端开发经验, 精通 Vue3 与 React, 熟悉前端工程化, 有小程序与跨端开发经验。",
        "skills": [
            {"skill_name": "Vue3", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "React", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "TypeScript", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "JavaScript", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Vite", "skill_level": "熟练", "weight": 0.75},
            {"skill_name": "Webpack", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Element Plus", "skill_level": "熟练", "weight": 0.75},
            {"skill_name": "CSS3", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "企业级管理后台", "description": "基于 Vue3 + TypeScript + Element Plus 搭建企业级中后台系统, 含 50+ 页面模块。", "role": "前端负责人"},
            {"name": "React 数据可视化平台", "description": "使用 React + ECharts 开发数据可视化大屏, 支持实时数据刷新与多维筛选。", "role": "核心开发"},
        ],
        "work_experience": [
            {"company": "阿里巴巴", "position": "前端开发工程师", "duration": "2022.07 - 至今"},
        ],
    },
    {
        "seeker_username": "seeker3",
        "name": "李芳",
        "gender": "女",
        "age": 26,
        "phone": "13800000003",
        "email": "lifang@example.com",
        "current_city": "上海",
        "intention_cities": ["上海", "深圳"],
        "education": "本科",
        "school": "浙江大学",
        "major": "软件工程",
        "work_years": 3,
        "expected_salary_min": 18,
        "expected_salary_max": 30,
        "self_evaluation": "专注小程序跨端开发, 熟悉 Uni-app 框架, 有微信/支付宝多端发布经验。",
        "skills": [
            {"skill_name": "小程序", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Uni-app", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Vue3", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "JavaScript", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "CSS3", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "HTML5", "skill_level": "精通", "weight": 0.85},
        ],
        "projects": [
            {"name": "多端电商小程序", "description": "使用 Uni-app 开发多端电商应用, 一套代码发布微信/支付宝/H5 三端, DAU 10万+。", "role": "前端负责人"},
        ],
        "work_experience": [
            {"company": "拼多多", "position": "前端开发工程师", "duration": "2021.07 - 2022.06"},
        ],
    },
    {
        "seeker_username": "seeker3",
        "name": "李芳",
        "gender": "女",
        "age": 26,
        "phone": "13800000003",
        "email": "lifang@example.com",
        "current_city": "上海",
        "intention_cities": ["北京", "上海"],
        "education": "本科",
        "school": "浙江大学",
        "major": "软件工程",
        "work_years": 3,
        "expected_salary_min": 18,
        "expected_salary_max": 30,
        "self_evaluation": "React 生态深度实践者, 熟悉 Hooks 模式与状态管理方案, 有大型 SPA 应用开发经验。",
        "skills": [
            {"skill_name": "React", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "React Hooks", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "TypeScript", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Ant Design", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Webpack", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "JavaScript", "skill_level": "精通", "weight": 0.9},
        ],
        "projects": [
            {"name": "React SaaS 应用", "description": "基于 React + Ant Design Pro 开发 SaaS 管理平台, 支持多租户与权限精细化控制。", "role": "前端开发"},
        ],
        "work_experience": [
            {"company": "阿里巴巴", "position": "前端开发工程师", "duration": "2022.07 - 至今"},
        ],
    },
    # ===== seeker4: 算法方向 (NLP + CV), 博士, 2年 =====
    {
        "seeker_username": "seeker4",
        "name": "王强",
        "gender": "男",
        "age": 29,
        "phone": "13800000004",
        "email": "wangqiang@example.com",
        "current_city": "深圳",
        "intention_cities": ["北京", "深圳", "上海"],
        "education": "博士",
        "school": "清华大学",
        "major": "人工智能",
        "work_years": 2,
        "expected_salary_min": 30,
        "expected_salary_max": 60,
        "self_evaluation": "清华大学人工智能博士, 2 年 NLP 工业界经验, 发表 ACL/EMNLP 论文 3 篇, 熟悉大模型微调与部署。",
        "skills": [
            {"skill_name": "NLP", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "深度学习", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "PyTorch", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Python", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "TensorFlow", "skill_level": "熟练", "weight": 0.75},
            {"skill_name": "机器学习", "skill_level": "精通", "weight": 0.85},
        ],
        "projects": [
            {"name": "大模型 RLHF 对齐", "description": "参与百亿参数大模型 RLHF 对齐工作, 设计 reward model 训练流程, 对齐效果提升 15%。", "role": "算法负责人"},
            {"name": "搜索语义匹配", "description": "基于 BERT 构建搜索语义匹配模型, AUC 达 0.92, 上线后搜索 CTR 提升 8%。", "role": "核心开发"},
        ],
        "work_experience": [
            {"company": "百度", "position": "NLP算法工程师", "duration": "2023.07 - 至今"},
        ],
    },
    {
        "seeker_username": "seeker4",
        "name": "王强",
        "gender": "男",
        "age": 29,
        "phone": "13800000004",
        "email": "wangqiang@example.com",
        "current_city": "深圳",
        "intention_cities": ["上海", "深圳"],
        "education": "博士",
        "school": "清华大学",
        "major": "人工智能",
        "work_years": 2,
        "expected_salary_min": 30,
        "expected_salary_max": 60,
        "self_evaluation": "同时具备计算机视觉研究经验, 熟悉目标检测与图像分割算法, 有顶会论文发表。",
        "skills": [
            {"skill_name": "计算机视觉", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "深度学习", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "PyTorch", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Python", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "TensorFlow", "skill_level": "掌握", "weight": 0.7},
        ],
        "projects": [
            {"name": "工业缺陷检测", "description": "基于 YOLOv8 开发工业产品表面缺陷检测系统, mAP 达 0.88, 部署于边缘设备。", "role": "算法工程师"},
        ],
        "work_experience": [
            {"company": "商汤科技", "position": "CV算法实习", "duration": "2022.01 - 2023.06"},
        ],
    },
    # ===== seeker5: 数据方向 (分析 + 挖掘 + ETL), 硕士, 4年 =====
    {
        "seeker_username": "seeker5",
        "name": "赵敏",
        "gender": "女",
        "age": 28,
        "phone": "13800000005",
        "email": "zhaomin@example.com",
        "current_city": "杭州",
        "intention_cities": ["杭州", "北京", "上海"],
        "education": "硕士",
        "school": "复旦大学",
        "major": "统计学",
        "work_years": 4,
        "expected_salary_min": 20,
        "expected_salary_max": 35,
        "self_evaluation": "4 年数据分析与挖掘经验, 熟练使用 SQL/Python/Spark, 擅长从数据中挖掘业务价值, 有完整的指标体系搭建经验。",
        "skills": [
            {"skill_name": "数据分析", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "SQL", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Python", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Pandas", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "NumPy", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "机器学习", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Spark", "skill_level": "掌握", "weight": 0.65},
        ],
        "projects": [
            {"name": "用户增长分析体系", "description": "搭建用户增长全链路分析体系, 包含 30+ 核心指标, 推动月活提升 20%。", "role": "数据分析师"},
            {"name": "流失预测模型", "description": "基于 XGBoost 构建用户流失预测模型, 准确率 87%, 支撑运营干预策略。", "role": "数据挖掘工程师"},
        ],
        "work_experience": [
            {"company": "京东", "position": "数据分析师", "duration": "2021.07 - 至今"},
        ],
    },
    {
        "seeker_username": "seeker5",
        "name": "赵敏",
        "gender": "女",
        "age": 28,
        "phone": "13800000005",
        "email": "zhaomin@example.com",
        "current_city": "杭州",
        "intention_cities": ["北京", "杭州"],
        "education": "硕士",
        "school": "复旦大学",
        "major": "统计学",
        "work_years": 4,
        "expected_salary_min": 20,
        "expected_salary_max": 40,
        "self_evaluation": "具备数据挖掘与机器学习建模能力, 熟悉 Spark 大规模数据处理, 有推荐系统特征工程经验。",
        "skills": [
            {"skill_name": "数据挖掘", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "机器学习", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Python", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Spark", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "SQL", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Pandas", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "推荐特征工程", "description": "负责推荐系统特征管道建设, 使用 Spark 处理 TB 级特征数据, 特征覆盖率提升 30%。", "role": "数据挖掘工程师"},
        ],
        "work_experience": [
            {"company": "滴滴出行", "position": "数据挖掘工程师", "duration": "2020.07 - 2021.06"},
        ],
    },
    {
        "seeker_username": "seeker5",
        "name": "赵敏",
        "gender": "女",
        "age": 28,
        "phone": "13800000005",
        "email": "zhaomin@example.com",
        "current_city": "杭州",
        "intention_cities": ["上海", "杭州"],
        "education": "硕士",
        "school": "复旦大学",
        "major": "统计学",
        "work_years": 4,
        "expected_salary_min": 15,
        "expected_salary_max": 30,
        "self_evaluation": "熟悉 ETL 流程开发与数据仓库建设, 有 Hive/Spark 数据加工经验。",
        "skills": [
            {"skill_name": "SQL", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Hive", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Spark", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Python", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Shell", "skill_level": "掌握", "weight": 0.6},
        ],
        "projects": [
            {"name": "数据仓库迁移", "description": "参与数仓从 Hive 迁移到 Spark SQL, 加工效率提升 40%, 保障数据质量。", "role": "ETL工程师"},
        ],
        "work_experience": [
            {"company": "携程", "position": "ETL工程师", "duration": "2019.07 - 2020.06"},
        ],
    },
    # ===== seeker6: 测试/运维方向, 本科, 6年 =====
    {
        "seeker_username": "seeker6",
        "name": "陈杰",
        "gender": "男",
        "age": 30,
        "phone": "13800000006",
        "email": "chenjie@example.com",
        "current_city": "广州",
        "intention_cities": ["广州", "深圳", "北京"],
        "education": "本科",
        "school": "华中科技大学",
        "major": "计算机科学与技术",
        "work_years": 6,
        "expected_salary_min": 18,
        "expected_salary_max": 35,
        "self_evaluation": "6 年测试开发经验, 搭建过多个自动化测试平台, 熟悉 Python/Java 测试框架, 推动过测试左移与持续集成落地。",
        "skills": [
            {"skill_name": "Python", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Selenium", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "JMeter", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Postman", "skill_level": "熟练", "weight": 0.75},
            {"skill_name": "Jenkins", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "GitLab CI", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Java", "skill_level": "掌握", "weight": 0.65},
        ],
        "projects": [
            {"name": "自动化测试平台", "description": "从零搭建公司级自动化测试平台, 集成 500+ 用例, 回归测试效率提升 60%。", "role": "测试负责人"},
            {"name": "性能压测体系", "description": "基于 JMeter 搭建全链路压测体系, 覆盖 20+ 核心接口, 发现并修复 15 项性能瓶颈。", "role": "测试开发"},
        ],
        "work_experience": [
            {"company": "哔哩哔哩", "position": "测试开发工程师", "duration": "2021.07 - 至今"},
            {"company": "美团", "position": "自动化测试", "duration": "2018.07 - 2021.06"},
        ],
    },
    {
        "seeker_username": "seeker6",
        "name": "陈杰",
        "gender": "男",
        "age": 30,
        "phone": "13800000006",
        "email": "chenjie@example.com",
        "current_city": "广州",
        "intention_cities": ["深圳", "杭州", "广州"],
        "education": "本科",
        "school": "华中科技大学",
        "major": "计算机科学与技术",
        "work_years": 6,
        "expected_salary_min": 20,
        "expected_salary_max": 40,
        "self_evaluation": "具备 DevOps 工程经验, 熟悉 Docker/Kubernetes 容器化与 CI/CD 流水线建设。",
        "skills": [
            {"skill_name": "Docker", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Kubernetes", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Jenkins", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "GitLab CI", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Linux", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "Shell", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Ansible", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Python", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "K8s 集群迁移", "description": "主导业务从虚拟机迁移至 Kubernetes 集群, 资源利用率提升 40%, 部署效率提升 5 倍。", "role": "DevOps负责人"},
        ],
        "work_experience": [
            {"company": "蚂蚁集团", "position": "DevOps工程师", "duration": "2020.07 - 2021.06"},
        ],
    },
    # ===== seeker7: 全栈方向, 本科, 8年 =====
    {
        "seeker_username": "seeker7",
        "name": "刘洋",
        "gender": "男",
        "age": 32,
        "phone": "13800000007",
        "email": "liuyang@example.com",
        "current_city": "成都",
        "intention_cities": ["成都", "杭州", "北京", "深圳"],
        "education": "本科",
        "school": "电子科技大学",
        "major": "软件工程",
        "work_years": 8,
        "expected_salary_min": 25,
        "expected_salary_max": 50,
        "self_evaluation": "8 年全栈开发经验, 熟悉 Vue/React 前端 + Java/Go/Python 后端, 有微服务与云原生实践经验, 可独立完成中型项目全链路开发。",
        "skills": [
            {"skill_name": "Vue3", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "React", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "TypeScript", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Python", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "Go", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Java", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "MySQL", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "Docker", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Kubernetes", "skill_level": "掌握", "weight": 0.7},
        ],
        "projects": [
            {"name": "SaaS 平台全栈开发", "description": "独立完成企业 SaaS 平台前后端开发, Vue3 + Go + MySQL, 服务 100+ 企业客户。", "role": "全栈工程师"},
            {"name": "物流追踪系统", "description": "开发物流实时追踪系统, React 前端 + Python 数据管道 + Go 高并发服务。", "role": "技术负责人"},
        ],
        "work_experience": [
            {"company": "菜鸟网络", "position": "全栈工程师", "duration": "2020.07 - 至今"},
            {"company": "美团", "position": "高级开发工程师", "duration": "2016.07 - 2020.06"},
        ],
    },
    {
        "seeker_username": "seeker7",
        "name": "刘洋",
        "gender": "男",
        "age": 32,
        "phone": "13800000007",
        "email": "liuyang@example.com",
        "current_city": "成都",
        "intention_cities": ["深圳", "杭州"],
        "education": "本科",
        "school": "电子科技大学",
        "major": "软件工程",
        "work_years": 8,
        "expected_salary_min": 22,
        "expected_salary_max": 45,
        "self_evaluation": "Go 后端专精, 有高性能微服务架构经验, 熟悉云原生技术栈。",
        "skills": [
            {"skill_name": "Go", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Gin", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "MySQL", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "Kubernetes", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Docker", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "Redis", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "Go 微服务网关", "description": "基于 Gin 开发 API 网关, 支持限流/熔断/鉴权, QPS 达 5 万。", "role": "后端负责人"},
        ],
        "work_experience": [
            {"company": "腾讯", "position": "Go开发工程师", "duration": "2018.07 - 2020.06"},
        ],
    },
    {
        "seeker_username": "seeker7",
        "name": "刘洋",
        "gender": "男",
        "age": 32,
        "phone": "13800000007",
        "email": "liuyang@example.com",
        "current_city": "成都",
        "intention_cities": ["北京", "成都"],
        "education": "本科",
        "school": "电子科技大学",
        "major": "软件工程",
        "work_years": 8,
        "expected_salary_min": 20,
        "expected_salary_max": 40,
        "self_evaluation": "前端 React 方向深度实践, 有大型 SPA 与 SSR 应用开发经验。",
        "skills": [
            {"skill_name": "React", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "React Hooks", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "TypeScript", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "Ant Design", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "Webpack", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "JavaScript", "skill_level": "精通", "weight": 0.9},
        ],
        "projects": [
            {"name": "React SSR 重构", "description": "将原有 CSR 应用重构为 SSR, 首屏加载时间从 3s 降至 1s, SEO 收录提升 50%。", "role": "前端架构师"},
        ],
        "work_experience": [
            {"company": "美团", "position": "前端开发", "duration": "2016.07 - 2018.06"},
        ],
    },
    # ===== seeker8: 应届生, 本科, 0年 =====
    {
        "seeker_username": "seeker8",
        "name": "周婷",
        "gender": "女",
        "age": 23,
        "phone": "13800000008",
        "email": "zhouting@example.com",
        "current_city": "武汉",
        "intention_cities": ["武汉", "北京", "深圳", "杭州"],
        "education": "本科",
        "school": "武汉大学",
        "major": "软件工程",
        "work_years": 0,
        "expected_salary_min": 8,
        "expected_salary_max": 15,
        "self_evaluation": "应届毕业生, 有前端实习经验, 熟悉 HTML/CSS/JS 基础, 学习能力强, 对前端工程化有浓厚兴趣。",
        "skills": [
            {"skill_name": "JavaScript", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "HTML5", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "CSS3", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Vue3", "skill_level": "了解", "weight": 0.5},
            {"skill_name": "Webpack", "skill_level": "了解", "weight": 0.4},
        ],
        "projects": [
            {"name": "校园二手交易平台", "description": "毕业设计: 使用 Vue3 + Node.js 开发校园二手交易平台, 含商品发布/搜索/聊天功能。", "role": "独立开发"},
        ],
        "work_experience": [],
    },
    {
        "seeker_username": "seeker8",
        "name": "周婷",
        "gender": "女",
        "age": 23,
        "phone": "13800000008",
        "email": "zhouting@example.com",
        "current_city": "武汉",
        "intention_cities": ["武汉", "北京", "深圳"],
        "education": "本科",
        "school": "武汉大学",
        "major": "软件工程",
        "work_years": 0,
        "expected_salary_min": 8,
        "expected_salary_max": 15,
        "self_evaluation": "应届毕业生, 有 Python 后端实习经验, 了解 Django 框架与数据库基础。",
        "skills": [
            {"skill_name": "Python", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Django", "skill_level": "了解", "weight": 0.5},
            {"skill_name": "MySQL", "skill_level": "掌握", "weight": 0.65},
            {"skill_name": "Linux", "skill_level": "了解", "weight": 0.45},
        ],
        "projects": [
            {"name": "博客系统后端", "description": "使用 Django 开发个人博客系统后端, 含文章管理/评论/标签功能。", "role": "独立开发"},
        ],
        "work_experience": [],
    },
    # ===== seeker9: 大专, 多面手, 3年 =====
    {
        "seeker_username": "seeker9",
        "name": "吴磊",
        "gender": "男",
        "age": 26,
        "phone": "13800000009",
        "email": "wulei@example.com",
        "current_city": "西安",
        "intention_cities": ["西安", "成都", "深圳"],
        "education": "大专",
        "school": "西安电子科技大学(继续教育)",
        "major": "计算机应用技术",
        "work_years": 3,
        "expected_salary_min": 10,
        "expected_salary_max": 18,
        "self_evaluation": "3 年测试经验, 熟悉自动化测试与接口测试, 学习能力强, 正在自学 Python 提升技能。",
        "skills": [
            {"skill_name": "Selenium", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Postman", "skill_level": "熟练", "weight": 0.75},
            {"skill_name": "Python", "skill_level": "掌握", "weight": 0.65},
            {"skill_name": "JMeter", "skill_level": "掌握", "weight": 0.6},
            {"skill_name": "Jenkins", "skill_level": "了解", "weight": 0.5},
        ],
        "projects": [
            {"name": "Web 自动化测试", "description": "使用 Selenium + Python 编写 Web UI 自动化用例 200+, 覆盖核心业务流程。", "role": "测试工程师"},
        ],
        "work_experience": [
            {"company": "中软国际", "position": "测试工程师", "duration": "2021.07 - 至今"},
        ],
    },
    {
        "seeker_username": "seeker9",
        "name": "吴磊",
        "gender": "男",
        "age": 26,
        "phone": "13800000009",
        "email": "wulei@example.com",
        "current_city": "西安",
        "intention_cities": ["西安", "成都"],
        "education": "大专",
        "school": "西安电子科技大学(继续教育)",
        "major": "计算机应用技术",
        "work_years": 3,
        "expected_salary_min": 10,
        "expected_salary_max": 18,
        "self_evaluation": "具备基础运维能力, 熟悉 Linux 常用命令与 Shell 脚本, 有 Docker 使用经验。",
        "skills": [
            {"skill_name": "Linux", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Shell", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Docker", "skill_level": "掌握", "weight": 0.65},
            {"skill_name": "Python", "skill_level": "掌握", "weight": 0.6},
            {"skill_name": "Ansible", "skill_level": "了解", "weight": 0.45},
        ],
        "projects": [
            {"name": "运维脚本工具", "description": "编写 Shell + Python 运维脚本, 实现日志清理/监控告警/批量部署自动化。", "role": "运维工程师"},
        ],
        "work_experience": [
            {"company": "华为外包", "position": "运维工程师", "duration": "2020.07 - 2021.06"},
        ],
    },
    {
        "seeker_username": "seeker9",
        "name": "吴磊",
        "gender": "男",
        "age": 26,
        "phone": "13800000009",
        "email": "wulei@example.com",
        "current_city": "西安",
        "intention_cities": ["西安", "深圳", "成都"],
        "education": "大专",
        "school": "西安电子科技大学(继续教育)",
        "major": "计算机应用技术",
        "work_years": 3,
        "expected_salary_min": 10,
        "expected_salary_max": 18,
        "self_evaluation": "自学前端开发, 熟悉 HTML/CSS/JS, 有 Vue 基础项目经验。",
        "skills": [
            {"skill_name": "JavaScript", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "HTML5", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "CSS3", "skill_level": "熟练", "weight": 0.75},
            {"skill_name": "Vue3", "skill_level": "掌握", "weight": 0.65},
            {"skill_name": "小程序", "skill_level": "了解", "weight": 0.45},
        ],
        "projects": [
            {"name": "个人作品集网站", "description": "使用 Vue3 + Vite 开发个人作品集网站, 响应式设计, 部署于云服务器。", "role": "独立开发"},
        ],
        "work_experience": [],
    },
]


# ============================================================
# 辅助函数
# ============================================================
def make_raw_parse_json(resume_data: dict) -> str:
    """构建简历 raw_parse_json (含 projects + work_experience)"""
    return json.dumps({
        "name": resume_data["name"],
        "gender": resume_data["gender"],
        "age": resume_data["age"],
        "phone": resume_data["phone"],
        "email": resume_data["email"],
        "current_city": resume_data["current_city"],
        "intention_cities": resume_data["intention_cities"],
        "education": resume_data["education"],
        "school": resume_data["school"],
        "major": resume_data["major"],
        "work_years": resume_data["work_years"],
        "expected_salary_min": resume_data["expected_salary_min"],
        "expected_salary_max": resume_data["expected_salary_max"],
        "self_evaluation": resume_data["self_evaluation"],
        "skills": [
            {"name": s["skill_name"], "level": s["skill_level"]}
            for s in resume_data["skills"]
        ],
        "projects": resume_data["projects"],
        "work_experience": resume_data["work_experience"],
    }, ensure_ascii=False)


def reset_data(db) -> None:
    """清空 resume/job/application/match_record 表 (保留所有用户)"""
    print("[RESET] 开始清空测试数据 (保留用户)...")
    # 按外键依赖顺序删除
    db.execute(text("DELETE FROM match_record"))
    db.execute(text("DELETE FROM job_application"))
    db.execute(text("DELETE FROM resume_skill"))
    db.execute(text("DELETE FROM job_requirement"))
    db.execute(text("DELETE FROM resume"))
    db.execute(text("DELETE FROM job"))
    db.commit()
    print("[RESET] 已清空 match_record / job_application / resume_skill / job_requirement / resume / job")


def get_or_create_corp_user(db) -> SysUser:
    """获取已有企业用户 corp1 (优先按 username 查找, 回退 id=3)"""
    corp = db.query(SysUser).filter(SysUser.username == "corp1").first()
    if corp is None:
        corp = db.query(SysUser).filter(SysUser.id == 3).first()
    if corp is None:
        raise RuntimeError("未找到企业用户 corp1 (id=3), 请先运行 init_db 或创建 corp1 用户")
    return corp


def create_seekers(db) -> int:
    """创建求职者用户 (已存在则跳过), 返回新增数量"""
    pwd_hash = hash_password(DEFAULT_PASSWORD)
    created = 0
    for s in SEEKERS:
        existing = db.query(SysUser).filter(SysUser.username == s["username"]).first()
        if existing:
            print(f"  [SKIP] 用户 {s['username']} 已存在 (id={existing.id})")
            continue
        user = SysUser(
            username=s["username"],
            password_hash=pwd_hash,
            role=ROLE_SEEKER,
            phone=s["phone"],
            email=s["email"],
            nickname=s["nickname"],
            real_name=s["real_name"],
            gender=s["gender"],
            status=1,
        )
        db.add(user)
        db.flush()
        created += 1
        print(f"  [NEW] 创建用户 {s['username']} (id={user.id})")
    db.commit()
    return created


def create_jobs(db, corp_user: SysUser) -> int:
    """为 corp_user 创建所有职位, 返回新增数量"""
    created = 0
    for j in JOBS:
        job = Job(
            user_id=corp_user.id,
            title=j["title"],
            company=j["company"],
            department=j["department"],
            job_type="全职",
            salary_min=j["salary_min"],
            salary_max=j["salary_max"],
            salary_unit="K",
            work_city=j["work_city"],
            experience_required=j["experience_required"],
            education_required=j["education_required"],
            headcount=j["headcount"],
            status=1,
            description=j["description"],
            doc_url=f"uploads/job/demo_{created + 1}.pdf",
        )
        db.add(job)
        db.flush()
        for req in j["requirements"]:
            db.add(JobRequirement(
                job_id=job.id,
                skill_name=req["skill_name"],
                req_type=req["req_type"],
                weight=req["weight"],
            ))
        created += 1
        print(f"  [NEW] 创建职位 #{job.id} {j['title']} @ {j['company']} ({j['work_city']})")
    db.commit()
    return created


def create_resumes(db) -> int:
    """为求职者创建简历, 返回新增数量"""
    created = 0
    for r in RESUMES:
        user = db.query(SysUser).filter(SysUser.username == r["seeker_username"]).first()
        if user is None:
            print(f"  [WARN] 用户 {r['seeker_username']} 不存在, 跳过该简历")
            continue
        resume = Resume(
            user_id=user.id,
            doc_url=f"uploads/resume/demo_{r['seeker_username']}_{created + 1}.pdf",
            doc_hash=None,
            parse_status=2,
            parse_error=None,
            name=r["name"],
            gender=r["gender"],
            age=r["age"],
            phone=r["phone"],
            email=r["email"],
            current_city=r["current_city"],
            intention_cities=json.dumps(r["intention_cities"], ensure_ascii=False),
            education=r["education"],
            school=r["school"],
            major=r["major"],
            work_years=r["work_years"],
            expected_salary_min=r["expected_salary_min"],
            expected_salary_max=r["expected_salary_max"],
            self_evaluation=r["self_evaluation"],
            raw_parse_json=make_raw_parse_json(r),
            embedding=None,
        )
        db.add(resume)
        db.flush()
        for sk in r["skills"]:
            db.add(ResumeSkill(
                resume_id=resume.id,
                skill_name=sk["skill_name"],
                skill_level=sk["skill_level"],
                weight=sk["weight"],
            ))
        created += 1
        print(f"  [NEW] 创建简历 #{resume.id} {r['name']} ({r['education']}/{r['work_years']}年) -> {r['seeker_username']}")
    db.commit()
    return created


# ============================================================
# 主函数
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="智聘云图 - 演示数据填充脚本")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="先清空 resume/job/application/match_record 表 (保留所有用户)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  智聘云图 - 演示数据填充脚本")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 1. 可选: 清空已有测试数据
        if args.reset:
            reset_data(db)
        else:
            print("[INFO] 追加模式 (如需清空已有数据请加 --reset)")

        # 2. 获取企业用户
        corp_user = get_or_create_corp_user(db)
        print(f"[INFO] 企业用户: {corp_user.username} (id={corp_user.id})")

        # 3. 创建求职者用户
        print("\n--- 创建求职者用户 ---")
        new_seekers = create_seekers(db)

        # 4. 创建职位
        print("\n--- 创建职位 ---")
        new_jobs = create_jobs(db, corp_user)

        # 5. 创建简历
        print("\n--- 创建简历 ---")
        new_resumes = create_resumes(db)

        # 6. 统计
        print("\n" + "=" * 60)
        print("  数据填充完成!")
        print("=" * 60)
        print(f"  新增求职者用户: {new_seekers} 人")
        print(f"  新增职位:       {new_jobs} 个")
        print(f"  新增简历:       {new_resumes} 份")
        print(f"  (embedding 未生成, 首次匹配时由 match_service 批量生成)")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
