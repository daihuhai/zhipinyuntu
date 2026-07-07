#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
智聘云图招聘平台 - 测试数据扩充脚本

参考中国科学技术大学 Job-SDF 数据集精神, 扩充更多测试数据, 覆盖客户端/游戏/安全/数据库/
嵌入式/架构/区块链/音视频/电商/汽车/教育/金融等更多技术方向。

用法:
    cd d:\\智聘云图\\backend
    .\\venv\\Scripts\\python.exe scripts\\seed_more_data.py                    # 追加模式
    .\\venv\\Scripts\\python.exe scripts\\seed_more_data.py --reset-jobs-only  # 只清空并重建职位

数据规模:
    - 企业用户:   新增 14 个 (corp_bytedance / corp_tencent 等)
    - 求职者:     新增 seeker10~seeker15 (6 个)
    - 简历:       新增 20 份 (覆盖 10 个技术方向, 每方向 2 份)
    - 职位:       新增 30 个 (覆盖 12 个技术方向, 每方向 2-3 个)
    - 不调用 AI, 不生成 embedding (由 match_service 首次匹配时批量生成)
    - 幂等执行: 重复运行不创建重复数据 (按 username / job title+company 判重)
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

ROLE_EMPLOYER = "ROLE_EMPLOYER"
ROLE_SEEKER = "ROLE_SEEKER"
DEFAULT_PASSWORD = "123456"


# ============================================================
# 企业用户数据 (14 个)
# ============================================================
CORP_USERS = [
    {"username": "corp_bytedance", "nickname": "字节跳动HR", "company": "字节跳动", "phone": "13900100001"},
    {"username": "corp_zhihu",     "nickname": "知乎HR",     "company": "知乎",     "phone": "13900100002"},
    {"username": "corp_tencent",   "nickname": "腾讯HR",     "company": "腾讯",     "phone": "13900100003"},
    {"username": "corp_huawei",    "nickname": "华为HR",     "company": "华为",     "phone": "13900100004"},
    {"username": "corp_netease",   "nickname": "网易HR",     "company": "网易",     "phone": "13900100005"},
    {"username": "corp_alibaba",   "nickname": "阿里巴巴HR", "company": "阿里巴巴", "phone": "13900100006"},
    {"username": "corp_meituan",   "nickname": "美团HR",     "company": "美团",     "phone": "13900100007"},
    {"username": "corp_pdd",       "nickname": "拼多多HR",   "company": "拼多多",   "phone": "13900100008"},
    {"username": "corp_xiaomi",    "nickname": "小米HR",     "company": "小米",     "phone": "13900100009"},
    {"username": "corp_baidu",     "nickname": "百度HR",     "company": "百度",     "phone": "13900100010"},
    {"username": "corp_sensetime", "nickname": "商汤科技HR", "company": "商汤科技", "phone": "13900100011"},
    {"username": "corp_kuaishou",  "nickname": "快手HR",     "company": "快手",     "phone": "13900100012"},
    {"username": "corp_jd",        "nickname": "京东HR",     "company": "京东",     "phone": "13900100013"},
    {"username": "corp_bilibili",  "nickname": "哔哩哔哩HR", "company": "哔哩哔哩", "phone": "13900100014"},
]


# ============================================================
# 新增求职者数据 (seeker10 ~ seeker15)
# ============================================================
NEW_SEEKERS = [
    {
        "username": "seeker10",
        "nickname": "孙浩",
        "real_name": "孙浩",
        "gender": "男",
        "phone": "13800000010",
        "email": "sunhao@example.com",
    },
    {
        "username": "seeker11",
        "nickname": "钱琪",
        "real_name": "钱琪",
        "gender": "女",
        "phone": "13800000011",
        "email": "qianqi@example.com",
    },
    {
        "username": "seeker12",
        "nickname": "冯涛",
        "real_name": "冯涛",
        "gender": "男",
        "phone": "13800000012",
        "email": "fengtao@example.com",
    },
    {
        "username": "seeker13",
        "nickname": "蒋勇",
        "real_name": "蒋勇",
        "gender": "男",
        "phone": "13800000013",
        "email": "jiangyong@example.com",
    },
    {
        "username": "seeker14",
        "nickname": "韩梅",
        "real_name": "韩梅",
        "gender": "女",
        "phone": "13800000014",
        "email": "hanmei@example.com",
    },
    {
        "username": "seeker15",
        "nickname": "沈磊",
        "real_name": "沈磊",
        "gender": "男",
        "phone": "13800000015",
        "email": "shenlei@example.com",
    },
]


