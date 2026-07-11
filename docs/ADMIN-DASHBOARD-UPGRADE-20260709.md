# 管理员大数据中心升级方案 (v2.0)

> 文档版本: 2026-07-09  
> 目标: 将当前单调的管理后台仪表盘升级为「大数据指挥中心」风格的可视化面板，支持多维度数据穿透、实时滚动监控、动态轮播与全屏大屏展示。

---

## 一、现状分析

### 1.1 当前 Dashboard.vue 痛点
| 维度 | 现状 | 问题 |
|------|------|------|
| 视觉风格 | 白底卡片 + 标准 ECharts | 缺乏科技感，与求职者端能力图谱的深色霓虹风格割裂 |
| 数据密度 | 4 KPI + 4 图表 + 2 表格 | 仅展示聚合数，缺少趋势/对比/排行/地图维度 |
| 交互能力 | 仅 hover tooltip | 无时间范围切换、无下钻、无全屏、无自动刷新 |
| 实时性 | 手动刷新 | 无 WebSocket / 轮询，数据滞后 |
| 图表类型 | 柱状/折线/饼图/横向柱 | 缺少漏斗、桑基、词云、地图、仪表盘、滚动榜单 |

### 1.2 后端可复用数据资产
- `get_dashboard_stats()` → users/resumes/jobs/matches 聚合 + recent_users/recent_jobs
- `get_dashboard_trend()` → user_growth(14d) / resume_status / job_status / hot_skills Top10
- `list_users/list_resumes/list_jobs/list_logs` → 分页明细，可用于实时滚动榜单

### 1.3 后端模型可挖掘维度
| 模型 | 字段 | 可视化维度 |
|------|------|-----------|
| SysUser | role / status / created_at / last_login_at / gender | 角色分布饼图、活跃度热力、性别比例、登录趋势 |
| Resume | education / school / major / work_years / parse_status / created_at | 学历分布、院校 TOP、专业 TOP、经验段位、解析成功率漏斗 |
| Job | title / company / work_city / salary_min/max / status / education_required / experience_required | 薪资分布箱线、城市热力、学历要求雷达、经验要求分布 |
| JobApplication | job_id / applicant_id / status / created_at | 投递趋势、状态漏斗、岗位热度榜 |
| MatchRecord | total_score / created_at | 匹配分分布直方图、匹配趋势 |
| ResumeSkill | skill_name | 技能词云、技能共生网络 |
| AdminLog | action / target_type / created_at / ip | 管理操作趋势、操作类型分布 |

---

## 二、设计目标

1. **视觉震撼**: 深色科技风 + 霓虹发光 + 粒子背景，对标阿里 DataV / 腾讯云图大屏
2. **数据全貌**: 一屏展示 12+ 图表模块，覆盖用户/简历/职位/投递/匹配/技能/日志 7 大域
3. **实时感知**: 30s 轮询刷新 KPI，操作日志实时滚动流入
4. **交互流畅**: 支持时间范围切换(今日/7日/30日/全部)、全屏模式、图表联动下钻
5. **响应式适配**: 1920×1080 大屏优先，兼容 1366 笔记本与移动端竖屏

---

## 三、整体布局设计 (1920×1080)

```
┌──────────────────────────────────────────────────────────────────────┐
│  [LOGO] 智聘云图 · 数据指挥中心    [时间] [全屏] [刷新] [时间范围▼]    │  Header (64px)
├──────────────────────────────────────────────────────────────────────┤
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐               │
│  │用户数│ │简历数│ │职位数│ │投递数│ │匹配数│ │均匹配│               │  KPI Row (96px)
│  │ 10w+ │ │ 8.6k │ │ 1.2k │ │ 5.4k │ │ 3.2k │ │ 78.5 │               │  6 卡片
│  └──────┘ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘               │
├────────────────────┬──────────────────────────┬──────────────────────┤
│  用户增长趋势       │  平台核心指标仪表盘        │  实时操作日志流       │
│  (双轴柱+线 14d)    │  (3 个圆形 Gauge)         │  (滚动列表 auto)     │
│  420px              │  420px                    │  420px               │
├────────────────────┼──────────────────────────┴──────────────────────┤
│  简历解析漏斗       │  职位城市分布 TOP10        │  热门技能词云         │
│  (Funnel)           │  (横向柱状 + 地图标注)     │  (WordCloud)         │
│  380px              │  380px                    │  380px               │
├────────────────────┼──────────────────────────┬──────────────────────┤
│  投递状态漏斗       │  匹配分分布直方图          │  院校 TOP10 滚动榜   │
│  (Sankey/Funnel)    │  (Histogram + 均值线)     │  (Ranking auto-roll) │
│  360px              │  360px                    │  360px               │
├────────────────────┴──────────────────────────┴──────────────────────┤
│  底部跑马灯: 今日新增 N 用户 · N 简历 · N 职位 · 系统运行正常          │  Footer (32px)
└──────────────────────────────────────────────────────────────────────┘
```

