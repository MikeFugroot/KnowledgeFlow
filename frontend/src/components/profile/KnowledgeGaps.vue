<template>
  <div class="knowledge-gaps">
    <div v-if="gaps.length === 0" class="text-center py-8 text-gray-500 text-sm">
      暂无知识缺口数据
    </div>
    <VChart v-else :option="chartOption" :autoresize="true" style="height: 350px" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import type { GapItem } from '@/api/profile'

const props = defineProps<{
  gaps: GapItem[]
}>()

const chartOption = computed(() => {
  const indicator = props.gaps.map((g) => ({
    name: g.area,
    max: 10,
  }))

  const currentData = props.gaps.map((g) => g.current_level)
  const importanceData = props.gaps.map((g) => g.importance)

  return {
    tooltip: {
      backgroundColor: 'rgba(26, 32, 44, 0.9)',
      borderColor: '#4a5568',
      textStyle: { color: '#e2e8f0' },
    },
    legend: {
      data: ['当前水平', '重要程度'],
      textStyle: { color: '#a0aec0' },
      bottom: 0,
    },
    radar: {
      indicator,
      shape: 'polygon',
      axisName: {
        color: '#a0aec0',
        fontSize: 12,
      },
      splitArea: {
        areaStyle: {
          color: ['rgba(59, 130, 246, 0.02)', 'rgba(59, 130, 246, 0.04)'],
        },
      },
      splitLine: {
        lineStyle: { color: 'rgba(255, 255, 255, 0.08)' },
      },
      axisLine: {
        lineStyle: { color: 'rgba(255, 255, 255, 0.1)' },
      },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: currentData,
            name: '当前水平',
            areaStyle: { color: 'rgba(59, 130, 246, 0.2)' },
            lineStyle: { color: '#3b82f6', width: 2 },
            itemStyle: { color: '#3b82f6' },
          },
          {
            value: importanceData,
            name: '重要程度',
            areaStyle: { color: 'rgba(245, 158, 11, 0.15)' },
            lineStyle: { color: '#f59e0b', width: 2, type: 'dashed' },
            itemStyle: { color: '#f59e0b' },
          },
        ],
      },
    ],
  }
})
</script>
