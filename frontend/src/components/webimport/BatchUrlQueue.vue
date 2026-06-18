<template>
  <div class="batch-url-queue">
    <!-- URL 输入区域 -->
    <div class="mb-4">
      <el-input
        v-model="newUrl"
        placeholder="输入 URL 后按回车添加到队列"
        size="default"
        clearable
        :prefix-icon="Link"
        @keyup.enter="addUrl"
      >
        <template #append>
          <el-button @click="addUrl" :disabled="!newUrl.trim()">添加</el-button>
        </template>
      </el-input>
    </div>

    <!-- 书签导入 -->
    <div class="mb-4">
      <el-upload
        ref="bookmarkUploadRef"
        :auto-upload="false"
        :show-file-list="false"
        accept=".html,.htm"
        :on-change="handleBookmarkFile"
      >
        <el-button size="default">
          <el-icon class="mr-1"><Upload /></el-icon>
          导入浏览器书签
        </el-button>
      </el-upload>
      <div class="text-xs text-gray-500 mt-1">支持 Chrome/Edge 书签 HTML 文件</div>
    </div>

    <!-- URL 队列列表 -->
    <div v-if="urlQueue.length > 0" class="mb-4">
      <div class="flex items-center justify-between mb-2">
        <span class="text-sm text-gray-400">待导入队列 ({{ urlQueue.length }})</span>
        <el-button text size="small" @click="clearQueue">清空队列</el-button>
      </div>
      <div class="url-list space-y-1 max-h-60 overflow-auto">
        <div
          v-for="(item, index) in urlQueue"
          :key="index"
          class="url-item flex items-center gap-2 py-2 px-3 rounded bg-gray-800/30 border border-gray-700/30"
        >
          <span class="text-xs text-gray-500 flex-shrink-0 w-6 text-right">{{ index + 1 }}.</span>
          <span class="text-sm text-gray-300 flex-1 truncate">{{ item }}</span>
          <el-button text size="small" type="danger" @click="removeUrl(index)">
            <el-icon><Close /></el-icon>
          </el-button>
        </div>
      </div>
    </div>

    <!-- 批量导入按钮 -->
    <el-button
      v-if="urlQueue.length > 0"
      type="primary"
      :loading="importing"
      @click="handleBatchImport"
    >
      批量导入 {{ urlQueue.length }} 个 URL
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Link, Upload, Close } from '@element-plus/icons-vue'
import { importUrls, importBookmarks, type BookmarkImportParams } from '@/api/webimport'
import { notifySuccess, notifyError } from '@/composables/useNotification'

const emit = defineEmits<{
  (e: 'task-created', taskId: number): void
}>()

const newUrl = ref('')
const urlQueue = ref<string[]>([])
const importing = ref(false)
const bookmarkUploadRef = ref()

/** 添加 URL 到队列 */
function addUrl(): void {
  const trimmed = newUrl.value.trim()
  if (!trimmed) return

  if (!trimmed.startsWith('http://') && !trimmed.startsWith('https://')) {
    notifyError('请输入有效的 URL')
    return
  }

  if (urlQueue.value.includes(trimmed)) {
    notifyError('该 URL 已在队列中')
    return
  }

  urlQueue.value.push(trimmed)
  newUrl.value = ''
}

/** 移除 URL */
function removeUrl(index: number): void {
  urlQueue.value.splice(index, 1)
}

/** 清空队列 */
function clearQueue(): void {
  urlQueue.value = []
}

/** 处理书签文件 */
async function handleBookmarkFile(file: { raw: File }): Promise<void> {
  importing.value = true
  try {
    const params: BookmarkImportParams = {
      bookmark_path: file.raw.name,
    }
    const result = await importBookmarks(params)
    notifySuccess(`书签导入任务已提交，任务ID: ${result.task_id}`)
    emit('task-created', result.task_id)
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : '书签导入失败'
    notifyError(msg)
  } finally {
    importing.value = false
  }
}

/** 批量导入 */
async function handleBatchImport(): Promise<void> {
  if (urlQueue.value.length === 0) return

  importing.value = true
  try {
    const result = await importUrls({ urls: urlQueue.value })
    notifySuccess(`批量导入任务已提交，共 ${urlQueue.value.length} 个 URL，任务ID: ${result.task_id}`)
    emit('task-created', result.task_id)
    urlQueue.value = []
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : '批量导入失败'
    notifyError(msg)
  } finally {
    importing.value = false
  }
}
</script>
