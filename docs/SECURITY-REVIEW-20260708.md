# 智聘云图 安全审查报告

> **审查日期**: 2026-07-08
> **审查范围**: 智聘云图招聘平台 (Vue3 前端 + FastAPI 后端)
> **审查方法**: 静态代码审计 (源码逐文件通读 + 数据流/控制流追踪)
> **审查人**: 安全审计
> **文档版本**: v1.0

---

## 1. 概述

### 1.1 审查范围

本次审查覆盖智聘云图项目的前后端核心代码,重点关注认证授权、输入校验、文件上传、敏感信息保护等安全维度。

| 模块 | 路径 | 关键文件 |
|------|------|----------|
| 后端 Core | `backend/app/core/` | `config.py`, `deps.py`, `security.py` |
| 后端 API | `backend/app/api/v1/` | `auth.py`, `resume.py`, `admin.py`, `job.py`, `application.py`, `match.py`, `message.py` |
| 后端 Services | `backend/app/services/` | `file_service.py`, `doc_parser.py`, `auth_service.py`, `resume_service.py`, `admin_service.py` |
| 后端 DB | `backend/app/db/` | `base.py` |
| 后端入口 | `backend/app/main.py` | 应用初始化、CORS、中间件 |
| 前端 Core | `frontend/src/` | `api/request.ts`, `stores/user.ts`, `router/index.ts` |
| 前端 Views | `frontend/src/views/` | `auth/`, `seeker/`, `employer/`, `admin/` |
| 部署配置 | `frontend/nginx.conf`, `backend/.env.example`, `backend/requirements.txt` | |

### 1.2 审查方法

1. **项目安全基线梳理**:识别项目已使用的安全原语(BCrypt 哈希、JWT、SQLAlchemy ORM、Pydantic 校验、字段白名单、脱敏工具)。
2. **逐文件审计**:对上述文件进行通读,标记潜在风险点。
3. **数据流追踪**:对每个候选风险点,追溯"输入入口 → 数据流向 → 危险 sink",验证可利用性。
4. **分级评估**:按"可直接利用 / 特定条件下利用 / 纵深防御缺口"三档划分严重程度。

### 1.3 总体结论

项目在密码哈希(BCrypt)、ORM 参数化查询、JWT 类型校验、字段白名单、手机号/邮箱脱敏等基础安全实践上做得较好,SQL 注入与存储型 XSS 风险较低。但存在 **多处越权访问(IDOR)漏洞** 导致的简历/投递 PII 跨企业泄露、**JWT 密钥默认弱值**、**默认管理员弱口令**、**上传文件无鉴权静态访问** 等高危问题,需在上线前修复。

| 风险等级 | 数量 |
|----------|------|
| 高 (HIGH) | 7 |
| 中 (MEDIUM) | 9 |
| 低 (LOW) | 5 |

---

## 2. 安全架构总览

### 2.1 认证授权流程

```
┌────────────┐   POST /auth/login     ┌──────────────┐
│  前端 Vue3  │ ─────────────────────▶ │  FastAPI     │
│  (axios)    │ ◀──── access_token ─── │  /auth/login │
└────────────┘   + refresh_token      └──────────────┘
       │
       │  后续请求: Authorization: Bearer <access_token>
       ▼
┌──────────────────────────────────────────────────────┐
│  deps.py: get_current_user                           │
│   1. HTTPBearer 提取 token                           │
│   2. jose.jwt.decode(SECRET_KEY, HS256)              │
│   3. 校验 type=="access" / sub 存在                  │
│   4. db.get(SysUser, user_id)                        │
│   5. 校验 user.status==1                             │
│   require_role(*roles): 角色白名单校验               │
└──────────────────────────────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│  业务路由 (resume/job/application/admin/...)          │
│  - 部分路由做对象级归属校验 (resume.delete, job.delete)│
│  - 部分路由缺失对象级校验 (见 §3 高危项)              │
└──────────────────────────────────────────────────────┘
```

- **认证**:无状态 JWT,access token 2h,refresh token 7d,HS256 对称签名。
- **授权**:两级——角色级(`require_role`) + 对象级(部分接口手写归属判断)。
- **令牌存储**:前端 localStorage(`access_token`、`user_info`)。

### 2.2 关键数据流

- **简历上传**:`POST /resumes/upload` → `file_service.save`(本地磁盘 `/uploads/resumes/YYYYMM/`) → `doc_parser.extract_text`(pdfplumber/python-docx) → `ark_client.chat_json`(豆包 LLM 结构化) → 回填 `Resume` 表。
- **简历文件访问**:`StaticFiles` 挂载 `/uploads` → **无鉴权**,任何拿到 URL 的访客可下载。
- **企业查看投递**:`GET /applications/job/{job_id}` / `/applications/employer` → 返回简历完整字段(姓名/手机/邮箱/年龄/学历等),企业视角在 `/employer` 接口对手机/邮箱脱敏,但 `/job/{job_id}` 接口未脱敏。

