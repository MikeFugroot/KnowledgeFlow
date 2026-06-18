<template>
  <el-drawer
    :model-value="visible"
    title="文档详情"
    direction="rtl"
    size="500px"
    :before-close="handleClose"
    class="document-detail-drawer"
  >
    <div v-if="document" class="px-2">
      <!-- 基本信息 -->
      <div class="mb-6">
        <h3 class="text-lg font-semibold text-gray-100 mb-3">
          {{ document.title || document.original_title }}
        </h3>
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <span class="text-gray-500">类型：</span>
            <el-tag size="small" effect="plain">{{ DOC_TYPE_LABELS[document.doc_type] || document.doc_type }}</el-tag>
          </div>
          <div>
            <span class="text-gray-500">分类：</span>
            <span class="text-gray-300">{{ document.category || '-' }}</span>
          </div>
          <div>
            <span class="text-gray-500">字数：</span>
            <span class="text-gray-300">{{ formatNumber(document.char_count) }}</span>
          </div>
          <div>
            <span class="text-gray-500">模型：</span>
            <span class="text-gray-300">{{ document.model || '-' }}</span>
          </div>
        </div>
      </div>

      <!-- 标签 -->
      <div v-if="document.tags && document.tags.length > 0" class="mb-5">
        <h4 class="text-sm text-gray-400 mb-2">标签</h4>
        <div class="flex flex-wrap gap-2">
          <el-tag
            v-for="tag in document.tags"
            :key="tag.id"
            size="small"
            effect="dark"
          >
            {{ tag.name }}
          </el-tag>
        </div>
      </div>

      <!-- 摘要 -->
      <div v-if="document.summary" class="mb-5">
        <h4 class="text-sm text-gray-400 mb-2">摘要</h4>
        <p class="text-sm text-gray-300 leading-relaxed bg-gray-800/40 rounded-lg p-3">
          {{ document.summary }}
        </p>
      </div>

      <!-- 综合评价 -->
      <div v-if="document.overall_evaluation" class="mb-5">
        <h4 class="text-sm text-gray-400 mb-2">综合评价</h4>
        <p class="text-sm text-gray-300 leading-relaxed bg-gray-800/40 rounded-lg p-3">
          {{ document.overall_evaluation }}
        </p>
      </div>

      <!-- 章节 -->
      <div v-if="document.sections && document.sections.length > 0" class="mb-5">
        <h4 class="text-sm text-gray-400 mb-2">知识单元 ({{ document.sections.length }})</h4>
        <div class="space-y-2">
          <div
            v-for="section in document.sections"
            :key="section.id"
            class="section-card rounded-lg p-3 bg-gray-800/30 border border-gray-700/30"
          >
            <div class="text-sm font-medium text-gray-200 mb-1">
              {{ section.section_title }}
            </div>
            <div v-if="section.location_hint" class="text-xs text-gray-500 mb-1">
              位置: {{ section.location_hint }}
            </div>
            <div v-if="section.summary" class="text-xs text-gray-400 leading-relaxed">
              {{ truncateText(section.summary, 150) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 来源信息 -->
      <div class="mb-5">
        <h4 class="text-sm text-gray-400 mb-2">来源</h4>
        <div class="text-xs text-gray-500 space-y-1">
          <div v-if="document.source_path">路径: {{ document.source_path }}</div>
          <div v-if="document.source_url">
            URL:
            <a :href="document.source_url" target="_blank" class="text-primary-400 hover:underline">
              {{ truncateText(document.source_url, 60) }}
            </a>
          </div>
          <div>创建: {{ formatDateTime(document.created_at) }}</div>
          <div>更新: {{ formatDateTime(document.updated_at) }}</div>
        </div>
      </div>

      <!-- 操作 -->
      <div class="flex gap-3 pt-4 border-t border-gray-700/40">
        <el-button size="small" @click="handleReorganize">
          <el-icon class="mr-1"><Refresh /></el-icon>
          重新整理
        </el-button>
        <el-button size="small" type="danger" @click="handleDelete">
          <el-icon class="mr-1"><Delete /></el-icon>
          删除
        </el-button>
      </div>
    </div>

    <div v-else class="text-center py-12 text-gray-500">
      未选择文档
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Refresh, Delete } from '@element-plus/icons-vue'
import { useDocumentStore } from '@/stores/document'
import { DOC_TYPE_LABELS } from '@/utils/constants'
import { formatDateTime, formatNumber, truncateText } from '@/utils/format'
import { confirmDelete, notifySuccess, notifyError } from '@/composables/useNotification'

const docStore = useDocumentStore()

const visible = computed(() => docStore.detailDrawerVisible)
const document = computed(() => docStore.currentDocument)

/** 关闭抽屉 */
function handleClose(): void {
  docStore.closeDetail()
}

/** 重新整理 */
async function handleReorganize(): Promise<void> {
  if (!document.value) return
  try {
    const taskId = await docStore.reorganizeAction(document.value.id)
    if (taskId) {
      notifySuccess(`已触发重新整理，任务ID: ${taskId}`)
    }
  } catch (error) {
    notifyError('重新整理失败')
  }
}

/** 删除 */
async function handleDelete(): Promise<void> {
  if (!document.value) return
  const ok = await confirmDelete(`确定删除文档「${document.value.title || document.value.original_title}」？`)
  if (!ok) return
  try {
    await docStore.deleteDocumentAction(document.value.id)
    notifySuccess('删除成功')
  } catch (error) {
    notifyError('删除失败')
  }
}
</script>

<style scoped>
.section-card:hover {
  border-color: rgba(59, 130, 246, 0.3);
}
</style>
