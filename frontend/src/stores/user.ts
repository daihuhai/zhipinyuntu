/**
 * 用户状态管理 (Pinia)
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface UserInfo {
  user_id: number
  username: string
  nickname: string
  role: 'ROLE_SEEKER' | 'ROLE_EMPLOYER' | 'ROLE_ADMIN'
  avatar_url?: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('access_token') || '')
  const userInfo = ref<UserInfo | null>(
    JSON.parse(localStorage.getItem('user_info') || 'null')
  )

  const setToken = (t: string) => {
    token.value = t
    localStorage.setItem('access_token', t)
  }

  const setUserInfo = (info: UserInfo) => {
    userInfo.value = info
    localStorage.setItem('user_info', JSON.stringify(info))
  }

  const logout = () => {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('user_info')
  }

  return {
    token,
    userInfo,
    setToken,
    setUserInfo,
    logout,
  }
})
