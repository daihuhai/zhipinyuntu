/**
 * 管理后台 API
 */
import request from './request'

export const adminApi = {
  /** 仪表盘统计 */
  dashboard: () => request.get('/admin/dashboard'),
  /** 仪表盘趋势 (图表, 支持日期筛选) */
  dashboardTrend: (params?: { start_date?: string; end_date?: string }) =>
    request.get('/admin/dashboard/trend', { params }),
  /** 大数据中心总览 (KPI+Gauge) */
  dashboardOverview: () => request.get('/admin/dashboard/overview'),
  /** 投递统计 */
  applicationStats: () => request.get('/admin/dashboard/applications'),
  /** 匹配分直方图 */
  matchDistribution: () => request.get('/admin/dashboard/match-dist'),
  /** 职位城市分布 TOP10 */
  cityDistribution: () => request.get('/admin/dashboard/city-dist'),
  /** 院校 TOP10 */
  schoolRank: () => request.get('/admin/dashboard/school-rank'),
  /** 实时操作日志 */
  realtimeLogs: (limit = 20) => request.get('/admin/dashboard/realtime-logs', { params: { limit } }),
  /** 用户列表 */
  users: (params: { page?: number; size?: number; role?: string; status?: number; keyword?: string; username?: string; phone?: string }) =>
    request.get('/admin/users', { params }),
  /** 用户详情 */
  userDetail: (id: number) => request.get(`/admin/users/${id}`),
  /** 用户详情 (含关联统计) */
  userDetailStats: (id: number) => request.get(`/admin/users/${id}/detail`),
  /** 修改用户状态 */
  updateUserStatus: (id: number, status: number) =>
    request.put(`/admin/users/${id}/status`, { status }),
  /** 批量修改用户状态 */
  batchUpdateUserStatus: (ids: number[], status: number) =>
    request.post('/admin/users/batch-status', { ids, status }),
  /** 修改用户角色 */
  updateUserRole: (id: number, role: string) =>
    request.put(`/admin/users/${id}/role`, { role }),
  /** 删除用户 */
  deleteUser: (id: number) => request.delete(`/admin/users/${id}`),
  /** 简历列表 */
  resumes: (params: { page?: number; size?: number; keyword?: string; parse_status?: number }) =>
    request.get('/admin/resumes', { params }),
  /** 删除简历 */
  deleteResume: (id: number) => request.delete(`/admin/resumes/${id}`),
  /** 批量删除简历 */
  batchDeleteResumes: (ids: number[]) => request.post('/admin/resumes/batch-delete', { ids }),
  /** 职位列表 */
  jobs: (params: { page?: number; size?: number; keyword?: string; status?: number }) =>
    request.get('/admin/jobs', { params }),
  /** 修改职位状态 */
  updateJobStatus: (id: number, status: number) =>
    request.put(`/admin/jobs/${id}/status`, { status }),
  /** 批量修改职位状态 */
  batchUpdateJobStatus: (ids: number[], status: number) =>
    request.post('/admin/jobs/batch-status', { ids, status }),
  /** 删除职位 */
  deleteJob: (id: number) => request.delete(`/admin/jobs/${id}`),
  /** 操作日志 */
  logs: (params: { page?: number; size?: number; admin_id?: number; action?: string }) =>
    request.get('/admin/logs', { params }),
  /** 导出数据为 CSV (blob), module: users | resumes | jobs */
  exportData: (module: string) =>
    request.get(`/admin/export/${module}`, { responseType: 'blob' }),
}
