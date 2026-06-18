<template>
  <div class="knowledge-profile-page">
    <div class="flex items-center justify-between mb-6">
      <div class="flex items-center gap-3">
        <h3 class="text-base font-semibold text-gray-200">知识画像</h3>
        <el-tag
          :color="profileStore.statusColor"
          effect="dark"
          size="small"
          style="border: none"
        >
          {{ profileStore.statusText }}
        </el-tag>
      </div>
      <el-button
        type="primary"
        :loading="profileStore.refreshing || profileStore.profileStatus.is_generating"
        @click="handleRefreshProfile"
      >
        <el-icon class="mr-1"><Refresh /></el-icon>
        重新生成画像
      </el-button>
    </div>

    <TaskProgress
      v-if="profileTaskId !== null"
      class="mb-6"
      :progress="profileTaskProgress.progress"
      :progress-message="profileTaskProgress.progressMessage"
      :is-completed="profileTaskProgress.isCompleted"
      :is-failed="profileTaskProgress.isFailed"
      :error-message="profileTaskProgress.errorMessage"
      :current="profileTaskProgress.current"
      :total="profileTaskProgress.total"
    />

    <div v-if="profileStore.hasProfile && profileStore.profileJson">
      <div class="mb-6">
        <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">总览</h4>
        <ProfileOverview />
      </div>

      <div class="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        <div class="xl:col-span-2 rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">画像摘要</h4>
          <p class="text-sm text-gray-300 leading-7">{{ profileSummary }}</p>
          <div class="flex flex-wrap gap-2 mt-4">
            <el-tag v-for="tag in overviewTopTags" :key="tag" effect="plain" type="info">
              {{ tag }}
            </el-tag>
          </div>
        </div>
        <div class="rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">当前判断</h4>
          <div class="space-y-3 text-sm">
            <div>
              <div class="text-xs text-gray-500 mb-1">主攻方向</div>
              <div class="text-primary-300 font-semibold">{{ mainFocus }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500 mb-1">学习阶段</div>
              <div class="text-green-300 font-semibold">{{ learningStage }}</div>
            </div>
            <div>
              <div class="text-xs text-gray-500 mb-1">主要类型</div>
              <div class="text-gray-200">{{ dominantType }}</div>
            </div>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">主题概览</h4>
          <div v-if="themeRows.length === 0" class="text-sm text-gray-500 py-6 text-center">暂无主题分布数据</div>
          <div v-else class="space-y-3">
            <div v-for="row in themeRows.slice(0, 6)" :key="row.name" class="grid grid-cols-[92px_1fr_32px] items-center gap-3 text-xs">
              <span class="text-gray-400 truncate">{{ row.name }}</span>
              <div class="h-2 rounded-full bg-gray-800 overflow-hidden">
                <div class="h-full rounded-full bg-primary-500" :style="{ width: `${row.percent}%` }"></div>
              </div>
              <span class="text-gray-500 text-right">{{ row.count }}</span>
            </div>
          </div>
        </div>

        <div class="rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">主题洞察</h4>
          <ul v-if="themeInsights.length > 0" class="space-y-2">
            <li v-for="item in themeInsights.slice(0, 4)" :key="item" class="text-sm text-gray-300 leading-6 flex gap-2">
              <span class="text-primary-400">•</span>
              <span>{{ item }}</span>
            </li>
          </ul>
          <p v-else class="text-sm text-gray-500 py-6 text-center">暂无深度洞察，生成 LLM 画像后会展示。</p>
        </div>
      </div>

      <div class="mb-6 rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
        <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">知识聚类预览</h4>
        <div v-if="clusterItems.length === 0" class="text-sm text-gray-500 py-6 text-center">暂无知识聚类数据</div>
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
          <div v-for="cluster in clusterItems.slice(0, 6)" :key="cluster.name" class="rounded-lg bg-gray-900/30 border border-gray-700/30 p-4">
            <div class="text-sm font-semibold text-gray-100 mb-2">{{ cluster.name }}</div>
            <p class="text-xs text-gray-400 leading-5 line-clamp-3">{{ cluster.description || '暂无描述' }}</p>
          </div>
        </div>
      </div>

      <div v-if="!renderDetails" class="mb-6 rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
        <div class="flex items-center justify-between gap-4">
          <div>
            <h4 class="text-sm font-semibold text-gray-300 mb-1">详细画像</h4>
            <p class="text-xs text-gray-500">图谱、雷达图、完整时间线和学习路径会在展开后加载，避免进入页面时卡顿。</p>
          </div>
          <el-button type="primary" plain @click="renderDetails = true">展开详细画像</el-button>
        </div>
      </div>

      <template v-if="renderDetails">
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">主题分布</h4>
          <ThemeDistribution :themes="themeItems" />
        </div>
        <div class="rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">高频标签</h4>
          <TagCloud :tags="tagItems" />
        </div>
      </div>

      <div class="mb-6">
        <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">知识聚类</h4>
        <KnowledgeClusters :clusters="clusterItems" />
      </div>

      <div class="mb-6">
        <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">知识图谱</h4>
        <ProfileMindMap :profile="profileStore.profileJson" />
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div class="rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">学习时间线</h4>
          <LearningTimeline :timeline="timelineItems" />
        </div>
        <div class="rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">知识缺口</h4>
          <KnowledgeGaps :gaps="gapItems" />
        </div>
      </div>

      <div class="mb-6">
        <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">学习路径</h4>
        <div class="rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <LearningPath :path="pathItems" />
        </div>
      </div>

      <div v-if="growthSuggestions.length > 0" class="mb-6">
        <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">成长建议</h4>
        <div class="rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <ul class="space-y-2">
            <li
              v-for="(suggestion, index) in growthSuggestions"
              :key="index"
              class="text-sm text-gray-300 flex items-start gap-2"
            >
              <span class="text-primary-400 flex-shrink-0 mt-0.5">•</span>
          {{ suggestion }}
            </li>
          </ul>
        </div>
      </div>

      <div v-if="dynamicNotes.length > 0" class="mb-6">
        <h4 class="text-sm font-semibold text-gray-400 mb-3 uppercase">动态画像说明</h4>
        <div class="rounded-lg border border-gray-700/40 bg-gray-800/20 p-5">
          <ul class="space-y-2">
            <li v-for="note in dynamicNotes" :key="note" class="text-sm text-gray-300 leading-6 flex gap-2">
              <span class="text-cyan-400">•</span>
              <span>{{ note }}</span>
            </li>
          </ul>
        </div>
      </div>
      </template>
    </div>

    <div v-else-if="profileStore.loading" class="text-center py-16">
      <el-icon :size="40" class="animate-spin text-primary-400"><Loading /></el-icon>
      <p class="text-gray-400 mt-3">正在加载画像数据...</p>
    </div>

    <div v-else-if="profileStore.profileStatus.is_generating" class="text-center py-16">
      <el-icon :size="40" class="animate-spin text-yellow-400"><Loading /></el-icon>
      <p class="text-gray-400 mt-3">知识画像正在生成...</p>
    </div>

    <EmptyState
      v-else
      title="暂无知识画像"
      description="先导入并整理一些文档，然后生成知识画像。"
      action-text="生成画像"
      @action="handleRefreshProfile"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, type Ref } from 'vue'
