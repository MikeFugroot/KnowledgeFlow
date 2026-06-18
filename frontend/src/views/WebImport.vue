<template>
  <div class="web-import-page">
    <el-tabs v-model="activeTab" type="border-card" class="dark-tabs">
      <el-tab-pane label="URL 导入" name="url">
        <UrlInput @task-created="handleTaskCreated" />
        <TaskProgress
          v-if="currentTaskId !== null"
          :progress="taskProgress.progress"
          :progress-message="taskProgress.progressMessage"
          :is-completed="taskProgress.isCompleted"
          :is-failed="taskProgress.isFailed"
          :error-message="taskProgress.errorMessage"
          class="mt-4"
        />
      </el-tab-pane>

      <el-tab-pane label="B站导入" name="bilibili">
        <BilibiliPanel @task-created="handleTaskCreated" />
        <TaskProgress
          v-if="currentTaskId !== null"
          :progress="taskProgress.progress"
          :progress-message="taskProgress.progressMessage"
          :is-completed="taskProgress.isCompleted"
          :is-failed="taskProgress.isFailed"
          :error-message="taskProgress.errorMessage"
          class="mt-4"
        />
      </el-tab-pane>

      <el-tab-pane label="小红书导入" name="xiaohongshu">
        <XiaohongshuPanel @task-created="handleTaskCreated" />
        <TaskProgress
          v-if="currentTaskId !== null"
          :progress="taskProgress.progress"
          :progress-message="taskProgress.progressMessage"
          :is-completed="taskProgress.isCompleted"
          :is-failed="taskProgress.isFailed"
          :error-message="taskProgress.errorMessage"
          class="mt-4"
        />
      </el-tab-pane>

      <el-tab-pane label="书签/批量导入" name="batch">
        <BatchUrlQueue @task-created="handleTaskCreated" />
        <TaskProgress
          v-if="currentTaskId !== null"
          :progress="taskProgress.progress"
          :progress-message="taskProgress.progressMessage"
          :is-completed="taskProgress.isCompleted"
          :is-failed="taskProgress.isFailed"
          :error-message="taskProgress.errorMessage"
          class="mt-4"
        />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, type Ref } from 'vue'
import { useTaskProgress } from '@/composables/useTaskProgress'
import { notifySuccess } from '@/composables/useNotification'
import UrlInput from '@/components/webimport/UrlInput.vue'
import BilibiliPanel from '@/components/webimport/BilibiliPanel.vue'
import XiaohongshuPanel from '@/components/webimport/XiaohongshuPanel.vue'
import BatchUrlQueue from '@/components/webimport/BatchUrlQueue.vue'
import TaskProgress from '@/components/common/TaskProgress.vue'

const activeTab = ref('url')
const currentTaskId: Ref<number | null> = ref(null)
const taskProgress = useTaskProgress(currentTaskId)

function handleTaskCreated(taskId: number): void {
  taskProgress.reset()
  currentTaskId.value = taskId
  notifySuccess(`导入任务已创建，任务ID: ${taskId}`)
}
</script>

<style scoped>
.dark-tabs :deep(.el-tabs__content) {
  padding: 20px;
}
</style>
