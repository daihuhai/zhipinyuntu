<!--
  骨架屏表格组件 - 表格加载占位
-->
<template>
  <div class="skeleton-table">
    <div v-for="i in count" :key="i" class="skeleton-row">
      <el-skeleton :rows="1" animated>
        <template #template>
          <div class="skeleton-cells">
            <el-skeleton-item v-for="c in cols" :key="c" variant="text" :style="{ width: cellWidth(c) }" />
          </div>
        </template>
      </el-skeleton>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  count?: number
  cols?: number
}>(), {
  count: 8,
  cols: 5,
})

const cellWidth = (idx: number) => {
  const widths = ['30%', '20%', '15%', '15%', '20%', '10%', '12%']
  return widths[idx % widths.length]
}
</script>

<style scoped>
.skeleton-table {
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 8px;
  overflow: hidden;
}
.skeleton-row {
  padding: 16px 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
}
.skeleton-row:last-child {
  border-bottom: none;
}
.skeleton-cells {
  display: flex;
  gap: 20px;
  align-items: center;
}
</style>
