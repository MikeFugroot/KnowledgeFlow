<template>
  <div class="theme-distribution">
    <div v-if="themes.length === 0" class="text-center py-8 text-gray-500 text-sm">
      暂无主题分布数据
    </div>
    <VChart v-else :option="chartOption" :autoresize="true" style="height: 300px" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import VChart from 'vue-echarts'
import type { ThemeItem } from '@/api/profile'

const props = defineProps<{
  /** 主题分布数据 */
  themes: ThemeItem[]
}>()

/** ECharts 配置 */
const chartOption = computed(() => {
  const data = props.themes.map((t) => ({
    name: t.category,
    value: t.count,
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)',
      backgroundColor: 'rgba(26, 32, 44, 0.9)',
      borderColor: '#4a5568',
      textStyle: { color: '#e2e8f0' },
    },
    legend: {
      orient: 'vertical',
      right: 10,
      top: 'center',
      textStyle: { color: '#a0aec0', fontSize: 12 },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['35%', '50%'],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 6,
          borderColor: '#0d1117',
          borderWidth: 2,
        },
        label: { show: false },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
            color: '#e2e8f0',
          },
        },
        labelLine: { show: false },
        data,
        color: ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899', '#84cc16'],
      },
    ],
  }
})
</script>
