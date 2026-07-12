<!--
  我的简历列表 - 含详情抽屉 (工作经历/项目经历) + 查看原文件
-->
<template>
  <div class="resume-list">
    <el-card shadow="never" class="list-card">
      <template #header>
        <div class="card-header">
          <span>我的简历</span>
          <el-button type="primary" :icon="Plus" @click="$router.push('/seeker/resume/upload')">上传新简历</el-button>
        </div>
      </template>
      <el-table :data="list" v-loading="loading" stripe>
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="education" label="学历" width="80" />
        <el-table-column prop="school" label="学校" width="160" />
        <el-table-column prop="major" label="专业" width="140" />
        <el-table-column prop="work_years" label="工作年限" width="100">
          <template #default="{ row }">{{ row.work_years || 0 }} 年</template>
        </el-table-column>
        <el-table-column label="解析状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusTag(row.parse_status)">{{ statusText(row.parse_status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" min-width="160">
          <template #default="{ row }">{{ formatDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="380" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="showDetail(row)">查看详情</el-button>
            <el-button link type="primary" @click="previewFile(row)">预览</el-button>
            <el-button link type="success" @click="$router.push(`/seeker/resume/${row.id}/edit`)">编辑</el-button>
            <el-button link type="info" @click="$router.push(`/seeker/graph?resume_id=${row.id}`)">能力图谱</el-button>
            <el-button link type="warning" @click="$router.push(`/seeker/recommend?resume_id=${row.id}`)">推荐职位</el-button>
            <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
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
              placement="top"
              type="primary"
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
              placement="top"
              type="success"
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
            <el-tag
              v-for="sk in currentDetail.skills"
              :key="sk.id"
              :type="levelTagType(sk.skill_level)"
              size="small"
            >{{ sk.skill_name }} · {{ sk.skill_level || '掌握' }}</el-tag>
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
import { onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document } from '@element-plus/icons-vue'
import { resumeApi } from '@/api/resume'

const list = ref<any[]>([])
const loading = ref(false)

// 详情抽屉
const drawerVisible = ref(false)
const detailLoading = ref(false)
const currentDetail = ref<any>(null)

const fetchList = async () => {
  loading.value = true
  try {
    const res: any = await resumeApi.list()
    list.value = res.data?.items || []
  } finally {
    loading.value = false
  }
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

const previewFile = async (row: any) => {
  const res: any = await resumeApi.getFile(row.id)
  const url = res.data?.doc_url || ''
  if (!url) { ElMessage.warning('文件不存在'); return }
  const fullUrl = url.startsWith('http') ? url : window.location.origin + url
  if (fullUrl.endsWith('.pdf')) {
    window.open(fullUrl, '_blank')
  } else {
    window.open(`https://docs.google.com/viewer?url=${encodeURIComponent(fullUrl)}&embedded=true`, '_blank')
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

const formatDate = (iso?: string) => {
  if (!iso) return '-'
  return new Date(iso).toLocaleString('zh-CN', { hour12: false })
}

const handleDelete = async (id: number) => {
  try {
    await ElMessageBox.confirm('确认删除该简历?', '提示', { type: 'warning' })
  } catch {
    return // 用户点击取消, 不报错
  }
  try {
    await resumeApi.remove(id)
    ElMessage.success('已删除')
    fetchList()
  } catch (e: any) {
    ElMessage.error(e?.message || '删除失败')
  }
}

onMounted(fetchList)
</script>

<style scoped>
.list-card { border-radius: 12px; }
.card-header { display: flex; align-items: center; justify-content: space-between; font-weight: 600; }
.detail-wrap { padding: 0 4px; }
.section-title {
  font-size: 14px; font-weight: 600; color: var(--text-primary);
  margin-bottom: 12px; padding-left: 8px; border-left: 3px solid #1677ff;
}
.info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0; }
.info-row {
  display: flex; padding: 6px 8px; border-bottom: 1px dashed #f0f0f0; font-size: 13px;
}
.info-label { width: 64px; color: #999; flex-shrink: 0; }
.info-value { color: #333; }

.exp-card { padding: 8px 12px; background: #f9fafc; border-radius: 6px; }
.exp-company { font-size: 14px; font-weight: 600; color: #333; }
.exp-desc { font-size: 12px; color: #666; margin-top: 4px; line-height: 1.5; }

.eval-text {
  font-size: 13px; color: #666; line-height: 1.6;
  padding: 10px; background: #fafafa; border-radius: 6px;
}
.skills-row { display: flex; flex-wrap: wrap; gap: 6px; }
.file-section { margin-top: 24px; text-align: center; padding-top: 16px; border-top: 1px solid #f0f0f0; }
</style>
