<script setup lang="ts">
import { computed, ref, watch, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import OnboardingGuide from '@/components/OnboardingGuide.vue'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api/auth'

const userStore = useUserStore()

const role = computed(() => userStore.userInfo?.role || '')

// 引导展示状态: 依据后端 onboard_done 判断 (0=未完成展示, 1=已完成不展示)
const showGuide = ref(false)

// 根据当前 userInfo.onboard_done 决定是否展示引导
const evaluateGuide = () => {
  const r = userStore.userInfo?.role || ''
  if (!r || !['ROLE_SEEKER', 'ROLE_EMPLOYER'].includes(r)) {
    showGuide.value = false
    return
  }
  // 老用户 onboard_done=1 不展示; 仅新用户 (onboard_done!==1) 展示一次
  showGuide.value = userStore.userInfo?.onboard_done !== 1
}

// 挂载时拉取权威用户信息, 确保刷新页面后引导状态与后端一致
onMounted(async () => {
  if (userStore.token) {
    try {
      const res: any = await authApi.me()
      const me = res.data
      if (me && userStore.userInfo) {
        userStore.setUserInfo({
          ...userStore.userInfo,
          onboard_done: me.onboard_done,
        })
      }
    } catch {
      // 拉取失败沿用本地缓存
    }
  }
  evaluateGuide()
})

watch(role, evaluateGuide, { immediate: true })

// 用户完成/跳过引导后, 调用后端持久化标记, 之后登录不再展示
const handleGuideSkip = async () => {
  showGuide.value = false
  try {
    await authApi.onboardDone()
    // 同步更新本地 userInfo, 保证刷新页面后也不展示
    if (userStore.userInfo) {
      userStore.setUserInfo({ ...userStore.userInfo, onboard_done: 1 })
    }
  } catch {
    // 标记失败不阻塞, 下次登录后端仍会尝试
  }
}
</script>

<template>
  <RouterView />
  <OnboardingGuide v-if="showGuide" :key="role" :role="role" @skip="handleGuideSkip" />
</template>