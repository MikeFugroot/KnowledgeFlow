<template>
  <div class="xiaohongshu-panel">
    <!-- Cookie 状态提示 -->
    <el-alert
      v-if="!hasCookie"
      title="未配置小红书 Cookie"
      description="需要小红书 Cookie 才能导入笔记内容，请先在系统设置中配置"
      type="warning"
      :closable="false"
      show-icon
      class="mb-4"
    />

    <!-- URL 输入 -->
    <div class="mb-4">
      <el-input
        v-model="noteUrl"
        placeholder="输入小红书笔记链接，如 https://www.xiaohongshu.com/explore/..."
        size="large"
        clearable
        :prefix-icon="Link"
        @keyup.enter="handleImport"
      />
    </div>

    <!-- 导入按钮 -->
    <el-button
      type="primary"
      :loading="importing"
      :disabled="!noteUrl.trim() || !hasCookie"
      @click="handleImport"
    >
      导入笔记
    </el-button>

    <div class="text-xs text-gray-500 mt-3">
      支持小红书笔记链接，需先配置 Cookie 以获取完整内容
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Link } from '@element-plus/icons-vue'
import { importUrl } from '@/api/webimport'
import { useSettingsStore } from '@/stores/settings'
import { notifySuccess, notifyError } from '@/composables/useNotification'

const emit = defineEmits<{
  (e: 'task-created', taskId: number): void
}>()

const settingsStore = useSettingsStore()
const noteUrl = ref('')
const importing = ref(false)

/** 是否有小红书 Cookie */
const hasCookie = computed(() => {
  return !!settingsStore.cookieConfig.xiaohongshu_cookie
})

/** 导入笔记 */
async function handleImport(): Promise<void> {
  const trimmedUrl = noteUrl.value.trim()
  if (!trimmedUrl) return

  importing.value = true
  try {
    const result = await importUrl({ url: trimmedUrl })
    notifySuccess(`已提交导入任务，任务ID: ${result.task_id}`)
    emit('task-created', result.task_id)
    noteUrl.value = ''
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : '导入小红书笔记失败'
    notifyError(msg)
  } finally {
    importing.value = false
  }
}
</script>
