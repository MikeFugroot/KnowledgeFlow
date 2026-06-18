<template>
  <div class="log-stream">
    <!-- 工具栏 -->
    <div class="log-toolbar flex items-center justify-between mb-3">
      <div class="flex items-center gap-3">
        <el-select
          v-model="levelFilter"
          size="small"
          placeholder="日志级别"
          class="w-32"
          clearable
        >
          <el-option label="全部" value="" />
          <el-option
            v-for="level in LOG_LEVELS"
            :key="level"
            :label="level"
            :value="level"
          />
        </el-select>
        <span class="text-xs text-gray-500">共 {{ filteredLogs.length }} 条</span>
      </div>
      <div class="flex items-center gap-2">
        <el-switch
          v-model="autoScroll"
          size="small"
          active-text="自动滚动"
          inactive-text=""
          class="auto-scroll-switch"
        />
        <el-button size="small" text @click="handleClear">
          <el-icon><Delete /></el-icon>
          清空
        </el-button>
      </div>
    </div>

    <!-- 日志内容区 -->
    <div
      ref="logContainerRef"
      class="log-container rounded-lg p-3 overflow-auto"
      :style="{ maxHeight: maxHeight }"
    >
      <div v-if="filteredLogs.length === 0" class="text-center py-8 text-gray-500 text-sm">
        暂无日志
      </div>
      <div
        v-for="log in filteredLogs"
        :key="log.id"
        class="log-entry flex items-start gap-2 py-1.5 border-b border-gray-700/30 last:border-0"
      >
        <span class="text-xs text-gray-500 w-40 flex-shrink-0 font-mono">
          {{ formatDateTime(log.timestamp, 'HH:mm:ss') }}
        </span>
        <el-tag
          :color="getLevelColor(log.level)"
          effect="dark"
          size="small"
          class="flex-shrink-0"
          style="border: none; min-width: 60px; text-align: center;"
        >
          {{ log.level }}
        </el-tag>
        <span class="text-sm text-gray-300 flex-1 break-all font-mono leading-relaxed">
          {{ log.message }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'
import { Delete } from '@element-plus/icons-vue'
import { useAppStore, type LogEntry } from '@/stores/app'
import { LOG_LEVELS, LOG_LEVEL_COLORS, type LogLevel } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'

withDefaults(defineProps<{
  /** 最大高度 */
  maxHeight?: string
}>(), {
  maxHeight: '500px',
})

const appStore = useAppStore()
const logContainerRef = ref<HTMLElement | null>(null)
const levelFilter = ref<string>('')
const autoScroll = ref(true)

/** 过滤后的日志 */
const filteredLogs = computed<LogEntry[]>(() => {
  const logs = appStore.recentLogs
  if (!levelFilter.value) return logs
  return logs.filter((log) => log.level === levelFilter.value)
})

/** 获取日志级别颜色 */
function getLevelColor(level: LogLevel): string {
  return LOG_LEVEL_COLORS[level] || '#909399'
}

/** 清空日志 */
function handleClear(): void {
  appStore.clearLogs()
}

/** 自动滚动到底部 */
watch(
  () => filteredLogs.value.length,
  () => {
    if (autoScroll.value) {
      nextTick(() => {
        if (logContainerRef.value) {
          logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
        }
      })
    }
  }
)
</script>

<style scoped>
.log-container {
  background-color: rgba(13, 17, 23, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.auto-scroll-switch :deep(.el-switch__label) {
  color: #a0aec0;
  font-size: 12px;
}
</style>
