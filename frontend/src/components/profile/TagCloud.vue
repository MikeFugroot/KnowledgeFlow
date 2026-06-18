<template>
  <div class="tag-cloud">
    <div v-if="tags.length === 0" class="text-center py-8 text-gray-500 text-sm">
      暂无标签数据
    </div>
    <div v-else class="flex flex-wrap gap-2 justify-center">
      <span
        v-for="(tag, index) in tags"
        :key="tag.name"
        class="tag-item inline-block px-3 py-1.5 rounded-full text-sm cursor-default transition-all duration-300 hover:scale-110"
        :style="getTagStyle(index, tag.count)"
      >
        {{ tag.name }}
        <span class="text-xs opacity-60 ml-1">{{ tag.count }}</span>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TagItem } from '@/api/profile'

const props = defineProps<{
  /** 标签列表 */
  tags: TagItem[]
}>()

/** 预定义颜色列表 */
const colorPalette = [
  { bg: 'rgba(59, 130, 246, 0.2)', border: 'rgba(59, 130, 246, 0.4)', text: '#60a5fa' },
  { bg: 'rgba(139, 92, 246, 0.2)', border: 'rgba(139, 92, 246, 0.4)', text: '#a78bfa' },
  { bg: 'rgba(16, 185, 129, 0.2)', border: 'rgba(16, 185, 129, 0.4)', text: '#34d399' },
  { bg: 'rgba(245, 158, 11, 0.2)', border: 'rgba(245, 158, 11, 0.4)', text: '#fbbf24' },
  { bg: 'rgba(236, 72, 153, 0.2)', border: 'rgba(236, 72, 153, 0.4)', text: '#f472b6' },
  { bg: 'rgba(6, 182, 212, 0.2)', border: 'rgba(6, 182, 212, 0.4)', text: '#22d3ee' },
  { bg: 'rgba(239, 68, 68, 0.2)', border: 'rgba(239, 68, 68, 0.4)', text: '#f87171' },
  { bg: 'rgba(132, 204, 22, 0.2)', border: 'rgba(132, 204, 22, 0.4)', text: '#a3e635' },
]

/** 获取标签样式 */
function getTagStyle(index: number, count: number) {
  const color = colorPalette[index % colorPalette.length]
  // 根据频次调整大小
  const maxCount = props.tags.length > 0 ? Math.max(...props.tags.map((t) => t.count)) : 1
  const scale = 0.85 + (count / maxCount) * 0.5

  return {
    backgroundColor: color.bg,
    border: `1px solid ${color.border}`,
    color: color.text,
    fontSize: `${Math.round(14 * scale)}px`,
  }
}
</script>