---

## 3. 发现的安全问题

### 🔴 高危 (HIGH)

---

#### H-1. JWT 签名密钥使用弱默认值,可导致令牌伪造

- **风险等级**: 高
- **代码位置**: `backend/app/core/config.py:22`
- **问题描述**:
  ```python
  SECRET_KEY: str = "change-me"
  ```
  `SECRET_KEY` 是 JWT 签名的对称密钥(HS256),默认值为字符串 `"change-me"`。该值同时被 `security.py:52`、`security.py:77` 用于 `jwt.encode` / `jwt.decode`。若部署时未在 `.env` 中覆盖(且 `.env.example:9` 也仅给出 `please-change-this-to-random-string` 的提示样例),攻击者可直接用已知密钥 `change-me` 自行签发任意用户、任意角色(含 `ROLE_ADMIN`)的合法 JWT,实现完全的认证绕过与权限提升。
- **修复建议**:
  - 应用启动时校验 `SECRET_KEY` 长度与熵(如 `<32 字节` 或等于已知弱值时拒绝启动)。
  - 生产环境强制通过环境变量注入至少 32 字节随机串(如 `python -c "import secrets;print(secrets.token_urlsafe(48))"`)。
  - 密钥不入库、不入 Git,通过密管系统(KMS / Vault / 环境变量)分发。

---

#### H-2. 默认管理员账号使用弱口令并在日志中明文打印

- **风险等级**: 高
- **代码位置**: `backend/app/main.py:48-57`
- **问题描述**:
  ```python
  admin = SysUser(
      username="admin",
      password_hash=hash_password("admin123"),
      ...
  )
  ...
  logger.info("✅ 默认管理员已创建 (admin / admin123)")
  ```
  1. 默认管理员口令 `admin123` 为常见弱口令,易被字典爆破命中。
  2. 该凭据被明文写入启动日志,任何能读取日志文件或日志服务的人员均可直接获取管理员账号。
  3. 该逻辑位于 `lifespan` 启动钩子,生产环境同样会触发。
- **修复建议**:
  - 生产环境(`APP_ENV == "production"`)禁止自动创建默认管理员,改为通过初始化脚本/CLI 由运维人工设置强口令。
  - 口令必须满足复杂度策略(≥12 位,含大小写/数字/符号)。
  - 日志中严禁出现任何明文凭据;仅输出"默认管理员已创建"即可。

---

#### H-3. 投递记录接口越权(IDOR),跨企业泄露简历 PII

- **风险等级**: 高
- **代码位置**: `backend/app/api/v1/application.py:189-253`(`list_applications_by_job`)
- **问题描述**:
  ```python
  @router.get("/job/{job_id}", ...)
  async def list_applications_by_job(
      job_id: int,
      current_user: SysUser = Depends(require_role("ROLE_EMPLOYER", "ROLE_ADMIN")),
      ...
  ):
      job = db.get(Job, job_id)
      if job is None:
          return fail(...)
      # ❌ 未校验 job.user_id == current_user.id
      ...
      "resume": {
          "name": resume.name, "gender": resume.gender, "age": resume.age,
          "phone": resume.phone, "email": resume.email,   # ❌ 未脱敏
          "education": ..., "school": ..., "self_evaluation": ...,
          "doc_url": resume.doc_url, ...
      }
  ```
  接口仅校验角色为 `ROLE_EMPLOYER`,**未校验该 `job_id` 是否属于当前企业**。任意企业用户遍历 `job_id` 即可查看其他企业职位收到的全部投递,且返回字段包含求职者**姓名、手机号、邮箱、年龄、学历、学校、自我评价、简历文件 URL**(均未脱敏)。
  对比同文件 `list_employer_applications`(L309-379)正确做了 `Job.user_id == current_user.id` 过滤并对手机/邮箱脱敏,可确认此处为遗漏。
- **影响**: 大规模个人敏感信息泄露;违反《个人信息保护法》第 13/14 条(处理个人信息须有合法基础并取得同意)。
- **修复建议**:
  - 在 L199 之后增加归属校验:`if current_user.role == "ROLE_EMPLOYER" and job.user_id != current_user.id: return fail(BizError.ROLE_FORBIDDEN, "无权查看该职位投递")`。
  - 对企业视角的 `phone`/`email` 字段统一调用 `mask_phone` / `mask_email`(与 `/employer` 接口保持一致)。

---

#### H-4. 投递状态更新接口越权,可篡改他人投递记录

- **风险等级**: 高
- **代码位置**:
  - `backend/app/api/v1/application.py:256-278`(`batch_update_status`)
  - `backend/app/api/v1/application.py:281-306`(`update_application_status`)
