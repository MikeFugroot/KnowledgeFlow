/**
 * 文档相关 API
 * CRUD、导出、重新整理
 */
import { get, post, put, del } from './client'
import { API_DOCUMENT } from '@/utils/constants'
import type { PaginatedData } from './client'

// ==================== 类型定义 ====================

/** 文档整理结果 */
export interface Document {
  id: number
  title: string
  original_title: string
  doc_type: string
  source_path: string
  source_url: string
  char_count: number
  ai_file_reading: boolean
  method: string
  model: string
  category: string
  summary: string
  overall_evaluation: string
  title_suggestion: string
  reason: string
  search_text: string
  tags: TagResponse[]
  sections: DocumentSection[]
  created_at: string
  updated_at: string
}

/** 标签 */
export interface TagResponse {
  id: number
  name: string
}

/** 文档章节 */
export interface DocumentSection {
  id: number
  section_title: string
  location_hint: string
  summary: string
  search_text: string
  created_at: string
}

/** 文档列表查询参数 */
export interface DocumentListParams {
  page?: number
  page_size?: number
  category?: string
  tag?: string
  doc_type?: string
  keyword?: string
}

/** 文档更新参数 */
export interface DocumentUpdateParams {
  title?: string
  category?: string
  tags?: string[]
  summary?: string
}

/** 批量删除参数 */
export interface BatchDeleteParams {
  ids: number[]
}

/** 导出参数 */
export interface ExportParams {
  ids?: number[]
  format?: 'json'
}

/** 文件 URL 响应 */
export interface FileUrlResponse {
  document_id: number
  doc_type: string
  title: string
  source_path: string
  source_url: string
  file_url: string | null
  location: string | null
  page_number: number | null
  video_start: number | null
  video_end: number | null
  is_available: boolean
}

/** 本地打开文件响应 */
export interface OpenLocallyResponse {
  opened: boolean
  method: string  // "local_file" | "url"
  path?: string
  url?: string
  doc_type: string
  location?: string | null
  page_number?: number | null
  video_start?: number | null
  video_end?: number | null
  sumatra_command?: string[] | Record<string, string[] | null>
}

// ==================== API 方法 ====================

/**
 * 获取整理结果列表（分页+筛选）
 */
export function getDocumentList(params: DocumentListParams = {}): Promise<PaginatedData<Document>> {
  return get<PaginatedData<Document>>(API_DOCUMENT.LIST, params as Record<string, unknown>)
}

/**
 * 获取单条整理结果详情
 */
export function getDocumentDetail(id: number): Promise<Document> {
  return get<Document>(API_DOCUMENT.DETAIL(id))
}

/**
 * 获取文档文件的访问 URL 和定位信息
 */
export function getDocumentFileUrl(id: number, location?: string): Promise<FileUrlResponse> {
  const params: Record<string, unknown> = {}
  if (location) params.location = location
  return get<FileUrlResponse>(API_DOCUMENT.FILE_URL(id), params)
}

/**
 * 本地打开文件（用系统默认应用）
 */
export function openDocumentLocally(id: number, location?: string): Promise<OpenLocallyResponse> {
  const params: Record<string, unknown> = {}
  if (location) params.location = location
  return post<OpenLocallyResponse>(API_DOCUMENT.OPEN_LOCALLY(id), undefined, { params })
}

/**
 * 更新整理结果
 */
export function updateDocument(id: number, data: DocumentUpdateParams): Promise<Document> {
  return put<Document>(API_DOCUMENT.DETAIL(id), data)
}

/**
 * 删除整理结果
 */
export function deleteDocument(id: number): Promise<void> {
  return del<void>(API_DOCUMENT.DETAIL(id))
}

/**
 * 批量删除整理结果
 */
export function batchDeleteDocuments(ids: number[]): Promise<void> {
  return post<void>(API_DOCUMENT.BATCH_DELETE, { ids } as BatchDeleteParams)
}

/**
 * 重新整理单条文档
 */
export function reorganizeDocument(id: number, provider?: string): Promise<{ task_id: number }> {
  return post<{ task_id: number }>(API_DOCUMENT.REORGANIZE(id), provider ? { provider } : {})
}

/**
 * 导出整理结果为 JSON
 */
export function exportDocuments(params: ExportParams = {}): Promise<Blob> {
  return post<Blob>(API_DOCUMENT.EXPORT, params, { responseType: 'blob' } as never)
}
