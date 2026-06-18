/**
 * 整理结果状态 Store
 * 列表、详情、筛选条件
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getDocumentList,
  getDocumentDetail,
  updateDocument,
  deleteDocument,
  batchDeleteDocuments,
  reorganizeDocument,
  type Document,
  type DocumentListParams,
  type DocumentUpdateParams,
} from '@/api/document'
import type { PaginatedData } from '@/api/client'

export const useDocumentStore = defineStore('document', () => {
  // ==================== State ====================

  /** 文档列表 */
  const documents = ref<Document[]>([])

  /** 总数 */
  const total = ref<number>(0)

  /** 当前页码 */
  const currentPage = ref<number>(1)

  /** 每页条数 */
  const pageSize = ref<number>(20)

  /** 加载状态 */
  const loading = ref<boolean>(false)

  /** 当前选中的文档详情 */
  const currentDocument = ref<Document | null>(null)

  /** 详情抽屉是否可见 */
  const detailDrawerVisible = ref<boolean>(false)

  /** 筛选条件 */
  const filters = ref<DocumentListParams>({
    category: undefined,
    tag: undefined,
    doc_type: undefined,
    keyword: undefined,
  })

  /** 已选中的文档 ID（用于批量操作） */
  const selectedIds = ref<number[]>([])

  // ==================== Getters ====================

  /** 是否有筛选条件 */
  const hasFilters = computed(() => {
    return !!(filters.value.category || filters.value.tag || filters.value.doc_type || filters.value.keyword)
  })

  /** 是否有选中项 */
  const hasSelection = computed(() => selectedIds.value.length > 0)

  /** 总页数 */
  const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

  // ==================== Actions ====================

  /**
   * 加载文档列表
   */
  async function fetchDocuments(page?: number): Promise<void> {
    loading.value = true
    try {
      const params: DocumentListParams = {
        page: page || currentPage.value,
        page_size: pageSize.value,
        ...filters.value,
      }
      const result: PaginatedData<Document> = await getDocumentList(params)
      documents.value = result.items
      total.value = result.total
      currentPage.value = result.page
    } catch (error) {
      console.error('获取文档列表失败:', error)
    } finally {
      loading.value = false
    }
  }

  /**
   * 加载文档详情
   */
  async function fetchDocumentDetail(id: number): Promise<void> {
    try {
      currentDocument.value = await getDocumentDetail(id)
      detailDrawerVisible.value = true
    } catch (error) {
      console.error('获取文档详情失败:', error)
    }
  }

  /**
   * 更新文档
   */
  async function updateDocumentAction(id: number, data: DocumentUpdateParams): Promise<void> {
    try {
      const updated = await updateDocument(id, data)
      // 更新列表中的对应项
      const index = documents.value.findIndex((doc) => doc.id === id)
      if (index !== -1) {
        documents.value[index] = updated
      }
      // 如果是当前详情，也更新
      if (currentDocument.value?.id === id) {
        currentDocument.value = updated
      }
    } catch (error) {
      console.error('更新文档失败:', error)
      throw error
    }
  }

  /**
   * 删除文档
   */
  async function deleteDocumentAction(id: number): Promise<void> {
    try {
      await deleteDocument(id)
      documents.value = documents.value.filter((doc) => doc.id !== id)
      total.value--
      if (currentDocument.value?.id === id) {
        currentDocument.value = null
        detailDrawerVisible.value = false
      }
    } catch (error) {
      console.error('删除文档失败:', error)
      throw error
    }
  }

  /**
   * 批量删除文档
   */
  async function batchDeleteAction(): Promise<void> {
    if (selectedIds.value.length === 0) return
    try {
      await batchDeleteDocuments(selectedIds.value)
      documents.value = documents.value.filter((doc) => !selectedIds.value.includes(doc.id))
      total.value -= selectedIds.value.length
      selectedIds.value = []
    } catch (error) {
      console.error('批量删除失败:', error)
      throw error
    }
  }

  /**
   * 重新整理文档
   */
  async function reorganizeAction(id: number): Promise<number | null> {
    try {
      const result = await reorganizeDocument(id)
      return result.task_id
    } catch (error) {
      console.error('重新整理失败:', error)
      return null
    }
  }

  /**
   * 设置筛选条件并刷新列表
   */
  function setFilters(newFilters: Partial<DocumentListParams>): void {
    filters.value = { ...filters.value, ...newFilters }
    currentPage.value = 1
    fetchDocuments(1)
  }

  /**
   * 清除筛选条件
   */
  function clearFilters(): void {
    filters.value = {
      category: undefined,
      tag: undefined,
      doc_type: undefined,
      keyword: undefined,
    }
    currentPage.value = 1
    fetchDocuments(1)
  }

  /**
   * 切换页码
   */
  function changePage(page: number): void {
    fetchDocuments(page)
  }

  /**
   * 关闭详情抽屉
   */
  function closeDetail(): void {
    detailDrawerVisible.value = false
    currentDocument.value = null
  }

  return {
    // State
    documents,
    total,
    currentPage,
    pageSize,
    loading,
    currentDocument,
    detailDrawerVisible,
    filters,
    selectedIds,
    // Getters
    hasFilters,
    hasSelection,
    totalPages,
    // Actions
    fetchDocuments,
    fetchDocumentDetail,
    updateDocumentAction,
    deleteDocumentAction,
    batchDeleteAction,
    reorganizeAction,
    setFilters,
    clearFilters,
    changePage,
    closeDetail,
  }
})
