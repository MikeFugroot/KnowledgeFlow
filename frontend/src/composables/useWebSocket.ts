/**
 * WebSocket 组合式函数
 * 提供 WebSocket 连接管理、订阅、消息处理的 Vue 响应式接口
 */
import { onMounted, onUnmounted, ref } from 'vue'
import { wsClient, type WSMessage } from '@/api/websocket'
import { useAppStore } from '@/stores/app'
import { useTaskStore } from '@/stores/task'
import { useSearchStore } from '@/stores/search'
import { useProfileStore } from '@/stores/profile'
import { WSMessageType } from '@/utils/constants'

/** WebSocket 连接状态（响应式） */
export function useWebSocket() {
  const appStore = useAppStore()
  const taskStore = useTaskStore()
  const searchStore = useSearchStore()
  const profileStore = useProfileStore()

  const isConnected = ref(false)

  /** 清理函数列表 */
  const cleanupFns: (() => void)[] = []

  /**
   * 初始化 WebSocket 连接和所有消息处理器
   */
  function init(): void {
    // 连接 WebSocket
    wsClient.connect()

    // 注册各类型消息处理器

    // 任务进度
    const unsubProgress = wsClient.on(WSMessageType.TASK_PROGRESS, (msg: WSMessage) => {
      taskStore.handleTaskProgress(msg)
    })
    cleanupFns.push(unsubProgress)

    // 任务完成
    const unsubCompleted = wsClient.on(WSMessageType.TASK_COMPLETED, (msg: WSMessage) => {
      taskStore.handleTaskCompleted(msg)
    })
    cleanupFns.push(unsubCompleted)

    // 任务失败
    const unsubFailed = wsClient.on(WSMessageType.TASK_FAILED, (msg: WSMessage) => {
      taskStore.handleTaskFailed(msg)
    })
    cleanupFns.push(unsubFailed)

    // 日志
    const unsubLog = wsClient.on(WSMessageType.LOG, (msg: WSMessage) => {
      const payload = msg.payload as { level: string; message: string }
      appStore.addLog(payload.level as 'INFO' | 'WARNING' | 'ERROR', payload.message)
    })
    cleanupFns.push(unsubLog)

    // 索引状态
    const unsubIndex = wsClient.on(WSMessageType.INDEX_STATUS, (msg: WSMessage) => {
      searchStore.updateIndexStatus(msg.payload as {
        is_ready: boolean
        total_chunks: number
        total_documents: number
        embedding_model: string
      })
    })
    cleanupFns.push(unsubIndex)

    // 画像状态
    const unsubProfile = wsClient.on(WSMessageType.PROFILE_STATUS, (msg: WSMessage) => {
      profileStore.updateProfileStatus(msg.payload as {
        is_generating: boolean
        has_profile: boolean
      })
    })
    cleanupFns.push(unsubProfile)

    // 定时更新连接状态
    const statusInterval = setInterval(() => {
      isConnected.value = wsClient.isConnected
      appStore.wsConnected = wsClient.isConnected
    }, 2000)
    cleanupFns.push(() => clearInterval(statusInterval))
  }

  /**
   * 断开连接并清理所有监听器
   */
  function cleanup(): void {
    cleanupFns.forEach((fn) => fn())
    cleanupFns.length = 0
  }

  /**
   * 订阅特定类型的消息
   * @param type - 消息类型
   * @param handler - 处理函数
   * @returns 取消订阅函数
   */
  function subscribe(type: string, handler: (msg: WSMessage) => void): () => void {
    const unsub = wsClient.on(type, handler)
    cleanupFns.push(unsub)
    return unsub
  }

  /**
   * 发送消息
   */
  function send(type: string, payload: unknown = {}): void {
    wsClient.send(type, payload)
  }

  // 自动在组件挂载/卸载时管理生命周期
  onMounted(() => {
    init()
  })

  onUnmounted(() => {
    cleanup()
  })

  return {
    isConnected,
    init,
    cleanup,
    subscribe,
    send,
  }
}
