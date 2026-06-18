/**
 * 仪表盘相关 API
 * 统计数据
 */
import { get } from './client'
import { API_DASHBOARD } from '@/utils/constants'

// ==================== 类型定义 ====================

/** 仪表盘统计数据 */
export interface DashboardStats {
  total_documents: number
  total_sections: number
  total_tags: number
  category_distribution: Record<string, number>
  type_distribution: Record<string, number>
  recent_documents: RecentDocument[]
  index_ready: boolean
  has_profile: boolean
}

/** 最近文档 */
export interface RecentDocument {
  id?: number
  title?: string
  doc_type?: string
  category?: string
  created_at?: string
  [key: string]: unknown  // Dict[str, Any] 可能有其他字段
}

// ==================== API 方法 ====================

/**
 * 获取仪表盘统计数据
 */
export function getDashboardStats(): Promise<DashboardStats> {
  return get<DashboardStats>(API_DASHBOARD.STATS)
}
