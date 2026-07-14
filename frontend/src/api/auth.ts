/**
 * 认证相关 API
 */
import request from './request'

export interface LoginParams {
  account: string
  password: string
}

export interface RegisterParams {
  username: string
  password: string
  role: 'ROLE_SEEKER' | 'ROLE_EMPLOYER'
  phone: string
  email?: string
  // 个人用户
  nickname?: string
  real_name?: string
  gender?: string
  // 企业用户
  company_name?: string
  credit_code?: string
  contact_person?: string
}

export interface LoginResult {
  user_id: number
  username: string
  nickname: string
  role: string
  avatar_url?: string
  access_token: string
  refresh_token: string
  expires_in: number
}

export const authApi = {
  login: (data: LoginParams) => request.post('/auth/login', data),
  register: (data: RegisterParams) => request.post('/auth/register', data),
  logout: () => request.post('/auth/logout'),
  refresh: (refreshToken: string) => request.post('/auth/refresh', { refresh_token: refreshToken }),
  /** 获取当前用户信息 */
  me: () => request.get('/auth/me'),
  /** 修改个人信息 */
  updateProfile: (data: Record<string, any>) => request.put('/auth/profile', data),
  /** 修改密码 (需登录) */
  changePassword: (data: { old_password: string; new_password: string }) =>
    request.put('/auth/change-password', data),
  /** 忘记密码重置 (用户名+手机号验证) */
  forgotPassword: (data: { username: string; phone: string; new_password: string }) =>
    request.post('/auth/forgot-password', data),
}

/** 健康检查 (M1 验证用) */
export const healthApi = {
  check: () => request.get('/health'),
  detail: () => request.get('/health/detail'),
}