---

## 四、模块详细设计

### 4.1 Header 顶部栏 (64px)

| 元素 | 说明 |
|------|------|
| Logo + 标题 | 左侧 logo.png 32px + "智聘云图 · 数据指挥中心" 渐变文字 |
| 实时时钟 | 中间 `YYYY-MM-DD HH:mm:ss` 每秒更新 |
| 全屏按钮 | `requestFullscreen()` 切换大屏模式 |
| 手动刷新 | 重新拉取所有数据 |
| 时间范围 | 下拉: 今日 / 近 7 日 / 近 30 日 / 全部，联动所有图表 |

### 4.2 KPI 卡片行 (96px, 6 张)

每张卡片包含: 图标 + 主数值(CountUp 动画) + 副标签 + 环比箭头(↑绿↓红)

| 卡片 | 数据源 | 环比计算 |
|------|--------|---------|
| 用户总数 | stats.users.total | 对比昨日同时刻 |
| 简历总数 | stats.resumes.total | 对比昨日 |
| 职位总数 | stats.jobs.total | 对比昨日 |
| 投递总数 | **新增** applications.total | 对比昨日 |
| 匹配记录 | stats.matches.total | 对比昨日 |
| 平均匹配分 | stats.matches.avg_score | 对比上周 |

卡片背景: 玻璃拟态 + 左侧 4px 霓虹色条 + hover 上浮 + 数值闪烁更新

### 4.3 主图表区 (3 列布局)

#### 模块 A: 用户增长趋势 (左上)
- **类型**: 双轴组合图 (柱状=每日新增, 折线=累计)
- **数据**: trend.user_growth (扩展为可切换 7/14/30 天)
- **增强**: 渐变柱体 + 平滑曲线 + areaStyle + hover 斑马线
- **交互**: 点击柱体下钻到当日新增用户列表抽屉

#### 模块 B: 核心指标仪表盘 (中上)
- **类型**: 3 个圆形 Gauge 横向排列
- **指标**: 简历解析成功率 / 职位活跃率 / 平均匹配分
- **样式**: 环形进度条 + 中心大数字 + 底部标签，颜色随阈值变化 (红<60 / 橙<80 / 绿≥80)

#### 模块 C: 实时操作日志流 (右上)
- **类型**: 滚动列表，每 3s 自动追加最新日志
- **数据**: adminApi.logs({ page:1, size:20 })
- **字段**: 时间 + 管理员 + 动作 + 目标 + IP
- **样式**: 新日志从顶部滑入，旧日志上移淡出，最多展示 8 条

#### 模块 D: 简历解析漏斗 (左中)
- **类型**: Funnel 漏斗图
- **阶段**: 上传 → 待解析 → 解析中 → 解析成功 (失败旁挂)
- **样式**: 渐变色块 + 转化率标注 + hover 高亮整条

#### 模块 E: 职位城市分布 TOP10 (中中)
- **类型**: 横向柱状 + 右侧迷你中国地图气泡
- **数据**: 按 work_city 聚合 Job 数量
- **样式**: 柱体渐变 + 城市名 + 数值标签，地图用散点标注

#### 模块 F: 热门技能词云 (右中)
- **类型**: WordCloud 词云
- **数据**: trend.hot_skills (扩展到 Top50)
- **样式**: 字号映射频次，颜色按技能类别分组，hover 显示具体数量

#### 模块 G: 投递状态漏斗 (左下)
- **类型**: Sankey 桑基图 或 Funnel
- **阶段**: 投递 → 已查看 → 面试邀约 → 录用
- **数据**: 按 JobApplication.status 聚合

