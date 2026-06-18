<template>
  <div class="file-import-page">
    <div class="mb-6">
      <h3 class="text-base font-semibold text-gray-200 mb-3">上传文件</h3>
      <FileUploader @select="handleFilesSelected" :disabled="uploading || processing" />
    </div>

    <div v-if="fileList.length > 0" class="mb-6">
      <div class="flex items-center justify-between mb-3">
        <h3 class="text-base font-semibold text-gray-200">
          已选文件 ({{ fileList.length }})
        </h3>
        <el-button text size="small" @click="clearFileList" :disabled="processing">
          清空列表
        </el-button>
      </div>
      <div class="file-list space-y-2 max-h-60 overflow-auto">
        <div
          v-for="file in fileList"
          :key="file.name"
          class="file-item flex items-center gap-3 py-2 px-3 rounded-lg bg-gray-800/30 border border-gray-700/30"
        >
          <el-icon :size="18" class="flex-shrink-0" :class="getFileIconColor(file.ext)">
            <component :is="getFileIcon(file.ext)" />
          </el-icon>
          <div class="flex-1 min-w-0">
            <div class="text-sm text-gray-300 truncate">{{ file.name }}</div>
          </div>
          <span class="text-xs text-gray-500 flex-shrink-0">{{ formatFileSize(file.size) }}</span>
          <el-tag :type="getFileStatusType(file.status)" size="small" effect="plain">
            {{ getFileStatusLabel(file.status) }}
          </el-tag>
          <el-button v-if="!processing" text size="small" type="danger" @click="removeFile(file.name)">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <div v-if="fileList.length > 0" class="config-section mb-6 rounded-xl border border-gray-700/40 bg-gray-800/20 p-5">
      <h3 class="text-sm font-semibold text-gray-300 mb-3">处理配置</h3>
      <div class="flex flex-wrap items-center gap-6">
        <div class="flex items-center gap-2">
          <span class="text-sm text-gray-400">API Provider:</span>
          <el-select v-model="provider" size="default" class="w-40" :disabled="processing">
            <el-option label="Qwen (通义千问)" value="qwen" />
            <el-option label="DeepSeek" value="deepseek" />
          </el-select>
        </div>
        <div class="flex items-center gap-2">
          <el-switch v-model="useRuleFallback" :disabled="processing" />
          <span class="text-sm text-gray-400">规则兜底（API 不可用时）</span>
        </div>
      </div>
    </div>

    <div v-if="fileList.length > 0" class="flex gap-3 mb-4">
      <el-button
        type="primary"
        size="large"
        :loading="uploading || processing"
        :disabled="uploading || processing"
        @click="handleProcess"
      >
        {{ processing ? '处理中...' : uploading ? '上传中...' : '开始处理' }}
      </el-button>
    </div>

    <TaskProgress
      :progress="taskProgress.progress"
      :progress-message="taskProgress.progressMessage"
      :is-completed="taskProgress.isCompleted"
      :is-failed="taskProgress.isFailed"
      :error-message="taskProgress.errorMessage"
      :current="taskProgress.current"
      :total="taskProgress.total"
    />

    <el-result
      v-if="taskProgress.isCompleted"
      icon="success"
      title="处理完成"
      sub-title="文件已成功处理并添加到知识库"
      class="mt-4"
    >
      <template #extra>
        <el-button type="primary" @click="$router.push('/documents')">查看整理结果</el-button>
      </template>
    </el-result>
  </div>
</template>

<script setup lang="ts">
import { ref, type Ref } from 'vue'
import {
  Document, VideoPlay, Headset, Tickets, DataBoard, Close,
} from '@element-plus/icons-vue'
import { uploadFiles, processFiles } from '@/api/upload'
import { useTaskProgress } from '@/composables/useTaskProgress'
import { notifySuccess, notifyError } from '@/composables/useNotification'
import { formatFileSize } from '@/utils/format'
import FileUploader from '@/components/common/FileUploader.vue'
import TaskProgress from '@/components/common/TaskProgress.vue'

