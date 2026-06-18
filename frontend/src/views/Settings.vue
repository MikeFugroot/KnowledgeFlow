<template>
  <div class="settings-page">
    <el-tabs v-model="activeTab" type="border-card" class="dark-tabs">
      <!-- Tab 1: API 配置 -->
      <el-tab-pane label="API 配置" name="api">
        <div class="space-y-5 max-w-lg">
          <div>
            <label class="block text-sm text-gray-400 mb-1">Provider</label>
            <el-select v-model="apiForm.provider" class="w-full">
              <el-option label="Qwen (通义千问)" value="qwen" />
              <el-option label="DeepSeek" value="deepseek" />
            </el-select>
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">API Key</label>
            <el-input
              v-model="apiForm.api_key"
              type="password"
              show-password
              placeholder="输入 API Key"
            />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">模型名称</label>
            <el-input v-model="apiForm.model_name" placeholder="如 qwen-plus, deepseek-chat" />
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 2: Cookie 管理 -->
      <el-tab-pane label="Cookie 管理" name="cookie">
        <div class="space-y-5 max-w-lg">
          <div>
            <label class="block text-sm text-gray-400 mb-1">B 站 Cookie</label>
            <el-input
              v-model="cookieForm.bilibili_cookie"
              type="textarea"
              :rows="3"
              placeholder="粘贴 Bilibili Cookie"
            />
            <div class="mt-2">
              <el-button size="small" :loading="testingBilibili" @click="handleTestBilibiliCookie">
                测试 Cookie
              </el-button>
            </div>
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">小红书 Cookie</label>
            <el-input
              v-model="cookieForm.xiaohongshu_cookie"
              type="textarea"
              :rows="3"
              placeholder="粘贴小红书 Cookie"
            />
            <div class="mt-2">
              <el-button size="small" :loading="testingXiaohongshu" @click="handleTestXiaohongshuCookie">
                测试 Cookie
              </el-button>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 3: Whisper 配置 -->
      <el-tab-pane label="Whisper 配置" name="whisper">
        <div class="space-y-5 max-w-lg">
          <div>
            <label class="block text-sm text-gray-400 mb-1">后端</label>
            <el-select v-model="whisperForm.backend" class="w-full">
              <el-option label="Faster Whisper" value="faster-whisper" />
              <el-option label="OpenAI Whisper" value="openai-whisper" />
            </el-select>
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">模型</label>
            <el-select v-model="whisperForm.model" class="w-full">
              <el-option label="Tiny" value="tiny" />
              <el-option label="Base" value="base" />
              <el-option label="Small" value="small" />
              <el-option label="Medium" value="medium" />
              <el-option label="Large" value="large" />
            </el-select>
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">语言</label>
            <el-select v-model="whisperForm.language" class="w-full">
              <el-option label="中文" value="zh" />
              <el-option label="英文" value="en" />
              <el-option label="日文" value="ja" />
              <el-option label="自动检测" value="auto" />
            </el-select>
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 4: 检索配置 -->
      <el-tab-pane label="检索配置" name="search">
        <div class="space-y-5 max-w-lg">
          <div>
            <label class="block text-sm text-gray-400 mb-1">Embedding 模型</label>
            <el-input v-model="searchForm.embedding_model" placeholder="如 all-MiniLM-L6-v2" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Chunk Size</label>
            <el-input-number v-model="searchForm.chunk_size" :min="100" :max="2000" :step="50" class="w-full" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Chunk Overlap</label>
            <el-input-number v-model="searchForm.chunk_overlap" :min="0" :max="500" :step="10" class="w-full" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Top K</label>
            <el-input-number v-model="searchForm.top_k" :min="1" :max="100" class="w-full" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">Candidate K</label>
            <el-input-number v-model="searchForm.candidate_k" :min="1" :max="200" class="w-full" />
          </div>
        </div>
      </el-tab-pane>

      <!-- Tab 5: 画像配置 -->
      <el-tab-pane label="画像配置" name="profile">
        <div class="space-y-5 max-w-lg">
          <div>
            <label class="block text-sm text-gray-400 mb-1">使用 LLM 生成画像</label>
            <el-switch v-model="profileForm.use_llm_profile" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">最大条目数</label>
            <el-input-number v-model="profileForm.max_items" :min="10" :max="500" :step="10" class="w-full" />
          </div>
          <div>
            <label class="block text-sm text-gray-400 mb-1">超时（秒）</label>
            <el-input-number v-model="profileForm.timeout" :min="30" :max="600" :step="10" class="w-full" />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 保存按钮 -->
    <div class="flex justify-end mt-6">
      <el-button type="primary" size="large" :loading="settingsStore.saving" @click="handleSave">
        保存配置
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import { testBilibiliCookie, testXiaohongshuCookie } from '@/api/webimport'
import { notifySuccess, notifyError } from '@/composables/useNotification'

const settingsStore = useSettingsStore()

const activeTab = ref('api')
const testingBilibili = ref(false)
const testingXiaohongshu = ref(false)

// 表单数据
const apiForm = reactive({
  provider: 'qwen' as 'qwen' | 'deepseek',
  api_key: '',
  model_name: '',
})

const cookieForm = reactive({
  bilibili_cookie: '',
  xiaohongshu_cookie: '',
})

const whisperForm = reactive({
  backend: 'faster-whisper' as 'faster-whisper' | 'openai-whisper',
  model: 'medium',
  language: 'zh',
})

const searchForm = reactive({
  embedding_model: 'all-MiniLM-L6-v2',
  chunk_size: 500,
  chunk_overlap: 50,
  top_k: 10,
  candidate_k: 50,
})

