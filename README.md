# 智聘云图 ZhiPin YunTu

> 基于文档智能解析的 B/S 架构人岗匹配平台

面向省级人才服务中心的招聘场景,采用 FastAPI + Vue3 + 豆包大模型 + Neo4j 知识图谱构建,提供简历智能解析、能力图谱构建、多维匹配推荐等核心能力,支持 LoongArch + 银河麒麟国产化部署。

---

## 一、技术栈

| 层级 | 技术选型 |
| --- | --- |
| 前端 | Vue 3.5 + Vite + TypeScript + Element Plus + Pinia + ECharts |
| 后端 | Python 3.12 + FastAPI + Uvicorn + SQLAlchemy 2.0 |
| 数据库 | SQLite (开发) / 达梦 DM8 (国产化生产) |
| 图数据库 | Neo4j 5 (含降级模式) |
| 缓存/队列 | Redis 7 + Celery |
| AI | 豆包 ARK API (OpenAI SDK 兼容) |
| 部署 | Docker + Docker Compose + Nginx |

---

## 二、项目结构

```
智聘云图/
├── backend/                # FastAPI 后端
│   ├── app/
│   │   ├── ai/             # 豆包 ARK 客户端 + Prompts
│   │   ├── api/v1/         # REST API 路由 (auth/resume/job/match/graph/admin)
│   │   ├── core/           # 配置、安全、依赖注入
│   │   ├── db/             # SQLAlchemy 基础 + Neo4j 客户端
│   │   ├── models/         # ORM 模型 (8 张表)
│   │   ├── schemas/        # Pydantic 数据模型
│   │   ├── services/       # 业务服务层
│   │   └── main.py         # 应用入口
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── .env.example
│   └── .env.prod
├── frontend/               # Vue3 前端
│   ├── src/
│   │   ├── api/            # Axios 接口封装
│   │   ├── layouts/        # 三种角色布局
│   │   ├── views/          # 业务页面
│   │   ├── router/         # 路由配置
│   │   └── stores/         # Pinia 状态管理
│   ├── vite.config.ts
│   ├── Dockerfile
│   └── nginx.conf
├── docker-compose.yml      # 服务编排
└── README.md
```

---

## 三、本地开发

### 3.1 环境准备

- Python 3.12+
- Node.js 20+
- Redis (可选,默认降级)
- Neo4j (可选,默认降级)

### 3.2 后端启动

```bash
cd backend
python -m venv venv
venv\Scripts\activate           # Windows
# source venv/bin/activate      # Linux/Mac

pip install -r requirements.txt

# 配置环境变量
copy .env.example .env.dev      # Windows
# cp .env.example .env.dev       # Linux
# 编辑 .env.dev,填入 ARK_API_KEY

# 启动开发服务 (热重载)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

访问 `http://localhost:8000/docs` 查看 Swagger 文档。
默认管理员账号: `admin` / `admin123` (首次启动自动创建)

### 3.3 前端启动

```bash
cd frontend
npm install
npm run dev
```

访问 `http://localhost:5173` 进入登录页。

---

## 四、Docker 部署 (推荐)

### 4.1 一键启动

```bash
# 1. 配置环境变量
cp backend/.env.prod.example backend/.env.prod
# 编辑 backend/.env.prod,关键配置:
#   ARK_API_KEY=your-real-key
#   SECRET_KEY=random-secure-string

# 2. 构建并启动所有服务
docker-compose up -d --build

# 3. 查看启动状态
docker-compose ps
docker-compose logs -f backend
```

### 4.2 访问入口

| 服务 | 地址 |
| --- | --- |
| 前端 Web | http://localhost |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| Neo4j Browser | http://localhost:7474 |
| Redis | localhost:6379 |

### 4.3 常用运维命令

```bash
# 查看实时日志
docker-compose logs -f backend frontend

# 重启单个服务
docker-compose restart backend

# 停止所有服务
docker-compose down

# 停止并删除数据卷 (清空数据)
docker-compose down -v

# 重新构建镜像
docker-compose build --no-cache backend frontend
```

---

## 五、LoongArch + 银河麒麟国产化部署

本项目赛题要求最终部署在 LoongArch 架构 + 银河麒麟操作系统上,以下为部署要点。

### 5.1 镜像选择

| 服务 | 龙架构镜像建议 |
| --- | --- |
| Python 后端 | `loongnix/python:3.12` 或基于龙架构构建的 `python:3.12-slim` |
| Node 构建 | `loongnix/node:20-alpine` |
| Nginx | `loongnix/nginx:1.27` 或银河麒麟自带 nginx |
| Redis | `loongnix/redis:7-alpine` |
| Neo4j | 龙架构暂无官方镜像,可使用 `neo4j:5-community` 多架构版本或自行编译 |

