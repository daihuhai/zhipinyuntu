<!--
  VIP 中心 (充值页面)
  - 顶部: 当前配额状态 (VIP状态 / 免费配额 / 付费配额)
  - VIP 套餐选择 (月卡29 / 季卡79 / 年卡299)
  - 单次付费购买 (0.5元/次, 可选数量)
  - 支付方式 (微信 / 支付宝)
  - 支付对话框 (模拟二维码 + 确认支付)
  - VIP 权益对比表
-->
<template>
  <div class="vip-page">
    <!-- 顶部导航条 -->
    <div class="topbar">
      <el-button :icon="ArrowLeft" text @click="goBack">返回</el-button>
      <span class="topbar-title">VIP 会员中心</span>
      <span class="topbar-placeholder"></span>
    </div>

    <div class="vip-container">
      <!-- ===== 配额状态卡片 ===== -->
      <el-card shadow="never" class="quota-card" v-loading="quotaLoading">
        <div class="quota-banner" :class="{ 'is-vip': quota.is_vip }">
          <div class="banner-left">
            <div class="vip-badge-wrap">
              <div class="vip-badge" v-if="quota.is_vip">
                <el-icon :size="20"><GoldMedal /></el-icon>
                <span>VIP 会员</span>
              </div>
              <div class="vip-badge normal" v-else>
                <el-icon :size="20"><User /></el-icon>
                <span>普通用户</span>
              </div>
            </div>
            <div class="vip-expire" v-if="quota.is_vip">
              <el-tag v-if="quota.vip_plan_type" type="warning" size="small" effect="plain" style="margin-right: 8px">
                {{ planLabel(quota.vip_plan_type) }}
              </el-tag>
              <span>到期时间: {{ formatDate(quota.vip_expire_at) }}</span>
              <span v-if="quota.vip_remaining_days > 0" class="remain-days">
                (剩余 {{ quota.vip_remaining_days }} 天)
              </span>
            </div>
            <div class="vip-expire" v-else>开通 VIP, 畅享更多权益</div>
          </div>
          <div class="banner-right">
            <div class="quota-stat">
              <div class="stat-label">免费配额</div>
              <div class="stat-value">
                {{ quota.free_used ?? 0 }} / {{ quota.free_total ?? 0 }}
              </div>
              <el-progress
                :percentage="freePercent"
                :stroke-width="6"
                :show-text="false"
                color="#faad14"
                class="stat-bar"
              />
            </div>
            <div class="quota-stat">
              <div class="stat-label">付费配额余额</div>
              <div class="stat-value paid">{{ quota.paid_remaining ?? 0 }} <span class="unit">次</span></div>
              <div class="stat-hint">购买单次或充值 VIP 获得</div>
            </div>
          </div>
        </div>
      </el-card>

      <!-- ===== VIP 套餐选择 ===== -->
      <div class="section-title">
        <el-icon :size="18" color="#faad14"><GoldMedal /></el-icon>
        <span>VIP 套餐选择</span>
      </div>
      <div class="plan-list">
        <div
          v-for="plan in plans"
          :key="plan.id"
          class="plan-card"
          :class="{ active: selectedPlan === plan.id, recommend: plan.recommend }"
          @click="selectedPlan = plan.id"
        >
          <div v-if="plan.recommend" class="recommend-tag">推荐</div>
          <div class="plan-name">{{ plan.name }}</div>
          <div class="plan-price">
            <span class="currency">¥</span>
            <span class="amount">{{ plan.price }}</span>
            <span class="period">/{{ plan.period }}</span>
          </div>
          <div class="plan-original" v-if="plan.original">¥{{ plan.original }}</div>
          <div class="plan-desc">{{ plan.desc }}</div>
          <div class="plan-check" v-if="selectedPlan === plan.id">
            <el-icon :size="18"><Check /></el-icon>
          </div>
        </div>
      </div>

      <!-- ===== 单次付费购买 ===== -->
      <div class="section-title">
        <el-icon :size="18" color="#1677ff"><Coin /></el-icon>
        <span>单次付费购买</span>
        <span class="section-hint">¥0.5 / 次, 永久有效, 适合偶尔使用</span>
      </div>
      <el-card shadow="never" class="single-card">
        <div class="single-row">
          <div class="single-info">
            <span class="single-label">购买数量</span>
            <el-input-number v-model="singleCount" :min="1" :max="100" :step="1" />
            <span class="single-price">合计: <span class="price">¥{{ (singleCount * 0.5).toFixed(2) }}</span></span>
          </div>
          <el-button type="primary" plain :icon="ShoppingCart" @click="handleBuySingle">购买单次</el-button>
        </div>
      </el-card>

      <!-- ===== 支付方式 ===== -->
      <div class="section-title">
        <el-icon :size="18" color="#52c41a"><Wallet /></el-icon>
        <span>支付方式</span>
      </div>
      <div class="pay-methods">
        <div
          class="pay-method"
          :class="{ active: payMethod === 'wechat' }"
          @click="payMethod = 'wechat'"
        >
          <el-icon :size="28" color="#07c160"><ChatDotRound /></el-icon>
          <span>微信支付</span>
          <el-icon v-if="payMethod === 'wechat'" class="pay-check" color="#07c160"><CircleCheckFilled /></el-icon>
        </div>
        <div
          class="pay-method"
          :class="{ active: payMethod === 'alipay' }"
          @click="payMethod = 'alipay'"
        >
          <el-icon :size="28" color="#1677ff"><Money /></el-icon>
          <span>支付宝</span>
          <el-icon v-if="payMethod === 'alipay'" class="pay-check" color="#1677ff"><CircleCheckFilled /></el-icon>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="action-bar">
        <div class="action-info">
          <span v-if="selectedPlan">
            {{ quota.is_vip ? '续费后到期时间: ' + renewExpireDate : '已选: ' + currentPlanName }}
          </span>
          <span v-else class="action-hint">请选择上方套餐或单次购买</span>
        </div>
        <el-button
          type="warning"
          size="large"
          :icon="GoldMedal"
          :disabled="!selectedPlan"
          :loading="paying"
          @click="handleRecharge"
        >
          {{ quota.is_vip ? '续费 VIP' : '立即开通 VIP' }}
        </el-button>
      </div>

      <!-- ===== VIP 权益对比表 ===== -->
      <div class="section-title">
        <el-icon :size="18" color="#faad14"><Trophy /></el-icon>
        <span>VIP 权益对比</span>
      </div>
      <el-card shadow="never" class="benefit-card">
        <el-table :data="benefitTable" border stripe>
          <el-table-column prop="feature" label="权益项" width="180" />
          <el-table-column label="普通用户" align="center">
            <template #default="{ row }">
              <el-icon v-if="row.normal" color="#52c41a" :size="16"><Check /></el-icon>
              <span v-else class="cross">—</span>
              <span v-if="row.normalText" class="benefit-text">{{ row.normalText }}</span>
            </template>
          </el-table-column>
          <el-table-column label="VIP 会员" align="center">
            <template #default="{ row }">
              <el-icon v-if="row.vip" color="#faad14" :size="16"><Check /></el-icon>
              <span v-else class="cross">—</span>
              <span v-if="row.vipText" class="benefit-text vip-text">{{ row.vipText }}</span>
            </template>
          </el-table-column>
        </el-table>
      </el-card>
    </div>

    <!-- ===== 支付对话框 ===== -->
    <el-dialog v-model="payDialogVisible" title="扫码支付" width="400px" :close-on-click-modal="false">
      <div class="pay-dialog">
        <div class="pay-amount">
          <span class="pay-label">支付金额</span>
          <span class="pay-money">¥{{ payAmount.toFixed(2) }}</span>
        </div>
        <div class="pay-method-tag">
          <el-icon :size="16" :color="payMethod === 'wechat' ? '#07c160' : '#1677ff'">
            <ChatDotRound v-if="payMethod === 'wechat'" /><Money v-else />
          </el-icon>
          <span>{{ payMethod === 'wechat' ? '微信支付' : '支付宝' }}</span>
        </div>
        <!-- 模拟二维码 -->
        <div class="qrcode-area">
          <div class="qrcode-mock">
            <div class="qr-grid">
              <div v-for="i in 64" :key="i" class="qr-cell" :class="{ on: qrPattern[i - 1] }"></div>
            </div>
            <div class="qr-center">
              <el-icon :size="24" :color="payMethod === 'wechat' ? '#07c160' : '#1677ff'">
                <ChatDotRound v-if="payMethod === 'wechat'" /><Money v-else />
              </el-icon>
            </div>
          </div>
          <div class="qr-hint">请使用{{ payMethod === 'wechat' ? '微信' : '支付宝' }}扫码支付</div>
        </div>
        <div class="pay-tips">
          <el-icon color="#faad14"><InfoFilled /></el-icon>
          <span>本平台为模拟支付, 点击下方按钮即可完成支付</span>
        </div>
      </div>
      <template #footer>
        <el-button @click="payDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="confirming" @click="handlePayConfirm">
          我已支付完成
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  ArrowLeft, GoldMedal, User, Check, Coin, ShoppingCart, Wallet,
  ChatDotRound, Money, CircleCheckFilled, Trophy, InfoFilled,
} from '@element-plus/icons-vue'
import { vipApi } from '@/api/vip'