- **问题描述**:
  ```python
  async def batch_update_status(req, current_user=Depends(require_role("ROLE_EMPLOYER","ROLE_ADMIN")), ...):
      for app_id in req.ids:
          app = db.get(JobApplication, app_id)
          if app is not None:
              app.status = req.status   # ❌ 未校验 app 对应的 job 是否属于当前企业
              updated += 1
  ```
  两个接口均仅校验角色,未校验投递记录所归属的职位是否属于当前企业。任意企业可遍历 `application_id` 篡改其他企业职位的投递状态(如把候选人标记为"不合适""已录用"),破坏业务数据完整性。
- **修复建议**:
  - 更新前通过 `JobApplication.job_id` → `Job.user_id` 联查,校验 `job.user_id == current_user.id`(管理员除外)。
  - 推荐在 `admin_service`/`application` 层抽取统一的归属校验辅助函数,避免重复遗漏。

---

#### H-5. 智能匹配接口越权,跨企业查看候选人简历

- **风险等级**: 高
- **代码位置**: `backend/app/api/v1/match.py:88-111`(`recommend_resumes`)
- **问题描述**:
  ```python
  @router.get("/job/{job_id}/resumes", ...)
  async def recommend_resumes(job_id: int, current_user=Depends(require_role("ROLE_EMPLOYER","ROLE_ADMIN")), ...):
      results = match_service.recommend_resumes_for_job(job_id, db, top_k=top_k)
      # ❌ 未校验 job.user_id == current_user.id
      data = [{"resume": _resume_to_dict(item["resume"]), ...} for item in results]
  ```
  `_resume_to_dict`(L41-59)返回 `name/gender/age/education/school/major/skills/self_evaluation` 等求职者 PII。任意企业传入他人 `job_id` 即可获取该职位的候选人简历推荐列表。
  同文件 `recommend_jobs`(L62-85)对求职者侧同样未校验 `resume.user_id == current_user.id`,求职者可枚举他人 `resume_id` 触发匹配(影响较轻,但应一并修复)。
- **修复建议**:
  - `recommend_resumes`:增加 `job = db.get(Job, job_id)` + `if current_user.role=="ROLE_EMPLOYER" and job.user_id != current_user.id: fail(...)`。
  - `recommend_jobs`:增加简历归属校验 `resume.user_id == current_user.id`。

---

#### H-6. 上传文件目录无鉴权静态访问,简历文件可被任意下载

- **风险等级**: 高
- **代码位置**: `backend/app/main.py:117-120`
- **问题描述**:
  ```python
  _uploads_dir = _os.path.abspath(settings.STORAGE_PATH)
  app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")
  ```
  `/uploads` 通过 `StaticFiles` 直接挂载,**无任何鉴权**。`resume.py:163-194` 的 `get_resume_file` 接口虽做了归属校验并返回 `doc_url`,但该 URL 一旦泄露(或被 H-3/H-5 越权接口返回),任何人通过浏览器或 `curl` 即可永久下载简历原文件(PDF/DOCX,含姓名/手机/邮箱/工作经历等完整 PII)。
  文件名格式 `DDHHMMSS_<md5前8位>.ext`(`file_service.py:56`),其中 8 位 md5 前缀提供一定不可猜测性,但:
  1. 越权接口已可直接返回 `doc_url`,无需猜测。
  2. 文件名中包含的时间戳部分可被枚举。
- **修复建议**:
  - 移除 `/uploads` 的 `StaticFiles` 公开挂载,改为通过鉴权接口(如 `GET /resumes/{id}/file`)以 `FileResponse` 流式返回,并在接口内做归属校验。
  - 或在 Nginx 层对 `/uploads/` 增加 `internal` 限制 + 后端鉴权转发(X-Accel-Redirect)。
  - 为简历文件 URL 增加短期签名(带过期时间的 token),避免 URL 泄露后被长期访问。

---

#### H-7. 生产环境暴露 API 文档与 OpenAPI Schema

- **风险等级**: 高
- **代码位置**: `backend/app/main.py:67-75`
- **问题描述**:
  ```python
  app = FastAPI(
      ...,
      docs_url="/docs", redoc_url="/redoc", openapi_url="/openapi.json",
      ...
  )
  ```
  交互式文档(`/docs` Swagger UI、`/redoc`、`/openapi.json`)在所有环境均开放,未根据 `APP_ENV` 关闭。攻击者可通过 OpenAPI Schema 获得全部接口、参数、模型结构,显著降低攻击成本(辅助发现 H-3~H-5 等越权点)。
- **修复建议**:
  - 生产环境设置 `docs_url=None, redoc_url=None, openapi_url=None`,或通过 `if settings.is_production:` 条件关闭。
  - 至少对 `/docs`、`/openapi.json` 增加管理员鉴权。

---

### 🟡 中危 (MEDIUM)

---

