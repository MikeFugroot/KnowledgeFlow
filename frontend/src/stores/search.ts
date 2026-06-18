/**
 * 语义检索 Store。
 * 管理查询、结果和索引状态。
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  search,
  buildIndex,
  getIndexStatus,
  type SearchParams,
  type SearchResult,
  type SearchResponse,
  type IndexStatus,
} from '@/api/search'
import { DEFAULT_SEARCH_TOP_K } from '@/utils/constants'

export const useSearchStore = defineStore('search', () => {
  const query = ref<string>('')
  const results = ref<SearchResult[]>([])
  const searching = ref<boolean>(false)
  const selectedIndex = ref<number>(-1)
  const indexStatus = ref<IndexStatus>({
    is_ready: false,
    total_chunks: 0,
    total_documents: 0,
    last_built_at: null,
    embedding_model: '',
  })
  const buildingIndex = ref<boolean>(false)
  const topK = ref<number>(DEFAULT_SEARCH_TOP_K)

  const hasResults = computed(() => results.value.length > 0)
  const selectedResult = computed(() => {
    if (selectedIndex.value >= 0 && selectedIndex.value < results.value.length) {
      return results.value[selectedIndex.value]
    }
    return null
  })
  const isIndexReady = computed(() => indexStatus.value.is_ready)
  const indexStatusText = computed(() => {
    if (indexStatus.value.is_ready) {
      return `就绪 (${indexStatus.value.total_chunks} 块)`
    }
    return '未构建'
  })

  async function doSearch(searchQuery?: string): Promise<void> {
    const q = searchQuery || query.value
    if (!q.trim()) return

    searching.value = true
    selectedIndex.value = -1
    try {
      const params: SearchParams = {
        query: q,
        top_k: topK.value,
      }
      const response: SearchResponse = await search(params)
      results.value = response.results
    } catch (error) {
      console.error('搜索失败:', error)
      results.value = []
    } finally {
      searching.value = false
    }
  }

  async function doBuildIndex(force: boolean = false): Promise<number | null> {
    if (buildingIndex.value) return null
    buildingIndex.value = true
    try {
      const result = await buildIndex({ force })
      return result.task_id
    } catch (error) {
      console.error('触发索引构建失败:', error)
      return null
    } finally {
      buildingIndex.value = false
    }
  }

  async function fetchIndexStatus(): Promise<void> {
    try {
      indexStatus.value = await getIndexStatus()
    } catch (error) {
      console.error('获取索引状态失败:', error)
    }
  }

  function selectResult(index: number): void {
    selectedIndex.value = index
  }

  function clearResults(): void {
    results.value = []
    selectedIndex.value = -1
    query.value = ''
  }

  function updateIndexStatus(payload: { is_ready: boolean; total_chunks: number; total_documents: number; embedding_model: string }): void {
    indexStatus.value = {
      is_ready: payload.is_ready,
      total_chunks: payload.total_chunks,
      total_documents: payload.total_documents,
      last_built_at: indexStatus.value.last_built_at,
      embedding_model: payload.embedding_model,
    }
  }

  return {
    query,
    results,
    searching,
    selectedIndex,
    indexStatus,
    buildingIndex,
    topK,
    hasResults,
    selectedResult,
    isIndexReady,
    indexStatusText,
    doSearch,
    doBuildIndex,
    fetchIndexStatus,
    selectResult,
    clearResults,
    updateIndexStatus,
  }
})
