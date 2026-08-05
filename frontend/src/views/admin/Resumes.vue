<!--
  简历管理 (管理员) - 含详情抽屉 + 查看原文件
-->
<template>
  <div class="resumes-page">
    <el-card shadow="never" class="filter-card">
      <el-input v-model="keyword" placeholder="搜索姓名/学校" clearable :prefix-icon="Search" style="width: 280px" @keyup.enter="fetchList" @clear="fetchList" />
      <el-select v-model="parseStatus" placeholder="解析状态" clearable style="width: 140px" @change="fetchList">
        <el-option label="待解析" :value="0" />
        <el-option label="解析中" :value="1" />
        <el-option label="成功" :value="2" />
        <el-option label="失败" :value="3" />
      </el-select>
      <el-button type="primary" :icon="Search" @click="fetchList">查询</el-button>
      <el-button @click="handleReset">重置</el-button>
      <el-button :icon="Download" :loading="exporting" @click="handleExport">导出CSV</el-button>
    </el-card>

    <el-card shadow="never" class="list-card">
      <div v-if="selectedRows.length" class="batch-bar">
        <span class="batch-info">已选 {{ selectedRows.length }} 项</span>
        <el-button type="danger" @click="handleBatchDelete">批量删除</el-button>
      </div>
      <el-table :data="list" v-loading="loading" stripe @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="70" />
        <el-table-column prop="age" label="年龄" width="70" />
        <el-table-column prop="education" label="学历" width="80" />
        <el-table-column prop="school" label="学校" min-width="140" />
        <el-table-column prop="major" label="专业" min-width="120" />
        <el-table-column prop="work_years" label="工作年限" width="100">
          <template #default="{ row }">{{ row.work_years || 0 }} 年</template>
        </el-table-column>
        <el-table-column label="解析状态" width="100">
          <template #default="{ row }"><el-tag :type="statusTag(row.parse_status)">{{ statusText(row.parse_status) }}</el-tag></template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" min-width="150">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">查看详情</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-if="total > size"
        v-model:current-page="page"
        :page-size="size"
        :total="total"
        layout="prev, pager, next, total"
        @current-change="fetchList"
        style="margin-top: 16px; justify-content: flex-end"
      />
    </el-card>

    <!-- 简历详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="简历详情"
      direction="rtl"
      size="600px"
      :destroy-on-close="true"
    >
      <div v-loading="detailLoading" class="detail-wrap">
        <template v-if="currentDetail">
          <!-- 基本信息 -->
          <div class="section-title">基本信息</div>
          <div class="info-grid">
            <div class="info-row"><span class="info-label">姓名</span><span class="info-value">{{ currentDetail.name || '-' }}</span></div>
            <div class="info-row"><span class="info-label">性别</span><span class="info-value">{{ currentDetail.gender || '-' }}</span></div>
            <div class="info-row"><span class="info-label">年龄</span><span class="info-value">{{ currentDetail.age || '-' }}</span></div>
            <div class="info-row"><span class="info-label">学历</span><span class="info-value">{{ currentDetail.education || '-' }}</span></div>
            <div class="info-row"><span class="info-label">学校</span><span class="info-value">{{ currentDetail.school || '-' }}</span></div>
            <div class="info-row"><span class="info-label">专业</span><span class="info-value">{{ currentDetail.major || '-' }}</span></div>
            <div class="info-row"><span class="info-label">工作年限</span><span class="info-value">{{ currentDetail.work_years ?? '-' }} 年</span></div>
            <div class="info-row"><span class="info-label">所在城市</span><span class="info-value">{{ currentDetail.current_city || '-' }}</span></div>
            <div class="info-row"><span class="info-label">电话</span><span class="info-value">{{ currentDetail.phone || '-' }}</span></div>
            <div class="info-row"><span class="info-label">邮箱</span><span class="info-value">{{ currentDetail.email || '-' }}</span></div>
          </div>

          <!-- 工作经历 -->
          <div v-if="currentDetail.work_experience?.length" class="section-title" style="margin-top:20px">工作经历</div>
          <el-timeline v-if="currentDetail.work_experience?.length">
            <el-timeline-item
              v-for="(w, i) in currentDetail.work_experience"
              :key="i"
              :timestamp="w.duration || w.start_date || ''"
              placement="top" type="primary"
            >
              <div class="exp-card">
                <div class="exp-company">{{ w.company || '-' }} · {{ w.position || w.title || '-' }}</div>
                <div v-if="w.description" class="exp-desc">{{ w.description }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>

          <!-- 项目经历 -->
          <div v-if="currentDetail.projects?.length" class="section-title" style="margin-top:20px">项目经历</div>
          <el-timeline v-if="currentDetail.projects?.length">
            <el-timeline-item
              v-for="(p, i) in currentDetail.projects"
              :key="i"
              :timestamp="p.duration || p.time || ''"
              placement="top" type="success"
            >
              <div class="exp-card">
                <div class="exp-company">{{ p.name || p.title || '-' }} · {{ p.role || '-' }}</div>
                <div v-if="p.description" class="exp-desc">{{ p.description }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>

          <!-- 自我评价 -->
          <div v-if="currentDetail.self_evaluation" class="section-title" style="margin-top:20px">自我评价</div>
          <div v-if="currentDetail.self_evaluation" class="eval-text">{{ currentDetail.self_evaluation }}</div>

          <!-- 技能列表 -->
          <div v-if="currentDetail.skills?.length" class="section-title" style="margin-top:20px">技能列表</div>
          <div v-if="currentDetail.skills?.length" class="skills-row">
            <el-tag v-for="sk in currentDetail.skills" :key="sk.id" :type="levelTagType(sk.skill_level)" size="small">
              {{ sk.skill_name }} · {{ sk.skill_level || '掌握' }}
            </el-tag>
          </div>

          <!-- 查看原文件 -->
          <div class="file-section">
            <el-button type="primary" :icon="Document" plain @click="viewOriginalFile">
              查看原文件 (PDF/DOC)
            </el-button>
          </div>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Document, Download } from '@element-plus/icons-vue'
import { adminApi } from '@/api/admin'
import { resumeApi } from '@/api/resume'

const list = ref<any[]>([])
const loading = ref(false)
const exporting = ref(false)
const keyword = ref('')
let debounceTimer: ReturnType<typeof setTimeout> | null = null
watch(keyword, () => {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = setTimeout(() => {
    fetchList()
  }, 300)
})
const parseStatus = ref<number | ''>('')
const page = ref(1)
const size = ref(20)
const total = ref(0)

// 详情抽屉
const drawerVisible = ref(false)
const detailLoading = ref(false)
const currentDetail = ref<any>(null)

// 批量操作 - 选中的行
const selectedRows = ref<any[]>([])
const handleSelectionChange = (rows: any[]) => selectedRows.value = rows

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await adminApi.resumes({
      page: page.value, size: size.value,
      keyword: keyword.value,
      parse_status: parseStatus.value === '' ? undefined : parseStatus.value,
    })
    list.value = res.data?.items || []
    total.value = res.data?.total || 0
  } finally {
    loading.value = false
  }
}

