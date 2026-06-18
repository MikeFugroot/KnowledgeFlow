/**
 * 后台任务状态 Store
 * 任务列表、进度
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { get, post } from '@/api/client'
import { API_TASK } from '@/utils/constants'
import { WSMessageType } from '@/utils/constants'
import { wsClient, type WSMessage } from '@/api/websocket'

/** 后台任务 */
export interface BackgroundTask {
  id: number
  task_type: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  progress: number
  message: string
  result_json: string | null
  error: string | null
  created_at: string
  updated_at: string
}

/** 任务进度更新 payload */
export interface TaskProgressPayload {
  task_id: number
  task_type: string
  current: number
  total: number
  message: string
}

export const useTaskStore = defineStore('task', () => {
  // ==================== State ====================

  /** 任务列表 */
  const tasks = ref<BackgroundTask[]>([])

  /** 加载状态 */
  const loading = ref<boolean>(false)

  /** 任务进度映射（task_id -> progress） */
  const taskProgressMap = ref<Map<number, TaskProgressPayload>>(new Map())

  // ==================== Getters ====================

  /** 运行中的任务数 */
  const runningTaskCount = computed(() => {
    return tasks.value.filter((t) => t.status === 'running').length
  })

  /** 待处理的任务数 */
  const pendingTaskCount = computed(() => {
    return tasks.value.filter((t) => t.status === 'pending').length
  })

  /** 活跃任务数（运行中+待处理） */
  const activeTaskCount = computed(() => {
    return runningTaskCount.value + pendingTaskCount.value
  })

  /** 最近的失败任务 */
  const recentFailedTasks = computed(() => {
    return tasks.value
      .filter((t) => t.status === 'failed')
      .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
      .slice(0, 5)
  })

  // ==================== Actions ====================

  /**
   * 获取后台任务列表
   */
  async function fetchTasks(): Promise<void> {
    loading.value = true
    try {
      tasks.value = await get<BackgroundTask[]>(API_TASK.LIST)
    } catch (error) {
      console.error('获取任务列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取单个任务状态
   */
  async function fetchTaskDetail(id: number): Promise<BackgroundTask | null> {
    try {
      return await get<BackgroundTask>(API_TASK.DETAIL(id))
    } catch (error) {
      console.error('获取任务详情失败:', error)
      return null
    }
  }

  /**
   * 取消后台任务
   */
  async function cancelTask(id: number): Promise<boolean> {
    try {
      await post<null>(API_TASK.CANCEL(id))
      // 更新本地任务状态
      const task = tasks.value.find((t) => t.id === id)
      if (task) {
        task.status = 'cancelled'
      }
      return true
    } catch (error) {
      console.error('取消任务失败:', error)
      return false
    }
  }

  /**
   * 处理任务进度 WebSocket 消息
   */
  function handleTaskProgress(message: WSMessage): void {
    const payload = message.payload as TaskProgressPayload
    taskProgressMap.value.set(payload.task_id, payload)

    // 更新任务列表中对应项的进度
    const task = tasks.value.find((t) => t.id === payload.task_id)
    if (task) {
      task.progress = payload.total > 0 ? Math.round((payload.current / payload.total) * 100) : 0
      task.message = payload.message
      task.status = 'running'
    }
  }

  /**
   * 处理任务完成 WebSocket 消息
   */
  function handleTaskCompleted(message: WSMessage): void {
    const payload = message.payload as { task_id: number }
    const task = tasks.value.find((t) => t.id === payload.task_id)
    if (task) {
      task.status = 'completed'
      task.progress = 100
    }
    taskProgressMap.value.delete(payload.task_id)
  }

  /**
   * 处理任务失败 WebSocket 消息
   */
  function handleTaskFailed(message: WSMessage): void {
    const payload = message.payload as { task_id: number; error: string }
    const task = tasks.value.find((t) => t.id === payload.task_id)
    if (task) {
      task.status = 'failed'
      task.error = payload.error
    }
    taskProgressMap.value.delete(payload.task_id)
  }

  /**
   * 初始化 WebSocket 消息监听
   */
  function initWebSocketListeners(): void {
    wsClient.on(WSMessageType.TASK_PROGRESS, handleTaskProgress)
    wsClient.on(WSMessageType.TASK_COMPLETED, handleTaskCompleted)
    wsClient.on(WSMessageType.TASK_FAILED, handleTaskFailed)
  }

  return {
    // State
    tasks,
    loading,
    taskProgressMap,
    // Getters
    runningTaskCount,
    pendingTaskCount,
    activeTaskCount,
    recentFailedTasks,
    // Actions
    fetchTasks,
    fetchTaskDetail,
    cancelTask,
    handleTaskProgress,
    handleTaskCompleted,
    handleTaskFailed,
    initWebSocketListeners,
  }
})
