# ===== 智聘云图前端镜像 (多阶段构建) =====

# ===== 阶段 1: 构建静态资源 =====
FROM node:20-alpine AS builder

LABEL maintainer="智聘云图团队"

WORKDIR /build

# 复制依赖描述文件 (利用 Docker 缓存层加速构建)
COPY package.json package-lock.json* ./

# 安装依赖 (使用国内镜像加速)
RUN npm config set registry https://registry.npmmirror.com && \
    npm ci --no-audit --no-fund

# 复制源代码并构建
COPY . .

# 构建生产版本 (输出至 /build/dist)
RUN npm run build

# ===== 阶段 2: Nginx 托管静态资源 =====
FROM nginx:1.27-alpine AS runner

LABEL maintainer="智聘云图团队"
LABEL description="智聘云图前端 Nginx 静态资源服务"

# 设置时区
RUN apk add --no-cache tzdata && \
    cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && \
    echo "Asia/Shanghai" > /etc/timezone

# 复制自定义 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 复制构建产物
COPY --from=builder /build/dist /usr/share/nginx/html

# 创建日志目录
RUN mkdir -p /var/log/nginx

EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD wget -q --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
