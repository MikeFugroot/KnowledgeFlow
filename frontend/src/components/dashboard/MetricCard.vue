<template>
  <div class="metric-card rounded-xl p-5 border border-gray-700/40 transition-all duration-300 hover:border-primary-500/30 hover:shadow-lg hover:shadow-primary-500/5">
    <div class="flex items-center justify-between mb-3">
      <span class="text-sm text-gray-400">{{ title }}</span>
      <el-icon :size="24" :class="iconColorClass">
        <component :is="icon" />
      </el-icon>
    </div>
    <div class="text-2xl font-bold text-gray-100 mb-1">
      {{ formattedValue }}
    </div>
    <div v-if="subtitle" class="text-xs text-gray-500">
      {{ subtitle }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, type Component } from 'vue'
import { formatNumber } from '@/utils/format'

const props = defineProps<{
  /** 标题 */
  title: string
  /** 数值 */
  value: number | string
  /** 图标 */
  icon: Component
  /** 图标颜色类名 */
  iconColor?: string
  /** 副标题 */
  subtitle?: string
}>()

/** 格式化后的值 */
const formattedValue = computed(() => {
  if (typeof props.value === 'string') return props.value
  return formatNumber(props.value)
})

/** 图标颜色类 */
const iconColorClass = computed(() => props.iconColor || 'text-primary-400')
</script>

<style scoped>
.metric-card {
  background-color: rgba(45, 55, 72, 0.4);
}
</style>