const router = useRouter()

// ===== 配额信息 =====
const quotaLoading = ref(false)
const quota = ref<any>({})

const freePercent = computed(() => {
  const total = quota.value.free_total ?? 0
  const used = quota.value.free_used ?? 0
  if (!total) return 0
  return Math.min(100, Math.round((used / total) * 100))
})

const fetchQuota = async () => {
  quotaLoading.value = true
  try {
    const res: any = await vipApi.getQuota()
    quota.value = res.data || {}
  } catch {
    // 错误已由拦截器提示
  } finally {
    quotaLoading.value = false
  }
}

// ===== 套餐定义 =====
const plans = [
  { id: 'monthly', name: '月卡', price: 29, original: 39, period: '月', desc: '适合短期求职', recommend: false },
  { id: 'quarterly', name: '季卡', price: 79, original: 99, period: '季', desc: '求职高峰期推荐', recommend: true },
  { id: 'yearly', name: '年卡', price: 299, original: 399, period: '年', desc: '全年畅享最划算', recommend: false },
]
const selectedPlan = ref('quarterly')
const currentPlanName = computed(() => plans.find(p => p.id === selectedPlan.value)?.name || '')

// 续费后到期时间预览
const renewExpireDate = computed(() => {
  if (!quota.value.is_vip || !quota.value.vip_expire_at) return ''
  const plan = plans.find(p => p.id === selectedPlan.value)
  if (!plan) return ''
  const days = plan.id === 'monthly' ? 30 : plan.id === 'quarterly' ? 90 : 365
  const current = new Date(quota.value.vip_expire_at)
  current.setDate(current.getDate() + days)
  return current.toLocaleDateString('zh-CN')
})

