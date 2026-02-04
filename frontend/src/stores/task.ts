/**
 * 任务状态管理
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Task, TaskStatus } from '@/types'
import { createMatchTask, getTaskStatus } from '@/api/tasks'
import { TaskWebSocket } from '@/api/websocket'

export const useTaskStore = defineStore('task', () => {
  const currentTask = ref<Task | null>(null)
  const isLoading = ref(false)

  const taskStatus = computed<TaskStatus>(() => currentTask.value?.status || 'pending')
  const taskProgress = computed<number>(() => currentTask.value?.progress || 0)
  const currentStep = computed<string>(() => currentTask.value?.current_step || '')

  async function createTask(excelFileId: string, jsonFileId: string): Promise<Task> {
    isLoading.value = true
    try {
      const task = await createMatchTask(excelFileId, jsonFileId)
      currentTask.value = task

      // 如果任务已经完成，不需要建立 WebSocket 连接
      if (task.status === 'completed' || task.status === 'failed') {
        return task
      }

      // 建立WebSocket连接（仅用于进行中的任务）
      try {
        const ws = new TaskWebSocket(task.task_id)
        ws.on('progress', (data: any) => {
          if (currentTask.value) {
            currentTask.value.progress = data.progress
            currentTask.value.current_step = data.message
            currentTask.value.status = data.status
          }
        })

        ws.connect()
      } catch (wsError) {
        console.warn('WebSocket connection failed, task may still complete:', wsError)
        // WebSocket 连接失败不影响任务创建
      }

      return task
    } catch (error) {
      throw error
    } finally {
      isLoading.value = false
    }
  }

  async function refreshTask(taskId: string): Promise<void> {
    const task = await getTaskStatus(taskId)
    currentTask.value = task
  }

  function resetTask(): void {
    currentTask.value = null
  }

  return {
    currentTask,
    isLoading,
    taskStatus,
    taskProgress,
    currentStep,
    createTask,
    refreshTask,
    resetTask
  }
})
