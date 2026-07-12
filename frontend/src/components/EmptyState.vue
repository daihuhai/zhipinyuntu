<!--
  空状态组件 - 统一空数据展示
  含插图 + 引导文案 + 操作按钮
-->
<template>
  <div class="empty-state">
    <el-empty :description="description" :image-size="imageSize">
      <template v-if="actionText" #default>
        <el-button type="primary" :icon="actionIcon" @click="$emit('action')">
          {{ actionText }}
        </el-button>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Upload, Plus, Search, Document } from '@element-plus/icons-vue'

const props = defineProps<{
  type?: 'resume' | 'job' | 'application' | 'search' | 'default'
  description?: string
  imageSize?: number
  actionText?: string
  actionIcon?: any
}>()

defineEmits<{
  (e: 'action'): void
}>()

const defaultConfig = {
  resume: { desc: '还没有简历, 上传一份让 AI 帮你解析', action: '去上传简历', icon: Upload },
  job: { desc: '还没有发布职位, 快来招募人才', action: '去发布职位', icon: Plus },
  application: { desc: '暂无投递记录', action: '去看看职位', icon: Search },
  search: { desc: '暂无符合条件的结果, 试试调整筛选', action: '', icon: Search },
  default: { desc: '暂无数据', action: '', icon: Document },
}

const config = computed(() => defaultConfig[props.type || 'default'])
const description = computed(() => props.description || config.value.desc)
const actionText = computed(() => props.actionText !== undefined ? props.actionText : config.value.action)
const actionIcon = computed(() => props.actionIcon || config.value.icon)
const imageSize = computed(() => props.imageSize || 120)
</script>

<style scoped>
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 40px 20px;
  min-height: 200px;
}
</style>