// ===== 单次购买 =====
const singleCount = ref(1)

// ===== 支付方式 =====
const payMethod = ref<'wechat' | 'alipay'>('wechat')

// ===== 支付流程 =====
const payDialogVisible = ref(false)
const paying = ref(false)
const confirming = ref(false)
const payAmount = ref(0)
const currentOrderId = ref('')
const currentMode = ref<'plan' | 'single'>('plan')

// 生成模拟二维码图案 (固定种子, 视觉效果)
const qrPattern = Array.from({ length: 64 }, (_, i) => {
  return ((i * 7 + 13) % 5 < 2) || ((i * 3 + 5) % 7 === 0)
})

const handleRecharge = async () => {
  if (!selectedPlan.value) {
    ElMessage.warning('请先选择套餐')
    return
  }
  paying.value = true
  try {
    const plan = plans.find(p => p.id === selectedPlan.value)!
    const res: any = await vipApi.recharge({ plan: plan.id, pay_method: payMethod.value })
    currentOrderId.value = res.data?.order_id || ''
    payAmount.value = plan.price
    currentMode.value = 'plan'
    payDialogVisible.value = true
  } catch {
    // 错误已由拦截器提示
  } finally {
    paying.value = false
  }
}

const handleBuySingle = async () => {
  paying.value = true
  try {
    const res: any = await vipApi.buySingle({ count: singleCount.value, pay_method: payMethod.value })
    currentOrderId.value = res.data?.order_id || ''
    payAmount.value = singleCount.value * 0.5
    currentMode.value = 'single'
    payDialogVisible.value = true
  } catch {
    // 错误已由拦截器提示
  } finally {
    paying.value = false
  }
}

const handlePayConfirm = async () => {
  if (!currentOrderId.value) {
    ElMessage.warning('订单信息缺失, 请重试')
    return
  }
  confirming.value = true
  try {
    await vipApi.payConfirm({ order_id: currentOrderId.value })
    ElMessage.success(currentMode.value === 'plan' ? 'VIP 开通成功!' : '购买成功!')
    payDialogVisible.value = false
    // 刷新配额
    fetchQuota()
  } catch {
    // 错误已由拦截器提示
  } finally {
    confirming.value = false
  }
}

// ===== 权益对比表 =====
const benefitTable = [
  { feature: '简历解析', normal: true, normalText: '3次/天', vip: true, vipText: '无限次' },
  { feature: '灵犀智能匹配', normal: true, normalText: '5次/天', vip: true, vipText: '无限次' },
  { feature: '简历能力图谱', normal: true, vip: true },
  { feature: '灵犀简历优化建议', normal: false, vip: true },
  { feature: '职位优先推荐', normal: false, vip: true },
  { feature: '专属客服通道', normal: false, vip: true },
  { feature: '数据导出', normal: false, vip: true },
  { feature: '广告免打扰', normal: false, vip: true },
]

