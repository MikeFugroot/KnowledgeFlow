<template>
  <div class="recent-activity">
    <div v-if="activities.length === 0" class="text-center py-8 text-gray-500 text-sm">
      暂无最近文档
    </div>
    <div v-else class="activity-list">
      <div
        v-for="activity in activities"
        :key="activity.id ?? activity.title ?? activity.created_at"
        class="activity-item flex items-start gap-3 py-3 border-b border-gray-700/30 last:border-0"
      >
        <el-icon :size="20" class="flex-shrink-0 mt-0.5" :class="getActivityIconColor(activity.doc_type || '')">
          <component :is="getActivityIcon(activity.doc_type || '')" />
        </el-icon>
        <div class="flex-1 min-w-0">
          <div class="text-sm text-gray-300 truncate">{{ activity.title || '-' }}</div>
          <div class="flex items-center gap-2 mt-1">
            <el-tag v-if="activity.doc_type" size="small" type="info" effect="plain">
              {{ DOC_TYPE_LABELS[activity.doc_type] || activity.doc_type }}
            </el-tag>
            <span v-if="activity.category" class="text-xs text-gray-500">{{ activity.category }}</span>
          </div>
        </div>
        <span v-if="activity.created_at" class="text-xs text-gray-500 flex-shrink-0 mt-1">
          {{ formatRelativeTime(activity.created_at) }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Upload, Link, Delete, Refresh, Edit } from '@element-plus/icons-vue'
import type { RecentDocument } from '@/api/dashboard'
import { DOC_TYPE_LABELS } from '@/utils/constants'
import { formatRelativeTime } from '@/utils/format'

defineProps<{
  /** 活动列表 */
  activities: RecentDocument[]
}>()

/** 根据操作类型获取图标 */
function getActivityIcon(action: string) {
  const iconMap: Record<string, typeof Upload> = {
    upload: Upload,
    import: Link,
    delete: Delete,
    reorganize: Refresh,
    update: Edit,
  }
  return iconMap[action] || Link
}

/** 根据操作类型获取图标颜色 */
function getActivityIconColor(action: string): string {
  const colorMap: Record<string, string> = {
    upload: 'text-blue-400',
    import: 'text-green-400',
    delete: 'text-red-400',
    reorganize: 'text-yellow-400',
    update: 'text-purple-400',
  }
  return colorMap[action] || 'text-gray-400'
}
</script>

<style scoped>
.activity-item:hover {
  background-color: rgba(59, 130, 246, 0.03);
  border-radius: 6px;
}
</style>
