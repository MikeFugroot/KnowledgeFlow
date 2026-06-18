<template>
  <div class="video-player">
    <div v-if="!src" class="text-center py-12 text-gray-500 text-sm">
      未指定视频源
    </div>
    <div v-else class="video-container rounded-lg overflow-hidden border border-gray-700/30">
      <video
        ref="videoRef"
        :src="src"
        controls
        class="w-full"
        :style="{ maxHeight: maxHeight }"
        @loadedmetadata="handleLoadedMetadata"
        @timeupdate="handleTimeUpdate"
      >
        您的浏览器不支持视频播放
      </video>
      <!-- 时间点跳转 -->
      <div v-if="timestamps && timestamps.length > 0" class="timestamps-bar flex gap-2 p-3 bg-gray-800/60 border-t border-gray-700/30">
        <el-button
          v-for="(ts, index) in timestamps"
          :key="index"
          size="small"
          text
          @click="jumpTo(ts.time)"
        >
          {{ ts.label }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

export interface Timestamp {
  time: number
  label: string
}

const props = withDefaults(defineProps<{
  /** 视频 URL */
  src?: string
  /** 最大高度 */
  maxHeight?: string
  /** 时间点列表 */
  timestamps?: Timestamp[]
  /** 初始播放时间（秒） */
  initialTime?: number
}>(), {
  maxHeight: '500px',
  timestamps: () => [],
  initialTime: 0,
})

const emit = defineEmits<{
  (e: 'time-update', currentTime: number): void
}>()

const videoRef = ref<HTMLVideoElement | null>(null)

/** 跳转到指定时间点 */
function jumpTo(time: number): void {
  if (videoRef.value) {
    videoRef.value.currentTime = time
    videoRef.value.play().catch(() => {
      // 自动播放被阻止时忽略
    })
  }
}

/** 视频元数据加载完成后跳转到初始时间 */
function handleLoadedMetadata(): void {
  if (props.initialTime > 0 && videoRef.value) {
    videoRef.value.currentTime = props.initialTime
  }
}

/** 时间更新 */
function handleTimeUpdate(): void {
  if (videoRef.value) {
    emit('time-update', videoRef.value.currentTime)
  }
}
</script>
