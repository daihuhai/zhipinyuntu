# ===== 智聘云图后端镜像 =====
# 基础镜像: 官方 Python 3.12 slim (LoongArch 部署时替换为 loongson/pypy3.10 或自定义龙架构镜像)
FROM python:3.12-slim AS backend-base

# 维护者
LABEL maintainer="智聘云图团队"
LABEL description="智聘云图 FastAPI 后端服务 - 基于文档智能解析的人岗匹配平台"

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai \
    APP_ENV=production \
    APP_DEBUG=false

# 安装系统依赖 (pdfplumber/docx 解析所需)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libxml2-dev \
    libxslt1-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    tini \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && \
    pip install -r /app/requirements.txt

# 复制应用代码
COPY app /app/app

# 创建上传目录
RUN mkdir -p /app/uploads /app/logs

# 暴露端口
EXPOSE 8000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

# 使用 tini 作为 init 进程 (正确处理信号)
ENTRYPOINT ["/usr/bin/tini", "--"]

# 启动命令: uvicorn 多 worker 生产模式
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*", \
     "--log-level", "info"]
