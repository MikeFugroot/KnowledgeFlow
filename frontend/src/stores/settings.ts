/**
 * 配置状态 Store
 * API 配置、Cookie、Whisper 配置
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getSettings,
  updateSettings,
  type SettingItem,
  type SettingsUpdateParams,
  type ApiConfig,
  type CookieConfig,
  type WhisperConfig,
  type SearchConfig,
  type ProfileConfig,
} from '@/api/settings'

export const useSettingsStore = defineStore('settings', () => {
  // ==================== State ====================

  /** 原始配置列表 */
  const settingsList = ref<SettingItem[]>([])

  /** 加载状态 */
  const loading = ref<boolean>(false)

  /** 保存中状态 */
  const saving = ref<boolean>(false)

  // ==================== Getters ====================

  /** API 配置 */
  const apiConfig = computed<ApiConfig>(() => {
    const getVal = (key: string, fallback: string = ''): string => {
      const item = settingsList.value.find((s) => s.key === key)
      return item ? item.value : fallback
    }
    return {
      provider: getVal('api_provider', 'qwen') as 'qwen' | 'deepseek',
      api_key: getVal('api_key'),
      model_name: getVal('model_name'),
    }
  })

  /** Cookie 配置 */
  const cookieConfig = computed<CookieConfig>(() => {
    const getVal = (key: string, fallback: string = ''): string => {
      const item = settingsList.value.find((s) => s.key === key)
      return item ? item.value : fallback
    }
    return {
      bilibili_cookie: getVal('bilibili_cookie'),
      xiaohongshu_cookie: getVal('xiaohongshu_cookie'),
    }
  })

  /** Whisper 配置 */
  const whisperConfig = computed<WhisperConfig>(() => {
    const getVal = (key: string, fallback: string = ''): string => {
      const item = settingsList.value.find((s) => s.key === key)
      return item ? item.value : fallback
    }
    return {
      backend: getVal('whisper_backend', 'faster-whisper') as 'faster-whisper' | 'openai-whisper',
      model: getVal('whisper_model', 'medium'),
      language: getVal('whisper_language', 'zh'),
    }
  })

  /** 检索配置 */
  const searchConfig = computed<SearchConfig>(() => {
    const getNum = (key: string, fallback: number): number => {
      const item = settingsList.value.find((s) => s.key === key)
      return item ? Number(item.value) : fallback
    }
    return {
      embedding_model: settingsList.value.find((s) => s.key === 'embedding_model')?.value ?? 'all-MiniLM-L6-v2',
      chunk_size: getNum('chunk_size', 500),
      chunk_overlap: getNum('chunk_overlap', 50),
      top_k: getNum('top_k', 10),
      candidate_k: getNum('candidate_k', 50),
    }
  })

  /** 画像配置 */
  const profileConfig = computed<ProfileConfig>(() => {
    const getBool = (key: string, fallback: boolean): boolean => {
      const item = settingsList.value.find((s) => s.key === key)
      return item ? item.value === 'true' : fallback
    }
    const getNum = (key: string, fallback: number): number => {
      const item = settingsList.value.find((s) => s.key === key)
      return item ? Number(item.value) : fallback
    }
    return {
      use_llm_profile: getBool('use_llm_profile', true),
      max_items: getNum('profile_max_items', 100),
      timeout: getNum('profile_timeout', 120),
    }
  })

  /** 是否有 API Key 配置 */
  const hasApiKey = computed(() => {
    return !!settingsList.value.find((s) => s.key === 'api_key' && s.value)?.value
  })

  /** 是否有 B 站 Cookie */
  const hasBilibiliCookie = computed(() => {
    return !!settingsList.value.find((s) => s.key === 'bilibili_cookie')?.value
  })

  // ==================== Actions ====================

  /**
   * 加载配置列表
   */
  async function fetchSettings(): Promise<void> {
    loading.value = true
    try {
      settingsList.value = await getSettings()
    } catch (error) {
      console.error('获取配置失败:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 更新配置
   */
  async function saveSettings(params: SettingsUpdateParams): Promise<boolean> {
    saving.value = true
    try {
      settingsList.value = await updateSettings(params)
      return true
    } catch (error) {
      console.error('更新配置失败:', error)
      return false
    } finally {
      saving.value = false
    }
  }

  /**
   * 获取单个配置值
   */
  function getSettingValue(key: string, fallback: string = ''): string {
    const item = settingsList.value.find((s) => s.key === key)
    return item ? item.value : fallback
  }

  return {
    // State
    settingsList,
    loading,
    saving,
    // Getters
    apiConfig,
    cookieConfig,
    whisperConfig,
    searchConfig,
    profileConfig,
    hasApiKey,
    hasBilibiliCookie,
    // Actions
    fetchSettings,
    saveSettings,
    getSettingValue,
  }
})
