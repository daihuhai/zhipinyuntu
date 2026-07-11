# 智聘云图 - 三端功能更新与优化文档 (2026-07-08)

> 基于赛题要求: "通过自然语言处理与知识图谱技术, 实现简历与职位要求的深度结构化解析、能力可视化与智能推荐"
> 对标场景: 省级人才服务中心管理 10 万+ 简历, 服务企业 5000+ 家, 双向精准匹配

---

## 一、赛题对标分析

### 1.1 赛题要求 vs 当前实现

| 赛题要求 | 当前实现状态 | 差距 |
|---------|------------|------|
| Word 文档批量录入简历 | 单个上传 + AI 解析 | 缺少**批量上传** |
| 职位描述结构化解析 | JD 文件上传 + 手动创建 | 已实现 |
| AI 提取技能标签 | 豆包 LLM 结构化解析 | 已实现 |
| 个人能力知识图谱 | ECharts 力导向图 (降级模式) | 已实现, Neo4j 降级 |
| 岗位要求知识图谱 | 未实现 | **缺失** |
| 双向精准匹配 | 召回→粗排→精排(带缓存) | 已实现 |
| 可视化图谱展示匹配度 | ResumeGraph 展示技能图谱 | 缺少**人岗对比图谱** |
| 企业推荐高分候选人 | 仅从投递者中选取 | 已实现 |

### 1.2 核心差距

1. **企业无法查看求职者原始简历文件** — 只展示结构化字段, 看不到原始 PDF/DOC
2. **简历解析的工作经历和项目经历未展示** — AI 解析了但前端未呈现
3. **岗位能力图谱缺失** — 只有求职者图谱, 没有职位要求图谱
4. **管理端缺少数据可视化** — 仪表盘只有数字和描述列表, 没有图表
5. **管理端简历/职位管理无详情查看** — 只能删除, 不能查看完整信息
6. **求职者个人设置不可编辑** — Profile 页面只读

---

## 二、求职者端 (Seeker) 功能更新

### 功能 S1: 简历详情完整展示 (P0)

**现状**: `ResumeList.vue` 只有表格列表, 点击操作只有"能力图谱""推荐职位""删除", 没有查看简历完整详情的入口。AI 解析的工作经历和项目经历存在 `raw_parse_json` 中但从未展示。

**方案**:
- 新增简历详情抽屉, 展示完整解析结果
- 包含: 基本信息 + 工作经历(el-timeline) + 项目经历(el-timeline) + 技能列表 + 自我评价
- 新增"查看原文件"按钮, 新窗口打开原始 PDF/DOC

**涉及文件**:
- `backend/app/api/v1/resume.py` — `get_resume` 接口增加返回 `work_experience` + `projects`
- `frontend/src/views/seeker/ResumeList.vue` — 新增详情抽屉 + 查看原文件按钮

### 功能 S2: 职位详情增加能力要求图谱 (P1)

**现状**: `JobDetail.vue` 只展示职位描述和技能要求列表, 缺少图谱可视化。

**方案**:
- 在职位详情页底部增加"岗位能力要求图谱"卡片
- ECharts 力导向图: 中心节点=职位, 周围节点=技能要求
- 技能节点颜色区分: 必须=红色, 优先=橙色
- 若求职者已登录且有简历, 叠加显示已匹配(绿色)/缺失(红色)技能

**涉及文件**:
- `frontend/src/views/seeker/JobDetail.vue` — 新增图谱卡片
- `frontend/src/api/graph.ts` — 新增职位图谱 API

### 功能 S3: 个人设置可编辑 (P1)

**现状**: `Profile.vue` 只展示基本信息, 无法修改。

**方案**:
- 支持修改昵称、手机号、邮箱
- 企业用户可修改公司名称
- 密码修改(需输入旧密码)

**涉及文件**:
- `backend/app/api/v1/auth.py` — 新增 `PUT /auth/profile` 接口
- `frontend/src/views/seeker/Profile.vue` — 改为表单编辑模式

### 功能 S4: 职位收藏功能 (P2)

**现状**: 求职者浏览职位后无法收藏, 只能直接投递。

**方案**:
- 职位详情页增加"收藏"按钮
- 仪表盘增加"收藏的职位"快捷入口
- 新增收藏列表页