#### M-1. 认证接口缺少速率限制与暴力破解防护

- **风险等级**: 中
- **代码位置**: `backend/app/api/v1/auth.py:37-58`(login)、`25-34`(register)、`49-58`(refresh)
- **问题描述**:
  `login` 接口接受 `用户名/手机号/邮箱` + 密码,无任何速率限制、账号锁定、验证码机制。结合 H-2 默认弱口令 `admin123`,攻击者可对 `admin` 账号及用户手机号进行字典爆破。`register` 同样无频控,可被批量注册垃圾账号。
- **修复建议**:
  - 引入 `slowapi` 或基于 Redis 的滑动窗口限流(如单 IP 登录 5 次/分钟,失败 5 次锁定账号 15 分钟)。
  - 登录连续失败触发图形验证码或账号锁定。
  - 注册接口限制单 IP/单手机号频次,并对手机号增加短信验证码校验。

---

#### M-2. JWT 退出无服务端失效机制,Refresh Token 无轮换

- **风险等级**: 中
- **代码位置**: `backend/app/api/v1/auth.py:61-64`(logout)、`backend/app/services/auth_service.py:106-121`(refresh)
- **问题描述**:
  ```python
  async def logout(current_user=Depends(get_current_user)):
      return success(message=...)   # ❌ 服务端无任何处理
  ```
  1. 退出登录仅靠前端清除 localStorage,access token(2h)与 refresh token(7d)在服务端仍有效,泄露后无法吊销。
  2. `refresh_access_token` 签发新令牌对后,**旧 refresh token 仍然有效**,无法检测 refresh token 被盗用(token rotation 缺失)。
- **修复建议**:
  - 引入 Redis 维护 token 黑名单/白名单(登出时将 `jti` 加入黑名单至过期)。
  - Refresh token 一次性使用:每次刷新后旧 token 立即失效,并记录 `jti` 防重放。
  - 关键操作(改密、角色变更)触发全量 token 失效。

---

#### M-3. CORS 配置过于宽松(allow_methods/allow_headers 通配 + credentials)

- **风险等级**: 中
- **代码位置**: `backend/app/main.py:78-84`
- **问题描述**:
  ```python
  app.add_middleware(
      CORSMiddleware,
      allow_origins=settings.cors_origins_list,
      allow_credentials=True,
      allow_methods=["*"],
      allow_headers=["*"],
  )
  ```
  虽 `allow_origins` 来自配置(默认 `localhost:5173,8080`),但 `allow_methods=["*"]`、`allow_headers=["*"]` 与 `allow_credentials=True` 同时启用,允许任意方法(含 DELETE/PUT)与任意自定义头跨域携带凭据。若后续 `cors_origins_list` 被错误配置为通配 `*`,将与 `allow_credentials=True` 产生更严重风险(浏览器虽拒绝 `*`+credentials 组合,但配置易出错)。
- **修复建议**:
  - 显式列出方法白名单:`["GET","POST","PUT","PATCH","DELETE","OPTIONS"]`。
  - 显式列出头白名单:`["Authorization","Content-Type","X-Trace-Id"]`。
  - 生产环境 `cors_origins_list` 严格限定为已知前端域名。

---

#### M-4. 异常信息直接回显客户端,泄露内部细节

- **风险等级**: 中
- **代码位置**: 多处
  - `backend/app/api/v1/auth.py:34,46,58`(`f"注册失败: {e}"` 等)
  - `backend/app/api/v1/resume.py:41`(`f"解析失败: {e}"`)
  - `backend/app/api/v1/job.py:74,94`(`f"JD 解析失败: {e}"`、`f"创建失败: {e}"`)
  - `backend/app/api/v1/application.py:112,278,306`
  - `backend/app/api/v1/message.py:77`
- **问题描述**:
  大量 `except Exception as e: return fail(..., f"...: {e}")` 将原始异常字符串回显给客户端,可能暴露数据库错误、文件路径、堆栈片段、第三方 API 错误(如豆包 ARK 的内部信息),辅助攻击者信息侦察。
  虽然 `main.py:99-110` 有全局异常处理返回"系统内部错误",但上述接口在路由内部 `try/except` 已先行捕获并拼入响应,绕过了全局处理。
- **修复建议**:
  - 业务异常返回固定友好提示,系统异常统一走全局 handler。
  - 详细异常仅写日志(含 `trace_id`),响应中仅返回 `trace_id` 供排查。
  - 对 `AuthException`/`ValueError` 等业务异常保留原 message,其余 `Exception` 一律不外泄。

---

#### M-5. 文件哈希使用 MD5(弱哈希算法)

- **风险等级**: 中
- **代码位置**: `backend/app/services/file_service.py:55`
- **问题描述**:
  ```python
  file_hash = hashlib.md5(content).hexdigest()
  ```
  MD5 已被密码学界证明存在碰撞攻击,虽此处仅用于去重与文件名生成,不直接用于安全决策,但属于弱哈希反模式。若未来被复用于完整性校验或安全场景,会埋下隐患。
