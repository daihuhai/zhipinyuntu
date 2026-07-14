<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { vipApi } from '@/api/vip'

const loading = ref(false)
const revenue = ref<any>({})

const fetchRevenue = async () => {
  loading.value = true
  try {
    const res: any = await vipApi.getRevenue()
    revenue.value = res.data || {}
  } finally {
    loading.value = false
  }
}

const totalOrders = () => {
  if (!revenue.value.revenue_breakdown) return 0
  return revenue.value.revenue_breakdown.reduce((sum: number, item: any) => sum + item.count, 0)
}

onMounted(fetchRevenue)
</script>

<template>
  <div class="revenue-page" v-loading="loading">
    <h2 class="page-title">平台营收监控</h2>

    <!-- KPI 卡片 -->
    <el-row :gutter="20" class="kpi-row">
      <el-col :span="6">
        <el-card class="kpi-card kpi-green">
          <div class="kpi-label">总收入（元）</div>
          <div class="kpi-value">{{ revenue.total_revenue_yuan || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="kpi-card kpi-blue">
          <div class="kpi-label">近 30 天收入（元）</div>
          <div class="kpi-value">{{ revenue.recent_30_days_yuan || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="kpi-card kpi-gold">
          <div class="kpi-label">VIP 用户数</div>
          <div class="kpi-value">{{ revenue.vip_count || 0 }}</div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card class="kpi-card kpi-purple">
          <div class="kpi-label">总订单数</div>
          <div class="kpi-value">{{ totalOrders() }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 中间三个表格 -->
    <el-row :gutter="20" class="chart-row">
      <el-col :span="8">
        <el-card class="table-card">
          <template #header>
            <span class="card-header-title">营收分类明细</span>
          </template>
          <el-table :data="revenue.revenue_breakdown || []" stripe>
            <el-table-column prop="type_label" label="类型" />
            <el-table-column prop="amount_yuan" label="金额（元）" />
            <el-table-column prop="count" label="订单数" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="table-card">
          <template #header>
            <span class="card-header-title">VIP 用户角色分布</span>
          </template>
          <el-table :data="revenue.vip_role_breakdown || []" stripe>
            <el-table-column prop="role_label" label="角色" />
            <el-table-column prop="count" label="用户数" />
          </el-table>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card class="table-card">
          <template #header>
            <span class="card-header-title">VIP 套餐分布</span>
          </template>
          <el-table :data="revenue.vip_plan_breakdown || []" stripe>
            <el-table-column prop="plan_label" label="套餐类型" />
            <el-table-column prop="count" label="用户数" />
          </el-table>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近支付流水 -->
    <el-card class="table-card payment-table">
      <template #header>
        <span class="card-header-title">最近支付流水</span>
      </template>
      <el-table :data="revenue.recent_records || []" stripe>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户" />
        <el-table-column prop="type_label" label="类型" />
        <el-table-column label="金额（元）">
          <template #default="{ row }">
            <span class="amount-cell">{{ row.amount_yuan }}</span>
          </template>
        </el-table-column>
        <el-table-column label="支付方式">
          <template #default="{ row }">
            <el-tag v-if="row.pay_method === 'wechat'" type="success">微信</el-tag>
            <el-tag v-else-if="row.pay_method === 'alipay'" type="primary">支付宝</el-tag>
            <el-tag v-else>{{ row.pay_method }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="detail" label="详情" />
        <el-table-column prop="created_at" label="时间" width="180" />
      </el-table>
    </el-card>
  </div>
</template>

<style scoped>
.revenue-page {
  padding: 0;
}

.page-title {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 20px;
  color: var(--text-primary);
}

/* KPI 卡片 */
.kpi-row {
  margin-bottom: 20px;
}

.kpi-card {
  border-radius: 12px;
  color: #fff;
  border: none;
}

.kpi-green :deep(.el-card__body) {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
  border-radius: 12px;
}

.kpi-blue :deep(.el-card__body) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
}

.kpi-gold :deep(.el-card__body) {
  background: linear-gradient(135deg, #f7971e 0%, #ffd200 100%);
  border-radius: 12px;
}

.kpi-purple :deep(.el-card__body) {
  background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%);
  border-radius: 12px;
}

.kpi-label {
  font-size: 14px;
  opacity: 0.9;
  margin-bottom: 8px;
}

.kpi-value {
  font-size: 28px;
  font-weight: 700;
}

/* 表格卡片 */
.chart-row {
  margin-bottom: 20px;
}

.table-card {
  border-radius: 12px;
}

.table-card + .table-card {
  margin-top: 0;
}

.payment-table {
  border-radius: 12px;
}

.card-header-title {
  font-size: 16px;
  font-weight: 600;
}

.amount-cell {
  color: #f56c6c;
  font-weight: 700;
}

@media (max-width: 768px) {
  .kpi-row .el-col {
    margin-bottom: 12px;
  }
  .chart-row .el-col {
    margin-bottom: 12px;
  }
}
</style>