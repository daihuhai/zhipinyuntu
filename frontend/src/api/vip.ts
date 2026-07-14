/**
 * VIP 会员相关 API
 */
import request from './request'

export const vipApi = {
  /** 获取当前用户的配额信息 (VIP状态 + 免费配额 + 付费配额) */
  getQuota: () => request.get('/vip/quota'),
  /** 获取 VIP 套餐列表 */
  getPlans: () => request.get('/vip/plans'),
  /** VIP 充值 (套餐) */
  recharge: (data: { plan: string; pay_method: 'wechat' | 'alipay' }) =>
    request.post('/vip/recharge', data),
  /** 购买单次解析 (按数量) */
  buySingle: (data: { count: number; pay_method: 'wechat' | 'alipay' }) =>
    request.post('/vip/buy-single', data),
  /** 支付确认 (模拟支付完成回调) */
  payConfirm: (data: { order_id: string }) =>
    request.post('/vip/pay/confirm', data),
  /** 管理员营收 API */
  getRevenue: () => request.get('/admin/vip/revenue'),
}

/** 管理员 VIP 管理 API */
export const adminVipApi = {
  /** 管理员设置用户 VIP (开通/取消) */
  setVip: (data: { user_id: number; is_vip: boolean; duration_days?: number }) =>
    request.put('/admin/vip/set-vip', data),
  /** 管理员查看 VIP 用户列表 */
  vipUsers: (params: { page?: number; size?: number; vip_only?: number; keyword?: string }) =>
    request.get('/admin/vip/users', { params }),
}