- **修复建议**:
  - 改用 `hashlib.sha256`,与现有逻辑无侵入替换,性能差异可忽略。

---

#### M-6. 文件上传仅校验扩展名,未校验文件内容/MIME

- **风险等级**: 中
- **代码位置**: `backend/app/services/file_service.py:34-40`
- **问题描述**:
  ```python
  def validate(self, filename: str, file_size: int) -> None:
      ext = self._ext(filename)
      if ext not in ALLOWED_EXTENSIONS:   # 仅看扩展名
          raise ValueError(...)
  ```
  校验完全依赖客户端提供的 `filename` 扩展名,未读取文件魔数(magic bytes)或 `upload.content_type`。攻击者可将恶意脚本改名为 `.pdf` 上传,文件会落盘到 `/uploads` 目录(虽 `StaticFiles` 不会执行,但结合 H-6 无鉴权访问,可作为恶意载荷分发点)。`ALLOWED_EXTENSIONS` 中 `.doc` 走 pdfplumber 解析(`doc_parser.py:27-29`),对非法 .doc 文件可能触发解析异常。
- **修复建议**:
  - 读取文件头魔数(PDF `%PDF`、DOCX/OOXML `PK\x03\x04` ZIP)二次校验。
  - 校验 `upload.content_type` 与扩展名一致性。
  - 对 OOXML(`.docx`)解压前做 zip bomb 防护(限制解压后大小)。

---

#### M-7. JWT 令牌载荷未校验签发方/接收方(aud/iss)

- **风险等级**: 中
- **代码位置**: `backend/app/core/security.py:43-52`、`74-80`
- **问题描述**:
  ```python
  payload = {
      "sub": str(subject), "type": token_type,
      "iat": now, "exp": now + expires_delta,
  }
  ...
  payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
  ```
  签发与解码均未设置/校验 `iss`、`aud`、`nbf` 等声明。虽当前单服务场景影响有限,但在多服务/多端共享同一 `SECRET_KEY` 时,某端签发的 token 可被其他端直接接受(令牌混淆)。
- **修复建议**:
  - 签发时增加 `"iss": "zhipin-auth"`,解码时 `jwt.decode(..., options={"verify_iss": True}, issuer="zhipin-auth")`。
  - 区分 access/refresh 之外,可增加 `aud` 标识消费方。

---

#### M-8. 匹配历史接口返回全局数据,未按用户隔离

- **风险等级**: 中
- **代码位置**: `backend/app/api/v1/match.py:114-149`(`match_history`)
- **问题描述**:
  ```python
  stmt = select(MatchRecord)
  if direction:
      stmt = stmt.where(MatchRecord.direction == direction)
  # ❌ 未按 current_user 过滤
  ```
  任意已认证用户(含普通求职者)可分页拉取全平台所有匹配记录(`resume_id`/`job_id`/评分/匹配原因),可据此推断其他用户的投递意向与职位匹配情况。
- **修复建议**:
  - 求职者仅返回 `resume.user_id == current_user.id` 的记录;企业仅返回 `job.user_id == current_user.id` 的记录;管理员可查全部。

---

#### M-9. 前端 JWT 存储于 localStorage,易受 XSS 窃取

- **风险等级**: 中
- **代码位置**: `frontend/src/api/request.ts:18`、`frontend/src/stores/user.ts:16,23,28`
- **问题描述**:
  ```ts
  const token = localStorage.getItem('access_token')
  ...
  localStorage.setItem('access_token', t)
  localStorage.setItem('user_info', JSON.stringify(info))
  ```
  access_token 与用户信息明文存于 localStorage。一旦页面存在 XSS(第三方依赖漏洞、未来引入 `v-html` 等),攻击者可直接 `localStorage.getItem('access_token')` 窃取令牌。相比 httpOnly cookie,localStorage 对 JS 完全可读。
  当前项目未发现 `v-html` 使用(已全局检索),XSS 面较小,但纵深防御不足。
- **修复建议**:
  - 中长期改为后端下发 `HttpOnly` + `Secure` + `SameSite=Strict` 的 cookie 存放 token,前端不再持有原始令牌。
  - 短期可保留 localStorage 方案,但应:限制 token 有效期(已 2h)、引入 CSP 策略、对第三方依赖做 SCA。

---

### 🟢 低危 (LOW)

---

#### L-1. 密码策略偏弱,缺少复杂度要求

- **风险等级**: 低
- **代码位置**: `backend/app/schemas/auth.py:21`、`frontend/src/views/auth/Login.vue:26`
- **问题描述**:
  ```python
  password: str = Field(..., min_length=6, max_length=64, description="密码")
  ```
  仅校验长度 6-64,无大小写/数字/符号复杂度要求,`123456`、`abcdef` 等弱口令可通过。前端登录页 `Login.vue:26` 进一步限制为 6-20 位,但注册侧无复杂度。