const profileForm = reactive({
  use_llm_profile: true,
  max_items: 100,
  timeout: 120,
})

/** 从 store 同步到表单 */
function syncFromStore(): void {
  const api = settingsStore.apiConfig
  apiForm.provider = api.provider
  apiForm.api_key = api.api_key
  apiForm.model_name = api.model_name

  const cookie = settingsStore.cookieConfig
  cookieForm.bilibili_cookie = cookie.bilibili_cookie
  cookieForm.xiaohongshu_cookie = cookie.xiaohongshu_cookie

  const whisper = settingsStore.whisperConfig
  whisperForm.backend = whisper.backend
  whisperForm.model = whisper.model
  whisperForm.language = whisper.language

  const search = settingsStore.searchConfig
  searchForm.embedding_model = search.embedding_model
  searchForm.chunk_size = search.chunk_size
  searchForm.chunk_overlap = search.chunk_overlap
  searchForm.top_k = search.top_k
  searchForm.candidate_k = search.candidate_k

  const profile = settingsStore.profileConfig
  profileForm.use_llm_profile = profile.use_llm_profile
  profileForm.max_items = profile.max_items
  profileForm.timeout = profile.timeout
}

/** 保存配置 */
async function handleSave(): Promise<void> {
  // 构建 configs 数组，匹配后端 ConfigUpdateRequest 格式
  const configs = [
    { key: 'api_provider', value: apiForm.provider, value_type: 'string' as const, description: 'API Provider', is_sensitive: false },
    { key: 'api_key', value: apiForm.api_key, value_type: 'string' as const, description: 'API Key', is_sensitive: true },
    { key: 'model_name', value: apiForm.model_name, value_type: 'string' as const, description: '模型名称', is_sensitive: false },
    { key: 'bilibili_cookie', value: cookieForm.bilibili_cookie, value_type: 'string' as const, description: 'B站 Cookie', is_sensitive: true },
    { key: 'xiaohongshu_cookie', value: cookieForm.xiaohongshu_cookie, value_type: 'string' as const, description: '小红书 Cookie', is_sensitive: true },
    { key: 'whisper_backend', value: whisperForm.backend, value_type: 'string' as const, description: 'Whisper 后端', is_sensitive: false },
    { key: 'whisper_model', value: whisperForm.model, value_type: 'string' as const, description: 'Whisper 模型', is_sensitive: false },
    { key: 'whisper_language', value: whisperForm.language, value_type: 'string' as const, description: 'Whisper 语言', is_sensitive: false },
    { key: 'embedding_model', value: searchForm.embedding_model, value_type: 'string' as const, description: 'Embedding 模型', is_sensitive: false },
    { key: 'chunk_size', value: String(searchForm.chunk_size), value_type: 'number' as const, description: 'Chunk Size', is_sensitive: false },
    { key: 'chunk_overlap', value: String(searchForm.chunk_overlap), value_type: 'number' as const, description: 'Chunk Overlap', is_sensitive: false },
    { key: 'top_k', value: String(searchForm.top_k), value_type: 'number' as const, description: 'Top K', is_sensitive: false },
    { key: 'candidate_k', value: String(searchForm.candidate_k), value_type: 'number' as const, description: 'Candidate K', is_sensitive: false },
    { key: 'use_llm_profile', value: String(profileForm.use_llm_profile), value_type: 'boolean' as const, description: '使用 LLM 生成画像', is_sensitive: false },
    { key: 'profile_max_items', value: String(profileForm.max_items), value_type: 'number' as const, description: '画像最大条目数', is_sensitive: false },
    { key: 'profile_timeout', value: String(profileForm.timeout), value_type: 'number' as const, description: '画像超时', is_sensitive: false },
  ]

  const ok = await settingsStore.saveSettings({ configs })
  if (ok) {
    notifySuccess('配置保存成功')
  } else {
    notifyError('配置保存失败')
  }
}

/** 测试 B 站 Cookie */
async function handleTestBilibiliCookie(): Promise<void> {
  if (!cookieForm.bilibili_cookie.trim()) {
    notifyError('请先输入 B 站 Cookie')
    return
  }

  testingBilibili.value = true
  try {
    const result = await testBilibiliCookie(cookieForm.bilibili_cookie)
    if (result.success) {
      notifySuccess(`Cookie 有效，用户: ${result.username || '未知'}`)
    } else {
      notifyError(`Cookie 无效: ${result.message}`)
    }
  } catch (error) {
    notifyError('测试 Cookie 请求失败')
  } finally {
    testingBilibili.value = false
  }
}

/** 测试小红书 Cookie */
async function handleTestXiaohongshuCookie(): Promise<void> {
  if (!cookieForm.xiaohongshu_cookie.trim()) {
    notifyError('请先输入小红书 Cookie')
    return
  }

  testingXiaohongshu.value = true
  try {
    const result = await testXiaohongshuCookie(cookieForm.xiaohongshu_cookie)
    if (result.success) {
      notifySuccess(`Cookie 有效，用户: ${result.username || '未知'}`)
    } else {
      notifyError(`Cookie 无效: ${result.message}`)
    }
  } catch (error) {
    notifyError('测试 Cookie 请求失败')
  } finally {
    testingXiaohongshu.value = false
  }
}

// 加载配置
onMounted(async () => {
  await settingsStore.fetchSettings()
  syncFromStore()
})

// 当 settingsList 变化时同步到表单
watch(() => settingsStore.settingsList, () => {
  syncFromStore()
}, { deep: true })
</script>

<style scoped>
.dark-tabs :deep(.el-tabs__content) {
  padding: 20px;
}
</style>
