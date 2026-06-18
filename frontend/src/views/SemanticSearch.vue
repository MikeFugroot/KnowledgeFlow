<template>
  <div class="semantic-search-page">
    <div class="mb-6">
      <SearchBar />
    </div>

    <div class="index-status flex items-center gap-4 mb-6 p-4 rounded-xl border border-gray-700/40 bg-gray-800/20">
      <div class="flex items-center gap-2">
        <el-icon :size="16" class="text-gray-400"><Search /></el-icon>
        <span class="text-sm text-gray-400">索引状态</span>
        <span :class="searchStore.isIndexReady ? 'text-green-400' : 'text-gray-500'" class="text-sm font-medium">
          {{ searchStore.indexStatusText }}
        </span>
      </div>
      <el-button
        v-if="!searchStore.indexStatus.is_ready || !buildingIndex"
        size="small"
        :loading="buildingIndex"
        @click="handleBuildIndex"
      >
        {{ searchStore.isIndexReady ? '重建索引' : '构建索引' }}
      </el-button>
      <el-progress
        v-if="buildingIndex"
        :percentage="100"
        :stroke-width="6"
        class="flex-1 max-w-xs"
        status="success"
        :indeterminate="true"
      />
    </div>

    <div v-if="searchStore.hasResults || searchStore.searching" class="grid grid-cols-1 lg:grid-cols-5 gap-6">
      <div class="lg:col-span-3">
        <div class="flex items-center justify-between mb-3">
          <h4 class="text-sm font-semibold text-gray-400">
            搜索结果 ({{ searchStore.results.length }})
          </h4>
          <el-button text size="small" @click="searchStore.clearResults()">
            清空结果
          </el-button>
        </div>
        <div v-if="searchStore.searching" class="text-center py-12">
          <el-icon :size="32" class="animate-spin text-primary-400"><Loading /></el-icon>
          <p class="text-gray-400 mt-2 text-sm">搜索中...</p>
        </div>
        <SearchResultList v-else />
      </div>

      <div class="lg:col-span-2">
        <div class="sticky top-0">
          <h4 class="text-sm font-semibold text-gray-400 mb-3">结果详情</h4>
          <SearchResultDetail />
        </div>
      </div>
    </div>

    <EmptyState
      v-if="!searchStore.hasResults && !searchStore.searching && !searchStore.query"
      title="语义检索"
      description="输入关键词，在知识库中进行智能语义检索"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, type Ref } from 'vue'
import { Search, Loading } from '@element-plus/icons-vue'
import { useSearchStore } from '@/stores/search'
import { useTaskProgress } from '@/composables/useTaskProgress'
import { notifySuccess, notifyError } from '@/composables/useNotification'
import SearchBar from '@/components/search/SearchBar.vue'
import SearchResultList from '@/components/search/SearchResultList.vue'
import SearchResultDetail from '@/components/search/SearchResultDetail.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const searchStore = useSearchStore()
const buildingIndex = ref(false)
const indexTaskId: Ref<number | null> = ref(null)
useTaskProgress(indexTaskId)

async function handleBuildIndex(): Promise<void> {
  buildingIndex.value = true
  try {
    const taskId = await searchStore.doBuildIndex()
    if (taskId) {
      indexTaskId.value = taskId
      notifySuccess(`索引构建任务已提交，任务ID: ${taskId}`)
    } else {
      notifyError('触发索引构建失败')
    }
  } catch (error) {
    notifyError('索引构建请求失败')
  } finally {
    buildingIndex.value = false
  }
}

onMounted(() => {
  searchStore.fetchIndexStatus()
})
</script>