- **修复建议**:
  - 注册时增加复杂度校验(至少包含字母+数字,建议 ≥8 位)。
  - 引入常见弱口令黑名单(`password`、`123456`、`admin123` 等)。

---

#### L-2. Neo4j 等凭据使用硬编码默认值

- **风险等级**: 低
- **代码位置**: `backend/app/core/config.py:35-37`、`backend/.env.example:27-28`
- **问题描述**:
  ```python
  NEO4J_USER: str = "neo4j"
  NEO4J_PASSWORD: str = "zhipin123"
  ```
  默认凭据硬编码在源码与示例配置中,若部署未覆盖则使用弱口令运行。
- **修复建议**:
  - 默认值置空,启动时校验非空;凭据统一走密管系统。

---

#### L-3. 开发态 DEBUG 日志级别可能泄露敏感信息

- **风险等级**: 低
- **代码位置**: `backend/app/main.py:19-24`、`backend/app/services/file_service.py:65`、`doc_parser.py:28`
- **问题描述**:
  `APP_DEBUG=True` 时日志级别为 DEBUG,会记录文件绝对路径(`file_service.py:65` `logger.info(f"文件已保存: {file_path} ...")`)、解析细节等。若开发态日志被收集到生产日志系统,可能泄露服务器目录结构。
- **修复建议**:
  - 生产环境强制 `APP_DEBUG=False` 并校验。
  - 日志中文件路径改为相对路径或脱敏。

---

#### L-4. 路由守卫仅做客户端角色前缀校验(纵深防御)

- **风险等级**: 低
- **代码位置**: `frontend/src/router/index.ts:194-231`
- **问题描述**:
  路由守卫基于 localStorage 中的 `user_info.role` 与路径前缀匹配,但 `user_info` 可由用户在浏览器控制台篡改。所幸后端 `require_role` 做了真实鉴权,此处仅影响用户体验而非安全。属可接受的纵深防御层。
- **修复建议**: 保持现状即可;确保所有敏感操作后端均有鉴权(已基本满足)。

---

#### L-5. 文件名生成包含时间戳,存在弱可预测性

- **风险等级**: 低
- **代码位置**: `backend/app/services/file_service.py:56`
- **问题描述**:
  ```python
  filename = f"{now.strftime('%d%H%M%S')}_{file_hash[:8]}{ext}"
  ```
  文件名前段为时间戳(日+时分秒),后段为 md5 前 8 位。仅靠 8 位 hash 防猜测,熵约 32 位。结合 H-6 无鉴权访问,若攻击者能枚举时间窗口,理论可猜中(实际成本较高)。修复 H-6 后此问题降级。
- **修复建议**: 随 H-6 一并修复;或文件名改为完整 UUIDv4。

---

## 4. 已有的安全措施

项目在以下方面已建立较好基线,审计中予以肯定:

| 措施 | 位置 | 说明 |
|------|------|------|
| **密码 BCrypt 哈希** | `core/security.py:19-32` | 使用 bcrypt,处理了 72 字节截断,异常安全返回 False |
| **JWT 类型校验** | `core/deps.py:41-45` | 校验 `type=="access"`,防 refresh 滥用 |
| **JWT 算法固定** | `core/security.py:77` | `algorithms=[settings.JWT_ALGORITHM]` 防 alg 混淆 |
| **账号禁用校验** | `core/deps.py:61-65` | `status != 1` 拒绝访问 |
| **SQLAlchemy ORM 参数化** | 全部 service / api | 无裸 SQL 拼接,`select().where()` 绑定参数,SQL 注入风险低 |
| **Pydantic 输入校验** | `schemas/auth.py` 等 | 注册字段类型/长度/正则(手机号 `^1[3-9]\d{9}$`)校验 |
| **字段白名单** | `api/v1/auth.py:97-100` | `update_profile` 用 `allowed_fields` 白名单,防 mass assignment |
| **PII 脱敏工具** | `utils/mask.py` | `mask_phone`(138****5678)、`mask_email`(z***@qq.com) |
| **企业视角简历脱敏** | `api/v1/resume.py:155-157`、`application.py:359-360` | 企业查看简历时手机/邮箱脱敏(本人/管理员不脱敏) |
| **简历归属校验** | `api/v1/resume.py:116-120,173-177`、`services/resume_service.py:136` | 求职者仅能查看/删除本人简历 |
| **职位归属校验** | `services/job_service.py`(delete/update_status 传 user_id) | 企业仅能操作本人职位 |
| **投递归属校验** | `api/v1/application.py:77-79` | 校验简历归属本人 |
| **管理接口角色守卫** | `api/v1/admin.py:18` | 路由级 `dependencies=[Depends(require_role("ROLE_ADMIN"))]` |
| **管理操作审计日志** | `services/admin_service.py:332-351` | 记录 admin_id/action/target/ip |
| **文件类型/大小限制** | `services/file_service.py:19-20,34-40` | 白名单扩展名 + 10MB 上限 |
| **统一异常处理** | `main.py:99-110` | 兜底返回"系统内部错误" |
| **Nginx 安全头** | `frontend/nginx.conf:101-105` | X-Frame-Options / X-Content-Type-Options / XSS-Protection / Referrer-Policy |
| **Nginx 禁止隐藏文件访问** | `frontend/nginx.conf:108-112` | `location ~ /\. { deny all; }` |
| **前端无 v-html** | 全局检索确认 | Vue 默认转义,无 `v-html`/`innerHTML`,存储型 XSS 面低 |
| **trace_id 追踪** | `main.py:88-95` | 请求级 trace_id 便于排查 |

