<template>
  <div class="learning-timeline">
    <div v-if="timeline.length === 0" class="text-center py-8 text-gray-500 text-sm">
      暂无学习时间线数据
    </div>
    <el-timeline v-else>
      <el-timeline-item
        v-for="(item, index) in timeline"
        :key="index"
        :timestamp="formatDateTime(item.date, 'MM-DD')"
        placement="top"
        :color="getTimelineColor(item.doc_type)"
      >
        <div class="timeline-content">
          <div class="text-sm text-gray-200">{{ item.title }}</div>
          <div class="flex items-center gap-2 mt-1">
            <el-tag v-if="item.doc_type" size="small" effect="plain" type="info">
              {{ DOC_TYPE_LABELS[item.doc_type] || item.doc_type }}
            </el-tag>
            <span v-if="item.category" class="text-xs text-gray-500">{{ item.category }}</span>
            <div v-if="item.tags && item.tags.length > 0" class="flex gap-1">
              <el-tag
                v-for="tag in item.tags.slice(0, 3)"
                :key="tag"
                size="small"
                effect="plain"
                type="info"
                class="text-xs"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </div>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>

<script setup lang="ts">
import type { TimelineItem } from '@/api/profile'
import { DOC_TYPE_LABELS } from '@/utils/constants'
import { formatDateTime } from '@/utils/format'

defineProps<{
  /** 时间线数据 */
  timeline: TimelineItem[]
}>()

/** 获取时间线颜色 */
function getTimelineColor(docType?: string): string {
  const colorMap: Record<string, string> = {
    pdf: '#3b82f6',
    docx: '#60a5fa',
    video: '#8b5cf6',
    audio: '#10b981',
    web: '#06b6d4',
    bilibili: '#ec4899',
    xiaohongshu: '#f472b6',
  }
  return colorMap[docType || ''] || '#6b7280'
}
</script>

<style scoped>
.timeline-content {
  padding: 4px 0;
}
</style>