### 5.2 系统依赖安装 (银河麒麟 V10)

```bash
# 启用龙架构仓库
sudo yum update -y

# 安装 Docker (龙架构版本)
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 启动 Docker
sudo systemctl enable --now docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
    -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 5.3 国产数据库适配 (达梦 DM8)

修改 `backend/.env.prod` 中的 `DATABASE_URL`:

```
DATABASE_URL=dm+dmPython://zhipin:zhipin123@dm8-host:5236/zhipin
```

需在 `requirements.txt` 中追加:

```
dmPython>=2.4
SQLAlchemy-Dm>=1.4
```

并修改 `app/db/base.py` 中的 `BigIntPK` 以适配 DM8 的 `BIGINT` 自增语义。

### 5.4 离线部署 (无外网环境)

1. 在有网环境预拉取镜像:
   ```bash
   docker-compose pull
   ```
2. 导出镜像:
   ```bash
   docker save -o zhipin-images.tar \
       loongnix/python:3.12 \
       loongnix/nginx:1.27 \
       loongnix/redis:7-alpine \
       neo4j:5-community
   ```
3. 传输至目标机器并加载:
   ```bash
   docker load -i zhipin-images.tar
   ```
4. 执行 `docker-compose up -d` 启动。

---

## 六、核心功能演示流程

1. **管理员登录** — `admin` / `admin123`,进入 `/admin/dashboard`
2. **注册求职者** — `/register` 注册 `seeker1`,角色 `ROLE_SEEKER`
3. **注册企业** — `/register` 注册 `corp1`,角色 `ROLE_EMPLOYER`
4. **求职者上传简历** — `/seeker/resume/upload` 上传 DOCX/PDF,系统自动调用豆包大模型解析
5. **企业发布职位** — `/employer/job/create` 粘贴 JD,后端自动结构化
6. **求职者查看推荐** — `/seeker/recommend` 选择简历,AI 推荐 Top10 职位
7. **企业查看候选人** — `/employer/candidates` 选择职位,AI 推荐 Top10 候选人
8. **能力图谱** — `/seeker/resume/graph` 可视化技能图谱
9. **管理后台** — `/admin/*` 用户/简历/职位/日志管理

---

## 七、智能匹配引擎说明

三阶段匹配架构:

1. **召回 (Recall)** — Embedding 余弦相似度,从全量数据中召回 Top200
2. **粗排 (Coarse Rank)** — 6 维度规则加权:技能 35% + 经验 20% + 学历 10% + 城市 10% + 薪资 10% + 项目 15%
3. **精排 (Fine Rerank)** — 豆包大模型对 Top20 进行语义精排,融合分 = 70% 规则 + 30% 大模型

精排阶段仅调用大模型有限次数以控制成本与延迟。

---

## 八、API 概览

| 模块 | 路径 | 说明 |
| --- | --- | --- |
| 认证 | `/api/v1/auth/*` | 注册/登录/刷新/me |
| 简历 | `/api/v1/resumes/*` | 上传/列表/详情/删除 |
| 职位 | `/api/v1/jobs/*` | 创建/列表/详情/状态/删除 |
| 匹配 | `/api/v1/match/*` | 求职者推荐职位 / 企业推荐简历 / 历史 |
| 图谱 | `/api/v1/graph/*` | 简历图谱 / 技能图谱 |
| 管理 | `/api/v1/admin/*` | 仪表盘/用户/简历/职位/日志 (需 ADMIN) |
| 健康 | `/api/v1/health` | 服务健康检查 |

完整接口文档:`http://localhost:8000/docs`

---

## 九、常见问题

### Q1: 上传简历后解析失败?
- 检查 `ARK_API_KEY` 是否正确配置
- 查看后端日志:`docker-compose logs backend`
- 确认网络可访问 `https://ark.cn-beijing.volces.com`

### Q2: Neo4j 连接失败但服务正常?
- 程序内置降级机制,Neo4j 不可用时自动从关系数据库构建图谱数据,不影响主流程
- 如需启用完整图谱能力,启动 Neo4j 并配置 `NEO4J_URL`

### Q3: 前端访问空白页?
- 检查 Nginx 是否启动:`docker-compose ps frontend`
- 查看 Nginx 日志:`docker-compose logs frontend`
- 确认后端健康:`curl http://localhost:8000/api/v1/health`

### Q4: Docker 构建缓慢?
- 配置国内镜像加速:`/etc/docker/daemon.json` 添加 `registry-mirrors`
- 使用 `npm config set registry https://registry.npmmirror.com` (Dockerfile 已内置)

---

## 十、License

本项目用于省级人才服务中心赛题演示,版权归开发团队所有。