#### 模块 H: 匹配分分布直方图 (中下)
- **类型**: Histogram 直方图 + 均值标线
- **数据**: 按 MatchRecord.total_score 分桶 (0-20/20-40/40-60/60-80/80-100)
- **增强**: 标注均值线 + 中位数线 + 优秀线(80)

#### 模块 I: 院校 TOP10 滚动榜 (右下)
- **类型**: 自动滚动排行榜 (每 5s 滚动一格)
- **数据**: 按 Resume.school 聚合 TOP10
- **样式**: 名次徽章(金银铜) + 院校名 + 人数 + 进度条

### 4.4 底部跑马灯 (32px)
- 滚动展示: 今日新增 {N} 用户 · {N} 简历 · {N} 职位 · {N} 投递 · 系统运行 {uptime} · 后端 {status}

---

## 五、技术实现方案

### 5.1 前端新增依赖
```bash
npm install echarts-wordcloud    # 词云
# echarts 已安装, 地图需额外引入:
# import 'echarts/map/js/china'  (或使用 echarts 5.x 的 registerMap)
```

### 5.2 后端新增接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/admin/dashboard/overview` | GET | 聚合返回 6 个 KPI + 环比数据，一次请求覆盖顶部栏 |
| `/admin/dashboard/applications` | GET | 投递统计: 总数 + 状态分布 + 近 14 天趋势 |
| `/admin/dashboard/match-dist` | GET | 匹配分直方图分桶统计 |
| `/admin/dashboard/city-dist` | GET | 职位城市分布 TOP10 |
| `/admin/dashboard/school-rank` | GET | 院校 TOP10 |
| `/admin/dashboard/education-dist` | GET | 学历分布 (备用雷达图) |
| `/admin/dashboard/realtime-logs` | GET | 最近 20 条操作日志 (供滚动流) |

#### 接口设计示例: `/admin/dashboard/overview`
```json
{
  "code": 0,
  "data": {
    "kpi": {
      "users": {"total": 10234, "delta": 56, "delta_pct": 0.55},
      "resumes": {"total": 8621, "delta": 42, "delta_pct": 0.49},
      "jobs": {"total": 1234, "delta": 8, "delta_pct": 0.65},
      "applications": {"total": 5421, "delta": 31, "delta_pct": 0.57},
      "matches": {"total": 3210, "delta": 25, "delta_pct": 0.78},
      "avg_score": {"total": 78.5, "delta": 1.2, "delta_pct": 1.55}
    },
    "gauges": {
      "parse_rate": 92.3,
      "job_active_rate": 68.5,
      "avg_match_score": 78.5
    },
    "uptime_hours": 720,
    "backend_status": "ok"
  }
}
```

#### 接口设计示例: `/admin/dashboard/match-dist`
```json
{
  "code": 0,
  "data": {
    "buckets": ["0-20", "20-40", "40-60", "60-80", "80-100"],
    "counts": [12, 45, 120, 890, 210],
    "avg_score": 78.5,
    "median_score": 76.0
  }
}
```

### 5.3 前端组件拆分

```
frontend/src/views/admin/
├── DashboardCenter.vue      # 大数据中心主页面 (容器)
├── components/
│   ├── DHeader.vue          # 顶部栏: 时钟 + 全屏 + 时间范围
│   ├── KpiRow.vue           # 6 张 KPI 卡片 (CountUp 动画)
│   ├── UserGrowthChart.vue  # 用户增长趋势
│   ├── CoreGauges.vue       # 3 个核心仪表盘
│   ├── LogStream.vue        # 实时日志滚动流
│   ├── ResumeFunnel.vue     # 简历解析漏斗
│   ├── CityDistChart.vue    # 城市分布 + 迷你地图
│   ├── SkillWordCloud.vue   # 技能词云
│   ├── ApplicationFunnel.vue# 投递状态漏斗
│   ├── MatchHistChart.vue   # 匹配分直方图
│   └── SchoolRank.vue       # 院校滚动榜
```

### 5.4 视觉规范

