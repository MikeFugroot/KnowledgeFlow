/**
 * 检索相关 API
 * 搜索、索引构建、索引状态
 */
import { get, post } from './client'
import { API_SEARCH } from '@/utils/constants'

// ==================== 类型定义 ====================

/** 搜索请求参数 */
export interface SearchParams {
  query: string
  top_k?: number
}

/** 搜索结果项 */
export interface SearchResult {
  rank: number
  doc_title: string
  doc_type: string
  source: string
  location: string
  section_title: string
  chunk_text: string
  score: number
  dense_score: number
  lexical_score: number
  match_reason: string
  hit_terms: string[]
  document_id: number | null
}

/** 搜索响应 */
export interface SearchResponse {
  query: string
  total: number
  results: SearchResult[]
}

/** 索引状态 */
export interface IndexStatus {
  is_ready: boolean
  total_chunks: number
  total_documents: number
  last_built_at: string | null
  embedding_model: string
}

/** 索引构建请求 */
export interface IndexBuildParams {
  force?: boolean
}

// ==================== API 方法 ====================

/**
 * 语义模糊查询
 */
export function search(params: SearchParams): Promise<SearchResponse> {
  return post<SearchResponse>(API_SEARCH.QUERY, params)
}

/**
 * 触发索引构建
 */
export function buildIndex(params: IndexBuildParams = {}): Promise<{ task_id: number }> {
  return post<{ task_id: number }>(API_SEARCH.INDEX_BUILD, params)
}

/**
 * 获取索引状态
 */
export function getIndexStatus(): Promise<IndexStatus> {
  return get<IndexStatus>(API_SEARCH.INDEX_STATUS)
}
