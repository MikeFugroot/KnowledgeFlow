/**
 * 网页导入相关 API
 * URL导入、收藏夹、书签、Cookie测试
 */
import { get, post } from './client'
import { API_WEBIMPORT } from '@/utils/constants'

// ==================== 类型定义 ====================

/** 单个 URL 导入参数 */
export interface UrlImportParams {
  url: string
}

/** 批量 URL 导入参数 */
export interface BatchUrlImportParams {
  urls: string[]
}

/** B 站收藏夹 */
export interface BilibiliFolder {
  folder_id: number
  title: string
  media_count: number
  intro: string
  is_public: boolean
}

/** B 站收藏夹导入参数 */
export interface BilibiliFavoritesParams {
  folder_id: number
  max_videos?: number
}

/** 书签导入参数 */
export interface BookmarkImportParams {
  bookmark_path: string
  max_links?: number
}

/** Cookie 测试结果 */
export interface CookieTestResult {
  success: boolean
  message: string
  username?: string
}

// ==================== API 方法 ====================

/**
 * 导入单个 URL
 */
export function importUrl(params: UrlImportParams): Promise<{ task_id: number }> {
  return post<{ task_id: number }>(API_WEBIMPORT.URL, params)
}

/**
 * 批量导入 URL 列表
 */
export function importUrls(params: BatchUrlImportParams): Promise<{ task_id: number }> {
  return post<{ task_id: number }>(API_WEBIMPORT.URLS, params)
}

/**
 * 获取 B 站收藏夹列表
 */
export function getBilibiliFolders(): Promise<BilibiliFolder[]> {
  return get<BilibiliFolder[]>(API_WEBIMPORT.BILIBILI_FOLDERS)
}

/**
 * 导入 B 站收藏夹
 */
export function importBilibiliFavorites(params: BilibiliFavoritesParams): Promise<{ task_id: number }> {
  return post<{ task_id: number }>(API_WEBIMPORT.BILIBILI_FAVORITES, params)
}

/**
 * 从书签 HTML 导入
 */
export function importBookmarks(params: BookmarkImportParams): Promise<{ task_id: number }> {
  return post<{ task_id: number }>(API_WEBIMPORT.BOOKMARKS, params)
}

/**
 * 测试 B 站 Cookie
 */
export function testBilibiliCookie(cookie: string): Promise<CookieTestResult> {
  return post<CookieTestResult>(API_WEBIMPORT.BILIBILI_TEST_COOKIE, { cookie })
}

/**
 * 测试小红书 Cookie
 */
export function testXiaohongshuCookie(cookie: string): Promise<CookieTestResult> {
  return post<CookieTestResult>(API_WEBIMPORT.XIAOHONGSHU_TEST_COOKIE, { cookie })
}
