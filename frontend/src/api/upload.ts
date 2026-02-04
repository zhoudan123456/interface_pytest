/**
 * 文件上传API
 */
import axios from 'axios'
import type { ApiResponse, FileInfo } from '@/types'

export async function uploadFile(file: File, type: 'excel' | 'json' | 'pdf'): Promise<ApiResponse<FileInfo>> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('type', type)

  const response = await axios.post<ApiResponse<FileInfo>>('/api/v1/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })

  return response.data
}

/**
 * 步骤1提取文件信息
 */
export interface ExtractFileInfo {
  filename: string
  size: number
  modified_time: number
  type: 'check_point' | 'bid_info'
}

/**
 * 获取步骤1生成的文件列表
 */
export async function getExtractionFiles(): Promise<ApiResponse<ExtractFileInfo[]>> {
  const response = await axios.get<ApiResponse<ExtractFileInfo[]>>('/api/v1/tasks/extract/files')
  return response.data
}

/**
 * 下载步骤1生成的JSON文件
 */
export function downloadExtractionFile(filename: string): void {
  const url = `/api/v1/tasks/extract/download/${filename}`
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

/**
 * 步骤2验证报告文件信息
 */
export interface ReportFileInfo {
  filename: string
  size: number
  modified_time: number
  type: 'validation_report'
}

/**
 * 获取步骤2生成的报告文件列表
 */
export async function getReportFiles(): Promise<ApiResponse<ReportFileInfo[]>> {
  const response = await axios.get<ApiResponse<ReportFileInfo[]>>('/api/v1/reports/files')
  return response.data
}

/**
 * 下载步骤2生成的报告文件
 */
export function downloadReportFile(filename: string): void {
  const url = `/api/v1/reports/download/${filename}`
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
