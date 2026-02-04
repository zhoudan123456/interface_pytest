/**
 * 任务API
 */
import api from './index'
import type { ApiResponse, Task } from '@/types'

export async function createMatchTask(excelFileId: string, jsonFileId: string): Promise<Task> {
  const formData = new FormData()
  formData.append('excel_file_id', excelFileId)
  formData.append('json_file_id', jsonFileId)

  const response = await api.post<any>('/tasks/match', formData)
  return response.data
}

export async function getTaskStatus(taskId: string): Promise<Task> {
  const response = await api.get<Task>(`/tasks/${taskId}`)
  return response
}

export async function listTasks(page: number = 1, pageSize: number = 10): Promise<Task[]> {
  const response = await api.get<Task[]>(`/tasks?page=${page}&page_size=${pageSize}`)
  return response
}
