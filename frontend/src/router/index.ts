/**
 * 路由配置 - 三角色分流 (个人/企业/管理后台)
 */
import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/auth/Login.vue'),
    meta: { title: '登录', public: true },
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/auth/Register.vue'),
    meta: { title: '注册', public: true },
  },
  // 个人用户工作台
  {
    path: '/seeker',
    component: () => import('@/layouts/SeekerLayout.vue'),
    redirect: '/seeker/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'SeekerDashboard',
        component: () => import('@/views/seeker/Dashboard.vue'),
        meta: { title: '个人仪表盘', role: 'ROLE_SEEKER' },
      },
      {
        path: 'resume/upload',
        name: 'SeekerResumeUpload',
        component: () => import('@/views/seeker/ResumeUpload.vue'),
        meta: { title: '上传简历', role: 'ROLE_SEEKER' },
      },
      {
        path: 'resume/list',
        name: 'SeekerResumeList',
        component: () => import('@/views/seeker/ResumeList.vue'),
        meta: { title: '我的简历', role: 'ROLE_SEEKER' },
      },
      {
        path: 'resume/:id/edit',
        name: 'SeekerResumeEdit',
        component: () => import('@/views/seeker/ResumeEdit.vue'),
        meta: { title: '编辑简历', role: 'ROLE_SEEKER' },
      },
      {
        path: 'jobs',
        name: 'SeekerJobs',
        component: () => import('@/views/seeker/Jobs.vue'),
        meta: { title: '职位广场', role: 'ROLE_SEEKER' },
      },
      {
        path: 'jobs/:id',
        name: 'SeekerJobDetail',
        component: () => import('@/views/seeker/JobDetail.vue'),
        meta: { title: '职位详情', role: 'ROLE_SEEKER' },
      },
      {
        path: 'recommend',
        name: 'SeekerRecommend',
        component: () => import('@/views/seeker/Recommend.vue'),
        meta: { title: '职位推荐', role: 'ROLE_SEEKER' },
      },
      {
        path: 'favorites',
        name: 'SeekerFavorites',
        component: () => import('@/views/seeker/Favorites.vue'),
        meta: { title: '我的收藏', icon: 'Star', role: 'ROLE_SEEKER' },
      },
      {
        path: 'graph',
        name: 'SeekerGraph',
        component: () => import('@/views/seeker/ResumeGraph.vue'),
        meta: { title: '能力图谱', role: 'ROLE_SEEKER' },
      },
      {
        path: 'applications',
        name: 'SeekerApplications',
        component: () => import('@/views/seeker/Applications.vue'),
        meta: { title: '投递记录', role: 'ROLE_SEEKER' },
      },
      {
        path: 'messages',
        name: 'SeekerMessages',
        component: () => import('@/views/Message.vue'),
        meta: { title: '消息', role: 'ROLE_SEEKER' },
      },
      {
        path: 'profile',
        name: 'SeekerProfile',
        component: () => import('@/views/seeker/Profile.vue'),
        meta: { title: '个人设置', role: 'ROLE_SEEKER' },
      },
    ],
  },
  // 企业用户工作台
  {
    path: '/employer',
    component: () => import('@/layouts/EmployerLayout.vue'),
    redirect: '/employer/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'EmployerDashboard',
        component: () => import('@/views/employer/Dashboard.vue'),
        meta: { title: '企业仪表盘', role: 'ROLE_EMPLOYER' },
      },
      {
        path: 'job/create',
        name: 'EmployerJobCreate',
        component: () => import('@/views/employer/JobCreate.vue'),
        meta: { title: '发布职位', role: 'ROLE_EMPLOYER' },
      },
      {
        path: 'job/list',
        name: 'EmployerJobList',
        component: () => import('@/views/employer/JobList.vue'),
        meta: { title: '职位列表', role: 'ROLE_EMPLOYER' },
      },
      {
        path: 'candidates',
        name: 'EmployerCandidates',
        component: () => import('@/views/employer/Candidates.vue'),
        meta: { title: '候选人推荐', role: 'ROLE_EMPLOYER' },
      },
      {
        path: 'applications',
        name: 'EmployerApplications',
        component: () => import('@/views/employer/Applications.vue'),
        meta: { title: '投递管理', role: 'ROLE_EMPLOYER' },
      },
      {
        path: 'messages',
        name: 'EmployerMessages',
        component: () => import('@/views/Message.vue'),
        meta: { title: '消息', role: 'ROLE_EMPLOYER' },
      },
      {
        path: 'profile',
        name: 'EmployerProfile',
        component: () => import('@/views/employer/Profile.vue'),
        meta: { title: '企业设置', role: 'ROLE_EMPLOYER' },
      },
    ],
  },
  // 管理后台
  {
    path: '/admin',
    component: () => import('@/layouts/AdminLayout.vue'),
    redirect: '/admin/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'AdminDashboard',
        component: () => import('@/views/admin/DashboardCenter.vue'),
        meta: { title: '数据指挥中心', role: 'ROLE_ADMIN' },
      },
      {
        path: 'users',
        name: 'AdminUsers',
        component: () => import('@/views/admin/Users.vue'),
        meta: { title: '用户管理', role: 'ROLE_ADMIN' },
      },
      {
        path: 'resumes',
        name: 'AdminResumes',
        component: () => import('@/views/admin/Resumes.vue'),
        meta: { title: '简历管理', role: 'ROLE_ADMIN' },
      },
      {
        path: 'jobs',
        name: 'AdminJobs',
        component: () => import('@/views/admin/Jobs.vue'),
        meta: { title: '职位管理', role: 'ROLE_ADMIN' },
      },
      {
        path: 'logs',
        name: 'AdminLogs',
        component: () => import('@/views/admin/Logs.vue'),
        meta: { title: '操作日志', role: 'ROLE_ADMIN' },
      },
    ],
  },
  // 404
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { title: '页面不存在', public: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// 路由守卫: 鉴权 + 角色校验
router.beforeEach((to, _from, next) => {
  // 设置页面标题
  document.title = `${to.meta.title || ''} - 智聘云图`

  // 公开页面直接放行
  if (to.meta.public) {
    return next()
  }

  const token = localStorage.getItem('access_token')
  if (!token) {
    return next('/login')
  }

  // 角色校验: 根据路径前缀与用户角色匹配
  const userInfoStr = localStorage.getItem('user_info')
  if (userInfoStr) {
    try {
      const info = JSON.parse(userInfoStr)
      const role: string = info.role || ''
      const pathPrefix = '/' + (to.path.split('/')[1] || '')
      const rolePrefixMap: Record<string, string> = {
        ROLE_SEEKER: '/seeker',
        ROLE_EMPLOYER: '/employer',
        ROLE_ADMIN: '/admin',
      }
      const expected = rolePrefixMap[role]
      // 若角色对应的前缀与访问路径不符, 跳转到自己的工作台
      if (expected && pathPrefix !== expected && !pathPrefix.startsWith('/login')) {
        return next(expected + '/dashboard')
      }
    } catch {
      // 解析失败忽略
    }
  }

  next()
})

export default router
