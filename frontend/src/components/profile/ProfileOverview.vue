<template>
  <div class="profile-overview">
    <div v-if="profile" class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      <div class="overview-item rounded-lg p-4 bg-gray-800/40 border border-gray-700/30">
        <div class="text-xs text-gray-500 mb-1">资料总数</div>
        <div class="text-xl font-bold text-gray-100">{{ formatNumber(profile.total_documents) }}</div>
      </div>
      <div class="overview-item rounded-lg p-4 bg-gray-800/40 border border-gray-700/30">
        <div class="text-xs text-gray-500 mb-1">知识单元</div>
        <div class="text-xl font-bold text-blue-400">{{ formatNumber(profile.knowledge_units) }}</div>
      </div>
      <div class="overview-item rounded-lg p-4 bg-gray-800/40 border border-gray-700/30">
        <div class="text-xs text-gray-500 mb-1">主攻方向</div>
        <div class="text-base font-semibold text-primary-400">{{ mainFocus || '-' }}</div>
      </div>
      <div class="overview-item rounded-lg p-4 bg-gray-800/40 border border-gray-700/30">
        <div class="text-xs text-gray-500 mb-1">学习阶段</div>
        <div class="text-base font-semibold text-green-400">{{ learningStage || '-' }}</div>
      </div>
    </div>

    <div v-if="summary" class="summary-card rounded-lg p-4 bg-gray-800/30 border border-gray-700/30 mb-4">
      <h4 class="text-sm text-gray-400 mb-2">画像摘要</h4>
      <p class="text-sm text-gray-300 leading-relaxed">{{ summary }}</p>
    </div>

    <div v-if="profile" class="text-xs text-gray-500">
      由 {{ profile.generated_by }} 生成 · {{ formatDateTime(profile.created_at) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useProfileStore } from '@/stores/profile'
import { formatDateTime, formatNumber } from '@/utils/format'

const profileStore = useProfileStore()

const profile = computed(() => profileStore.profile)
const profileJson = computed(() => profileStore.profileJson)
const summary = computed(() => profileJson.value?.llm_profile?.profile_summary || profileJson.value?.summary || '')
const mainFocus = computed(() => profileJson.value?.llm_profile?.main_focus || profile.value?.main_focus || profileJson.value?.overview?.main_focus || '')
const learningStage = computed(() => profileJson.value?.llm_profile?.learning_stage || profileJson.value?.learning_stage || '')
</script>
