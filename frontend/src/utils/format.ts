/**
 * 格式化工具函数
 * 包含日期、文件大小、数字等格式化方法
 */
import dayjs from 'dayjs'
import relativeTime from 'dayjs/plugin/relativeTime'
import 'dayjs/locale/zh-cn'

// 配置 dayjs 中文语言包和相对时间插件
dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

/**
 * 格式化日期时间
 * @param dateStr - ISO 日期字符串或时间戳
 * @param format - dayjs 格式化模板，默认 'YYYY-MM-DD HH:mm:ss'
 * @returns 格式化后的日期字符串
 */
export function formatDateTime(
  dateStr: string | number | Date,
  format: string = 'YYYY-MM-DD HH:mm:ss'
): string {
  if (!dateStr) return '-'
  return dayjs(dateStr).format(format)
}

/**
 * 格式化为相对时间（如 "3 小时前"）
 * @param dateStr - ISO 日期字符串或时间戳
 * @returns 相对时间字符串
 */
export function formatRelativeTime(dateStr: string | number | Date): string {
  if (!dateStr) return '-'
  return dayjs(dateStr).fromNow()
}

/**
 * 格式化文件大小
 * @param bytes - 文件字节数
 * @param decimals - 保留小数位数，默认 2
 * @returns 格式化后的文件大小字符串（如 "1.50 MB"）
 */
export function formatFileSize(bytes: number | undefined, decimals: number = 2): string {
  if (bytes === undefined || bytes === null || bytes === 0) return '0 B'
  const k = 1024
  const dm = Math.max(0, decimals)
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(dm))} ${sizes[i]}`
}

/**
 * 格式化数字（千分位）
 * @param num - 数字
 * @returns 带千分位的字符串（如 "1,234"）
 */
export function formatNumber(num: number | undefined): string {
  if (num === undefined || num === null) return '0'
  return num.toLocaleString('zh-CN')
}

/**
 * 格式化百分比
 * @param value - 数值（0-1 之间）
 * @param decimals - 保留小数位数，默认 1
 * @returns 百分比字符串（如 "85.5%"）
 */
export function formatPercent(value: number | undefined, decimals: number = 1): string {
  if (value === undefined || value === null) return '0%'
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * 截断文本
 * @param text - 原始文本
 * @param maxLength - 最大长度，默认 100
 * @param suffix - 截断后缀，默认 "..."
 * @returns 截断后的文本
 */
export function truncateText(text: string | undefined, maxLength: number = 100, suffix: string = '...'): string {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength) + suffix
}

/**
 * 格式化进度（0-100 整数）
 * @param current - 当前进度
 * @param total - 总数
 * @returns 进度百分比整数
 */
export function formatProgress(current: number, total: number): number {
  if (total <= 0) return 0
  return Math.min(Math.round((current / total) * 100), 100)
}

/**
 * 格式化持续时间（秒 → 可读字符串）
 * @param seconds - 秒数
 * @returns 格式化后的时间字符串（如 "2分30秒"）
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)}秒`
  const minutes = Math.floor(seconds / 60)
  const remainSeconds = Math.round(seconds % 60)
  if (minutes < 60) return `${minutes}分${remainSeconds}秒`
  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60
  return `${hours}小时${remainMinutes}分`
}
