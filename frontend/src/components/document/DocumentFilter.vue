<template>
  <div class="document-filter flex flex-wrap items-center gap-3 mb-4">
    <!-- 分类筛选 -->
    <el-select
      v-model="filterCategory"
      placeholder="全部分类"
      size="default"
      class="w-32"
      clearable
      @change="handleFilterChange"
    >
      <el-option
        v-for="cat in CATEGORIES"
        :key="cat"
        :label="cat"
        :value="cat"
      />
    </el-select>

    <!-- 来源类型筛选 -->
    <el-select
      v-model="filterDocType"
      placeholder="全部类型"
      size="default"
      class="w-36"
      clearable
      @change="handleFilterChange"
    >
      <el-option
        v-for="(label, key) in DOC_TYPE_LABELS"
        :key="key"
        :label="label"
        :value="key"
      />
    </el-select>

    <!-- 标签筛选 -->
    <el-select
      v-model="filterTag"
      placeholder="全部标签"
      size="default"
      class="w-36"
      clearable
      filterable
      allow-create
      @change="handleFilterChange"
    >
      <el-option
        v-for="tag in availableTags"
        :key="tag"
        :label="tag"
        :value="tag"
      />
    </el-select>

    <!-- 关键词搜索 -->
    <el-input
      v-model="filterKeyword"
      placeholder="搜索标题/摘要..."
      size="default"
      class="w-52"
      clearable
      :prefix-icon="Search"
      @keyup.enter="handleFilterChange"
      @clear="handleFilterChange"
    />

    <!-- 搜索按钮 -->
    <el-button type="primary" size="default" @click="handleFilterChange">
      搜索
    </el-button>

    <!-- 清除筛选 -->
    <el-button v-if="hasFilters" text size="default" @click="handleClearFilters">
      清除筛选
    </el-button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useDocumentStore } from '@/stores/document'
import { CATEGORIES, DOC_TYPE_LABELS } from '@/utils/constants'

const docStore = useDocumentStore()

const filterCategory = ref<string>('')
const filterDocType = ref<string>('')
const filterTag = ref<string>('')
const filterKeyword = ref<string>('')

/** 可用标签列表 */
const availableTags = computed(() => {
  const tagSet = new Set<string>()
  docStore.documents.forEach((doc) => {
    doc.tags?.forEach((tag) => tagSet.add(tag.name))
  })
  return Array.from(tagSet).sort()
})

/** 是否有筛选条件 */
const hasFilters = computed(() => {
  return !!filterCategory.value || !!filterDocType.value || !!filterTag.value || !!filterKeyword.value
})

/** 应用筛选 */
function handleFilterChange(): void {
  docStore.setFilters({
    category: filterCategory.value || undefined,
    doc_type: filterDocType.value || undefined,
    tag: filterTag.value || undefined,
    keyword: filterKeyword.value || undefined,
  })
}

/** 清除筛选 */
function handleClearFilters(): void {
  filterCategory.value = ''
  filterDocType.value = ''
  filterTag.value = ''
  filterKeyword.value = ''
  docStore.clearFilters()
}
</script>
