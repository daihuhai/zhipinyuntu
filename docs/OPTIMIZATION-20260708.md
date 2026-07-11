# 智聘云图 产品优化方案

> 日期：2026-07-08
> 范围：求职者端 / 企业端 / 管理端 全链路体验与性能优化
> 技术栈：Vue3 + Element Plus + FastAPI + MySQL

## 一、优化项总览

| 编号 | 优化项 | 端 | 优先级 | 状态 |
|------|--------|----|--------|------|
| OPT-01 | 消息中心新增新消息轮询 | 求职者/企业 | P0 | 已实现 |
| OPT-02 | 求职者投递记录增加状态筛选 | 求职者 | P0 | 已实现 |
| OPT-03 | 企业投递管理增加状态筛选与关键字搜索 | 企业 | P0 | 已实现 |
| OPT-04 | 企业投递管理与职位列表补充分页 | 企业 | P1 | 待实施 |
| OPT-05 | 管理端运营看板增加自动刷新与手动刷新 | 管理 | P1 | 待实施 |
| OPT-06 | echarts 改为按需引入降低包体积 | 全端 | P1 | 待实施 |
| OPT-07 | 求职者仪表盘推荐职位 KPI 取真实值 + 职位广场空状态布局修正 | 求职者 | P2 | 待实施 |

---

## 二、详细优化方案

### OPT-01 消息中心新增新消息轮询（P0）

**问题描述**
`frontend/src/views/Message.vue` 在选中某个会话后，仅在「选择会话」「发送消息」时拉取消息记录，缺少定时轮询。后果是：当用户停留在某个聊天窗口时，对方发来的新消息不会实时呈现，必须手动切换会话再切回来才能看到。对于一个招聘沟通场景，这种“消息收不到”的体验会直接导致面试邀请、沟通意向被延误。

虽然 `SeekerLayout.vue` / `EmployerLayout.vue` 每 15 秒轮询未读总数并更新菜单角标，但角标变化并不会刷新当前已打开会话的消息流，用户依然看不到正文。

**优化方案**
在 `Message.vue` 中：
1. 当存在 `activeUserId`（已选中会话）时，启动 10 秒间隔的轮询定时器，静默拉取当前会话消息与未读总数；
2. 拉取到新消息（消息条数增加）时，自动滚动到底部；
3. 轮询失败时静默处理，不打扰用户；
4. 组件卸毁或切换会话时清理定时器，避免内存泄漏与重复请求。

**涉及文件**
- `frontend/src/views/Message.vue`

**优先级**：P0（核心沟通链路体验缺陷）

---

### OPT-02 求职者投递记录增加状态筛选（P0）

**问题描述**
`frontend/src/views/seeker/Applications.vue` 仅提供「刷新」按钮，无法按投递状态（已投递 / 已查看 / 面试邀请 / 不合适 / 已录用）筛选。求职者投递量一旦上升，无法快速定位“面试邀请”“已录用”等需要重点关注的状态，只能逐页翻看表格。后端 `GET /applications` 也未支持 `status` 查询参数。

**优化方案**
1. 后端 `list_my_applications` 增加 `status: Optional[int]` 查询参数，命中时追加 `JobApplication.status == status` 过滤；`total` 统计同步带上过滤条件；
2. 前端在顶部筛选区增加状态选择器（全部 / 已投递 / 已查看 / 面试邀请 / 不合适 / 已录用），切换时重置到第 1 页并重新拉取；
3. 空状态文案随筛选条件变化（如“暂无面试邀请”）。

**涉及文件**
- `backend/app/api/v1/application.py`
- `frontend/src/views/seeker/Applications.vue`

**优先级**：P0（求职者最高频的进度追踪任务缺失关键筛选）

---

### OPT-03 企业投递管理增加状态筛选与关键字搜索（P0）

**问题描述**
`frontend/src/views/employer/Applications.vue` 只能按职位筛选，无法按投递状态、候选人姓名等过滤。企业收到大量投递后，无法快速筛出“面试邀请”待处理项，也无法按候选人姓名查找。后端 `GET /applications/employer` 虽然全量返回数据，但前端未提供任何二次过滤手段。

**优化方案**
由于企业端投递接口已全量返回数据到前端，采用前端过滤即可，无需改动后端：
1. 增加状态筛选选择器（全部 / 已投递 / 已查看 / 面试邀请 / 不合适 / 已录用）；
2. 增加候选人姓名关键字搜索框（带 300ms 防抖）；
3. 用 `computed` 派生过滤后的列表渲染表格，并显示“已筛选 X / 共 Y 条”；
4. 选中职位变化时重置过滤条件。

**涉及文件**
- `frontend/src/views/employer/Applications.vue`

**优先级**：P0（企业端筛选候选人的核心流程缺失）

---

### OPT-04 企业投递管理与职位列表补充分页（P1）

