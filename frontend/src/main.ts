import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

import App from './App.vue'
import router from './router'
import './style.css'

const app = createApp(App)

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

// ===== 全局错误边界: 捕获未处理异常, 避免白屏 =====
app.config.errorHandler = (err, _instance, info) => {
  console.error('Vue 错误:', err, info)
  ElMessage.error('页面渲染异常, 请刷新重试')
}

// 捕获未处理的 Promise 异常
window.addEventListener('unhandledrejection', (event) => {
  console.error('未处理的 Promise 异常:', event.reason)
  ElMessage.error('请求异常, 请稍后重试')
})

app.use(createPinia())
app.use(router)
app.use(ElementPlus, { locale: zhCn })

app.mount('#app')

// ===== Web Vitals 性能监控 =====
if (import.meta.env.PROD) {
  // 使用 web-vitals 库采集核心指标
  import('web-vitals').then(({ onCLS, onFCP, onLCP, onTTFB }) => {
    const reportMetric = (metric: { name: string; value: number; rating: string }) => {
      // 发送到后端 /api/v1/metrics/web-vitals
      try {
        const body = JSON.stringify({
          name: metric.name,
          value: Math.round(metric.value),
          rating: metric.rating,
          page: window.location.pathname,
        })
        if (navigator.sendBeacon) {
          navigator.sendBeacon('/api/v1/metrics/web-vitals', body)
        } else {
          fetch('/api/v1/metrics/web-vitals', {
            method: 'POST',
            body,
            headers: { 'Content-Type': 'application/json' },
            keepalive: true,
          })
        }
      } catch {}
    }
    onCLS(reportMetric)
    onFCP(reportMetric)
    onLCP(reportMetric)
    onTTFB(reportMetric)
  })
}
