<template>
  <div class="bilibili-panel">
    <!-- Cookie 状态提示 -->
    <el-alert
      v-if="!hasCookie"
      title="未配置 B 站 Cookie"
      description="部分收藏夹内容需要登录后才能访问，请先在系统设置中配置 B 站 Cookie"
      type="warning"
      :closable="false"
      show-icon
      class="mb-4"
    />

    <!-- 加载收藏夹列表 -->
    <div class="mb-4">
      <el-button
        type="primary"
        :loading="loadingFolders"
        @click="loadFolders"
      >
        <el-icon class="mr-1"><FolderOpened /></el-icon>
        获取收藏夹列表
      </el-button>
    </div>

    <!-- 收藏夹列表 -->
    <div v-if="folders.length > 0" class="space-y-3 mb-4">
      <div
        v-for="folder in folders"
        :key="folder.folder_id"
        class="folder-item flex items-center justify-between p-3 rounded-lg border border-gray-700/40 bg-gray-800/30 hover:border-primary-500/30 transition-colors"
      >
        <div>
          <div class="text-sm text-gray-200">{{ folder.title }}</div>
          <div class="text-xs text-gray-500 mt-1">{{ folder.media_count }} 个视频</div>
        </div>
        <div class="flex items-center gap-2">
          <el-input-number
            v-model="folderMaxVideos[folder.folder_id]"
            :min="1"
            :max="100"
            size="small"
            class="w-24"
            placeholder="最大数"
          />
          <el-button
            size="small"
            type="primary"
            :loading="importingFolderId === folder.folder_id"
            @click="handleImportFolder(folder)"
          >
            导入
          </el-button>
        </div>
      </div>
    </div>

    <div v-else-if="foldersLoaded && folders.length === 0" class="text-center py-6 text-gray-500 text-sm">
      暂无收藏夹
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { FolderOpened } from '@element-plus/icons-vue'
import { getBilibiliFolders, importBilibiliFavorites, type BilibiliFolder } from '@/api/webimport'
import { useSettingsStore } from '@/stores/settings'
import { notifySuccess, notifyError } from '@/composables/useNotification'

const emit = defineEmits<{
  (e: 'task-created', taskId: number): void
}>()

const settingsStore = useSettingsStore()

const folders = ref<BilibiliFolder[]>([])
const loadingFolders = ref(false)
const importingFolderId = ref<number | null>(null)
const foldersLoaded = ref(false)
const folderMaxVideos = reactive<Record<number, number>>({})

/** 是否有 B 站 Cookie */
const hasCookie = computed(() => settingsStore.hasBilibiliCookie)

/** 加载收藏夹列表 */
async function loadFolders(): Promise<void> {
  loadingFolders.value = true
  try {
    folders.value = await getBilibiliFolders()
    foldersLoaded.value = true
    // 初始化每个收藏夹的最大视频数
    folders.value.forEach((f) => {
      if (!folderMaxVideos[f.folder_id]) {
        folderMaxVideos[f.folder_id] = Math.min(f.media_count, 20)
      }
    })
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : '获取收藏夹列表失败'
    notifyError(msg)
  } finally {
    loadingFolders.value = false
  }
}

/** 导入收藏夹 */
async function handleImportFolder(folder: BilibiliFolder): Promise<void> {
  importingFolderId.value = folder.folder_id
  try {
    const result = await importBilibiliFavorites({
      folder_id: folder.folder_id,
      max_videos: folderMaxVideos[folder.folder_id] || 20,
    })
    notifySuccess(`已提交导入任务「${folder.title}」，任务ID: ${result.task_id}`)
    emit('task-created', result.task_id)
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : '导入收藏夹失败'
    notifyError(msg)
  } finally {
    importingFolderId.value = null
  }
}
</script>