**涉及文件**:
- `backend/app/models/` — 新增 `Favorite` 模型
- `backend/app/api/v1/job.py` — 新增收藏/取消收藏/收藏列表接口
- `frontend/src/views/seeker/JobDetail.vue` — 增加收藏按钮
- `frontend/src/views/seeker/Dashboard.vue` — 增加收藏入口

---

## 三、企业端 (Employer) 功能更新

### 功能 E1: 简历预览增强 — 查看原始简历文件 (P0)

**现状**: 投递管理中点击"查看简历"只显示结构化字段, 无法查看求职者上传的原始 PDF/DOC 简历。

**方案**:
- 后端新增 `GET /resumes/{id}/file` 接口, 返回文件 URL + 权限校验
- 企业只能查看投递了自己职位的简历
- 前端在简历预览抽屉中新增"查看原文件"按钮, 新窗口打开

**涉及文件**:
- `backend/app/api/v1/resume.py` — 新增文件接口 + 企业权限校验
- `frontend/src/views/employer/Applications.vue` — 简历抽屉增加查看原文件按钮

### 功能 E2: 简历预览增强 — 工作经历和项目经历 (P0)

**现状**: 简历预览抽屉只展示基本信息和技能标签, 缺少工作经历和项目经历。

**方案**:
- `list_employer_applications` 接口返回数据中增加 `work_experience` 和 `projects`
- 前端用 `el-timeline` 组件展示, 符合简历视觉习惯

**涉及文件**:
- `backend/app/api/v1/application.py` — `list_employer_applications` 解析 `raw_parse_json`
- `frontend/src/views/employer/Applications.vue` — 增加工作经历和项目经历时间线

### 功能 E3: 候选人推荐详情增强 (P1)

**现状**: `Candidates.vue` 只展示候选人卡片(分数+原因), 无法查看候选人简历详情。

**方案**:
- 候选人卡片增加"查看简历"按钮
- 弹出简历预览抽屉, 展示完整简历信息(同投递管理的简历预览)
- 包含工作经历、项目经历、技能列表、查看原文件

**涉及文件**:
- `frontend/src/views/employer/Candidates.vue` — 增加简历预览抽屉

### 功能 E4: 企业设置可编辑 (P1)

**现状**: 企业 `Profile.vue` 只展示信息, 无法修改。

**方案**:
- 支持修改企业名称、联系人、联系电话、企业简介
- 复用求职者端的 `PUT /auth/profile` 接口

**涉及文件**:
- `frontend/src/views/employer/Profile.vue` — 改为表单编辑模式

---

## 四、管理端 (Admin) 功能更新

### 功能 A1: 仪表盘数据可视化增强 (P0)

**现状**: `Dashboard.vue` 只有 KPI 数字和 `el-descriptions` 文字列表, 没有图表, 作为"运营监控看板"缺乏视觉冲击力。

**方案**:
- 新增 ECharts 图表:
  - 用户增长趋势线图 (近 14 天)
  - 简历解析状态饼图 (成功/失败/待解析)
  - 职位状态分布柱状图 (招聘中/下架/草稿)
  - 热门技能 Top10 横向柱状图
- 保留现有 KPI 卡片

**涉及文件**:
- `backend/app/api/v1/admin.py` — 新增 `/admin/dashboard/trend` 接口
- `frontend/src/views/admin/Dashboard.vue` — 增加 ECharts 图表

### 功能 A2: 简历管理增加详情查看 (P0)

**现状**: `Resumes.vue` 只有列表, 操作只有"删除", 无法查看简历详情。

**方案**:
- 表格操作列增加"查看详情"按钮
- 弹出抽屉展示完整简历信息(基本信息 + 工作经历 + 项目经历 + 技能列表)
- 增加"查看原文件"按钮, 管理员可查看原始 PDF/DOC

**涉及文件**:
- `frontend/src/views/admin/Resumes.vue` — 增加详情抽屉
- `backend/app/api/v1/resume.py` — `get_resume` 已支持 ADMIN 权限

### 功能 A3: 职位管理增加详情查看 (P1)

**现状**: `Jobs.vue` 只有列表, 操作只有"修改状态"和"删除", 无法查看职位完整信息。

