<template>
  <el-container class="main-layout h-screen">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="sidebar-container">
      <div class="sidebar-inner h-full flex flex-col">
        <div class="sidebar-logo flex items-center px-4 h-14 border-b border-dark-600">
          <el-icon :size="24" class="text-primary-400 flex-shrink-0">
            <Promotion />
          </el-icon>
          <transition name="fade">
            <span v-if="!sidebarCollapsed" class="ml-3 text-base font-bold gradient-text whitespace-nowrap">
              KnowledgeFlow
            </span>
          </transition>
        </div>

        <el-menu
          :default-active="currentRoute"
          :collapse="sidebarCollapsed"
          :collapse-transition="true"
          class="sidebar-menu flex-1"
          background-color="transparent"
          text-color="#a0aec0"
          active-text-color="#3b82f6"
          router
        >
          <el-menu-item
            v-for="navItem in navigationItems"
            :key="navItem.path"
            :index="navItem.path"
          >
            <el-icon>
              <component :is="navItem.icon" />
            </el-icon>
            <template #title>{{ navItem.title }}</template>
          </el-menu-item>
        </el-menu>

        <div class="sidebar-footer p-2 border-t border-dark-600">
          <el-button text class="w-full" @click="appStore.toggleSidebar()">
            <el-icon :size="18">
              <Fold v-if="!sidebarCollapsed" />
              <Expand v-else />
            </el-icon>
          </el-button>
        </div>
      </div>
    </el-aside>

    <el-container class="main-container">
      <el-header class="top-bar h-14 flex items-center justify-between px-6 border-b border-dark-600">
        <div class="flex items-center">
          <h2 class="text-lg font-semibold text-gray-100">
            {{ currentPageTitle }}
          </h2>
        </div>

        <div class="flex items-center gap-4">
          <el-tooltip :content="`API: ${appStore.apiStatusText}`" placement="bottom">
            <div class="flex items-center gap-1.5 cursor-pointer" @click="appStore.checkApiHealth()">
              <span
                class="w-2 h-2 rounded-full"
                :style="{ backgroundColor: appStore.apiAvailable ? '#67c23a' : '#f56c6c' }"
              ></span>
              <span class="text-xs text-gray-400">API</span>
            </div>
          </el-tooltip>

          <el-tooltip :content="`WebSocket: ${appStore.wsStatusText}`" placement="bottom">
            <div class="flex items-center gap-1.5">
              <span
                class="w-2 h-2 rounded-full"
                :style="{ backgroundColor: appStore.wsStatusColor }"
              ></span>
              <span class="text-xs text-gray-400">WS</span>
            </div>
          </el-tooltip>

          <el-tooltip content="系统设置" placement="bottom">
            <el-button text @click="navigateToSettings">
              <el-icon :size="18" class="text-gray-400 hover:text-primary-400">
                <Setting />
              </el-icon>
            </el-button>
          </el-tooltip>
        </div>
      </el-header>

      <el-main class="content-area overflow-auto p-6">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>

      <el-footer class="status-bar h-8 flex items-center justify-between px-4 text-xs border-t border-dark-600">
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-1">
            <el-icon :size="12" class="text-gray-400"><Search /></el-icon>
            <span class="text-gray-400">索引:</span>
            <span :class="searchStore.isIndexReady ? 'text-green-400' : 'text-gray-500'">
              {{ searchStore.indexStatusText }}
            </span>
          </div>

          <div class="flex items-center gap-1">
            <el-icon :size="12" class="text-gray-400"><DataAnalysis /></el-icon>
            <span class="text-gray-400">画像:</span>
            <span :style="{ color: profileStore.statusColor }">
              {{ profileStore.statusText }}
            </span>
          </div>

          <div class="flex items-center gap-1">
            <el-icon :size="12" class="text-gray-400"><Clock /></el-icon>
            <span class="text-gray-400">任务:</span>
            <span :class="taskStore.activeTaskCount > 0 ? 'text-yellow-400' : 'text-gray-500'">
              {{ taskStore.activeTaskCount }} 个运行中
            </span>
          </div>
        </div>

        <div class="text-gray-500">
          KnowledgeFlow Web v1.0
        </div>
      </el-footer>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Monitor,
  Upload,
  Link,
  Document,
  DataAnalysis,
  Search,
  Notebook,
  Setting,
  Promotion,
  Fold,
  Expand,
  Clock,
} from '@element-plus/icons-vue'
import { useAppStore } from '@/stores/app'
import { useSearchStore } from '@/stores/search'
import { useProfileStore } from '@/stores/profile'
import { useTaskStore } from '@/stores/task'
import { useWebSocket } from '@/composables/useWebSocket'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const searchStore = useSearchStore()
const profileStore = useProfileStore()
const taskStore = useTaskStore()

useWebSocket()

const navigationItems = [
  { path: '/', title: '智能工作台', icon: Monitor },
  { path: '/import/files', title: '本地文件导入', icon: Upload },
  { path: '/import/web', title: '网页导入', icon: Link },
  { path: '/documents', title: '整理结果', icon: Document },
  { path: '/profile', title: '知识画像', icon: DataAnalysis },
  { path: '/search', title: '语义检索', icon: Search },
  { path: '/logs', title: '运行日志', icon: Notebook },
  { path: '/settings', title: '系统设置', icon: Setting },
]

const currentRoute = computed(() => route.path)
const sidebarCollapsed = computed(() => appStore.sidebarCollapsed)
const currentPageTitle = computed(() => {
  return (route.meta.title as string) || 'KnowledgeFlow'
})

function navigateToSettings(): void {
  router.push('/settings')
}

onMounted(async () => {
  await appStore.checkApiHealth()
  searchStore.fetchIndexStatus()
  profileStore.fetchProfileStatus()
  taskStore.fetchTasks()
})
</script>

<style scoped>
.main-layout {
  background-color: #0d1117;
}

.sidebar-container {
  background-color: #1a202c;
  transition: width 0.3s ease;
  overflow: hidden;
}

.sidebar-inner {
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}

.sidebar-logo {
  min-height: 56px;
}

.sidebar-menu {
  border-right: none;
}

.sidebar-menu .el-menu-item {
  height: 48px;
  line-height: 48px;
  margin: 2px 8px;
  border-radius: 8px;
}

.sidebar-menu .el-menu-item:hover {
  background-color: rgba(59, 130, 246, 0.1) !important;
}

.sidebar-menu .el-menu-item.is-active {
  background-color: rgba(59, 130, 246, 0.15) !important;
  color: #3b82f6 !important;
}

.sidebar-footer .el-button {
  color: #a0aec0;
}

.sidebar-footer .el-button:hover {
  color: #e2e8f0;
}

.main-container,
.content-area {
  background-color: #0d1117;
}

.top-bar,
.status-bar {
  background-color: #1a202c;
}
</style>
