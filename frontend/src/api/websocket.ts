/**
 * WebSocket管理
 */
import type { WSMessage, TaskProgress } from '@/types'

export class TaskWebSocket {
  private ws: WebSocket | null = null
  private taskId: string
  private handlers: Map<string, (data: any) => void> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 3

  constructor(taskId: string) {
    this.taskId = taskId
  }

  connect(): void {
    // 使用相对路径，这样会通过 Vite 代理连接到后端
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/ws/${this.taskId}`
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      // 订阅任务
      this.send({ type: 'subscribe', data: { task_id: this.taskId } })
    }

    this.ws.onmessage = (event) => {
      try {
        const message: WSMessage = JSON.parse(event.data)
        const handler = this.handlers.get(message.type)
        if (handler) {
          handler(message.data)
        }
      } catch (error) {
        console.error('WebSocket message error:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    this.ws.onclose = () => {
      console.log('WebSocket closed')
      // 自动重连
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++
        setTimeout(() => {
          console.log(`Reconnecting... Attempt ${this.reconnectAttempts}`)
          this.connect()
        }, 3000)
      }
    }
  }

  on(event: string, handler: (data: any) => void): void {
    this.handlers.set(event, handler)
  }

  off(event: string): void {
    this.handlers.delete(event)
  }

  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message))
    }
  }

  disconnect(): void {
    if (this.ws) {
      this.send({ type: 'unsubscribe', data: {} })
      this.ws.close()
      this.ws = null
    }
  }
}
