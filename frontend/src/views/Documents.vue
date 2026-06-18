<template>
  <div class="documents-page">
    <!-- 顶部筛选栏 -->
    <DocumentFilter />

    <!-- 批量操作栏 -->
    <div v-if="docStore.hasSelection" class="batch-actions flex items-center gap-3 mb-4">
      <span class="text-sm text-gray-400">已选 {{ docStore.selectedIds.length }} 项</span>
      <el-button size="small" type="danger" @click="handleBatchDelete">
        批量删除
      </el-button>
      <el-button size="small" @click="handleBatchReorganize">
        重新整理
      </el-button>
      <el-button size="small" @click="handleExport">
        导出 JSON
      </el-button>
    </div>

    <!-- 文档表格 -->
    <DocumentTable
      @view="handleViewDoc"
      @delete="handleDeleteDoc"
    />

    <!-- 详情抽屉 -->
    <DocumentDetail />

    <!-- 空状态 -->
    <EmptyState
      v-if="!docStore.loading && docStore.documents.length === 0 && !docStore.hasFilters"
      title="暂无文档"
      description="导入文件或网页后，整理结果将显示在这里"
      action-text="导入文件"
      :icon="Upload"
      @action="$router.push('/import/files')"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { useDocumentStore } from '@/stores/document'
import { exportDocuments } from '@/api/document'
import { confirmDelete, notifySuccess, notifyError, notifyWarning } from '@/composables/useNotification'
import DocumentFilter from '@/components/document/DocumentFilter.vue'
import DocumentTable from '@/components/document/DocumentTable.vue'
import DocumentDetail from '@/components/document/DocumentDetail.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import type { Document } from '@/api/document'

const docStore = useDocumentStore()

onMounted(() => {
  docStore.fetchDocuments(1)
})

/** 查看文档详情 */
function handleViewDoc(doc: Document): void {
  docStore.fetchDocumentDetail(doc.id)
}

/** 删除文档 */
async function handleDeleteDoc(id: number): Promise<void> {
  try {
    await docStore.deleteDocumentAction(id)
    notifySuccess('删除成功')
  } catch (error) {
    notifyError('删除失败')
  }
}

/** 批量删除 */
async function handleBatchDelete(): Promise<void> {
  const ok = await confirmDelete(`确定删除选中的 ${docStore.selectedIds.length} 个文档？此操作不可恢复。`)
  if (!ok) return
  try {
    await docStore.batchDeleteAction()
    notifySuccess('批量删除成功')
  } catch (error) {
    notifyError('批量删除失败')
  }
}

/** 批量重新整理 */
async function handleBatchReorganize(): Promise<void> {
  notifyWarning('批量重新整理功能开发中')
}

/** 导出 JSON */
async function handleExport(): Promise<void> {
  try {
    const blob = await exportDocuments({ ids: docStore.selectedIds.length > 0 ? docStore.selectedIds : undefined })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `knowledgeflow_export_${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
    notifySuccess('导出成功')
  } catch (error) {
    notifyError('导出失败')
  }
}
</script>