**方案**:
- 表格操作列增加"查看详情"按钮
- 弹出抽屉展示职位完整信息(描述 + 技能要求 + 公司信息)
- 增加职位能力要求图谱

**涉及文件**:
- `frontend/src/views/admin/Jobs.vue` — 增加详情抽屉

### 功能 A4: 用户管理增加详情查看 (P1)

**现状**: `Users.vue` 只有列表, 无法查看用户的简历数、投递数等关联信息。

**方案**:
- 表格操作列增加"查看详情"按钮
- 弹出抽屉展示用户信息 + 关联统计(简历数、投递数、匹配记录数)
- 企业用户: 展示发布的职位数和收到投递数
- 求职者: 展示简历数和投递记录

**涉及文件**:
- `backend/app/api/v1/admin.py` — 新增 `/admin/users/{id}/detail` 接口
- `frontend/src/views/admin/Users.vue` — 增加详情抽屉

### 功能 A5: 批量操作功能 (P2)

**现状**: 简历管理和职位管理都不支持批量操作。

**方案**:
- 简历管理: 批量删除、批量重新解析
- 职位管理: 批量上架/下架
- 用户管理: 批量禁用/启用

**涉及文件**:
- `backend/app/api/v1/admin.py` — 新增批量接口
- `frontend/src/views/admin/Resumes.vue` / `Jobs.vue` / `Users.vue` — 增加批量操作栏

---

## 五、实施计划

### 阶段一: 后端接口增强 (P0 功能)

| 序号 | 任务 | 涉及文件 |
|------|------|---------|
| 1.1 | `get_resume` 接口增加 `work_experience` + `projects` 返回 | `resume.py` |
| 1.2 | `get_resume` 接口开放企业权限 (校验投递关系) | `resume.py` |
| 1.3 | 新增 `GET /resumes/{id}/file` 接口 (返回文件 URL + 权限校验) | `resume.py` |
| 1.4 | `list_employer_applications` 补充工作经历和项目经历 | `application.py` |
| 1.5 | 新增 `PUT /auth/profile` 接口 (修改个人信息) | `auth.py` |
| 1.6 | 新增 `/admin/dashboard/trend` 接口 (仪表盘趋势数据) | `admin.py` |
| 1.7 | 新增 `/admin/users/{id}/detail` 接口 (用户详情) | `admin.py` |

### 阶段二: 前端 P0 功能实现

| 序号 | 任务 | 涉及文件 |
|------|------|---------|
| 2.1 | 求职者简历列表增加详情抽屉 + 查看原文件 | `seeker/ResumeList.vue` |
| 2.2 | 企业投递管理简历预览增加工作经历/项目经历/查看原文件 | `employer/Applications.vue` |
| 2.3 | 管理端仪表盘增加 ECharts 图表 | `admin/Dashboard.vue` |
| 2.4 | 管理端简历管理增加详情抽屉 | `admin/Resumes.vue` |

### 阶段三: 前端 P1 功能实现

| 序号 | 任务 | 涉及文件 |
|------|------|---------|
| 3.1 | 求职者职位详情增加能力要求图谱 | `seeker/JobDetail.vue` |
| 3.2 | 求职者个人设置改为可编辑表单 | `seeker/Profile.vue` |
| 3.3 | 企业候选人推荐增加简历预览 | `employer/Candidates.vue` |
| 3.4 | 企业设置改为可编辑表单 | `employer/Profile.vue` |
| 3.5 | 管理端职位管理增加详情查看 | `admin/Jobs.vue` |
| 3.6 | 管理端用户管理增加详情查看 | `admin/Users.vue` |

### 阶段四: 功能测试与验证

| 序号 | 任务 |
|------|------|
| 4.1 | 求职者端: 简历详情 → 工作经历展示 → 查看原文件 |
| 4.2 | 企业端: 投递管理 → 简历预览 → 工作经历 → 查看原文件 |
| 4.3 | 管理端: 仪表盘图表渲染 → 简历详情查看 |
| 4.4 | 三端 Profile 编辑功能验证 |

---

## 六、技术设计

### 6.1 后端接口设计

#### 接口 1: 获取简历详情 (增强)

