/**
 * 画像相关 API
 * 获取、刷新、状态
 */
import { get, post } from './client'
import { API_PROFILE } from '@/utils/constants'

// ==================== 类型定义 ====================

/** 标签项（组件通用格式） */
export interface TagItem {
  name: string
  count: number
}

/** 标签排名项（后端实际返回格式） */
export interface TagRankingItem {
  tag: string
  count: number
}

/** 主题分布项（组件通用格式） */
export interface ThemeItem {
  category: string
  count: number
  percentage: number
}

/** 知识聚类项（后端规则画像格式） */
export interface ClusterItem {
  cluster: string
  score: number
  related_items: string[]
}

/** 知识聚类项（组件通用格式，适配 LLM 和规则画像） */
export interface ClusterDisplayItem {
  name: string
  description: string
  keywords: string[]
  next_step: string
}

/** 知识缺口项（组件通用格式，雷达图用） */
export interface GapItem {
  area: string
  current_level: number
  importance: number
}

/** 学习路径项（组件通用格式） */
export interface PathItem {
  step: number
  title: string
  description: string
  resources: string[]
}

/** 时间线条目（后端实际返回格式） */
export interface TimelineItem {
  date: string
  title: string
  category: string
  tags: string[]
  doc_type?: string  // 可选，规则画像不含此字段
}

/** 画像总览（后端实际返回格式） */
export interface ProfileOverview {
  total_documents: number
  knowledge_units: number
  total_chars: number
  main_focus: string
  top_tags: string[]
  dominant_type: string
}

/** LLM 画像数据 */
export interface LlmProfile {
  profile_summary?: string
  main_focus?: string
  learning_stage?: string
  theme_insights?: string[]
  knowledge_clusters?: Array<{
    cluster: string
    description: string
    related_keywords: string[]
    suggested_next_step: string
  }>
  knowledge_gaps?: string[]
  learning_path?: string[]
  growth_suggestions?: string[]
  dynamic_profile_notes?: string[]
}

/** 画像 JSON 结构（后端 profile_json 字段的实际格式） */
export interface ProfileJson {
  generated_by?: string
  summary?: string
  learning_stage?: string
  overview?: ProfileOverview
  theme_distribution?: Record<string, number>
  type_distribution?: Record<string, number>
  method_distribution?: Record<string, number>
  tag_ranking?: TagRankingItem[]
  knowledge_clusters?: ClusterItem[]
  learning_timeline?: TimelineItem[]
  knowledge_gaps?: string[]
  learning_path?: string[]
  growth_suggestions?: string[]
  llm_profile?: LlmProfile
}

/** 知识画像数据（后端 API 响应） */
export interface KnowledgeProfileData {
  id: number
  generated_by: string
  profile_json: ProfileJson
  total_documents: number
  knowledge_units: number
  main_focus: string
  created_at: string
}

/** 画像状态 */
export interface ProfileStatus {
  is_generating: boolean
  has_profile: boolean
  last_generated_at: string | null
}

// ==================== API 方法 ====================

/**
 * 获取知识画像
 */
export function getProfile(): Promise<KnowledgeProfileData> {
  return get<KnowledgeProfileData>(API_PROFILE.GET)
}

/**
 * 手动刷新画像
 */
export function refreshProfile(): Promise<{ task_id: number }> {
  return post<{ task_id: number }>(API_PROFILE.REFRESH)
}

/**
 * 获取画像生成状态
 */
export function getProfileStatus(): Promise<ProfileStatus> {
  return get<ProfileStatus>(API_PROFILE.STATUS)
}
