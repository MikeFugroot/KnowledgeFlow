<template>
  <div class="search-result-list">
    <div v-if="results.length === 0" class="text-center py-8 text-gray-500 text-sm">
      暂无搜索结果
    </div>
    <div v-else class="space-y-2">
      <div
        v-for="result in results"
        :key="result.rank"
        class="result-item rounded-lg p-4 border border-gray-700/40 bg-gray-800/30 cursor-pointer transition-all duration-200 hover:border-primary-500/40 hover:bg-gray-800/50"
        :class="{ 'border-primary-500/60 bg-primary-500/5': selectedIndex === result.rank - 1 }"
        @click="handleSelect(result)"
      >
        <div class="flex items-start gap-3">
          <div
            class="rank-badge flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold"
            :class="getRankClass(result.rank)"
          >
            {{ result.rank }}
          </div>
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2 mb-1">
              <span class="text-sm font-medium text-gray-200 truncate">
                {{ result.doc_title }}
              </span>
              <el-tag size="small" effect="plain" type="info">
                {{ DOC_TYPE_LABELS[result.doc_type] || result.doc_type }}
              </el-tag>
            </div>
            <div v-if="result.section_title" class="text-xs text-gray-500 mb-1">
              {{ result.section_title }} · {{ result.location }}
            </div>
            <div class="text-xs text-gray-400 line-clamp-2 mb-2">
              {{ truncateText(result.chunk_text, 120) }}
            </div>
            <div class="flex items-center gap-3 text-xs">
              <span class="text-primary-400">综合: {{ result.score.toFixed(3) }}</span>
              <span class="text-green-400">语义: {{ result.dense_score.toFixed(3) }}</span>
              <span class="text-yellow-400">词面: {{ result.lexical_score.toFixed(3) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useSearchStore } from '@/stores/search'
import { DOC_TYPE_LABELS } from '@/utils/constants'
import { truncateText } from '@/utils/format'
import type { SearchResult } from '@/api/search'

const searchStore = useSearchStore()

const results = computed(() => searchStore.results)
const selectedIndex = computed(() => searchStore.selectedIndex)

function handleSelect(result: SearchResult): void {
  searchStore.selectResult(result.rank - 1)
}

function getRankClass(rank: number): string {
  if (rank === 1) return 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30'
  if (rank === 2) return 'bg-gray-400/20 text-gray-300 border border-gray-500/30'
  if (rank === 3) return 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
  return 'bg-gray-700/30 text-gray-500 border border-gray-600/30'
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