```
GET /api/v1/resumes/{resume_id}

权限: ROLE_SEEKER(本人) | ROLE_EMPLOYER(投递了自己职位) | ROLE_ADMIN

响应新增字段:
{
  "work_experience": [
    {"company": "...", "position": "...", "duration": "...", "description": "..."}
  ],
  "projects": [
    {"name": "...", "role": "...", "description": "..."}
  ]
}
```

#### 接口 2: 获取简历文件 URL

```
GET /api/v1/resumes/{resume_id}/file

权限: ROLE_SEEKER(本人) | ROLE_EMPLOYER(投递了自己职位) | ROLE_ADMIN

响应:
{
  "code": 0,
  "data": {
    "doc_url": "/uploads/resumes/202607/xxx.pdf",
    "filename": "张明_简历.pdf"
  }
}
```

#### 接口 3: 修改个人信息

```
PUT /api/v1/auth/profile

权限: 所有登录用户

请求体: { "nickname": "...", "phone": "...", "email": "...", "company_name": "..." }
响应: { "code": 0, "message": "更新成功" }
```

#### 接口 4: 管理端仪表盘趋势

```
GET /api/v1/admin/dashboard/trend

权限: ROLE_ADMIN

响应:
{
  "user_growth": { "days": [...], "counts": [...] },
  "resume_status": { "success": N, "failed": N, "pending": N },
  "job_status": { "active": N, "inactive": N, "draft": N },
  "hot_skills": [{ "name": "Java", "count": N }, ...]
}
```

#### 接口 5: 用户详情 (管理端)

```
GET /api/v1/admin/users/{user_id}/detail

权限: ROLE_ADMIN

响应:
{
  "user": { ... },
  "stats": {
    "resume_count": N,
    "application_count": N,
    "job_count": N,        // 企业用户
    "received_count": N     // 企业用户
  }
}
```

### 6.2 前端组件设计

#### 简历详情抽屉 (三端共用)

```
el-drawer (简历详情)
├── 基本信息 (姓名/学历/学校/专业/工作年限/城市)
├── 【新】工作经历 (el-timeline)
│   └── 每段经历: 公司 + 职位 + 时长 + 描述
├── 【新】项目经历 (el-timeline)
│   └── 每个项目: 名称 + 角色 + 描述
├── 技能列表 (el-tag 标签)
├── 自我评价
└── 操作按钮
    ├── 【已有】联系候选人 (企业端)
    └── 【新】查看原文件 (新窗口打开 PDF/DOC)
```

#### 管理端仪表盘 (增强后)

```
el-row (KPI 卡片 — 已有)
el-row
├── el-col(12) — 用户增长趋势线图 (ECharts)
└── el-col(12) — 简历解析状态饼图 (ECharts)
el-row
├── el-col(12) — 职位状态分布柱状图 (ECharts)
└── el-col(12) — 热门技能 Top10 横向柱状图 (ECharts)
el-row
├── el-col(12) — 最近新增用户 (已有)
└── el-col(12) — 匹配统计 (已有)
```

---

## 七、预期效果

### 求职者端
1. 简历列表 → 点击查看详情 → 看到完整解析结果(含工作经历/项目经历) + 查看原文件
2. 职位详情 → 看到岗位能力要求图谱 → 直观了解技能要求
3. 个人设置 → 可修改昵称/手机/邮箱

### 企业端
1. 投递管理 → 查看简历 → 看到工作经历时间线 + 查看原始 PDF 简历
2. 候选人推荐 → 点击查看简历 → 看到完整简历详情
3. 企业设置 → 可修改企业名称/联系方式

### 管理端
1. 仪表盘 → 看到 4 个 ECharts 图表 + KPI 卡片, 具备"运营监控"视觉效果
2. 简历管理 → 点击查看详情 → 看到完整简历 + 查看原文件
3. 职位管理 → 点击查看详情 → 看到职位完整信息
4. 用户管理 → 点击查看详情 → 看到用户关联统计

### 答辩展示
- 体现"文档智能解析"深度: 不只是提取字段, 还保留完整工作履历
- 体现"知识图谱"应用: 求职者图谱 + 岗位图谱 + 匹配可视化
- 体现"三端完整": 求职者/企业/管理端功能闭环
- 体现"数据驾驶舱": 管理端仪表盘具备专业可视化

---

*文档创建时间: 2026-07-08*
*创建人: 智聘云图开发团队*
