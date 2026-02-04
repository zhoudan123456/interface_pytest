/**
 * API响应类型
 */
export interface ApiResponse<T = any> {
  code: number
  message: string
  data?: T
}

/**
 * 文件信息
 */
export interface FileInfo {
  file_id: string
  filename: string
  size: number
  path: string
}

/**
 * 任务状态
 */
export type TaskStatus = 'pending' | 'processing' | 'completed' | 'failed'

/**
 * 任务信息
 */
export interface Task {
  task_id: string
  status: TaskStatus
  progress: number
  current_step?: string
  created_at: string
  updated_at?: string
  result?: TaskResult
  error?: string
}

/**
 * 任务结果
 */
export interface TaskResult {
  report_path?: string
}

/**
 * WebSocket消息
 */
export interface WSMessage {
  type: 'progress' | 'log' | 'error' | 'completed'
  data: any
}

/**
 * 任务进度数据
 */
export interface TaskProgress {
  task_id?: string
  progress: number
  message: string
  status: TaskStatus
}
