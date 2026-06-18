/**
 * 全局应用状态 Store
 * WebSocket 连接状态、全局 loading、通知
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { wsClient, type WSMessage } from '@/api/websocket'
import { WSMessageType } from '@/utils/constants'
import type { LogLevel } from '@/utils/constants'

/** 日志条目 */
export interface LogEntry {
  id: string
  level: LogLevel
  message: string
  timestamp: string
}

export const useAppStore = defineStore('app', () => {
  // ==================== State ====================

  /** 侧边栏是否折叠 */
  const sidebarCollapsed = ref<boolean>(false)

  /** 全局 loading */
  const globalLoading = ref<boolean>(false)

  /** globalLoading 文本 */
  const globalLoadingText = ref<string>('加载中...')

  /** WebSocket 连接状态 */
  const wsConnected = ref<boolean>(false)

  /** 后端 API 可用状态 */
  const apiAvailable = ref<boolean>(true)

  /** 日志条目列表 */
  const logEntries = ref<LogEntry[]>([])

  /** 日志最大条数（超出后删除最早的） */
  const maxLogEntries = ref<number>(1000)

  /** 是否自动滚动日志 */
  const autoScrollLog = ref<boolean>(true)

  // ==================== Getters ====================

  /** WebSocket 连接状态文本 */
  const wsStatusText = computed(() => {
    return wsConnected.value ? '已连接' : '未连接'
  })

  /** WebSocket 连接状态颜色 */
  const wsStatusColor = computed(() => {
    return wsConnected.value ? '#67c23a' : '#f56c6c'
  })

  /** API 状态文本 */
  const apiStatusText = computed(() => {
    return apiAvailable.value ? '在线' : '离线'
  })

  /** 日志条数 */
  const logCount = computed(() => logEntries.value.length)

  /** 最新日志 */
  const recentLogs = computed(() => {
    return logEntries.value.slice(-50)
  })

  // ==================== Actions ====================

  /**
   * 切换侧边栏折叠状态
   */
  function toggleSidebar(): void {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  /**
   * 设置全局 loading
   */
  function setGlobalLoading(loading: boolean, text: string = '加载中...'): void {
    globalLoading.value = loading
    globalLoadingText.value = text
  }

  /**
   * 添加日志条目
   */
  function addLog(level: LogLevel, message: string): void {
    const entry: LogEntry = {
      id: `log_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      level,
      message,
      timestamp: new Date().toISOString(),
    }
    logEntries.value.push(entry)

    // 超出最大条数时删除最早的
    if (logEntries.value.length > maxLogEntries.value) {
      logEntries.value = logEntries.value.slice(-maxLogEntries.value)
    }
  }

  /**
   * 清空日志
   */
  function clearLogs(): void {
    logEntries.value = []
  }

  /**
   * 初始化 WebSocket 连接和消息监听
   */
  function initWebSocket(): void {
    // 监听连接状态变化
    wsClient.onAny((message: WSMessage) => {
      // 根据消息类型分发到对应的 store 处理
      switch (message.type) {
        case WSMessageType.LOG: {
          const payload = message.payload as { level: LogLevel; message: string }
          addLog(payload.level, payload.message)
          break
        }
        default:
          break
      }
    })

    // 启动连接
    wsClient.connect()

    // 监控连接状态
    const checkInterval = setInterval(() => {
      wsConnected.value = wsClient.isConnected
    }, 2000)

    // 组件卸载时清理（在应用层面无法直接调用 onUnmounted，由 main.ts 统一管理）
    // 这里存储 interval ID 用于后续清理
    window.addEventListener('beforeunload', () => {
      clearInterval(checkInterval)
      wsClient.disconnect()
    })
  }

  /**
   * 检查 API 可用性
   */
  async function checkApiHealth(): Promise<void> {
    try {
      const response = await fetch('/api/settings')
      apiAvailable.value = response.ok
    } catch {
      apiAvailable.value = false
    }
  }

  return {
    // State
    sidebarCollapsed,
    globalLoading,
    globalLoadingText,
    wsConnected,
    apiAvailable,
    logEntries,
    maxLogEntries,
    autoScrollLog,
    // Getters
    wsStatusText,
    wsStatusColor,
    apiStatusText,
    logCount,
    recentLogs,
    // Actions
    toggleSidebar,
    setGlobalLoading,
    addLog,
    clearLogs,
    initWebSocket,
    checkApiHealth,
  }
})
