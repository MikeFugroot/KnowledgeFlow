<template>
  <div class="learning-path">
    <div v-if="path.length === 0" class="text-center py-8 text-gray-500 text-sm">
      暂无学习路径数据
    </div>
    <el-steps v-else :active="0" direction="vertical" finish-status="success">
      <el-step
        v-for="step in path"
        :key="step.step"
        :title="`步骤 ${step.step}: ${step.title}`"
        :description="stepDescription(step)"
      >
        <template #description>
          <div class="step-description">
            <p class="text-sm text-gray-400 mb-2">{{ step.description }}</p>
            <div v-if="step.resources && step.resources.length > 0" class="flex flex-wrap gap-1">
              <el-tag
                v-for="(res, idx) in step.resources"
                :key="idx"
                size="small"
                effect="plain"
                type="info"
                class="text-xs"
              >
                {{ res }}
              </el-tag>
            </div>
          </div>
        </template>
      </el-step>
    </el-steps>
  </div>
</template>

<script setup lang="ts">
import type { PathItem } from '@/api/profile'

defineProps<{
  path: PathItem[]
}>()

function stepDescription(step: PathItem): string {
  return step.description
}
</script>

<style scoped>
.step-description {
  padding: 4px 0 8px;
}
</style>
