<template>
  <div class="logs-page">
    <h3 class="text-base font-semibold text-gray-200 mb-4">运行日志</h3>
    <LogStream max-height="calc(100vh - 240px)" />
  </div>
</template>

<script setup lang="ts">
import LogStream from '@/components/common/LogStream.vue'
</script>