// ===== 工具函数 =====
const planLabel = (type?: string) => {
  const map: Record<string, string> = {
    monthly: '月卡', quarterly: '季卡', yearly: '年卡', admin: '管理员开通',
  }
  return map[type || ''] || type || '-'
}

const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleDateString('zh-CN') : '-'

const goBack = () => {
  const userInfoStr = localStorage.getItem('user_info')
  let fallback = '/login'
  if (userInfoStr) {
    try {
      const info = JSON.parse(userInfoStr)
      const map: Record<string, string> = {
        ROLE_SEEKER: '/seeker/dashboard',
        ROLE_EMPLOYER: '/employer/dashboard',
        ROLE_ADMIN: '/admin/dashboard',
      }
      fallback = map[info.role] || fallback
    } catch {
      // 忽略
    }
  }
  router.push(fallback)
}

onMounted(fetchQuota)
</script>

<style scoped>
.vip-page {
  min-height: 100vh; background: var(--bg-page);
}

/* ===== 顶部导航 ===== */
.topbar {
  height: 56px; background: #fff; display: flex; align-items: center;
  justify-content: space-between; padding: 0 20px;
  border-bottom: 1px solid var(--border-color);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04); position: sticky; top: 0; z-index: 10;
}
.topbar-title { font-size: 18px; font-weight: 700; color: var(--text-primary); }
.topbar-placeholder { width: 60px; }

.vip-container {
  max-width: 960px; margin: 0 auto; padding: 12px 20px 80px;
}