interface FileItem {
  name: string
  size: number
  ext: string
  file: File
  status: 'pending' | 'uploading' | 'uploaded' | 'error'
}

const fileList = ref<FileItem[]>([])
const provider = ref<'qwen' | 'deepseek'>('qwen')
const useRuleFallback = ref(true)
const uploading = ref(false)
const processing = ref(false)
const taskIdRef: Ref<number | null> = ref(null)
const taskProgress = useTaskProgress(taskIdRef)

function handleFilesSelected(files: File[]): void {
  for (const file of files) {
    if (fileList.value.some((f) => f.name === file.name && f.size === file.size)) continue

    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    fileList.value.push({
      name: file.name,
      size: file.size,
      ext,
      file,
      status: 'pending',
    })
  }
}

function removeFile(name: string): void {
  fileList.value = fileList.value.filter((f) => f.name !== name)
}

function clearFileList(): void {
  fileList.value = []
  taskProgress.reset()
}

async function handleProcess(): Promise<void> {
  if (fileList.value.length === 0) return

  taskProgress.reset()
  taskIdRef.value = null
  uploading.value = true
  taskProgress.setManualProgress(1, '准备上传文件...', 0, 100)

  try {
    const rawFiles = fileList.value.map((f) => f.file)
    fileList.value.forEach((f) => { f.status = 'uploading' })

    const uploadResult = await uploadFiles(rawFiles, (percent) => {
      const visiblePercent = Math.max(1, Math.min(99, percent))
      taskProgress.setManualProgress(visiblePercent, `上传中... ${visiblePercent}%`, visiblePercent, 100)
    })

    fileList.value.forEach((f) => { f.status = 'uploaded' })
    uploading.value = false

    processing.value = true
    taskProgress.setManualProgress(1, '上传完成，正在创建处理任务...', 0, 0)

    const processResult = await processFiles({
      document_ids: uploadResult.document_ids,
      provider: provider.value,
      use_rule_fallback: useRuleFallback.value,
    })

    taskIdRef.value = processResult.task_id
    taskProgress.setManualProgress(1, '处理任务已创建，等待进度更新...', 0, 0)
    notifySuccess(`处理任务已提交，任务ID: ${processResult.task_id}`)
  } catch (error: unknown) {
    fileList.value.forEach((f) => {
      if (f.status === 'uploading') f.status = 'error'
    })

    const msg = error instanceof Error ? error.message : '文件处理失败'
    notifyError(msg)
    taskProgress.markFailed(msg)
  } finally {
    uploading.value = false
    processing.value = false
  }
}

function getFileIcon(ext: string) {
  const iconMap: Record<string, typeof Document> = {
    '.pdf': Document,
    '.docx': Document,
    '.doc': Document,
    '.txt': Tickets,
    '.md': Tickets,
    '.mp4': VideoPlay,
    '.avi': VideoPlay,
    '.mkv': VideoPlay,
    '.mp3': Headset,
    '.wav': Headset,
    '.ppt': DataBoard,
    '.pptx': DataBoard,
  }
  return iconMap[ext] || Document
}

function getFileIconColor(ext: string): string {
  const colorMap: Record<string, string> = {
    '.pdf': 'text-red-400',
    '.docx': 'text-blue-400',
    '.txt': 'text-gray-400',
    '.mp4': 'text-purple-400',
    '.mp3': 'text-green-400',
    '.ppt': 'text-orange-400',
    '.pptx': 'text-orange-400',
  }
  return colorMap[ext] || 'text-gray-400'
}

function getFileStatusType(status: FileItem['status']): '' | 'success' | 'warning' | 'danger' | 'info' {
  const typeMap: Record<FileItem['status'], '' | 'success' | 'warning' | 'danger' | 'info'> = {
    pending: 'info',
    uploading: 'warning',
    uploaded: 'success',
    error: 'danger',
  }
  return typeMap[status]
}

function getFileStatusLabel(status: FileItem['status']): string {
  const labelMap: Record<FileItem['status'], string> = {
    pending: '待上传',
    uploading: '上传中',
    uploaded: '已上传',
    error: '失败',
  }
  return labelMap[status]
}
</script>

