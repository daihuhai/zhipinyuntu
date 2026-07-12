<!--
  骨架屏列表组件 - 列表加载占位
-->
<template>
  <div class="skeleton-list">
    <div v-for="i in count" :key="i" class="skeleton-item">
      <el-skeleton :rows="rows" animated>
        <template #template>
          <el-skeleton-item variant="h3" style="width: 50%; margin-bottom: 12px" />
          <el-skeleton-item variant="text" style="width: 80%; margin-bottom: 8px" />
          <el-skeleton-item variant="text" style="width: 60%" />
        </template>
      </el-skeleton>
    </div>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  count?: number
  rows?: number
}>(), {
  count: 6,
  rows: 3,
})
</script>

<style scoped>
.skeleton-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
}
.skeleton-item {
  padding: 20px;
  border-radius: 8px;
  border: 1px solid var(--el-border-color-lighter);
  background: var(--el-bg-color);
}
</style>
