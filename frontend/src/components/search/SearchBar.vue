<template>
  <div class="search-bar flex items-center gap-3">
    <el-input
      v-model="query"
      placeholder="输入关键词进行语义检索..."
      size="large"
      clearable
      :prefix-icon="Search"
      class="flex-1"
      @keyup.enter="handleSearch"
    />
    <el-input-number
      v-model="topKValue"
      :min="1"
      :max="50"
      size="large"
      class="w-28"
      controls-position="right"
    />
    <el-button
      type="primary"
      size="large"
      :loading="searching"
      :disabled="!query.trim()"
      @click="handleSearch"
    >
      搜索
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useSearchStore } from '@/stores/search'

const searchStore = useSearchStore()

const query = computed({
  get: () => searchStore.query,
  set: (val: string) => { searchStore.query = val },
})

const topKValue = computed({
  get: () => searchStore.topK,
  set: (val: number) => { searchStore.topK = val },
})

const searching = computed(() => searchStore.searching)

function handleSearch(): void {
  searchStore.doSearch()
}
</script>
