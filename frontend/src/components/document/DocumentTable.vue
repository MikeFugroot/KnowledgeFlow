<template>
  <div class="document-table">
    <el-table
      :data="documents"
      v-loading="loading"
      stripe
      @selection-change="handleSelectionChange"
      @row-click="handleRowClick"
      class="dark-table"
      style="width: 100%"
    >
      <el-table-column type="selection" width="45" />
      <el-table-column prop="title" label="标题" min-width="240" show-overflow-tooltip>
        <template #default="{ row }">
          <div class="flex items-center gap-2">
            <el-icon :size="16" class="flex-shrink-0" :class="getDocTypeColor(row.doc_type)">
              <component :is="getDocTypeIcon(row.doc_type)" />
            </el-icon>
            <span class="text-gray-200 cursor-pointer hover:text-primary-400 transition-colors">
              {{ row.title || row.original_title }}
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="doc_type" label="类型" width="110">
        <template #default="{ row }">
          <el-tag size="small" effect="plain" type="info">
            {{ DOC_TYPE_LABELS[row.doc_type] || row.doc_type }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="category" label="分类" width="90">
        <template #default="{ row }">
          <span class="text-gray-400 text-sm">{{ row.category || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="char_count" label="字数" width="90" align="right">
        <template #default="{ row }">
          <span class="text-gray-400 text-sm">{{ formatNumber(row.char_count) }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="tags" label="标签" min-width="150">
        <template #default="{ row }">
          <div class="flex flex-wrap gap-1">
            <el-tag
              v-for="tag in (row.tags || []).slice(0, 3)"
              :key="tag.id"
              size="small"
              effect="dark"
              class="text-xs"
            >
              {{ tag.name }}
            </el-tag>
            <el-tag
              v-if="(row.tags || []).length > 3"
              size="small"
              effect="plain"
              type="info"
              class="text-xs"
            >
              +{{ row.tags.length - 3 }}
            </el-tag>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="时间" width="160">
        <template #default="{ row }">
          <span class="text-gray-500 text-sm">{{ formatDateTime(row.created_at) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="100" fixed="right">
        <template #default="{ row }">
          <el-button text size="small" type="danger" @click.stop="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="flex justify-end mt-4">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSizeVal"
        :total="total"
        :page-sizes="[10, 20, 50]"
        layout="total, sizes, prev, pager, next"
        background
        @current-change="handlePageChange"
        @size-change="handleSizeChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Document, VideoPlay, Headset, Link, VideoCamera, PictureFilled, Tickets, DataBoard } from '@element-plus/icons-vue'
import { useDocumentStore } from '@/stores/document'
import { DOC_TYPE_LABELS } from '@/utils/constants'
import { formatDateTime, formatNumber } from '@/utils/format'
import { confirmDelete } from '@/composables/useNotification'
import type { Document as DocType } from '@/api/document'

const emit = defineEmits<{
  (e: 'view', doc: DocType): void
  (e: 'delete', id: number): void
}>()

const docStore = useDocumentStore()

const documents = computed(() => docStore.documents)
const loading = computed(() => docStore.loading)
const total = computed(() => docStore.total)
const currentPage = computed(() => docStore.currentPage)
const pageSizeVal = computed(() => docStore.pageSize)

/** 获取文档类型图标 */
function getDocTypeIcon(docType: string) {
  const iconMap: Record<string, typeof Document> = {
    pdf: Document,
    docx: Document,
    txt: Tickets,
    markdown: Tickets,
    video: VideoPlay,
    audio: Headset,
    web: Link,
    bilibili: VideoCamera,
    xiaohongshu: PictureFilled,
    ppt: DataBoard,
    pptx: DataBoard,
  }
  return iconMap[docType] || Document
}

/** 获取文档类型颜色 */
function getDocTypeColor(docType: string): string {
  const colorMap: Record<string, string> = {
    pdf: 'text-red-400',
    docx: 'text-blue-400',
    txt: 'text-gray-400',
    markdown: 'text-gray-400',
    video: 'text-purple-400',
    audio: 'text-green-400',
    web: 'text-cyan-400',
    bilibili: 'text-pink-400',
    xiaohongshu: 'text-rose-400',
    ppt: 'text-orange-400',
    pptx: 'text-orange-400',
  }
  return colorMap[docType] || 'text-gray-400'
}

/** 多选变化 */
function handleSelectionChange(selection: DocType[]): void {
  docStore.selectedIds = selection.map((doc) => doc.id)
}

/** 行点击 → 查看详情 */
function handleRowClick(row: DocType): void {
  emit('view', row)
}

/** 删除 */
async function handleDelete(row: DocType): Promise<void> {
  const ok = await confirmDelete(`确定删除文档「${row.title || row.original_title}」？`)
  if (!ok) return
  emit('delete', row.id)
}

/** 翻页 */
function handlePageChange(page: number): void {
  docStore.changePage(page)
}

/** 改变每页条数 */
function handleSizeChange(size: number): void {
  docStore.pageSize = size
  docStore.changePage(1)
}
</script>

<style scoped>
.dark-table :deep(.el-table__row) {
  cursor: pointer;
}
</style>
