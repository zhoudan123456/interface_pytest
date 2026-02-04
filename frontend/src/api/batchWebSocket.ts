/**
 * 批量任务WebSocket管理
 */
import type { BatchTask, CaseResult } from './batch'

export interface BatchWSMessage {
  type: 'init' | 'progress' | 'case_update' | 'complete' | 'ping' | 'pong'
  data: any
}

export interface BatchProgressData {
  task_id: string
  status: string
  progress: number
  current_step: string
  total: number
  success: number
  failed: number
}

export interface CaseUpdateData {
  task_id: string
  case_name: string
  status: string
  step1_output: string | null
  step2_output: string | null
  error: string | null
}

export class BatchWebSocket {
  private ws: WebSocket | null = null
  private taskId: string
  private handlers: Map<string, (data: any) => void> = new Map()
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5
  private reconnectTimer: number | null = null
  private isManualClose = false

  constructor(taskId: string) {
    this.taskId = taskId
  }

  connect(): void {
    this.isManualClose = false

    // 使用相对路径
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/api/v1/batch/ws/${this.taskId}`
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('Batch WebSocket connected')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      try {
        const message: BatchWSMessage = JSON.parse(event.data)
        const handler = this.handlers.get(message.type)
        if (handler) {
          handler(message.data)
        }
      } catch (error) {
        console.error('Batch WebSocket message error:', error)
      }
    }

    this.ws.onerror = (error) => {
      console.error('Batch WebSocket error:', error)
    }

    this.ws.onclose = () => {
      console.log('Batch WebSocket closed')
      if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++
        this.reconnectTimer = window.setTimeout(() => {
          console.log(`Batch WebSocket reconnecting... Attempt ${this.reconnectAttempts}`)
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
    this.isManualClose = true
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  // 便捷方法
  onProgress(handler: (data: BatchProgressData) => void): void {
    this.on('progress', handler)
  }

  onCaseUpdate(handler: (data: CaseUpdateData) => void): void {
    this.on('case_update', handler)
  }

  onComplete(handler: (data: BatchTask) => void): void {
    this.on('complete', handler)
  }

  onInit(handler: (data: BatchTask) => void): void {
    this.on('init', handler)
  }
}