# ============================================================
# 新增职位数据 (30 个, 覆盖 12 个技术方向)
# ============================================================
NEW_JOBS = [
    # ---- 客户端开发 (3) ----
    {
        "title": "Android工程师",
        "company": "字节跳动",
        "department": "客户端架构",
        "work_city": "北京",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 3,
        "description": "负责字节跳动核心产品 Android 客户端开发, 涉及抖音/今日头条等亿级用户应用, 持续优化性能与用户体验。",
        "requirements": [
            {"skill_name": "Java", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Kotlin", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Android SDK", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Jetpack", "req_type": "必须", "weight": 0.8},
            {"skill_name": "RxJava", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Flutter", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "iOS工程师",
        "company": "腾讯",
        "department": "移动事业部",
        "work_city": "深圳",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责腾讯核心社交产品 iOS 客户端开发, 参与 QQ/微信生态建设, 优化客户端架构与性能。",
        "requirements": [
            {"skill_name": "Swift", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Objective-C", "req_type": "必须", "weight": 0.9},
            {"skill_name": "SwiftUI", "req_type": "必须", "weight": 0.8},
            {"skill_name": "CoreData", "req_type": "优先", "weight": 0.6},
            {"skill_name": "AVFoundation", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "Flutter跨端工程师",
        "company": "小米",
        "department": "MIUI国际部",
        "work_city": "北京",
        "salary_min": 20,
        "salary_max": 40,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责小米国际业务 Flutter 跨端应用开发, 一套代码覆盖 Android/iOS 双端, 保障体验一致性。",
        "requirements": [
            {"skill_name": "Flutter", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Dart", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Android SDK", "req_type": "必须", "weight": 0.8},
            {"skill_name": "iOS", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Kotlin", "req_type": "优先", "weight": 0.5},
            {"skill_name": "Swift", "req_type": "优先", "weight": 0.5},
        ],
    },
    # ---- 游戏开发 (3) ----
    {
        "title": "Unity3D开发工程师",
        "company": "网易",
        "department": "雷火工作室",
        "work_city": "杭州",
        "salary_min": 22,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责网易游戏 Unity3D 客户端开发, 涉及角色控制/战斗系统/UI框架等核心模块。",
        "requirements": [
            {"skill_name": "Unity3D", "req_type": "必须", "weight": 1.0},
            {"skill_name": "C#", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Shader", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Lua", "req_type": "优先", "weight": 0.6},
            {"skill_name": "3D数学", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "Cocos游戏开发",
        "company": "哔哩哔哩",
        "department": "游戏事业部",
        "work_city": "上海",
        "salary_min": 18,
        "salary_max": 35,
        "experience_required": "1-3年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责 B 站休闲游戏 Cocos 引擎开发, 涉及游戏逻辑/渲染优化/性能调优。",
        "requirements": [
            {"skill_name": "Cocos2d-x", "req_type": "必须", "weight": 1.0},
            {"skill_name": "C++", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Lua", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Shader", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "Unreal开发工程师",
        "company": "腾讯",
        "department": "天美工作室",
        "work_city": "深圳",
        "salary_min": 28,
        "salary_max": 55,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责腾讯 AAA 级游戏 Unreal Engine 开发, 涉及渲染管线/物理引擎/工具链建设。",
        "requirements": [
            {"skill_name": "Unreal Engine", "req_type": "必须", "weight": 1.0},
            {"skill_name": "C++", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Shader", "req_type": "必须", "weight": 0.8},
            {"skill_name": "3D数学", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Blueprint", "req_type": "优先", "weight": 0.6},
        ],
    },
    # ---- 安全方向 (2) ----
    {
        "title": "网络安全工程师",
        "company": "腾讯",
        "department": "安全应急响应中心",
        "work_city": "深圳",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责腾讯产品安全防护体系建设, 包括 WAF/入侵检测/漏洞修复等, 保障亿万用户数据安全。",
        "requirements": [
            {"skill_name": "Python", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Linux", "req_type": "必须", "weight": 0.9},
            {"skill_name": "渗透测试", "req_type": "必须", "weight": 0.9},
            {"skill_name": "漏洞挖掘", "req_type": "必须", "weight": 0.8},
            {"skill_name": "密码学", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "渗透测试工程师",
        "company": "京东",
        "department": "安全部",
        "work_city": "北京",
        "salary_min": 22,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责京东核心业务系统渗透测试与红蓝对抗, 发现并修复安全隐患, 提升整体安全水位。",
        "requirements": [
            {"skill_name": "渗透测试", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Linux", "req_type": "必须", "weight": 0.8},
            {"skill_name": "漏洞挖掘", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Metasploit", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Burp Suite", "req_type": "优先", "weight": 0.6},
        ],
    },
    # ---- 数据库方向 (3) ----
    {
        "title": "DBA数据库工程师",
        "company": "阿里巴巴",
        "department": "数据库平台",
        "work_city": "杭州",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "5-10年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责阿里云数据库运维与优化, 保障核心交易系统数据库高可用, 涉及 MySQL/Redis/OceanBase 等。",
        "requirements": [
            {"skill_name": "MySQL", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Redis", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Linux", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Oracle", "req_type": "优先", "weight": 0.6},
            {"skill_name": "PostgreSQL", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "数据库内核开发",
        "company": "华为",
        "department": "高斯实验室",
        "work_city": "深圳",
        "salary_min": 30,
        "salary_max": 60,
        "experience_required": "3-5年",
        "education_required": "硕士",
        "headcount": 2,
        "description": "参与华为 openGauss 数据库内核研发, 涉及存储引擎/查询优化器/事务管理等核心模块。",
        "requirements": [
            {"skill_name": "C++", "req_type": "必须", "weight": 1.0},
            {"skill_name": "MySQL", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Linux", "req_type": "必须", "weight": 0.8},
            {"skill_name": "数据结构", "req_type": "必须", "weight": 0.9},
            {"skill_name": "PostgreSQL", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "大数据DBA",
        "company": "字节跳动",
        "department": "数据平台",
        "work_city": "北京",
        "salary_min": 28,
        "salary_max": 55,
        "experience_required": "5-10年",
        "education_required": "本科",
        "headcount": 1,
        "description": "负责字节跳动大数据平台数据库运维, 涉及 ClickHouse/HBase/MySQL 等, 保障数据稳定性。",
        "requirements": [
            {"skill_name": "MySQL", "req_type": "必须", "weight": 0.9},
            {"skill_name": "HBase", "req_type": "必须", "weight": 0.8},
            {"skill_name": "ClickHouse", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Linux", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Hadoop", "req_type": "优先", "weight": 0.6},
        ],
    },
    # ---- 嵌入式/硬件 (3) ----
    {
        "title": "嵌入式软件工程师",
        "company": "华为",
        "department": "终端BG",
        "work_city": "深圳",
        "salary_min": 22,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 3,
        "description": "负责华为终端产品嵌入式软件开发, 涉及手机/平板/穿戴设备底层系统与驱动。",
        "requirements": [
            {"skill_name": "C", "req_type": "必须", "weight": 1.0},
            {"skill_name": "C++", "req_type": "必须", "weight": 0.9},
            {"skill_name": "RTOS", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Linux", "req_type": "必须", "weight": 0.8},
            {"skill_name": "ARM", "req_type": "优先", "weight": 0.6},
            {"skill_name": "单片机", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "固件开发工程师",
        "company": "小米",
        "department": "生态链部",
        "work_city": "北京",
        "salary_min": 20,
        "salary_max": 40,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责小米 IoT 生态链产品固件开发, 涉及智能家居/可穿戴设备固件设计与优化。",
        "requirements": [
            {"skill_name": "C", "req_type": "必须", "weight": 1.0},
            {"skill_name": "单片机", "req_type": "必须", "weight": 0.9},
            {"skill_name": "ARM", "req_type": "必须", "weight": 0.8},
            {"skill_name": "RTOS", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Linux", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "物联网开发工程师",
        "company": "华为",
        "department": "云核心网",
        "work_city": "深圳",
        "salary_min": 22,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责华为 IoT 平台开发, 涉及设备接入/协议适配/边缘计算等物联网核心能力建设。",
        "requirements": [
            {"skill_name": "C", "req_type": "必须", "weight": 0.9},
            {"skill_name": "C++", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Linux", "req_type": "必须", "weight": 0.8},
            {"skill_name": "MQTT", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Python", "req_type": "优先", "weight": 0.5},
        ],
    },
    # ---- 架构/管理 (3) ----
    {
        "title": "高级架构师",
        "company": "字节跳动",
        "department": "技术架构部",
        "work_city": "北京",
        "salary_min": 40,
        "salary_max": 70,
        "experience_required": "5-10年",
        "education_required": "本科",
        "headcount": 1,
        "description": "负责字节跳动核心业务系统架构设计, 主导微服务拆分/高可用方案/技术选型, 指导团队技术演进。",
        "requirements": [
            {"skill_name": "Java", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Spring Cloud", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Kubernetes", "req_type": "必须", "weight": 0.9},
            {"skill_name": "微服务", "req_type": "必须", "weight": 0.9},
            {"skill_name": "分布式", "req_type": "必须", "weight": 0.9},
            {"skill_name": "MySQL", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "技术Leader",
        "company": "美团",
        "department": "到店事业群",
        "work_city": "北京",
        "salary_min": 35,
        "salary_max": 60,
        "experience_required": "5-10年",
        "education_required": "本科",
        "headcount": 1,
        "description": "负责美团到店业务技术团队管理, 主导技术方案设计, 推进项目落地, 培养团队成员。",
        "requirements": [
            {"skill_name": "Java", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Spring Boot", "req_type": "必须", "weight": 0.9},
            {"skill_name": "微服务", "req_type": "必须", "weight": 0.8},
            {"skill_name": "MySQL", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Redis", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Kubernetes", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "CTO助理",
        "company": "快手",
        "department": "技术战略部",
        "work_city": "北京",
        "salary_min": 30,
        "salary_max": 55,
        "experience_required": "5-10年",
        "education_required": "硕士",
        "headcount": 1,
        "description": "协助 CTO 推进技术战略落地, 负责技术调研/跨部门协调/技术规划, 搭建技术管理体系。",
        "requirements": [
            {"skill_name": "Java", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.8},
            {"skill_name": "微服务", "req_type": "优先", "weight": 0.7},
            {"skill_name": "Kubernetes", "req_type": "优先", "weight": 0.6},
            {"skill_name": "数据分析", "req_type": "优先", "weight": 0.5},
        ],
    },
    # ---- 区块链/Web3 (2) ----
    {
        "title": "区块链开发工程师",
        "company": "蚂蚁集团",
        "department": "蚂蚁链",
        "work_city": "杭州",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责蚂蚁链底层区块链平台开发, 涉及共识算法/智能合约/跨链协议等核心模块。",
        "requirements": [
            {"skill_name": "Go", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Solidity", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Ethereum", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Hyperledger", "req_type": "优先", "weight": 0.7},
            {"skill_name": "分布式", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "智能合约工程师",
        "company": "币安",
        "department": "DeFi实验室",
        "work_city": "远程",
        "salary_min": 30,
        "salary_max": 60,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责币安 DeFi 产品智能合约开发与审计, 涉及 ERC-20/ERC-721/闪电贷等链上协议。",
        "requirements": [
            {"skill_name": "Solidity", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Ethereum", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Go", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Web3.js", "req_type": "必须", "weight": 0.8},
            {"skill_name": "密码学", "req_type": "优先", "weight": 0.6},
        ],
    },
    # ---- 音视频 (2) ----
    {
        "title": "音视频开发工程师",
        "company": "字节跳动",
        "department": "多媒体实验室",
        "work_city": "北京",
        "salary_min": 28,
        "salary_max": 55,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责字节跳动音视频 SDK 开发, 涉及抖音/飞书实时音视频通话, 优化编解码与传输性能。",
        "requirements": [
            {"skill_name": "C++", "req_type": "必须", "weight": 1.0},
            {"skill_name": "FFmpeg", "req_type": "必须", "weight": 0.9},
            {"skill_name": "WebRTC", "req_type": "必须", "weight": 0.9},
            {"skill_name": "RTMP", "req_type": "优先", "weight": 0.6},
            {"skill_name": "HLS", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "流媒体工程师",
        "company": "哔哩哔哩",
        "department": "直播技术",
        "work_city": "上海",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责 B 站直播流媒体分发系统开发, 涉及转码/CDN 调度/低延迟直播等核心技术。",
        "requirements": [
            {"skill_name": "C++", "req_type": "必须", "weight": 1.0},
            {"skill_name": "FFmpeg", "req_type": "必须", "weight": 0.9},
            {"skill_name": "RTMP", "req_type": "必须", "weight": 0.8},
            {"skill_name": "HLS", "req_type": "必须", "weight": 0.8},
            {"skill_name": "WebRTC", "req_type": "优先", "weight": 0.6},
        ],
    },
    # ---- 电商/运营 (2) ----
    {
        "title": "电商运营工程师",
        "company": "拼多多",
        "department": "用户增长",
        "work_city": "上海",
        "salary_min": 18,
        "salary_max": 35,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责拼多多电商运营系统开发, 涉及活动玩法/营销工具/数据看板, 用技术驱动业务增长。",
        "requirements": [
            {"skill_name": "Python", "req_type": "必须", "weight": 0.9},
            {"skill_name": "SQL", "req_type": "必须", "weight": 0.9},
            {"skill_name": "数据分析", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Java", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Vue3", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "增长黑客",
        "company": "小红书",
        "department": "增长团队",
        "work_city": "上海",
        "salary_min": 22,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 1,
        "description": "负责小红书用户增长策略落地, 搭建 A/B 实验平台, 通过数据驱动产品迭代与用户裂变。",
        "requirements": [
            {"skill_name": "Python", "req_type": "必须", "weight": 0.9},
            {"skill_name": "数据分析", "req_type": "必须", "weight": 0.9},
            {"skill_name": "SQL", "req_type": "必须", "weight": 0.8},
            {"skill_name": "机器学习", "req_type": "优先", "weight": 0.6},
            {"skill_name": "A/B测试", "req_type": "优先", "weight": 0.6},
        ],
    },
    # ---- 汽车/出行 (2) ----
    {
        "title": "自动驾驶工程师",
        "company": "百度",
        "department": "Apollo",
        "work_city": "北京",
        "salary_min": 30,
        "salary_max": 60,
        "experience_required": "3-5年",
        "education_required": "硕士",
        "headcount": 3,
        "description": "负责百度 Apollo 自动驾驶系统研发, 涉及感知/决策/控制等核心模块, 推动无人驾驶落地。",
        "requirements": [
            {"skill_name": "C++", "req_type": "必须", "weight": 1.0},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.9},
            {"skill_name": "深度学习", "req_type": "必须", "weight": 0.9},
            {"skill_name": "计算机视觉", "req_type": "必须", "weight": 0.8},
            {"skill_name": "ROS", "req_type": "优先", "weight": 0.6},
            {"skill_name": "Linux", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "车联网开发",
        "company": "蔚来",
        "department": "智能座舱",
        "work_city": "上海",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责蔚来汽车车联网平台开发, 涉及车机系统/远程控制/OTA 升级等智能座舱能力。",
        "requirements": [
            {"skill_name": "Java", "req_type": "必须", "weight": 0.9},
            {"skill_name": "C++", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Linux", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Android SDK", "req_type": "优先", "weight": 0.6},
            {"skill_name": "MQTT", "req_type": "优先", "weight": 0.5},
        ],
    },
    # ---- 教育/医疗 (2) ----
    {
        "title": "教育产品开发",
        "company": "猿辅导",
        "department": "技术中台",
        "work_city": "北京",
        "salary_min": 22,
        "salary_max": 45,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责猿辅导在线教育产品开发, 涉及直播课堂/互动白板/智能题库等核心功能。",
        "requirements": [
            {"skill_name": "Java", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Go", "req_type": "必须", "weight": 0.8},
            {"skill_name": "WebRTC", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Redis", "req_type": "优先", "weight": 0.6},
            {"skill_name": "MySQL", "req_type": "优先", "weight": 0.5},
        ],
    },
    {
        "title": "医疗AI工程师",
        "company": "平安科技",
        "department": "医疗AI实验室",
        "work_city": "深圳",
        "salary_min": 28,
        "salary_max": 55,
        "experience_required": "3-5年",
        "education_required": "硕士",
        "headcount": 2,
        "description": "负责平安医疗 AI 产品研发, 涉及医学影像分析/病历结构化/辅助诊断等方向。",
        "requirements": [
            {"skill_name": "Python", "req_type": "必须", "weight": 1.0},
            {"skill_name": "深度学习", "req_type": "必须", "weight": 0.9},
            {"skill_name": "PyTorch", "req_type": "必须", "weight": 0.9},
            {"skill_name": "计算机视觉", "req_type": "必须", "weight": 0.8},
            {"skill_name": "NLP", "req_type": "优先", "weight": 0.6},
        ],
    },
    # ---- 金融 (3) ----
    {
        "title": "量化开发工程师",
        "company": "华泰证券",
        "department": "量化自营",
        "work_city": "上海",
        "salary_min": 30,
        "salary_max": 60,
        "experience_required": "3-5年",
        "education_required": "硕士",
        "headcount": 2,
        "description": "负责华泰证券量化交易系统开发, 涉及策略回测/低延迟交易/风控引擎等核心模块。",
        "requirements": [
            {"skill_name": "Python", "req_type": "必须", "weight": 1.0},
            {"skill_name": "C++", "req_type": "必须", "weight": 0.9},
            {"skill_name": "NumPy", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Pandas", "req_type": "必须", "weight": 0.8},
            {"skill_name": "机器学习", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "风控工程师",
        "company": "蚂蚁集团",
        "department": "风险管理部",
        "work_city": "杭州",
        "salary_min": 25,
        "salary_max": 50,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 2,
        "description": "负责蚂蚁集团风控引擎开发, 涉及实时反欺诈/信用评估/模型部署等, 保障资金安全。",
        "requirements": [
            {"skill_name": "Java", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Python", "req_type": "必须", "weight": 0.9},
            {"skill_name": "机器学习", "req_type": "必须", "weight": 0.8},
            {"skill_name": "SQL", "req_type": "必须", "weight": 0.7},
            {"skill_name": "Flink", "req_type": "优先", "weight": 0.6},
        ],
    },
    {
        "title": "区块链金融工程师",
        "company": "蚂蚁集团",
        "department": "数字金融",
        "work_city": "杭州",
        "salary_min": 28,
        "salary_max": 55,
        "experience_required": "3-5年",
        "education_required": "本科",
        "headcount": 1,
        "description": "负责蚂蚁集团区块链金融产品开发, 涉及跨境支付/供应链金融/数字资产等创新场景。",
        "requirements": [
            {"skill_name": "Go", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Java", "req_type": "必须", "weight": 0.9},
            {"skill_name": "Solidity", "req_type": "必须", "weight": 0.8},
            {"skill_name": "Hyperledger", "req_type": "优先", "weight": 0.6},
            {"skill_name": "分布式", "req_type": "优先", "weight": 0.5},
        ],
    },
]


# ============================================================
# 新增简历数据 (20 份, 覆盖 10 个技术方向)
# ============================================================
NEW_RESUMES = [
    # ===== seeker10: Android开发 (5年) =====
    {
        "seeker_username": "seeker10",
        "name": "孙浩",
        "gender": "男",
        "age": 27,
        "phone": "13800000010",
        "email": "sunhao@example.com",
        "current_city": "北京",
        "intention_cities": ["北京", "深圳"],
        "education": "本科",
        "school": "北京邮电大学",
        "major": "计算机科学与技术",
        "work_years": 5,
        "expected_salary_min": 25,
        "expected_salary_max": 45,
        "self_evaluation": "5 年 Android 开发经验, 熟悉 Java/Kotlin 双语言栈, 主导过亿级用户应用架构升级, 对性能优化有深入实践。",
        "skills": [
            {"skill_name": "Java", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "Kotlin", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Android SDK", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Jetpack", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "RxJava", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Flutter", "skill_level": "掌握", "weight": 0.65},
        ],
        "projects": [
            {"name": "短视频客户端重构", "description": "主导短视频应用从 Java 迁移到 Kotlin, 引入 Jetpack MVVM 架构, 启动速度提升 40%。", "role": "技术负责人"},
            {"name": "Android 性能监控 SDK", "description": "开发线上性能监控 SDK, 覆盖 FPS/内存/卡顿/ANR 等指标, 接入 10+ 业务线。", "role": "核心开发"},
        ],
        "work_experience": [
            {"company": "字节跳动", "position": "Android开发工程师", "duration": "2021.07 - 至今"},
            {"company": "美团", "position": "Android开发工程师", "duration": "2019.07 - 2021.06"},
        ],
    },
    {
        "seeker_username": "seeker10",
        "name": "孙浩",
        "gender": "男",
        "age": 27,
        "phone": "13800000010",
        "email": "sunhao@example.com",
        "current_city": "北京",
        "intention_cities": ["北京", "上海", "深圳"],
        "education": "本科",
        "school": "北京邮电大学",
        "major": "计算机科学与技术",
        "work_years": 5,
        "expected_salary_min": 25,
        "expected_salary_max": 50,
        "self_evaluation": "具备 Flutter 跨端开发能力, 有 Android/iOS 双端项目经验, 熟悉 Dart 语言与 Flutter 引擎原理。",
        "skills": [
            {"skill_name": "Flutter", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Dart", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Android SDK", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Kotlin", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Swift", "skill_level": "掌握", "weight": 0.6},
            {"skill_name": "Java", "skill_level": "精通", "weight": 0.9},
        ],
        "projects": [
            {"name": "Flutter 跨端电商应用", "description": "使用 Flutter 开发电商应用, 一套代码覆盖 Android/iOS 双端, 研发效率提升 50%。", "role": "前端负责人"},
        ],
        "work_experience": [
            {"company": "字节跳动", "position": "Android开发工程师", "duration": "2021.07 - 至今"},
        ],
    },
    # ===== seeker11: iOS开发 (6年) =====
    {
        "seeker_username": "seeker11",
        "name": "钱琪",
        "gender": "女",
        "age": 28,
        "phone": "13800000011",
        "email": "qianqi@example.com",
        "current_city": "深圳",
        "intention_cities": ["深圳", "广州", "北京"],
        "education": "本科",
        "school": "哈尔滨工业大学",
        "major": "软件工程",
        "work_years": 6,
        "expected_salary_min": 25,
        "expected_salary_max": 45,
        "self_evaluation": "6 年 iOS 开发经验, 精通 Swift/Objective-C, 熟悉 SwiftUI 声明式 UI, 有大型社交应用开发经验。",
        "skills": [
            {"skill_name": "Swift", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "Objective-C", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "SwiftUI", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "CoreData", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "AVFoundation", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Combine", "skill_level": "熟练", "weight": 0.75},
        ],
        "projects": [
            {"name": "社交应用 SwiftUI 重构", "description": "将 OC 老项目逐步迁移到 SwiftUI, 引入 Combine 响应式框架, 代码量减少 30%。", "role": "iOS负责人"},
            {"name": "短视频拍摄 SDK", "description": "基于 AVFoundation 开发短视频拍摄 SDK, 支持滤镜/美颜/特效, 接入 5+ 应用。", "role": "核心开发"},
        ],
        "work_experience": [
            {"company": "腾讯", "position": "iOS开发工程师", "duration": "2020.07 - 至今"},
            {"company": "网易", "position": "iOS开发工程师", "duration": "2018.07 - 2020.06"},
        ],
    },
    {
        "seeker_username": "seeker11",
        "name": "钱琪",
        "gender": "女",
        "age": 28,
        "phone": "13800000011",
        "email": "qianqi@example.com",
        "current_city": "深圳",
        "intention_cities": ["深圳", "上海"],
        "education": "本科",
        "school": "哈尔滨工业大学",
        "major": "软件工程",
        "work_years": 6,
        "expected_salary_min": 28,
        "expected_salary_max": 50,
        "self_evaluation": "专注 iOS 音视频方向, 熟悉 AVFoundation/VideoToolbox, 有实时音视频通话开发经验。",
        "skills": [
            {"skill_name": "Swift", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "AVFoundation", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Objective-C", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "CoreData", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "SwiftUI", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "iOS 实时通话模块", "description": "基于 WebRTC 开发 iOS 端实时通话模块, 支持多人视频/语音, 弱网体验优化。", "role": "iOS开发"},
        ],
        "work_experience": [
            {"company": "腾讯", "position": "iOS开发工程师", "duration": "2020.07 - 至今"},
        ],
    },
    # ===== seeker12: 游戏开发 (4年) =====
    {
        "seeker_username": "seeker12",
        "name": "冯涛",
        "gender": "男",
        "age": 26,
        "phone": "13800000012",
        "email": "fengtao@example.com",
        "current_city": "上海",
        "intention_cities": ["上海", "杭州", "深圳"],
        "education": "本科",
        "school": "上海交通大学",
        "major": "数字媒体技术",
        "work_years": 4,
        "expected_salary_min": 20,
        "expected_salary_max": 40,
        "self_evaluation": "4 年 Unity3D 游戏开发经验, 熟悉 C#/Shader/Lua, 参与过 2 款 MMORPG 上线项目, 对渲染优化有深入实践。",
        "skills": [
            {"skill_name": "Unity3D", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "C#", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Shader", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Lua", "skill_level": "熟练", "weight": 0.75},
            {"skill_name": "3D数学", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "MMORPG 战斗系统", "description": "负责战斗系统核心逻辑开发, 包括技能系统/Buff系统/伤害计算, 支持 100v100 团战。", "role": "客户端开发"},
            {"name": "渲染优化", "description": "优化 GPU 渲染管线, DrawCall 从 800 降至 200, 帧率提升 50%。", "role": "性能优化"},
        ],
        "work_experience": [
            {"company": "网易", "position": "Unity3D开发工程师", "duration": "2021.07 - 至今"},
        ],
    },
    {
        "seeker_username": "seeker12",
        "name": "冯涛",
        "gender": "男",
        "age": 26,
        "phone": "13800000012",
        "email": "fengtao@example.com",
        "current_city": "上海",
        "intention_cities": ["上海", "广州"],
        "education": "本科",
        "school": "上海交通大学",
        "major": "数字媒体技术",
        "work_years": 4,
        "expected_salary_min": 18,
        "expected_salary_max": 35,
        "self_evaluation": "同时具备 Cocos 引擎开发经验, 熟悉 C++/Lua, 有休闲小游戏项目经验。",
        "skills": [
            {"skill_name": "Cocos2d-x", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "C++", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Lua", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Shader", "skill_level": "掌握", "weight": 0.7},
            {"skill_name": "Unity3D", "skill_level": "精通", "weight": 0.9},
        ],
        "projects": [
            {"name": "休闲小游戏合集", "description": "使用 Cocos2d-x 开发休闲小游戏合集, 包含 10+ 玩法, 累计下载 500 万+。", "role": "主程"},
        ],
        "work_experience": [
            {"company": "哔哩哔哩", "position": "游戏开发工程师", "duration": "2020.07 - 2021.06"},
        ],
    },
    # ===== seeker13: 安全工程师 (5年) =====
    {
        "seeker_username": "seeker13",
        "name": "蒋勇",
        "gender": "男",
        "age": 29,
        "phone": "13800000013",
        "email": "jiangyong@example.com",
        "current_city": "北京",
        "intention_cities": ["北京", "深圳", "上海"],
        "education": "硕士",
        "school": "中国科学院大学",
        "major": "信息安全",
        "work_years": 5,
        "expected_salary_min": 25,
        "expected_salary_max": 50,
        "self_evaluation": "5 年网络安全工程师经验, 熟悉渗透测试与漏洞挖掘, 曾发现多个 CVE 漏洞, 有大型互联网安全防护经验。",
        "skills": [
            {"skill_name": "Python", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Linux", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "渗透测试", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "漏洞挖掘", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "密码学", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Burp Suite", "skill_level": "熟练", "weight": 0.85},
        ],
        "projects": [
            {"name": "企业红蓝对抗", "description": "主导年度红蓝对抗演练, 发现高危漏洞 15 个, 推动修复并完善安全防护体系。", "role": "红队队长"},
            {"name": "WAF 规则引擎", "description": "开发 WAF 规则引擎, 覆盖 OWASP Top 10 攻击类型, 误报率低于 0.1%。", "role": "安全开发"},
        ],
        "work_experience": [
            {"company": "腾讯", "position": "安全工程师", "duration": "2021.07 - 至今"},
            {"company": "奇安信", "position": "渗透测试工程师", "duration": "2019.07 - 2021.06"},
        ],
    },
    {
        "seeker_username": "seeker13",
        "name": "蒋勇",
        "gender": "男",
        "age": 29,
        "phone": "13800000013",
        "email": "jiangyong@example.com",
        "current_city": "北京",
        "intention_cities": ["北京", "杭州"],
        "education": "硕士",
        "school": "中国科学院大学",
        "major": "信息安全",
        "work_years": 5,
        "expected_salary_min": 25,
        "expected_salary_max": 50,
        "self_evaluation": "具备安全研究能力, 熟悉密码学与逆向工程, 有区块链安全审计经验。",
        "skills": [
            {"skill_name": "Python", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "密码学", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "漏洞挖掘", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "逆向工程", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Solidity", "skill_level": "掌握", "weight": 0.65},
            {"skill_name": "Linux", "skill_level": "精通", "weight": 0.85},
        ],
        "projects": [
            {"name": "智能合约安全审计", "description": "对 50+ 智能合约进行安全审计, 发现重入攻击/整数溢出等漏洞 20+ 个。", "role": "安全审计员"},
        ],
        "work_experience": [
            {"company": "腾讯", "position": "安全工程师", "duration": "2021.07 - 至今"},
        ],
    },
    # ===== seeker14: DBA (8年) =====
    {
        "seeker_username": "seeker14",
        "name": "韩梅",
        "gender": "女",
        "age": 32,
        "phone": "13800000014",
        "email": "hanmei@example.com",
        "current_city": "杭州",
        "intention_cities": ["杭州", "北京", "上海"],
        "education": "本科",
        "school": "南京大学",
        "major": "计算机科学与技术",
        "work_years": 8,
        "expected_salary_min": 28,
        "expected_salary_max": 55,
        "self_evaluation": "8 年 DBA 经验, 精通 MySQL/Redis 运维与优化, 管理过 PB 级数据库集群, 有丰富的故障处理与性能调优经验。",
        "skills": [
            {"skill_name": "MySQL", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "Redis", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Linux", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Oracle", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "PostgreSQL", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Shell", "skill_level": "熟练", "weight": 0.75},
        ],
        "projects": [
            {"name": "MySQL 分库分表迁移", "description": "主导核心交易系统 MySQL 分库分表, 数据量 50 亿+ 平滑迁移, 零停机。", "role": "DBA负责人"},
            {"name": "Redis 集群高可用", "description": "搭建 Redis Cluster 千节点集群, 实现自动故障转移, 可用性达 99.99%。", "role": "DBA"},
        ],
        "work_experience": [
            {"company": "阿里巴巴", "position": "高级DBA", "duration": "2020.07 - 至今"},
            {"company": "京东", "position": "DBA", "duration": "2016.07 - 2020.06"},
        ],
    },
    {
        "seeker_username": "seeker14",
        "name": "韩梅",
        "gender": "女",
        "age": 32,
        "phone": "13800000014",
        "email": "hanmei@example.com",
        "current_city": "杭州",
        "intention_cities": ["杭州", "深圳"],
        "education": "本科",
        "school": "南京大学",
        "major": "计算机科学与技术",
        "work_years": 8,
        "expected_salary_min": 25,
        "expected_salary_max": 50,
        "self_evaluation": "同时具备 MongoDB/PostgreSQL 运维经验, 有 NoSQL 数据库迁移与优化经验。",
        "skills": [
            {"skill_name": "MongoDB", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "PostgreSQL", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "MySQL", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "Redis", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Linux", "skill_level": "精通", "weight": 0.85},
        ],
        "projects": [
            {"name": "MongoDB 大规模迁移", "description": "将 20TB MongoDB 数据从 3.6 升级到 6.0, 无损迁移, 性能提升 30%。", "role": "DBA负责人"},
        ],
        "work_experience": [
            {"company": "阿里巴巴", "position": "高级DBA", "duration": "2020.07 - 至今"},
        ],
    },
    # ===== seeker15: 嵌入式 (7年) =====
    {
        "seeker_username": "seeker15",
        "name": "沈磊",
        "gender": "男",
        "age": 30,
        "phone": "13800000015",
        "email": "shenlei@example.com",
        "current_city": "深圳",
        "intention_cities": ["深圳", "北京", "上海"],
        "education": "硕士",
        "school": "北京航空航天大学",
        "major": "电子信息工程",
        "work_years": 7,
        "expected_salary_min": 25,
        "expected_salary_max": 50,
        "self_evaluation": "7 年嵌入式开发经验, 精通 C/C++, 熟悉 RTOS/Linux/ARM 平台, 有手机/穿戴设备底层系统开发经验。",
        "skills": [
            {"skill_name": "C", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "C++", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "RTOS", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Linux", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "ARM", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "单片机", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "智能手表固件开发", "description": "负责智能手表 FreeRTOS 固件开发, 含心率/血氧/运动算法, 低功耗续航 14 天。", "role": "嵌入式负责人"},
            {"name": "手机驱动开发", "description": "开发 Android 手机 Linux 驱动, 涉及摄像头/指纹/传感器, 适配 10+ 机型。", "role": "驱动工程师"},
        ],
        "work_experience": [
            {"company": "华为", "position": "嵌入式软件工程师", "duration": "2019.07 - 至今"},
            {"company": "大疆", "position": "嵌入式工程师", "duration": "2017.07 - 2019.06"},
        ],
    },
    {
        "seeker_username": "seeker15",
        "name": "沈磊",
        "gender": "男",
        "age": 30,
        "phone": "13800000015",
        "email": "shenlei@example.com",
        "current_city": "深圳",
        "intention_cities": ["深圳", "杭州"],
        "education": "硕士",
        "school": "北京航空航天大学",
        "major": "电子信息工程",
        "work_years": 7,
        "expected_salary_min": 22,
        "expected_salary_max": 45,
        "self_evaluation": "具备固件开发与物联网协议经验, 熟悉 MQTT/CoAP 协议, 有 IoT 设备接入平台开发经验。",
        "skills": [
            {"skill_name": "C", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "C++", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "单片机", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "ARM", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "RTOS", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "MQTT", "skill_level": "掌握", "weight": 0.7},
        ],
        "projects": [
            {"name": "IoT 设备接入网关", "description": "开发 IoT 设备接入网关, 支持 MQTT/CoAP 协议, 接入设备 100 万+。", "role": "固件开发"},
        ],
        "work_experience": [
            {"company": "华为", "position": "嵌入式软件工程师", "duration": "2019.07 - 至今"},
        ],
    },
    # ===== seeker7: 架构师 (8年, 复用已有用户) =====
    {
        "seeker_username": "seeker7",
        "name": "刘洋",
        "gender": "男",
        "age": 32,
        "phone": "13800000007",
        "email": "liuyang@example.com",
        "current_city": "成都",
        "intention_cities": ["北京", "成都", "深圳", "杭州"],
        "education": "本科",
        "school": "电子科技大学",
        "major": "软件工程",
        "work_years": 8,
        "expected_salary_min": 35,
        "expected_salary_max": 65,
        "self_evaluation": "8 年后端架构经验, 精通 Java/Spring Cloud/K8s 微服务架构, 主导过百万级 QPS 系统设计, 具备分布式系统理论功底。",
        "skills": [
            {"skill_name": "Java", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "Spring Cloud", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Kubernetes", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "微服务", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "分布式", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "MySQL", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "Redis", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "电商微服务架构", "description": "主导电商系统从单体到微服务拆分, 拆分 50+ 服务, QPS 从 1 万提升至 50 万。", "role": "首席架构师"},
            {"name": "分布式事务方案", "description": "设计基于 Saga 的分布式事务方案, 解决跨服务数据一致性问题, 可用性 99.99%。", "role": "架构师"},
            {"name": "K8s 多集群容灾", "description": "搭建 K8s 多集群容灾体系, 实现跨机房故障自动切换, RTO < 30 秒。", "role": "架构师"},
        ],
        "work_experience": [
            {"company": "字节跳动", "position": "高级架构师", "duration": "2021.07 - 至今"},
            {"company": "美团", "position": "后端架构师", "duration": "2016.07 - 2021.06"},
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
        "intention_cities": ["北京", "深圳"],
        "education": "本科",
        "school": "电子科技大学",
        "major": "软件工程",
        "work_years": 8,
        "expected_salary_min": 30,
        "expected_salary_max": 60,
        "self_evaluation": "专注分布式系统与高可用架构, 有消息队列/缓存/数据库中间件设计经验, 擅长技术选型与方案评审。",
        "skills": [
            {"skill_name": "Java", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "分布式", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "微服务", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Kubernetes", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "Kafka", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Spring Cloud", "skill_level": "精通", "weight": 0.9},
        ],
        "projects": [
            {"name": "消息队列中间件", "description": "设计并实现公司级消息队列中间件, 支撑日均千亿级消息流转, 延迟 < 10ms。", "role": "架构师"},
        ],
        "work_experience": [
            {"company": "字节跳动", "position": "高级架构师", "duration": "2021.07 - 至今"},
        ],
    },
    # ===== seeker2: 区块链 (5年, 复用已有用户) =====
    {
        "seeker_username": "seeker2",
        "name": "张明",
        "gender": "男",
        "age": 28,
        "phone": "13800000002",
        "email": "zhangming@example.com",
        "current_city": "北京",
        "intention_cities": ["北京", "杭州", "深圳"],
        "education": "硕士",
        "school": "中国科学技术大学",
        "major": "计算机科学与技术",
        "work_years": 5,
        "expected_salary_min": 25,
        "expected_salary_max": 50,
        "self_evaluation": "5 年区块链开发经验, 熟悉 Solidity/Go/Ethereum, 有 DeFi/NFT 项目上线经验, 深入理解共识算法与密码学。",
        "skills": [
            {"skill_name": "Solidity", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Go", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Ethereum", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "智能合约", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Hyperledger", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Java", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "密码学", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "DeFi 交易平台", "description": "开发去中心化交易平台智能合约, TVL 峰值 5000 万美元, 通过 3 次安全审计。", "role": "区块链开发"},
            {"name": "联盟链溯源系统", "description": "基于 Hyperledger Fabric 开发供应链溯源系统, 接入 100+ 企业节点。", "role": "技术负责人"},
        ],
        "work_experience": [
            {"company": "蚂蚁集团", "position": "区块链开发工程师", "duration": "2021.07 - 至今"},
            {"company": "腾讯", "position": "后端开发工程师", "duration": "2019.07 - 2021.06"},
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
        "intention_cities": ["北京", "上海"],
        "education": "硕士",
        "school": "中国科学技术大学",
        "major": "计算机科学与技术",
        "work_years": 5,
        "expected_salary_min": 28,
        "expected_salary_max": 55,
        "self_evaluation": "同时具备 Hyperledger 联盟链开发经验, 熟悉跨链协议与 Layer2 方案, 有区块链安全审计能力。",
        "skills": [
            {"skill_name": "Go", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Hyperledger", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Solidity", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "分布式", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Java", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "密码学", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "跨链桥协议", "description": "开发 Ethereum/BSC 跨链桥协议, 支撑资产跨链转移, 累计转移金额 2 亿+。", "role": "核心开发"},
        ],
        "work_experience": [
            {"company": "蚂蚁集团", "position": "区块链开发工程师", "duration": "2021.07 - 至今"},
        ],
    },
    # ===== seeker6: 音视频 (6年, 复用已有用户) =====
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
        "major": "通信工程",
        "work_years": 6,
        "expected_salary_min": 25,
        "expected_salary_max": 50,
        "self_evaluation": "6 年音视频开发经验, 精通 C++/FFmpeg/WebRTC, 有亿级用户实时音视频 SDK 开发经验, 擅长弱网优化。",
        "skills": [
            {"skill_name": "C++", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "FFmpeg", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "WebRTC", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "RTMP", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "HLS", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Linux", "skill_level": "熟练", "weight": 0.8},
        ],
        "projects": [
            {"name": "实时视频通话 SDK", "description": "基于 WebRTC 开发跨平台视频通话 SDK, 支持 16 人视频, 弱网抗丢包 30%。", "role": "音视频负责人"},
            {"name": "直播推流优化", "description": "优化直播推流链路, 端到端延迟从 3s 降至 800ms, 节省带宽 20%。", "role": "核心开发"},
        ],
        "work_experience": [
            {"company": "字节跳动", "position": "音视频开发工程师", "duration": "2021.07 - 至今"},
            {"company": "虎牙直播", "position": "流媒体工程师", "duration": "2018.07 - 2021.06"},
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
        "intention_cities": ["深圳", "上海", "广州"],
        "education": "本科",
        "school": "华中科技大学",
        "major": "通信工程",
        "work_years": 6,
        "expected_salary_min": 25,
        "expected_salary_max": 50,
        "self_evaluation": "同时具备流媒体分发系统开发经验, 熟悉 RTMP/HLS/WebRTC 协议, 有大规模 CDN 调度经验。",
        "skills": [
            {"skill_name": "C++", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "FFmpeg", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "RTMP", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "HLS", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "WebRTC", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "Python", "skill_level": "掌握", "weight": 0.6},
        ],
        "projects": [
            {"name": "直播 CDN 调度系统", "description": "开发直播 CDN 智能调度系统, 根据网络质量动态选择最优节点, 卡顿率降低 40%。", "role": "流媒体工程师"},
        ],
        "work_experience": [
            {"company": "哔哩哔哩", "position": "流媒体工程师", "duration": "2020.07 - 2021.06"},
        ],
    },
    # ===== seeker5: 量化开发 (4年, 复用已有用户) =====
    {
        "seeker_username": "seeker5",
        "name": "赵敏",
        "gender": "女",
        "age": 28,
        "phone": "13800000005",
        "email": "zhaomin@example.com",
        "current_city": "杭州",
        "intention_cities": ["上海", "杭州", "北京"],
        "education": "硕士",
        "school": "复旦大学",
        "major": "统计学",
        "work_years": 4,
        "expected_salary_min": 28,
        "expected_salary_max": 55,
        "self_evaluation": "4 年量化开发经验, 熟悉 Python/C++ 双语言栈, 有低延迟交易系统开发经验, 擅长统计建模与因子挖掘。",
        "skills": [
            {"skill_name": "Python", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "C++", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "NumPy", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Pandas", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "机器学习", "skill_level": "熟练", "weight": 0.8},
            {"skill_name": "SQL", "skill_level": "精通", "weight": 0.85},
        ],
        "projects": [
            {"name": "量化回测框架", "description": "开发量化策略回测框架, 支持 10 年 Tick 级回测, 回测速度提升 10 倍。", "role": "量化开发"},
            {"name": "Alpha 因子挖掘", "description": "基于机器学习挖掘 Alpha 因子 100+, 年化超额收益 15%。", "role": "量化研究员"},
        ],
        "work_experience": [
            {"company": "华泰证券", "position": "量化开发工程师", "duration": "2021.07 - 至今"},
            {"company": "国泰君安", "position": "量化研究员", "duration": "2020.07 - 2021.06"},
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
        "intention_cities": ["上海", "北京"],
        "education": "硕士",
        "school": "复旦大学",
        "major": "统计学",
        "work_years": 4,
        "expected_salary_min": 25,
        "expected_salary_max": 50,
        "self_evaluation": "具备机器学习与数据分析能力, 有风控模型开发经验, 熟悉 XGBoost/LightGBM 等算法。",
        "skills": [
            {"skill_name": "Python", "skill_level": "精通", "weight": 0.95},
            {"skill_name": "机器学习", "skill_level": "熟练", "weight": 0.85},
            {"skill_name": "数据分析", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "SQL", "skill_level": "精通", "weight": 0.85},
            {"skill_name": "NumPy", "skill_level": "精通", "weight": 0.9},
            {"skill_name": "Pandas", "skill_level": "精通", "weight": 0.9},
        ],
        "projects": [
            {"name": "信用风控模型", "description": "基于 XGBoost 开发信用评分模型, AUC 达 0.85, 坏账率降低 20%。", "role": "量化开发"},
        ],
        "work_experience": [
            {"company": "华泰证券", "position": "量化开发工程师", "duration": "2021.07 - 至今"},
        ],
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


def get_corp1_user(db) -> SysUser:
    """获取已有企业用户 corp1 (优先按 username 查找, 回退 id=3), 用作 fallback"""
    corp = db.query(SysUser).filter(SysUser.username == "corp1").first()
    if corp is None:
        corp = db.query(SysUser).filter(SysUser.id == 3).first()
    return corp


def build_company_to_user_map(db) -> dict:
    """构建 company_name -> user_id 映射, 用于职位重新分配与新职位归属"""
    mapping = {}
    for corp in CORP_USERS:
        user = db.query(SysUser).filter(SysUser.username == corp["username"]).first()
        if user:
            mapping[corp["company"]] = user.id
    return mapping


# ============================================================
# 步骤 1: 创建企业用户
# ============================================================
def create_corp_users(db) -> int:
    """创建企业用户 (已存在则跳过), 返回新增数量"""
    pwd_hash = hash_password(DEFAULT_PASSWORD)
    created = 0
    for corp in CORP_USERS:
        existing = db.query(SysUser).filter(SysUser.username == corp["username"]).first()
        if existing:
            print(f"  [SKIP] 企业用户 {corp['username']} 已存在 (id={existing.id})")
            continue
        user = SysUser(
            username=corp["username"],
            password_hash=pwd_hash,
            role=ROLE_EMPLOYER,
            phone=corp["phone"],
            nickname=corp["nickname"],
            company_name=corp["company"],
            contact_person=corp["nickname"],
            status=1,
        )
        db.add(user)
        db.flush()
        created += 1
        print(f"  [NEW] 创建企业用户 {corp['username']} (id={user.id}, company={corp['company']})")
    db.commit()
    return created


# ============================================================
# 步骤 2: 重新分配现有职位的 user_id
# ============================================================
def reassign_jobs(db) -> int:
    """遍历所有 Job, 根据 job.company 重新分配 user_id, 返回重新分配数量"""
    company_map = build_company_to_user_map(db)
    if not company_map:
        print("  [WARN] 未找到任何企业用户, 跳过重新分配")
        return 0

    reassigned = 0
    jobs = db.query(Job).all()
    for job in jobs:
        new_user_id = company_map.get(job.company)
        if new_user_id and job.user_id != new_user_id:
            old_id = job.user_id
            job.user_id = new_user_id
            reassigned += 1
            print(f"  [REASSIGN] 职位 #{job.id} '{job.title}' @ {job.company}: user_id {old_id} -> {new_user_id}")
    db.commit()
    return reassigned


# ============================================================
# 步骤 3: 新增职位
# ============================================================
def create_new_jobs(db) -> int:
    """创建新增职位 (按 title+company 判重), 返回新增数量"""
    company_map = build_company_to_user_map(db)
    corp1 = get_corp1_user(db)

    created = 0
    for idx, j in enumerate(NEW_JOBS, start=1):
        # 判重: title + company
        existing = db.query(Job).filter(
            Job.title == j["title"],
            Job.company == j["company"],
        ).first()
        if existing:
            print(f"  [SKIP] 职位 '{j['title']}' @ {j['company']} 已存在 (id={existing.id})")
            continue

        # 分配 user_id: 优先按 company 匹配企业用户, 否则回退 corp1
        user_id = company_map.get(j["company"])
        if user_id is None:
            if corp1 is None:
                print(f"  [WARN] 无法为职位 '{j['title']}' 分配企业用户 (corp1 不存在), 跳过")
                continue
            user_id = corp1.id
            print(f"  [INFO] 职位 '{j['title']}' @ {j['company']} 无专属企业用户, 回退至 corp1")

        job = Job(
            user_id=user_id,
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
            doc_url=f"uploads/job/demo_more_{idx}.pdf",
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


# ============================================================
# 步骤 4a: 新增求职者
# ============================================================
def create_new_seekers(db) -> int:
    """创建新增求职者用户 (已存在则跳过), 返回新增数量"""
    pwd_hash = hash_password(DEFAULT_PASSWORD)
    created = 0
    for s in NEW_SEEKERS:
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


# ============================================================
# 步骤 4b: 新增简历
# ============================================================
def create_new_resumes(db) -> int:
    """为求职者创建新增简历 (按 doc_url 判重), 返回新增数量"""
    created = 0
    for idx, r in enumerate(NEW_RESUMES, start=1):
        user = db.query(SysUser).filter(SysUser.username == r["seeker_username"]).first()
        if user is None:
            print(f"  [WARN] 用户 {r['seeker_username']} 不存在, 跳过该简历")
            continue

        doc_url = f"uploads/resume/demo_more_{idx}.pdf"
        # 判重: doc_url
        existing = db.query(Resume).filter(Resume.doc_url == doc_url).first()
        if existing:
            print(f"  [SKIP] 简历 doc_url={doc_url} 已存在 (id={existing.id})")
            continue

        resume = Resume(
            user_id=user.id,
            doc_url=doc_url,
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
# 步骤 5: 修复 testseeker 昵称乱码
# ============================================================
def fix_testseeker_nickname(db) -> int:
    """修复 testseeker 用户昵称乱码 (含 '?' 的替换为 '测试求职者')"""
    user = db.query(SysUser).filter(SysUser.username == "testseeker").first()
    if user is None:
        print("  [SKIP] testseeker 用户不存在, 跳过修复")
        return 0
    if user.nickname and "?" in user.nickname:
        old_nick = user.nickname
        user.nickname = "测试求职者"
        db.commit()
        print(f"  [FIX] testseeker 昵称乱码修复: '{old_nick}' -> '测试求职者'")
        return 1
    print(f"  [SKIP] testseeker 昵称无需修复 (当前: '{user.nickname}')")
    return 0


# ============================================================
# 主函数
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="智聘云图 - 测试数据扩充脚本")
    parser.add_argument(
        "--reset-jobs-only",
        action="store_true",
        help="只清空 job_requirement + job 表后重建职位 (不清空简历)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  智聘云图 - 测试数据扩充脚本 (seed_more_data)")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 可选: 只清空职位表
        if args.reset_jobs_only:
            print("\n--- 清空职位数据 (仅职位, 保留简历) ---")
            db.execute(text("DELETE FROM job_requirement"))
            db.execute(text("DELETE FROM job"))
            db.commit()
            print("[RESET] 已清空 job_requirement + job 表")
        else:
            print("[INFO] 追加模式 (如需只重建职位请加 --reset-jobs-only)")

        # 步骤 1: 创建企业用户
        print("\n--- 步骤 1: 创建企业用户 ---")
        new_corps = create_corp_users(db)

        # 步骤 2: 重新分配现有职位的 user_id (reset-jobs-only 模式下跳过)
        if args.reset_jobs_only:
            print("\n--- 步骤 2: 重新分配职位 user_id (跳过, 已清空职位表) ---")
            reassigned = 0
        else:
            print("\n--- 步骤 2: 重新分配现有职位 user_id ---")
            reassigned = reassign_jobs(db)

        # 步骤 3: 新增 30 个职位
        print("\n--- 步骤 3: 新增职位 ---")
        new_jobs = create_new_jobs(db)

        # 步骤 4: 新增求职者 + 简历 (reset-jobs-only 模式下跳过)
        if args.reset_jobs_only:
            print("\n--- 步骤 4: 新增求职者与简历 (跳过, --reset-jobs-only 模式) ---")
            new_seekers = 0
            new_resumes = 0
        else:
            print("\n--- 步骤 4a: 新增求职者 ---")
            new_seekers = create_new_seekers(db)
            print("\n--- 步骤 4b: 新增简历 ---")
            new_resumes = create_new_resumes(db)

        # 步骤 5: 修复 testseeker 昵称乱码
        print("\n--- 步骤 5: 修复 testseeker 昵称乱码 ---")
        fixed = fix_testseeker_nickname(db)

        # 最终统计
        print("\n" + "=" * 60)
        print("  数据扩充完成!")
        print("=" * 60)
        print(f"  新增企业用户:     {new_corps} 个")
        print(f"  重新分配职位:     {reassigned} 个")
        print(f"  新增职位:         {new_jobs} 个")
        print(f"  新增求职者:       {new_seekers} 人")
        print(f"  新增简历:         {new_resumes} 份")
        print(f"  修复乱码:         {fixed} 条")
        print(f"  (embedding 未生成, 首次匹配时由 match_service 批量生成)")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
