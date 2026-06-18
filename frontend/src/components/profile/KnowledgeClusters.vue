<template>
  <div class="knowledge-clusters">
    <div v-if="clusters.length === 0" class="text-center py-8 text-gray-500 text-sm">
      暂无知识聚类数据
    </div>
    <div v-else class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="cluster in clusters"
        :key="cluster.name"
        class="cluster-card rounded-lg p-4 border border-gray-700/40 bg-gray-800/30 hover:border-primary-500/30 transition-colors"
      >
        <h4 class="text-sm font-semibold text-gray-200 mb-2">{{ cluster.name }}</h4>
        <p class="text-xs text-gray-400 mb-3 leading-relaxed">{{ cluster.description }}</p>
        <div class="flex flex-wrap gap-1 mb-3">
          <el-tag
            v-for="keyword in cluster.keywords.slice(0, 5)"
            :key="keyword"
            size="small"
            effect="plain"
            type="info"
            class="text-xs"
          >
            {{ keyword }}
          </el-tag>
        </div>
        <div v-if="cluster.next_step" class="text-xs text-primary-400 bg-primary-500/10 rounded px-2 py-1">
          下一步：{{ cluster.next_step }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { ClusterDisplayItem } from '@/api/profile'

defineProps<{
  clusters: ClusterDisplayItem[]
}>()
</script>
