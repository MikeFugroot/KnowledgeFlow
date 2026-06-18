<template>
  <div class="task-progress" v-if="visible">
    <div class="flex items-center justify-between mb-2">
      <span class="text-sm text-gray-300">
        {{ progressMessage || '处理中...' }}
      </span>
      <span class="text-sm font-mono" :class="statusClass">
        {{ progress }}%
      </span>
    </div>
    <el-progress
      :percentage="progress"
      :status="progressStatus"
      :stroke-width="8"
      :show-text="false"
    />
    <div v-if="total > 0" class="text-xs text-gray-500 mt-1">
      {{ current }} / {{ total }}
    </div>
    <div v-if="isFailed" class="text-xs text-red-400 mt-2">
      <el-icon class="mr-1"><WarningFilled /></el-icon>
      {{ errorMessage }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { WarningFilled } from '@element-plus/icons-vue'

const props = withDefaults(defineProps<{
  progress?: number
  progressMessage?: string
  isCompleted?: boolean
  isFailed?: boolean
  errorMessage?: string
  current?: number
  total?: number
}>(), {
  progress: 0,
  progressMessage: '',
  isCompleted: false,
  isFailed: false,
  errorMessage: '',
  current: 0,
  total: 0,
})

const visible = computed(() => {
  return props.progress > 0 || props.isCompleted || props.isFailed
})

const progressStatus = computed<'' | 'success' | 'warning' | 'exception'>(() => {
  if (props.isFailed) return 'exception'
  if (props.isCompleted) return 'success'
  return ''
})

const statusClass = computed(() => {
  if (props.isFailed) return 'text-red-400'
  if (props.isCompleted) return 'text-green-400'
  return 'text-blue-400'
})
</script>

<style scoped>
.task-progress {
  padding: 12px 16px;
  background-color: rgba(45, 55, 72, 0.4);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
</style>