| 元素 | 规范 |
|------|------|
| 主背景 | `linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%)` |
| 面板背景 | `rgba(48,43,99,0.25)` + `backdrop-filter: blur(16px)` |
| 面板边框 | `1px solid rgba(167,139,250,0.2)` |
| 主色调 | `#a78bfa` (紫) / `#1677ff` (蓝) / `#52c41a` (绿) / `#ff6b35` (橙) |
| 文字主色 | `#e0e7ff` |
| 文字次色 | `#c4b5fd` |
| 数值字体 | `DIN Alternate` / `Helvetica Neue` 等宽 |
| 标题字体 | 14px / 600 / letter-spacing 1px |
| 卡片圆角 | 12px |
| 发光效果 | `box-shadow: 0 0 20px rgba(167,139,250,0.3)` |

### 5.5 动画与交互

| 效果 | 实现 |
|------|------|
| KPI 数值滚动 | `CountUp.js` 或自定义 `requestAnimationFrame` tween |
| 卡片入场 | `animation: fadeInUp 0.6s both` 错峰 delay |
| 图表加载 | 骨架屏 + 数据就绪后 `setOption` |
| 日志流入 | `transform: translateY` + `opacity` 过渡 |
| 排行榜滚动 | `setInterval` 每 5s `translateY(-44px)` 循环 |
| 跑马灯 | CSS `@keyframes marquee` 无限滚动 |
| 全屏 | `document.documentElement.requestFullscreen()` |
| 自动刷新 | 30s `setInterval` 重拉 overview + 日志 |

### 5.6 数据轮询策略

```typescript
// 30s 刷新 KPI + 日志 (轻量)
setInterval(() => { fetchOverview(); fetchLogs() }, 30000)
// 5min 刷新全量图表 (重量)
setInterval(() => { fetchAllCharts() }, 300000)
// 页面不可见时暂停 (节省请求)
document.addEventListener('visibilitychange', () => {
  if (document.hidden) clearTimers()
  else startTimers()
})
```

---

## 六、实施计划

### Phase 1: 后端接口扩展 (基础)
- [ ] `get_dashboard_overview()` 聚合 KPI + 环比 + gauges
- [ ] `get_application_stats()` 投递总数 + 状态分布
- [ ] `get_match_distribution()` 匹配分直方图分桶
- [ ] `get_city_distribution()` 城市聚合 TOP10
- [ ] `get_school_rank()` 院校聚合 TOP10
- [ ] `get_realtime_logs()` 最近 20 条日志

### Phase 2: 前端框架搭建
- [ ] 创建 `DashboardCenter.vue` 深色背景 + 网格布局
- [ ] 实现 `DHeader.vue` (时钟/全屏/刷新/时间范围)
- [ ] 实现 `KpiRow.vue` 6 卡片 + CountUp 动画
- [ ] 路由切换: `/admin/dashboard` → DashboardCenter

### Phase 3: 图表模块开发 (按优先级)
- [ ] P0: UserGrowthChart / CoreGauges / LogStream (复用现有数据)
- [ ] P1: ResumeFunnel / SkillWordCloud / MatchHistChart (依赖新接口)
- [ ] P2: CityDistChart / ApplicationFunnel / SchoolRank (依赖新接口)

### Phase 4: 交互与打磨
- [ ] 时间范围切换联动
- [ ] 自动刷新 + visibilitychange 优化
- [ ] 全屏模式样式适配
- [ ] 响应式断点 (1366 / 1920 / 2560)
- [ ] 底部跑马灯

### Phase 5: 性能与测试
- [ ] 图表按需 `dispose` 防内存泄漏
- [ ] 接口请求并发控制 (`Promise.all`)
- [ ] 错误兜底 + 骨架屏
- [ ] 大屏真机验证

---

## 七、预期效果

升级后管理后台将从「静态报表」进化为「实时指挥中心」:
- **一屏全览**: 6 KPI + 9 图表 + 日志流 + 跑马灯，信息密度提升 3 倍
- **实时感知**: 30s 刷新 + 日志滚动流入，运营状态秒级感知
- **视觉震撼**: 深色霓虹科技风，对标商业大屏产品
- **交互流畅**: 时间范围切换 / 全屏 / 下钻 / 自动刷新，操作闭环

适合毕业设计答辩演示与实际运营监控双重场景。
