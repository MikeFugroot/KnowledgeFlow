import type { AxiosProgressEvent } from 'axios'
import { upload, post } from './client'
import { API_UPLOAD } from '@/utils/constants'

export interface UploadFileInfo {
  filename: string
  file_size: number
  doc_type: string
  file_path: string
}

export interface UploadResult {
  document_ids: number[]
  files: UploadFileInfo[]
}

export interface ProcessParams {
  document_ids: number[]
  provider?: 'qwen' | 'deepseek'
  use_rule_fallback?: boolean
}

export interface ProcessResult {
  task_id: number
  document_count: number
}

export function uploadFiles(
  files: File[],
  onProgress?: (percent: number) => void
): Promise<UploadResult> {
  const formData = new FormData()
  files.forEach((file) => {
    formData.append('files', file)
  })

  return upload<UploadResult>(API_UPLOAD.FILES, formData, {
    onUploadProgress: (event: AxiosProgressEvent) => {
      if (onProgress && event.total) {
        const percent = Math.round((event.loaded * 100) / event.total)
        onProgress(percent)
      }
    },
  })
}

export function processFiles(params: ProcessParams): Promise<ProcessResult> {
  return post<ProcessResult>(API_UPLOAD.PROCESS, params)
}

export function getDownloadUrl(id: number): string {
  return API_UPLOAD.DOWNLOAD(id)
}
