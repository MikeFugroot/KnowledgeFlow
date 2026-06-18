<template>
  <div class="pdf-viewer">
    <div v-if="!src" class="text-center py-12 text-gray-500 text-sm">
      未指定 PDF 文件
    </div>
    <div v-else class="pdf-container">
      <VuePdfEmbed
        :source="src"
        :page="currentPage"
        @rendered="handleRendered"
        @loading-failed="handleLoadingFailed"
        @rendering-failed="handleRenderingFailed"
      />
      <!-- 分页控制 -->
      <div class="pdf-controls flex items-center justify-center gap-3 py-3 bg-gray-800/60 rounded-b-lg border-t border-gray-700/30">
        <el-button size="small" :disabled="currentPage <= 1" @click="currentPage--">
          <el-icon><ArrowLeft /></el-icon>
        </el-button>
        <span class="text-sm text-gray-400">{{ currentPage }} / {{ pageCount || '?' }}</span>
        <el-button size="small" :disabled="currentPage >= pageCount" @click="currentPage++">
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import VuePdfEmbed from 'vue-pdf-embed'
import { ArrowLeft, ArrowRight } from '@element-plus/icons-vue'
import { notifyError } from '@/composables/useNotification'

const props = withDefaults(defineProps<{
  /** PDF 文件 URL */
  src?: string
  /** 初始页码 */
  initialPage?: number
}>(), {
  initialPage: 1,
})

const currentPage = ref(props.initialPage)
const pageCount = ref(0)

// 当 initialPage 变化时跳转
watch(() => props.initialPage, (val) => {
  if (val && val > 0) {
    currentPage.value = val
  }
})

/** 渲染完成 */
function handleRendered(): void {
  if (pageCount.value < currentPage.value) {
    pageCount.value = currentPage.value
  }
}

/** 加载失败 */
function handleLoadingFailed(error: unknown): void {
  notifyError('PDF 文件加载失败')
  console.error('PDF loading failed:', error)
}

/** 渲染失败 */
function handleRenderingFailed(error: unknown): void {
  notifyError('PDF 页面渲染失败')
  console.error('PDF rendering failed:', error)
}
</script>

<style scoped>
.pdf-container {
  background-color: rgba(13, 17, 23, 0.5);
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
</style>
