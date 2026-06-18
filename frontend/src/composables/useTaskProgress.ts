import { computed, onMounted, onUnmounted, reactive, ref, watch, type Ref } from 'vue'
import { get } from '@/api/client'
import { wsClient, type WSMessage } from '@/api/websocket'
import { API_TASK, WSMessageType } from '@/utils/constants'
import type { BackgroundTask, TaskProgressPayload } from '@/stores/task'

const POLL_INTERVAL = 1000

export interface TaskProgressState {
  progress: number
  progressMessage: string
  isCompleted: boolean
  isFailed: boolean
  errorMessage: string
  current: number
  total: number
  isInProgress: boolean
  reset: () => void
  setManualProgress: (nextProgress: number, message?: string, nextCurrent?: number, nextTotal?: number) => void
  markFailed: (message: string) => void
  startListening: () => void
  stopListening: () => void
}

export function useTaskProgress(taskId: Ref<number | null>): TaskProgressState {
  const progress = ref(0)
  const progressMessage = ref('')
  const isCompleted = ref(false)
  const isFailed = ref(false)
  const errorMessage = ref('')
  const current = ref(0)
  const total = ref(0)

  const isInProgress = computed(() => {
    return progress.value > 0 && progress.value < 100 && !isCompleted.value && !isFailed.value
  })

  let cleanupFn: (() => void) | null = null
  let pollTimer: ReturnType<typeof setInterval> | null = null

  function applyTask(task: BackgroundTask): void {
    const pct = Math.max(0, Math.min(100, Math.round((task.progress || 0) * 100)))
    progress.value = pct
    current.value = pct
    total.value = 100
    progressMessage.value = task.message || statusText(task.status)
    isCompleted.value = task.status === 'completed'
    isFailed.value = task.status === 'failed'
    errorMessage.value = task.error || ''

    if (task.status === 'completed' || task.status === 'failed' || task.status === 'cancelled') {
      stopPolling()
    }
  }

  function applyPayload(payload: TaskProgressPayload): void {
    current.value = payload.current
    total.value = payload.total
    progress.value = payload.total > 0 ? Math.round((payload.current / payload.total) * 100) : 0
    progressMessage.value = payload.message
  }

  async function pollOnce(): Promise<void> {
    if (taskId.value === null) return
    try {
      const task = await get<BackgroundTask>(API_TASK.DETAIL(taskId.value))
      applyTask(task)
    } catch (error) {
      console.warn('获取任务进度失败:', error)
    }
  }

  function startPolling(): void {
    stopPolling()
    if (taskId.value === null) return
    void pollOnce()
    pollTimer = setInterval(() => {
      void pollOnce()
    }, POLL_INTERVAL)
  }

  function stopPolling(): void {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function startListening(): void {
    if (cleanupFn) return

    const unsubProgress = wsClient.on(WSMessageType.TASK_PROGRESS, (msg: WSMessage) => {
      const payload = msg.payload as TaskProgressPayload
      if (taskId.value !== null && payload.task_id === taskId.value) {
        applyPayload(payload)
      }
    })

    const unsubCompleted = wsClient.on(WSMessageType.TASK_COMPLETED, (msg: WSMessage) => {
      const payload = msg.payload as TaskProgressPayload
      if (taskId.value !== null && payload.task_id === taskId.value) {
        applyPayload({ ...payload, current: 100, total: 100 })
        isCompleted.value = true
        progressMessage.value = payload.message || '任务完成'
        stopPolling()
      }
    })

    const unsubFailed = wsClient.on(WSMessageType.TASK_FAILED, (msg: WSMessage) => {
      const payload = msg.payload as TaskProgressPayload & { error?: string }
      if (taskId.value !== null && payload.task_id === taskId.value) {
        isFailed.value = true
        errorMessage.value = payload.error || ''
        progressMessage.value = payload.message || '任务失败'
        stopPolling()
      }
    })

    cleanupFn = () => {
      unsubProgress()
      unsubCompleted()
      unsubFailed()
    }
  }

  function stopListening(): void {
    if (cleanupFn) {
      cleanupFn()
      cleanupFn = null
    }
  }

  function reset(): void {
    progress.value = 0
    progressMessage.value = ''
    isCompleted.value = false
    isFailed.value = false
    errorMessage.value = ''
    current.value = 0
    total.value = 0
    stopPolling()
  }

  function setManualProgress(nextProgress: number, message = '', nextCurrent?: number, nextTotal?: number): void {
    progress.value = Math.max(0, Math.min(100, Math.round(nextProgress)))
    progressMessage.value = message
    current.value = nextCurrent ?? progress.value
    total.value = nextTotal ?? 100
    isCompleted.value = false
    isFailed.value = false
    errorMessage.value = ''
  }

  function markFailed(message: string): void {
    isFailed.value = true
    errorMessage.value = message
    progressMessage.value = message
    stopPolling()
  }

  watch(taskId, (id) => {
    reset()
    if (id !== null) {
      progressMessage.value = '任务已提交'
      startPolling()
    }
  })

  onMounted(() => {
    startListening()
    if (taskId.value !== null) startPolling()
  })

  onUnmounted(() => {
    stopListening()
    stopPolling()
  })

  return reactive({
    progress,
    progressMessage,
    isCompleted,
    isFailed,
    errorMessage,
    current,
    total,
    isInProgress,
    reset,
    setManualProgress,
    markFailed,
    startListening,
    stopListening,
  }) as TaskProgressState
}

function statusText(status: BackgroundTask['status']): string {
  switch (status) {
    case 'pending':
      return '等待处理'
    case 'running':
      return '处理中'
    case 'completed':
      return '任务完成'
    case 'failed':
      return '任务失败'
    case 'cancelled':
      return '任务已取消'
    default:
      return ''
  }
}
