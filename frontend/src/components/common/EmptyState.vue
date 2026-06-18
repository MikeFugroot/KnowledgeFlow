<template>
  <div class="empty-state flex flex-col items-center justify-center py-16">
    <el-icon :size="64" class="text-gray-600 mb-4">
      <component :is="icon" />
    </el-icon>
    <h3 class="text-gray-400 text-lg mb-2">{{ title }}</h3>
    <p class="text-gray-500 text-sm mb-6 text-center max-w-sm">{{ description }}</p>
    <el-button v-if="actionText" type="primary" @click="$emit('action')">
      {{ actionText }}
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { FolderOpened } from '@element-plus/icons-vue'

withDefaults(defineProps<{
  /** 图标组件 */
  icon?: typeof FolderOpened
  /** 标题 */
  title?: string
  /** 描述 */
  description?: string
  /** 操作按钮文字 */
  actionText?: string
}>(), {
  icon: FolderOpened,
  title: '暂无数据',
  description: '还没有相关内容，开始添加吧',
  actionText: '',
})

defineEmits<{
  (e: 'action'): void
}>()
</script>

<style scoped>
.empty-state {
  min-height: 200px;
}
</style>
