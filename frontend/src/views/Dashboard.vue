<template>
  <div class="dashboard-page">
    <!-- 指标卡片 -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      <MetricCard
        title="资料总数"
        :value="stats.total_documents"
        :icon="Document"
        icon-color="text-blue-400"
        subtitle="所有导入的文档"
      />
      <MetricCard
        title="知识单元"
        :value="stats.total_sections"
        :icon="DataBoard"
        icon-color="text-green-400"
        subtitle="整理后的知识片段"
      />
      <MetricCard
        title="标签总数"
        :value="stats.total_tags"
        :icon="Search"
        icon-color="text-purple-400"
        subtitle="文档标签"
      />
      <MetricCard
        title="索引状态"
        :value="stats.index_ready ? '就绪' : '未构建'"
        :icon="DataAnalysis"
        icon-color="text-yellow-400"
        subtitle="知识画像生成情况"
      />
    </div>

    <!-- 快捷操作 -->
    <div class="quick-actions mb-6">
      <h3 class="text-base font-semibold text-gray-200 mb-3">快捷操作</h3>
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div
          class="action-card flex items-center gap-4 p-4 rounded-xl border border-gray-700/40 bg-gray-800/30 cursor-pointer transition-all duration-300 hover:border-blue-500/40 hover:bg-blue-500/5"
          @click="$router.push('/import/files')"
        >
          <div class="action-icon w-12 h-12 rounded-lg bg-blue-500/15 flex items-center justify-center">
            <el-icon :size="24" class="text-blue-400"><Upload /></el-icon>
          </div>
          <div>
            <div class="text-sm font-medium text-gray-200">上传文件</div>
            <div class="text-xs text-gray-500">导入本地 PDF/文档/音视频</div>
          </div>
        </div>
        <div
          class="action-card flex items-center gap-4 p-4 rounded-xl border border-gray-700/40 bg-gray-800/30 cursor-pointer transition-all duration-300 hover:border-green-500/40 hover:bg-green-500/5"
          @click="$router.push('/import/web')"
        >
          <div class="action-icon w-12 h-12 rounded-lg bg-green-500/15 flex items-center justify-center">
            <el-icon :size="24" class="text-green-400"><Link /></el-icon>
          </div>
          <div>
            <div class="text-sm font-medium text-gray-200">粘贴 URL</div>
            <div class="text-xs text-gray-500">导入网页/B站/小红书</div>
          </div>
        </div>
        <div
          class="action-card flex items-center gap-4 p-4 rounded-xl border border-gray-700/40 bg-gray-800/30 cursor-pointer transition-all duration-300 hover:border-purple-500/40 hover:bg-purple-500/5"
          @click="$router.push('/search')"
        >
          <div class="action-icon w-12 h-12 rounded-lg bg-purple-500/15 flex items-center justify-center">
            <el-icon :size="24" class="text-purple-400"><Search /></el-icon>
          </div>
          <div>
            <div class="text-sm font-medium text-gray-200">语义搜索</div>
            <div class="text-xs text-gray-500">在知识库中智能检索</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近文档 -->
    <div class="recent-activity-section rounded-xl border border-gray-700/40 bg-gray-800/20 p-5">
      <h3 class="text-base font-semibold text-gray-200 mb-3">最近文档</h3>
      <RecentActivity :activities="stats.recent_documents" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { Document, DataBoard, Search, DataAnalysis, Upload, Link } from '@element-plus/icons-vue'
import { getDashboardStats, type DashboardStats } from '@/api/dashboard'
import MetricCard from '@/components/dashboard/MetricCard.vue'
import RecentActivity from '@/components/dashboard/RecentActivity.vue'

/** 仪表盘统计数据 */
const stats = reactive<DashboardStats>({
  total_documents: 0,
  total_sections: 0,
  total_tags: 0,
  category_distribution: {},
  type_distribution: {},
  recent_documents: [],
  index_ready: false,
  has_profile: false,
})

onMounted(async () => {
  try {
    const data = await getDashboardStats()
    Object.assign(stats, data)
  } catch (error) {
    console.error('获取仪表盘数据失败:', error)
  }
})
</script>
