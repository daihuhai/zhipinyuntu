<!--
  我的收藏 (求职者)
  - 展示当前用户收藏的职位列表
  - 点击卡片跳转职位详情, 可取消收藏
-->
<template>
  <div class="favorites-page">
    <el-card shadow="never" class="header-card">
      <div class="header-row">
        <div class="header-title">
          <el-icon class="title-icon"><Star /></el-icon>
          <span>我的收藏</span>
          <el-tag type="info" size="small" round>共 {{ list.length }} 个</el-tag>
        </div>
        <el-button :icon="Refresh" @click="fetchList" :loading="loading">刷新</el-button>
      </div>
    </el-card>

    <div v-loading="loading" class="fav-grid">
      <el-card v-for="item in list" :key="item.id" shadow="hover" class="fav-card" @click="goDetail(item)">
        <div class="fav-header">
          <div class="fav-title">{{ item.title || item.job?.title || '未命名职位' }}</div>
          <div class="fav-salary">{{ formatSalary(salaryOf(item).salary_min, salaryOf(item).salary_max) }}</div>
        </div>
        <div class="fav-company">
          <el-icon><OfficeBuilding /></el-icon>
          <span>{{ companyOf(item) }}</span>
          <el-divider direction="vertical" />
          <span>{{ cityOf(item) || '城市不限' }}</span>
        </div>
        <div class="fav-meta">
          <el-tag size="small" type="info">{{ expOf(item) || '经验不限' }}</el-tag>
          <el-tag size="small" type="info">{{ eduOf(item) || '学历不限' }}</el-tag>
          <el-tag size="small" type="info">{{ typeOf(item) || '全职' }}</el-tag>
        </div>
        <div class="fav-footer">
          <span class="fav-time">
            <el-icon><Clock /></el-icon>
            收藏于 {{ formatDate(item.created_at || item.favorited_at) }}
          </span>
          <el-button
            link
            type="danger"
            :icon="Delete"
            :loading="cancelId === jobIdOf(item)"
            @click.stop="cancelFavorite(item)"
          >
            取消收藏
          </el-button>
        </div>
      </el-card>
      <el-empty v-if="!loading && !list.length" description="还没有收藏的职位, 去职位广场看看吧">
        <el-button type="primary" @click="$router.push('/seeker/jobs')">浏览职位广场</el-button>
      </el-empty>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Star, OfficeBuilding, Clock, Delete, Refresh } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'
import { formatSalary } from '@/utils/format'

const router = useRouter()
const list = ref<any[]>([])
const loading = ref(false)
const cancelId = ref<number | null>(null)

// 字段兼容: 收藏记录可能直接展开 job 字段, 也可能嵌套在 item.job 内
const jobIdOf = (item: any) => Number(item.job_id || item.id || item.job?.id)
const companyOf = (item: any) => item.company || item.job?.company || '匿名企业'
const cityOf = (item: any) => item.work_city || item.job?.work_city
const expOf = (item: any) => item.experience_required || item.job?.experience_required
const eduOf = (item: any) => item.education_required || item.job?.education_required
const typeOf = (item: any) => item.job_type || item.job?.job_type
const salaryOf = (item: any) => ({
  salary_min: item.salary_min ?? item.job?.salary_min,
  salary_max: item.salary_max ?? item.job?.salary_max,
})

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await jobApi.listFavorites()
    list.value = res.data?.items || res.data || []
  } catch (e) {
    list.value = []
  } finally {
    loading.value = false
  }
}

const goDetail = (item: any) => {
  const id = jobIdOf(item)
  if (id) router.push(`/seeker/jobs/${id}`)
}

const cancelFavorite = async (item: any) => {
  const jobId = jobIdOf(item)
  if (!jobId) return
  try {
    await ElMessageBox.confirm('确定取消收藏该职位吗?', '提示', {
      type: 'warning',
      confirmButtonText: '确定',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  cancelId.value = jobId
  try {
    await jobApi.removeFavorite(jobId)
    list.value = list.value.filter((it) => jobIdOf(it) !== jobId)
    ElMessage.success('已取消收藏')
  } catch (e) {
    // 拦截器已提示
  } finally {
    cancelId.value = null
  }
}

const formatDate = (iso?: string) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

onMounted(fetchList)
</script>

<style scoped>
.favorites-page { max-width: 1100px; margin: 0 auto; }
.header-card { border-radius: 12px; margin-bottom: 16px; }
.header-card :deep(.el-card__body) { padding: 16px 20px; }
.header-row {
  display: flex; align-items: center; justify-content: space-between;
}
.header-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 18px; font-weight: 600;
}
.title-icon { color: #faad14; font-size: 22px; }
.fav-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px;
}
.fav-card {
  border-radius: 10px; cursor: pointer; transition: transform 0.2s;
}
.fav-card:hover { transform: translateY(-2px); }
.fav-header {
  display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;
}
.fav-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.fav-salary { font-size: 16px; font-weight: 700; color: #ff6b35; }
.fav-company {
  display: flex; align-items: center; gap: 6px;
  color: var(--text-secondary); font-size: 13px; margin-bottom: 10px;
}
.fav-meta { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.fav-footer {
  display: flex; align-items: center; justify-content: space-between;
  border-top: 1px dashed var(--border-color); padding-top: 10px;
}
.fav-time {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; color: var(--text-secondary);
}
</style>
