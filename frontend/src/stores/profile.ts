/**
 * 知识画像 Store。
 * 管理画像数据、生成状态和轮询刷新。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getProfile,
  refreshProfile,
  getProfileStatus,
  type KnowledgeProfileData,
  type ProfileStatus,
  type ProfileJson,
} from '@/api/profile'

const POLL_INTERVAL = 3000

export const useProfileStore = defineStore('profile', () => {
  const profile = ref<KnowledgeProfileData | null>(null)
  const profileStatus = ref<ProfileStatus>({
    is_generating: false,
    has_profile: false,
    last_generated_at: null,
  })
  const loading = ref<boolean>(false)
  const refreshing = ref<boolean>(false)

  let pollTimer: ReturnType<typeof setInterval> | null = null

  const hasProfile = computed(() => profile.value !== null)
  const profileJson = computed<ProfileJson | null>(() => profile.value?.profile_json ?? null)

  const statusText = computed(() => {
    if (profileStatus.value.is_generating) return '生成中'
    if (profileStatus.value.has_profile) return '已生成'
    return '未生成'
  })

  const statusColor = computed(() => {
    if (profileStatus.value.is_generating) return '#e6a23c'
    if (profileStatus.value.has_profile || profile.value) return '#67c23a'
    return '#909399'
  })

  async function fetchProfile(): Promise<void> {
    loading.value = true
    try {
      profile.value = await getProfile()
    } catch (error) {
      console.warn('获取知识画像失败:', error)
      profile.value = null
    } finally {
      loading.value = false
    }
  }

  async function doRefreshProfile(): Promise<number | null> {
    if (refreshing.value) return null
    refreshing.value = true
    try {
      const result = await refreshProfile()
      profileStatus.value = {
        ...profileStatus.value,
        is_generating: true,
      }
      startPolling()
      return result.task_id
    } catch (error) {
      console.error('刷新知识画像失败:', error)
      return null
    } finally {
      refreshing.value = false
    }
  }

  async function fetchProfileStatus(): Promise<void> {
    try {
      profileStatus.value = await getProfileStatus()
      if (profileStatus.value.is_generating) {
        startPolling()
      }
    } catch (error) {
      console.error('获取知识画像状态失败:', error)
    }
  }

  function updateProfileStatus(payload: { is_generating?: boolean; has_profile?: boolean; status?: string }): void {
    const isGenerating = payload.is_generating ?? !['completed', 'failed'].includes(payload.status || '')
    const hasProfile = payload.has_profile ?? (payload.status === 'completed' ? true : profileStatus.value.has_profile)

    profileStatus.value = {
      ...profileStatus.value,
      is_generating: isGenerating,
      has_profile: hasProfile,
    }

    if (!isGenerating && hasProfile) {
      fetchProfile()
      stopPolling()
    }
  }

  function startPolling(): void {
    if (pollTimer) return
    pollTimer = setInterval(async () => {
      try {
        const status = await getProfileStatus()
        profileStatus.value = status
        if (!status.is_generating) {
          if (status.has_profile) {
            await fetchProfile()
          }
          stopPolling()
        }
      } catch (error) {
        console.error('轮询知识画像状态失败:', error)
      }
    }, POLL_INTERVAL)
  }

  function stopPolling(): void {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  return {
    profile,
    profileStatus,
    loading,
    refreshing,
    hasProfile,
    profileJson,
    statusText,
    statusColor,
    fetchProfile,
    doRefreshProfile,
    fetchProfileStatus,
    updateProfileStatus,
    startPolling,
    stopPolling,
  }
})
