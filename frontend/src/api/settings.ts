/**
 * 配置相关 API
 * 获取、更新
 */
import { get, put } from './client'
import { API_SETTINGS } from '@/utils/constants'

// ==================== 类型定义 ====================

/** 配置项 */
export interface SettingItem {
  key: string
  value: string
  value_type: 'string' | 'number' | 'boolean' | 'json'
  description: string
  is_sensitive: boolean
}

/** 配置更新参数 */
export interface SettingsUpdateParams {
  configs: SettingItem[]
}

/** API 配置 */
export interface ApiConfig {
  provider: 'qwen' | 'deepseek'
  api_key: string
  model_name: string
}

/** Cookie 配置 */
export interface CookieConfig {
  bilibili_cookie: string
  xiaohongshu_cookie: string
}

/** Whisper 配置 */
export interface WhisperConfig {
  backend: 'faster-whisper' | 'openai-whisper'
  model: string
  language: string
}

/** 检索配置 */
export interface SearchConfig {
  embedding_model: string
  chunk_size: number
  chunk_overlap: number
  top_k: number
  candidate_k: number
}

/** 画像配置 */
export interface ProfileConfig {
  use_llm_profile: boolean
  max_items: number
  timeout: number
}

// ==================== API 方法 ====================

/**
 * 获取全部配置
 */
export function getSettings(): Promise<SettingItem[]> {
  return get<SettingItem[]>(API_SETTINGS.GET)
}

/**
 * 更新配置
 */
export function updateSettings(params: SettingsUpdateParams): Promise<SettingItem[]> {
  return put<SettingItem[]>(API_SETTINGS.UPDATE, params)
}