import { Refresh, Loading } from '@element-plus/icons-vue'
import { useProfileStore } from '@/stores/profile'
import { useTaskProgress } from '@/composables/useTaskProgress'
import { notifySuccess, notifyError } from '@/composables/useNotification'
import type { TagRankingItem, ClusterItem, TimelineItem } from '@/api/profile'
import ProfileOverview from '@/components/profile/ProfileOverview.vue'
import ThemeDistribution from '@/components/profile/ThemeDistribution.vue'
import TagCloud from '@/components/profile/TagCloud.vue'
import KnowledgeClusters from '@/components/profile/KnowledgeClusters.vue'
import LearningTimeline from '@/components/profile/LearningTimeline.vue'
import KnowledgeGaps from '@/components/profile/KnowledgeGaps.vue'
import LearningPath from '@/components/profile/LearningPath.vue'
import ProfileMindMap from '@/components/profile/ProfileMindMap.vue'
import EmptyState from '@/components/common/EmptyState.vue'
import TaskProgress from '@/components/common/TaskProgress.vue'

const profileStore = useProfileStore()
const profileTaskId: Ref<number | null> = ref(null)
const profileTaskProgress = useTaskProgress(profileTaskId)
const renderDetails = ref(false)

const llmProfile = computed(() => profileStore.profileJson?.llm_profile)
const MAX_THEME_ITEMS = 12
const MAX_TAG_ITEMS = 30
const MAX_CLUSTER_ITEMS = 12
const MAX_TIMELINE_ITEMS = 40
const MAX_GAP_ITEMS = 10
const MAX_PATH_ITEMS = 10
const MAX_SUGGESTIONS = 20