---

## 5. 安全加固建议

### 5.1 短期(上线前必做,1-2 周)

1. **修复 H-1**:强制 `SECRET_KEY` 生产环境注入随机强密钥,启动校验。
2. **修复 H-2**:生产环境移除默认管理员自动创建,弱口令清零,日志去明文凭据。
3. **修复 H-3 / H-4 / H-5 / M-8**:统一补齐对象级归属校验,建议抽取公共装饰器/依赖:
   ```python
   def require_job_owner(job_id: int, current_user, db): ...
   def require_application_owner(app_id: int, current_user, db): ...
   ```
4. **修复 H-6**:`/uploads` 改为鉴权接口下发文件,移除公开 `StaticFiles` 挂载。
5. **修复 H-7**:生产环境关闭 `/docs`、`/redoc`、`/openapi.json`。
6. **修复 M-1**:登录/注册接入速率限制(slowapi + Redis),失败锁定。
7. **修复 M-4**:统一异常外发策略,系统异常不外泄细节。

### 5.2 中期(1-2 个月)

1. **M-2**:实现 token 黑名单与 refresh token 轮换(一次性使用)。
2. **M-5/M-6**:文件哈希升级 SHA-256,增加文件魔数校验。
3. **M-7**:JWT 增加 `iss`/`aud` 声明校验。
4. **M-9**:评估 token 迁移至 httpOnly cookie 的可行性,引入 CSRF token。
5. **L-1**:密码复杂度策略 + 弱口令黑名单。
6. 引入 **CSP(Content-Security-Policy)** 响应头(nginx 增加 `add_header Content-Security-Policy ...`)。
7. 引入 **依赖安全扫描**(pip-audit / npm audit)接入 CI。

### 5.3 中长期(3-6 个月)

1. 接入 **SIEM/日志审计** 平台,对认证、越权、异常访问做实时告警。
2. 引入 **WAF**(云厂商或 ModSecurity)防护常见 Web 攻击。
3. 实施 **零信任/最小权限**:数据库账号按业务角色拆分,应用不使用 root 库账号。
4. 建立 **漏洞响应流程** 与定期安全审计机制(每季度一次)。
5. 简历等敏感文件存储迁移至 **对象存储(OSS)+ 临时签名 URL**。
6. 关键操作(登录、改密、角色变更)引入 **多因素认证(MFA)**。

---

## 6. 合规性评估(个人信息保护法相关)

项目作为招聘平台,处理大量求职者个人信息(姓名、手机、邮箱、年龄、学历、工作经历、简历文档),属《个人信息保护法》(PIPL)规制的个人信息处理者。结合本次审计,合规性评估如下:

| 合规要点 | 法条依据 | 当前状态 | 风险与建议 |
|----------|----------|----------|------------|
| **处理合法基础** | 第 13 条 | 注册时未明确告知/同意 | 建议注册流程增加《隐私政策》明示告知与同意留痕 |
| **最小必要原则** | 第 6 条 | 简历字段均与招聘相关,基本合理 | 建议 `gender`/`age` 等敏感字段评估必要性(就业歧视风险) |
| **敏感个人信息** | 第 28-32 条 | 手机/邮箱已脱敏(企业视角) | 需取得单独同意;H-3/H-5 越权导致敏感信息泄露,违反本条 |
| **访问控制与授权** | 第 51 条(安全措施) | 角色级授权完善,对象级存在 IDOR 缺口(H-3/4/5) | **必须修复**,否则构成未授权访问个人信息 |
| **数据泄露防护** | 第 57 条(泄露通知) | 无泄露检测/告警机制 | 建议:修复越权漏洞 + 建立访问审计日志 + 制定泄露应急响应预案 |
| **存储安全** | 第 51 条 | 简历文件明文存储于本地磁盘,无鉴权可访问(H-6) | 建议:迁移至加密对象存储 + 鉴权访问 + 静态加密 |
| **个人信息跨境** | 第 38-43 条 | 豆包 ARK API 为国内服务,无跨境 | 当前合规;若引入境外 LLM 需重新评估 |
| **用户权利保障** | 第 44-50 条 | 支持删除简历/账号(管理员) | 建议增加用户自助导出/删除个人信息功能,响应"查阅/复制/删除"请求 |
| **自动化决策** | 第 24 条 | 智能匹配基于规则+向量,非纯自动化决策 | 建议向求职者说明匹配机制,提供退出/解释途径 |
| **未成年人信息** | 第 31 条 | 注册无年龄校验,理论可采集未成年人信息 | 建议注册增加成年声明/年龄校验 |
| **留存期限** | 第 19 条 | 未规定信息留存/删除策略 | 建议制定分类分级留存策略,过期自动删除 |

