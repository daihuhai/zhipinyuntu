/**
 * useRealtime - WebSocket 实时消息推送封装
 * - 登录后建立长连接 (携带 token), 断线自动重连 (指数退避)
 * - 心跳 ping 保活
 * - 模块级单例, 避免多组件重复建连
 */
import { ref } from 'vue'

let ws: WebSocket | null = null
let currentToken = ''
let reconnectTimer: ReturnType<typeof setTimeout> | null = null
let heartbeatTimer: ReturnType<typeof setInterval> | null = null
let reconnectAttempts = 0
const listeners = new Set<(data: any) => void>()

export function useRealtime() {
  const connected = ref(false)

  function connect(token: string) {
    if (!token) return
    currentToken = token
    // 已连接或正在连接则跳过
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) return

    const proto = location.protocol === 'https:' ? 'wss' : 'ws'
    try {
      ws = new WebSocket(`${proto}://${location.host}/api/v1/ws/messages?token=${encodeURIComponent(token)}`)
    } catch {
      scheduleReconnect()
      return
    }

    ws.onopen = () => {
      connected.value = true
      reconnectAttempts = 0
      startHeartbeat()
    }
    ws.onmessage = (ev) => {
      try {
        const data = JSON.parse(ev.data)
        listeners.forEach((fn) => fn(data))
      } catch { /* 忽略非 JSON 消息 */ }
    }
    ws.onclose = () => {
      connected.value = false
      stopHeartbeat()
      scheduleReconnect()
    }
    ws.onerror = () => {
      try { ws?.close() } catch { /* noop */ }
    }
  }

  function scheduleReconnect() {
    if (reconnectTimer) return
    const delay = Math.min(1000 * 2 ** reconnectAttempts, 15000)
    reconnectAttempts += 1
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null
      if (currentToken) connect(currentToken)
    }, delay)
  }

  function startHeartbeat() {
    stopHeartbeat()
    heartbeatTimer = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) ws.send('ping')
    }, 25000)
  }

  function stopHeartbeat() {
    if (heartbeatTimer) { clearInterval(heartbeatTimer); heartbeatTimer = null }
  }

  /** 注册消息回调, 返回取消订阅函数 */
  function onMessage(fn: (data: any) => void) {
    listeners.add(fn)
    return () => { listeners.delete(fn) }
  }

  function disconnect() {
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null }
    stopHeartbeat()
    if (ws) { try { ws.close() } catch { /* noop */ } ws = null }
    connected.value = false
  }

  return { connected, connect, onMessage, disconnect }
}