/**
 * 管理后台 API
 */
import request from './request'

export const adminApi = {
  /** 仪表盘统计 */
  dashboard: () => request.get('/admin/dashboard'),
  /** 用户列表 */
  users: (params: { page?: number; size?: number; role?: string; status?: number; keyword?: string }) =>
    request.get('/admin/users', { params }),
  /** 用户详情 */
  userDetail: (id: number) => request.get(`/admin/users/${id}`),
  /** 修改用户状态 */
  updateUserStatus: (id: number, status: number) =>
    request.put(`/admin/users/${id}/status`, { status }),
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
  /** 职位列表 */
  jobs: (params: { page?: number; size?: number; keyword?: string; status?: number }) =>
    request.get('/admin/jobs', { params }),
  /** 修改职位状态 */
  updateJobStatus: (id: number, status: number) =>
    request.put(`/admin/jobs/${id}/status`, { status }),
  /** 删除职位 */
  deleteJob: (id: number) => request.delete(`/admin/jobs/${id}`),
  /** 操作日志 */
  logs: (params: { page?: number; size?: number; admin_id?: number; action?: string }) =>
    request.get('/admin/logs', { params }),
}