const handleReset = () => {
  keyword.value = ''
  parseStatus.value = ''
  page.value = 1
  fetchList()
}

const showDetail = async (row: any) => {
  drawerVisible.value = true
  detailLoading.value = true
  currentDetail.value = null
  try {
    const res: any = await resumeApi.detail(row.id)
    currentDetail.value = res.data || null
  } catch (e: any) {
    ElMessage.error(e?.message || '加载简历详情失败')
  } finally {
    detailLoading.value = false
  }
}

const viewOriginalFile = async () => {
  if (!currentDetail.value?.id) return
  try {
    const res: any = await resumeApi.getFile(currentDetail.value.id)
    const url = res.data?.doc_url
    if (url) {
      window.open(url, '_blank')
    } else {
      ElMessage.warning('简历文件路径不存在')
    }
  } catch (e: any) {
    ElMessage.error(e?.message || '获取文件失败')
  }
}

const statusText = (s: number) => ({ 0: '待解析', 1: '解析中', 2: '成功', 3: '失败' }[s] || '未知')
const statusTag = (s: number): any => ({ 0: 'info', 1: 'warning', 2: 'success', 3: 'danger' }[s] || 'info')
const levelTagType = (l?: string): any => {
  if (l === '精通') return 'danger'
  if (l === '熟练') return 'warning'
  if (l === '掌握') return 'success'
  return 'info'
}
const formatDate = (iso?: string) => iso ? new Date(iso).toLocaleString('zh-CN', { hour12: false }) : '-'

const handleBatchDelete = async () => {
  const ids = selectedRows.value.map(r => r.id)
  try {
    await ElMessageBox.confirm(`确认批量删除选中的 ${ids.length} 条记录?`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    const res: any = await adminApi.batchDeleteResumes(ids)
    ElMessage.success(`已删除 ${res.data?.deleted ?? ids.length} 条`)
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '删除失败')
  }
}

const handleDelete = async (row: any) => {
  try {
    await ElMessageBox.confirm(`确认删除简历 ${row.name || '#' + row.id}?`, '提示', { type: 'warning' })
  } catch {
    return
  }
  try {
    await adminApi.deleteResume(row.id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '删除失败')
  }
}

// 导出简历数据为 CSV
const handleExport = async () => {
  exporting.value = true
  try {
    const res: any = await adminApi.exportData('resumes')
    const blob = new Blob([res], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `resumes_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    ElMessage.success('导出成功')
  } catch (e: any) {
    ElMessage.error(e?.message || '导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(fetchList)
</script>

<style scoped>
.filter-card { border-radius: 12px; margin-bottom: 16px; }
.filter-card :deep(.el-card__body) { display: flex; gap: 8px; padding: 16px; flex-wrap: wrap; }
.list-card { border-radius: 12px; }
.batch-bar { display: flex; align-items: center; gap: 12px; margin-bottom: 12px; padding: 8px 12px; background: #fdf6ec; border-radius: 6px; }
.batch-info { color: #e6a23c; font-weight: 600; font-size: 13px; }
.detail-wrap { padding: 0 4px; }
.section-title {
  font-size: 14px; font-weight: 600; color: var(--text-primary);
  margin-bottom: 12px; padding-left: 8px; border-left: 3px solid #1677ff;
}
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.info-row { display: flex; padding: 6px 8px; border-bottom: 1px dashed #f0f0f0; font-size: 13px; }
.info-label { width: 64px; color: #999; flex-shrink: 0; }
.info-value { color: #333; }
.exp-card { padding: 8px 12px; background: #f9fafc; border-radius: 6px; }
.exp-company { font-size: 13px; font-weight: 600; color: #333; }
.exp-desc { font-size: 12px; color: #666; margin-top: 4px; line-height: 1.5; }
.eval-text { font-size: 13px; color: #666; line-height: 1.6; padding: 10px; background: #fafafa; border-radius: 6px; }
.skills-row { display: flex; flex-wrap: wrap; gap: 6px; }
.file-section { margin-top: 24px; text-align: center; padding-top: 16px; border-top: 1px solid #f0f0f0; }
</style>
