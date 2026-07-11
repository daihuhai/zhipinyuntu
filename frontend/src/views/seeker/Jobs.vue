<!--
  职位广场 (求职者浏览) - 搜索 + 多条件筛选
-->
<template>
  <div class="jobs-page">
    <!-- 搜索 + 筛选区 -->
    <el-card shadow="never" class="filter-card">
      <div class="filter-row">
        <el-input
          v-model="keyword"
          placeholder="搜索职位名称/公司/城市"
          clearable
          :prefix-icon="Search"
          style="width: 280px"
          @keyup.enter="handleSearch"
          @clear="handleSearch"
        />
        <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
        <el-button text :icon="filterOpen ? ArrowUp : ArrowDown" @click="filterOpen = !filterOpen">
          {{ filterOpen ? '收起筛选' : '展开筛选' }}
        </el-button>
      </div>
      <transition name="el-zoom-in-top">
        <div v-show="filterOpen" class="filter-row" style="margin-top: 12px">
          <el-select v-model="filters.city" placeholder="城市" clearable style="width: 130px" @change="handleSearch">
            <el-option v-for="c in cityOptions" :key="c" :label="c" :value="c" />
          </el-select>
          <el-select v-model="filters.job_type" placeholder="工作性质" clearable style="width: 120px" @change="handleSearch">
            <el-option label="全职" value="全职" />
            <el-option label="兼职" value="兼职" />
            <el-option label="实习" value="实习" />
          </el-select>
          <el-select v-model="filters.experience" placeholder="经验要求" clearable style="width: 130px" @change="handleSearch">
            <el-option v-for="e in expOptions" :key="e" :label="e" :value="e" />
          </el-select>
          <el-select v-model="filters.education" placeholder="学历要求" clearable style="width: 130px" @change="handleSearch">
            <el-option label="专科及以上" value="专科及以上" />
            <el-option label="本科及以上" value="本科及以上" />
            <el-option label="硕士及以上" value="硕士及以上" />
            <el-option label="博士及以上" value="博士及以上" />
          </el-select>
          <el-select v-model="filters.salaryRange" placeholder="薪资范围" clearable style="width: 150px" @change="onSalaryChange">
            <el-option label="5K 以下" value="0-5" />
            <el-option label="5-10K" value="5-10" />
            <el-option label="10-20K" value="10-20" />
            <el-option label="20-30K" value="20-30" />
            <el-option label="30-50K" value="30-50" />
            <el-option label="50K 以上" value="50-999" />
          </el-select>
          <el-button text type="info" :icon="RefreshLeft" @click="resetFilters">重置</el-button>
        </div>
      </transition>
    </el-card>

    <div v-loading="loading" class="job-grid">
      <el-card v-for="job in list" :key="job.id" shadow="hover" class="job-card" @click="goDetail(job.id)">
        <div class="job-card-inner">
          <div class="job-top">
            <div class="job-header">
              <div class="job-title">{{ job.title }}</div>
              <div class="job-salary">{{ formatSalary(job.salary_min, job.salary_max) }}</div>
            </div>
            <div class="job-company">{{ job.company || '匿名企业' }} · {{ job.work_city || '不限' }}</div>
            <div class="job-meta">
              <el-tag size="small" type="info">{{ job.experience_required || '经验不限' }}</el-tag>
              <el-tag size="small" type="info">{{ job.education_required || '学历不限' }}</el-tag>
              <el-tag size="small" type="info">{{ job.job_type || '全职' }}</el-tag>
            </div>
            <div class="job-desc">{{ job.description?.slice(0, 100) }}{{ job.description?.length > 100 ? '...' : '' }}</div>
          </div>
          <div class="job-footer">
            <el-button link type="primary" @click.stop="goDetail(job.id)">查看详情 →</el-button>
          </div>
        </div>
      </el-card>
      <el-empty v-if="!loading && !list.length" description="暂无符合条件的职位, 试试调整筛选条件" />
    </div>

    <el-pagination
      v-if="total > size"
      v-model:current-page="page"
      :page-size="size"
      :total="total"
      layout="prev, pager, next"
      @current-change="fetchList"
      style="margin-top: 16px; justify-content: center"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Search, ArrowDown, ArrowUp, RefreshLeft } from '@element-plus/icons-vue'
import { jobApi } from '@/api/job'
import { formatSalary } from '@/utils/format'

const router = useRouter()
const list = ref<any[]>([])
const loading = ref(false)
const keyword = ref('')
const page = ref(1)
const size = ref(12)
const total = ref(0)

// 筛选
const filterOpen = ref(true)
const filters = ref({
  city: '',
  job_type: '',
  experience: '',
  education: '',
  salaryRange: '',
  salary_min: undefined as number | undefined,
  salary_max: undefined as number | undefined,
})

// 城市与经验选项 (从已有数据动态提取, 兜底常用值)
const cityOptions = ref<string[]>(['北京', '上海', '深圳', '杭州', '广州', '成都', '南京', '武汉', '西安'])
const expOptions = ref<string[]>(['应届', '1-3年', '3-5年', '5-10年', '10年以上'])

const onSalaryChange = (val: string) => {
  if (!val) {
    filters.value.salary_min = undefined
    filters.value.salary_max = undefined
  } else {
    const [min, max] = val.split('-').map(Number)
    filters.value.salary_min = min
    filters.value.salary_max = max
  }
  handleSearch()
}

const resetFilters = () => {
  keyword.value = ''
  filters.value = {
    city: '', job_type: '', experience: '', education: '',
    salaryRange: '', salary_min: undefined, salary_max: undefined,
  }
  handleSearch()
}

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await jobApi.list({
      page: page.value,
      size: size.value,
      keyword: keyword.value.trim(),
      city: filters.value.city || undefined,
      job_type: filters.value.job_type || undefined,
      experience: filters.value.experience || undefined,
      education: filters.value.education || undefined,
      salary_min: filters.value.salary_min,
      salary_max: filters.value.salary_max,
    })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
    // 从结果中动态补充城市选项
    const cities = new Set<string>(cityOptions.value)
    list.value.forEach((j: any) => j.work_city && cities.add(j.work_city))
    cityOptions.value = Array.from(cities)
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  page.value = 1
  fetchList()
}

const goDetail = (id: number) => {
  router.push(`/seeker/jobs/${id}`)
}

onMounted(fetchList)
</script>

<style scoped>
.filter-card { border-radius: 12px; margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { padding: 16px; }
.filter-row { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.job-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.job-card { border-radius: 10px; cursor: pointer; transition: transform 0.2s; }
.job-card:hover { transform: translateY(-2px); }
.job-card :deep(.el-card__body) { padding: 16px; height: 100%; }
.job-card-inner { display: flex; flex-direction: column; height: 100%; min-height: 220px; }
.job-top { flex: 1; }
.job-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px; }
.job-title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.job-salary { font-size: 16px; font-weight: 700; color: #ff6b35; }
.job-company { color: var(--text-secondary); font-size: 13px; margin-bottom: 10px; }
.job-meta { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
.job-desc { font-size: 13px; color: var(--text-secondary); line-height: 1.5; }
.job-footer { margin-top: 12px; padding-top: 10px; border-top: 1px solid #f5f5f5; display: flex; justify-content: flex-end; }
</style>
