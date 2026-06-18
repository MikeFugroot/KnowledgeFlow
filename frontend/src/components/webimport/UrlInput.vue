<template>
  <div class="url-input">
    <div class="flex gap-3 mb-4">
      <el-input
        v-model="url"
        placeholder="输入网页 URL，如 https://example.com/article"
        size="large"
        clearable
        :prefix-icon="Link"
        @keyup.enter="handleImport"
      />
      <el-button
        type="primary"
        size="large"
        :loading="importing"
        :disabled="!url.trim()"
        @click="handleImport"
      >
        导入
      </el-button>
    </div>
    <div class="text-xs text-gray-500">
      支持普通网页、微信公众号、知乎、掘金等文章链接
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { Link } from '@element-plus/icons-vue'
import { importUrl } from '@/api/webimport'
import { notifySuccess, notifyError } from '@/composables/useNotification'

const emit = defineEmits<{
  (e: 'task-created', taskId: number): void
}>()

const url = ref('')
const importing = ref(false)

/** 导入 URL */
async function handleImport(): Promise<void> {
  const trimmedUrl = url.value.trim()
  if (!trimmedUrl) return

  // 简单 URL 格式校验
  if (!trimmedUrl.startsWith('http://') && !trimmedUrl.startsWith('https://')) {
    notifyError('请输入有效的 URL（需以 http:// 或 https:// 开头）')
    return
  }

  importing.value = true
  try {
    const result = await importUrl({ url: trimmedUrl })
    notifySuccess(`已提交导入任务，任务ID: ${result.task_id}`)
    emit('task-created', result.task_id)
    url.value = ''
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : 'URL 导入失败'
    notifyError(msg)
  } finally {
    importing.value = false
  }
}
</script>