const overview = computed(() => profileStore.profileJson?.overview)
const profileSummary = computed(() => {
  return llmProfile.value?.profile_summary || profileStore.profileJson?.summary || '当前为规则画像，尚未生成大模型深度摘要。'
})
const mainFocus = computed(() => llmProfile.value?.main_focus || overview.value?.main_focus || profileStore.profile?.main_focus || '暂无')
const learningStage = computed(() => llmProfile.value?.learning_stage || profileStore.profileJson?.learning_stage || '暂未判断')
const dominantType = computed(() => overview.value?.dominant_type || '暂无')
const overviewTopTags = computed(() => overview.value?.top_tags || tagItems.value.slice(0, 5).map((tag) => tag.name))
const themeInsights = computed(() => llmProfile.value?.theme_insights || [])
const dynamicNotes = computed(() => llmProfile.value?.dynamic_profile_notes || [])

const themeItems = computed(() => {
  const dist = profileStore.profileJson?.theme_distribution
  if (!dist || typeof dist !== 'object') return []
  const total = Object.values(dist).reduce((sum: number, v) => sum + Number(v || 0), 0) || 1
  return Object.entries(dist)
    .map(([category, count]) => ({
      category,
      count: Number(count),
      percentage: Math.round((Number(count) / total) * 1000) / 10,
    }))
    .sort((a, b) => b.count - a.count)
    .slice(0, MAX_THEME_ITEMS)
})

const themeRows = computed(() => {
  const max = Math.max(1, ...themeItems.value.map((item) => item.count))
  return themeItems.value.map((item) => ({
    name: item.category,
    count: item.count,
    percent: Math.max(4, Math.round((item.count / max) * 100)),
  }))
})

const tagItems = computed(() => {
  const ranking = profileStore.profileJson?.tag_ranking
  if (!ranking || !Array.isArray(ranking)) return []
  return ranking
    .map((t: TagRankingItem) => ({
      name: t.tag,
      count: t.count,
    }))
    .slice(0, MAX_TAG_ITEMS)
})

const clusterItems = computed(() => {
  const llmClusters = llmProfile.value?.knowledge_clusters
  if (llmClusters && llmClusters.length > 0) {
    return llmClusters.slice(0, MAX_CLUSTER_ITEMS).map((c) => ({
      name: c.cluster || '未命名',
      description: c.description || '',
      keywords: c.related_keywords || [],
      next_step: c.suggested_next_step || '',
    }))
  }

  const clusters = profileStore.profileJson?.knowledge_clusters
  if (!clusters || !Array.isArray(clusters)) return []
  return clusters.slice(0, MAX_CLUSTER_ITEMS).map((c: ClusterItem) => ({
    name: c.cluster || '未命名',
    description: c.related_items?.length
      ? `相关资料：${c.related_items.join('、')}`
      : `相关度评分：${c.score}`,
    keywords: [],
    next_step: '',
  }))
})

const timelineItems = computed(() => {
  const timeline = profileStore.profileJson?.learning_timeline
  if (!timeline || !Array.isArray(timeline)) return []
  return timeline.slice(0, MAX_TIMELINE_ITEMS).map((t: TimelineItem) => ({
    ...t,
    doc_type: t.doc_type || 'unknown',
  }))
})

const gapItems = computed(() => {
  const gaps = llmProfile.value?.knowledge_gaps || profileStore.profileJson?.knowledge_gaps
  if (!gaps || !Array.isArray(gaps)) return []
  return gaps.slice(0, MAX_GAP_ITEMS).map((g: string, index: number) => ({
    area: g.length > 20 ? `${g.substring(0, 20)}...` : g,
    current_level: 3 + (index % 3),
    importance: 7 + (index % 3),
  }))
})

const pathItems = computed(() => {
  const path = llmProfile.value?.learning_path || profileStore.profileJson?.learning_path
  if (!path || !Array.isArray(path)) return []
  return path.slice(0, MAX_PATH_ITEMS).map((step: string, index: number) => ({
    step: index + 1,
    title: step.length > 18 ? `${step.substring(0, 18)}...` : step,
    description: step,
    resources: [],
  }))
})

const growthSuggestions = computed(() => {
  return (llmProfile.value?.growth_suggestions || profileStore.profileJson?.growth_suggestions || []).slice(0, MAX_SUGGESTIONS)
})

async function handleRefreshProfile(): Promise<void> {
  try {
    profileTaskProgress.reset()
    const taskId = await profileStore.doRefreshProfile()
    if (taskId) {
      profileTaskId.value = taskId
      notifySuccess(`知识画像生成任务已提交，任务ID: ${taskId}`)
    } else {
      notifyError('提交画像生成任务失败')
    }
  } catch (error) {
    notifyError('刷新知识画像请求失败')
  }
}

onMounted(() => {
  profileStore.fetchProfile()
  profileStore.fetchProfileStatus()
})

onUnmounted(() => {
  profileStore.stopPolling()
  profileTaskProgress.reset()
  profileTaskId.value = null
  renderDetails.value = false
})
</script>