/* ===== 配额状态卡片 ===== */
.quota-card { border-radius: 14px; margin-bottom: 28px; overflow: hidden; }
.quota-card :deep(.el-card__body) { padding: 0; }
.quota-banner {
  display: flex; justify-content: space-between; align-items: center;
  padding: 28px 32px;
  background: linear-gradient(135deg, #e6f4ff 0%, #f0f5ff 100%);
  transition: background 0.3s;
}
.quota-banner.is-vip {
  background: linear-gradient(135deg, #fff7e6 0%, #fffbe6 50%, #fff1e6 100%);
}
.banner-left { display: flex; flex-direction: column; gap: 10px; }
.vip-badge-wrap { display: flex; align-items: center; }
.vip-badge {
  display: flex; align-items: center; gap: 8px;
  padding: 6px 16px; border-radius: 20px; font-size: 16px; font-weight: 700;
  background: linear-gradient(135deg, #faad14 0%, #ffc53d 100%);
  color: #fff; box-shadow: 0 4px 12px rgba(250, 173, 20, 0.35);
}
.vip-badge.normal {
  background: linear-gradient(135deg, #bfbfbf 0%, #d9d9d9 100%);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.vip-expire { font-size: 13px; color: var(--text-secondary); }
.remain-days { font-size: 12px; color: #faad14; font-weight: 500; margin-left: 4px; }
.banner-right { display: flex; gap: 40px; }
.quota-stat { display: flex; flex-direction: column; gap: 6px; min-width: 140px; }
.stat-label { font-size: 13px; color: var(--text-secondary); }
.stat-value { font-size: 22px; font-weight: 700; color: var(--text-primary); }
.stat-value.paid { color: #faad14; }
.stat-value .unit { font-size: 13px; font-weight: 400; color: var(--text-secondary); }
.stat-bar { width: 140px; }
.stat-hint { font-size: 12px; color: var(--text-secondary); }

/* ===== 区块标题 ===== */
.section-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 16px; font-weight: 700; color: var(--text-primary);
  margin-bottom: 14px; margin-top: 8px;
}
.section-hint { font-size: 13px; font-weight: 400; color: var(--text-secondary); }

/* ===== 套餐卡片 ===== */
.plan-list {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 28px;
}
.plan-card {
  position: relative; padding: 24px 20px; border-radius: 14px;
  border: 2px solid #f0f0f0; background: #fff; cursor: pointer;
  transition: all 0.3s; display: flex; flex-direction: column; gap: 8px;
}
.plan-card:hover {
  border-color: #faad14; box-shadow: 0 6px 16px rgba(250, 173, 20, 0.15);
  transform: translateY(-2px);
}
.plan-card.active {
  border-color: #faad14; background: linear-gradient(135deg, #fffbe6 0%, #fff7e6 100%);
  box-shadow: 0 8px 24px rgba(250, 173, 20, 0.25);
}
.plan-card.recommend::before {
  content: ''; position: absolute; inset: 0; border-radius: 14px;
  border: 2px solid transparent; pointer-events: none;
}
.recommend-tag {
  position: absolute; top: -10px; right: 16px;
  padding: 2px 12px; border-radius: 10px; font-size: 12px; font-weight: 600;
  background: linear-gradient(135deg, #ff4d4f 0%, #ff7875 100%); color: #fff;
  box-shadow: 0 2px 6px rgba(255, 77, 79, 0.4);
}
.plan-name { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.plan-price { display: flex; align-items: baseline; gap: 2px; color: #faad14; }
.plan-price .currency { font-size: 14px; }
.plan-price .amount { font-size: 32px; font-weight: 700; }
.plan-price .period { font-size: 13px; color: var(--text-secondary); }
.plan-original { font-size: 13px; color: #bfbfbf; text-decoration: line-through; }
.plan-desc { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.plan-check {
  position: absolute; top: 12px; right: 12px;
  width: 24px; height: 24px; border-radius: 50%;
  background: #faad14; color: #fff;
  display: flex; align-items: center; justify-content: center;
}

/* ===== 单次购买 ===== */
.single-card { border-radius: 12px; margin-bottom: 28px; }
.single-row { display: flex; align-items: center; justify-content: space-between; }
.single-info { display: flex; align-items: center; gap: 16px; }
.single-label { font-size: 14px; color: var(--text-primary); font-weight: 500; }
.single-price { font-size: 14px; color: var(--text-secondary); }
.single-price .price { font-size: 18px; font-weight: 700; color: #faad14; }

/* ===== 支付方式 ===== */
.pay-methods { display: flex; gap: 16px; margin-bottom: 28px; }
.pay-method {
  position: relative; display: flex; align-items: center; gap: 10px;
  padding: 16px 24px; border-radius: 10px; border: 2px solid #f0f0f0;
  background: #fff; cursor: pointer; transition: all 0.2s; min-width: 160px;
}
.pay-method:hover { border-color: #1677ff; }
.pay-method.active { border-color: #1677ff; background: #f0f5ff; }
.pay-method span { font-size: 14px; font-weight: 500; }
.pay-check { position: absolute; top: 8px; right: 8px; }

/* ===== 底部操作栏 ===== */
.action-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 24px; background: #fff; border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06); margin-bottom: 28px;
}
.action-info { font-size: 14px; color: var(--text-primary); }
.action-hint { color: var(--text-secondary); }

/* ===== 权益对比表 ===== */
.benefit-card { border-radius: 12px; }
.benefit-text { margin-left: 4px; font-size: 13px; color: var(--text-secondary); }
.vip-text { color: #faad14; font-weight: 500; }
.cross { color: #d9d9d9; }

/* ===== 支付对话框 ===== */
.pay-dialog { display: flex; flex-direction: column; align-items: center; padding: 12px 0; }
.pay-amount {
  display: flex; flex-direction: column; align-items: center; margin-bottom: 12px;
}
.pay-label { font-size: 13px; color: var(--text-secondary); }
.pay-money { font-size: 32px; font-weight: 700; color: #ff4d4f; }
.pay-method-tag {
  display: flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 12px; background: #f5f7fa;
  font-size: 13px; color: var(--text-secondary); margin-bottom: 20px;
}
.qrcode-area { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.qrcode-mock {
  position: relative; width: 180px; height: 180px;
  padding: 12px; background: #fff; border: 1px solid #f0f0f0; border-radius: 8px;
}
.qr-grid {
  display: grid; grid-template-columns: repeat(8, 1fr); gap: 2px;
  width: 100%; height: 100%;
}
.qr-cell { background: transparent; border-radius: 1px; }
.qr-cell.on { background: #333; }
.qr-center {
  position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 36px; height: 36px; border-radius: 8px; background: #fff;
  display: flex; align-items: center; justify-content: center;
  border: 2px solid #fff; box-shadow: 0 0 0 2px rgba(0, 0, 0, 0.05);
}
.qr-hint { font-size: 13px; color: var(--text-secondary); }
.pay-tips {
  display: flex; align-items: center; gap: 6px; margin-top: 16px;
  padding: 8px 14px; background: #fffbe6; border-radius: 6px;
  font-size: 12px; color: #8c6e2a;
}

/* ===== 响应式 ===== */
@media (max-width: 768px) {
  .quota-banner { flex-direction: column; gap: 20px; align-items: flex-start; }
  .banner-right { width: 100%; gap: 20px; }
  .plan-list { grid-template-columns: 1fr; }
  .pay-methods { flex-direction: column; }
  .single-row { flex-direction: column; gap: 12px; align-items: flex-start; }
  .action-bar { flex-direction: column; gap: 12px; }
}
</style>
