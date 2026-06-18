/**
 * WebSocket 连接管理
 * 支持自动重连、心跳检测、消息类型分发
 */
import { WSMessageType, WS_RECONNECT_INTERVAL, WS_MAX_RECONNECT_ATTEMPTS, WS_HEARTBEAT_INTERVAL } from '@/utils/constants'

/** WebSocket 消息格式 */
export interface WSMessage {
  type: string
  payload: unknown
  timestamp: string
}

/** 消息处理回调函数类型 */
export type MessageHandler = (message: WSMessage) => void

/**
 * WebSocket 客户端管理类
 * - 自动重连：连接断开后按指数退避策略重连
 * - 心跳检测：定时发送 ping 维持连接
 * - 消息分发：按消息类型注册处理函数
 */
export class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number
  private reconnectInterval: number
  private heartbeatInterval: number
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private handlers: Map<string, Set<MessageHandler>> = new Map()
  private globalHandlers: Set<MessageHandler> = new Set()
  private _isConnected: boolean = false
  private isManualClose: boolean = false

  constructor(url?: string) {
    this.url = url || import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws`
    this.maxReconnectAttempts = WS_MAX_RECONNECT_ATTEMPTS
    this.reconnectInterval = WS_RECONNECT_INTERVAL
    this.heartbeatInterval = WS_HEARTBEAT_INTERVAL
  }

  /** 连接状态 */
  get isConnected(): boolean {
    return this._isConnected
  }

  /**
   * 建立 WebSocket 连接
   */
  connect(): void {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      return
    }

    this.isManualClose = false
    this.ws = new WebSocket(this.url)

    this.ws.onopen = () => {
      this._isConnected = true
      this.reconnectAttempts = 0
      this.startHeartbeat()
      console.log('[WebSocket] 连接成功')
    }

    this.ws.onmessage = (event: MessageEvent) => {
      try {
        const message: WSMessage = JSON.parse(event.data as string)

        // 处理 pong 响应
        if (message.type === WSMessageType.PONG) {
          return
        }

        // 分发到全局处理器
        this.globalHandlers.forEach((handler) => {
          try {
            handler(message)
          } catch (err) {
            console.error('[WebSocket] 全局处理器异常:', err)
          }
        })

        // 按类型分发到特定处理器
        const typeHandlers = this.handlers.get(message.type)
        if (typeHandlers) {
          typeHandlers.forEach((handler) => {
            try {
              handler(message)
            } catch (err) {
              console.error(`[WebSocket] 类型处理器(${message.type})异常:`, err)
            }
          })
        }
      } catch (err) {
        console.error('[WebSocket] 消息解析失败:', err)
      }
    }

    this.ws.onclose = () => {
      this._isConnected = false
      this.stopHeartbeat()
      console.log('[WebSocket] 连接关闭')

      // 非手动关闭时自动重连
      if (!this.isManualClose) {
        this.scheduleReconnect()
      }
    }

    this.ws.onerror = (error) => {
      console.error('[WebSocket] 连接错误:', error)
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isManualClose = true
    this.stopHeartbeat()
    this.clearReconnectTimer()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
    this._isConnected = false
  }

  /**
   * 发送消息
   * @param type - 消息类型
   * @param payload - 消息负载
   */
  send(type: string, payload: unknown = {}): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.warn('[WebSocket] 连接未就绪，无法发送消息')
      return
    }

    const message: WSMessage = {
      type,
      payload,
      timestamp: new Date().toISOString(),
    }

    this.ws.send(JSON.stringify(message))
  }

  /**
   * 注册消息处理器（按类型）
   * @param type - 消息类型
   * @param handler - 处理回调
   * @returns 取消注册的函数
   */
  on(type: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(type)) {
      this.handlers.set(type, new Set())
    }
    this.handlers.get(type)!.add(handler)

    // 返回取消注册函数
    return () => {
      const typeHandlers = this.handlers.get(type)
      if (typeHandlers) {
        typeHandlers.delete(handler)
        if (typeHandlers.size === 0) {
          this.handlers.delete(type)
        }
      }
    }
  }

  /**
   * 注册全局消息处理器（接收所有消息）
   * @param handler - 处理回调
   * @returns 取消注册的函数
   */
  onAny(handler: MessageHandler): () => void {
    this.globalHandlers.add(handler)
    return () => {
      this.globalHandlers.delete(handler)
    }
  }

  /**
   * 启动心跳定时器
   */
  private startHeartbeat(): void {
    this.stopHeartbeat()
    this.heartbeatTimer = setInterval(() => {
      this.send(WSMessageType.PING)
    }, this.heartbeatInterval)
  }

  /**
   * 停止心跳定时器
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }

  /**
   * 安排重连（指数退避）
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.warn(`[WebSocket] 已达最大重连次数(${this.maxReconnectAttempts})，停止重连`)
      return
    }

    // 指数退避：间隔随重连次数增长
    const delay = Math.min(
      this.reconnectInterval * Math.pow(1.5, this.reconnectAttempts),
      30000 // 最大 30 秒
    )

    console.log(`[WebSocket] 将在 ${Math.round(delay / 1000)}s 后重连 (第 ${this.reconnectAttempts + 1} 次)`)

    this.reconnectTimer = setTimeout(() => {
      this.reconnectAttempts++
      this.connect()
    }, delay)
  }

  /**
   * 清除重连定时器
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
  }
}

/** 全局 WebSocket 客户端单例 */
export const wsClient = new WebSocketClient()