**问题描述**
- `GET /applications/employer` 后端一次性返回企业所有职位的全部投递记录（含完整简历、技能、匹配分析），前端 `employer/Applications.vue` 也无分页器。当投递量达到数百上千时，单次请求耗时与前端渲染压力都会陡增。
- `employer/JobList.vue` 调用 `jobApi.myList` 同样未传分页参数，职位数量多时全量加载。

**优化方案**
1. 后端 `list_employer_applications` 增加 `page` / `size` 查询参数，返回 `{items, total}`，匹配分析与简历信息仍随项返回；
2. 前端 `applicationApi.employerList` 透传 `page`/`size`，视图层增加分页器；
3. `jobApi.myList` 后端补充分页参数，`JobList.vue` 增加分页器。

**涉及文件**
- `backend/app/api/v1/application.py`
- `backend/app/api/v1/job.py`
- `frontend/src/api/application.ts`
- `frontend/src/views/employer/Applications.vue`
- `frontend/src/views/employer/JobList.vue`

**优先级**：P1（数据量增长后的性能与可用性问题）

---

### OPT-05 管理端运营看板增加自动刷新与手动刷新（P1）

**问题描述**
`frontend/src/views/admin/Dashboard.vue` 作为“运营监控看板”，数据仅在进入页面时加载一次，之后既无定时刷新也无手动刷新按钮。运营人员查看实时用户增长、简历解析状态时必须手动刷新整个页面，体验割裂。

**优化方案**
1. 增加手动「刷新」按钮（带 loading 态）；
2. 增加 60 秒自动刷新（页面可见时才刷新，用 `document.visibilitychange` 监听，切到后台暂停）；
3. 在卡片头部展示“最近更新时间”。

**涉及文件**
- `frontend/src/views/admin/Dashboard.vue`

**优先级**：P1（监控类页面缺少实时性）

---

### OPT-06 echarts 改为按需引入降低包体积（P1）

**问题描述**
`admin/Dashboard.vue`、`seeker/Dashboard.vue`、`seeker/JobDetail.vue` 均使用 `import * as echarts from 'echarts'` 全量引入，会将整个 echarts（含所有图表类型与组件）打进主 bundle，显著增加首屏体积与加载时间。

**优化方案**
改为 `echarts/core` + 按需注册：
```ts
import * as echarts from 'echarts/core'
import { LineChart, BarChart, PieChart, GraphChart } from 'echarts/charts'
import { GridComponent, TooltipComponent, LegendComponent, TitleComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
echarts.use([LineChart, BarChart, PieChart, GraphChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent, CanvasRenderer])
```
预期可减少 echarts 产物体积 50% 以上。

**涉及文件**
- `frontend/src/views/admin/Dashboard.vue`
- `frontend/src/views/seeker/Dashboard.vue`
- `frontend/src/views/seeker/JobDetail.vue`

**优先级**：P1（前端性能）

---

### OPT-07 求职者仪表盘推荐职位 KPI 取真实值 + 职位广场空状态布局修正（P2）

**问题描述**
1. `seeker/Dashboard.vue` 中 KPI“推荐职位”写死为 `value: '0'`（注释标注 “M4 接入”一直未接入），数据失真；
2. `seeker/Jobs.vue` 的 `el-empty` 放在 `.job-grid`（CSS Grid）内部，会作为网格项渲染，空状态被挤压在单列宽度内，布局错乱。

**优化方案**
1. 仪表盘“推荐职位”调用推荐接口取真实条数，或暂未接入时改为隐藏该 KPI，避免展示误导性 0；
2. `Jobs.vue` 将 `el-empty` 移出 `.job-grid` 容器，或给空状态加 `grid-column: 1 / -1` 占满整行。

**涉及文件**
- `frontend/src/views/seeker/Dashboard.vue`
- `frontend/src/views/seeker/Jobs.vue`

**优先级**：P2（数据准确性与交互细节）

---

## 三、P0 已实现清单

以下 3 项 P0 优化已在本轮完成代码实现：

- ✅ **OPT-01 消息中心新增新消息轮询** — 修改 `frontend/src/views/Message.vue`，已选中会话时每 10 秒静默拉取新消息并自动滚动到底部，卸毁/切会话时清理定时器。
- ✅ **OPT-02 求职者投递记录增加状态筛选** — 后端 `application.py` 的 `GET /applications` 增加 `status` 查询参数并同步过滤 `total`；前端 `seeker/Applications.vue` 增加状态选择器，切换重置到第 1 页。
- ✅ **OPT-03 企业投递管理增加状态筛选与关键字搜索** — `employer/Applications.vue` 增加状态选择器与候选人姓名搜索（300ms 防抖），`computed` 派生过滤结果并展示筛选计数。

P1 / P2 项留待后续迭代。