### 合规风险结论

当前存在 **H-3 / H-5 / H-6** 三项高危直接导致求职者个人信息可被未授权第三方(其他企业/任意访客)获取,涉嫌违反 PIPL 第 51 条(未采取相应技术措施保障信息安全)与第 28-32 条(敏感个人信息处理),若发生实际泄露需按第 57 条履行通知义务并可能面临第 66 条行政处罚(最高营业额 5% 罚款)。

**建议优先级最高的整改动作**:修复全部对象级越权漏洞(H-3/4/5、M-8)、关闭上传文件无鉴权访问(H-6),并补充访问审计日志,以满足合规底线。

---

## 附录 A:问题清单速查表

| 编号 | 等级 | 类别 | 标题 | 位置 |
|------|------|------|------|------|
| H-1 | 高 | weak_crypto/secret | JWT 密钥弱默认值 | `core/config.py:22` |
| H-2 | 高 | weak_credentials | 默认管理员弱口令+日志明文 | `main.py:48-57` |
| H-3 | 高 | idor | 投递记录越权泄露简历 PII | `api/v1/application.py:189-253` |
| H-4 | 高 | idor | 投递状态更新越权 | `api/v1/application.py:256-306` |
| H-5 | 高 | idor | 匹配候选人推荐越权 | `api/v1/match.py:88-111` |
| H-6 | 高 | sensitive_data_exposure | 上传文件无鉴权静态访问 | `main.py:117-120` |
| H-7 | 高 | info_disclosure | 生产暴露 API 文档 | `main.py:67-75` |
| M-1 | 中 | brute_force | 认证无限流/锁定 | `api/v1/auth.py:37-58` |
| M-2 | 中 | broken_session | 退出无失效/refresh 无轮换 | `auth.py:61-64`、`auth_service.py:106-121` |
| M-3 | 中 | cors | CORS 方法/头通配+credentials | `main.py:78-84` |
| M-4 | 中 | info_disclosure | 异常细节回显客户端 | 多处 api/v1 |
| M-5 | 中 | weak_crypto | 文件哈希用 MD5 | `file_service.py:55` |
| M-6 | 中 | file_upload | 仅校验扩展名未校验内容 | `file_service.py:34-40` |
| M-7 | 中 | jwt | 缺 iss/aud 声明校验 | `core/security.py:43-80` |
| M-8 | 中 | idor | 匹配历史未按用户隔离 | `api/v1/match.py:114-149` |
| M-9 | 中 | token_storage | JWT 存 localStorage | `request.ts:18`、`stores/user.ts:16-28` |
| L-1 | 低 | weak_policy | 密码策略偏弱 | `schemas/auth.py:21` |
| L-2 | 低 | hardcoded_secret | Neo4j 凭据硬编码 | `core/config.py:35-37` |
| L-3 | 低 | info_disclosure | DEBUG 日志泄露路径 | `main.py:19-24` |
| L-4 | 低 | authz_client | 路由守卫仅客户端校验 | `router/index.ts:194-231` |
| L-5 | 低 | weak_randomness | 文件名时间戳弱可预测 | `file_service.py:56` |

---

## 附录 B:审查文件清单

**后端已审查**:`main.py`、`core/{config,deps,security}.py`、`db/base.py`、`api/v1/{auth,resume,admin,job,application,match,message}.py`、`services/{file_service,doc_parser,auth_service,resume_service,admin_service}.py`、`utils/mask.py`、`schemas/auth.py`、`requirements.txt`、`.env.example`

**前端已审查**:`api/request.ts`、`stores/user.ts`、`router/index.ts`、`views/auth/Login.vue`、`nginx.conf`、`package.json`,并对 `frontend/src` 全局检索 `v-html`/`innerHTML`/`localStorage`。

**未深入审查**(声明):`ai/ark_client.py`、`services/graph_service.py`、`db/neo4j_client.py`、`api/v1/{graph,health}.py`、前端业务页面(非核心安全文件),如需要可补充专项审计。

---

*报告结束*
