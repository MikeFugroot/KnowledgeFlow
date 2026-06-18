<template>
  <router-view v-if="authorized" />
  <div v-else class="access-page">
    <div class="access-panel">
      <div class="access-title">KnowledgeFlow</div>
      <div class="access-subtitle">输入访问口令后继续</div>
      <el-input
        v-model="code"
        type="password"
        size="large"
        show-password
        placeholder="访问口令"
        @keyup.enter="handleLogin"
      />
      <el-button
        type="primary"
        size="large"
        :loading="loading"
        class="access-button"
        @click="handleLogin"
      >
        进入
      </el-button>
      <div class="access-hint">同一设备只需输入一次。</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import axios from 'axios'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getAccessCode, setAccessCode } from '@/utils/accessCode'

const authorized = ref(false)
const loading = ref(false)
const code = ref('')

onMounted(() => {
  const storedCode = getAccessCode()
  if (storedCode) {
    code.value = storedCode
    authorized.value = true
  }
  window.addEventListener('kf-access-denied', handleAccessDenied)
})

onBeforeUnmount(() => {
  window.removeEventListener('kf-access-denied', handleAccessDenied)
})

async function handleLogin(): Promise<void> {
  const trimmed = code.value.trim()
  if (!trimmed) {
    ElMessage.warning('请输入访问口令')
    return
  }

  loading.value = true
  try {
    const baseURL = import.meta.env.VITE_API_BASE_URL || ''
    await axios.post(`${baseURL}/api/auth/login`, { code: trimmed })
    setAccessCode(trimmed)
    authorized.value = true
  } catch (error) {
    ElMessage.error('访问口令不正确')
  } finally {
    loading.value = false
  }
}

function handleAccessDenied(): void {
  authorized.value = false
  code.value = ''
}
</script>

<style>
#app {
  width: 100%;
  height: 100vh;
  overflow: hidden;
}

.access-page {
  width: 100%;
  height: 100%;
  display: grid;
  place-items: center;
  background:
    linear-gradient(180deg, rgba(15, 23, 42, 0.94), rgba(3, 7, 18, 0.98)),
    #050914;
}

.access-panel {
  width: min(360px, calc(100vw - 40px));
  padding: 28px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.82);
  box-shadow: 0 20px 80px rgba(0, 0, 0, 0.42);
}

.access-title {
  color: #f8fafc;
  font-size: 24px;
  font-weight: 800;
  margin-bottom: 6px;
}

.access-subtitle {
  color: #94a3b8;
  font-size: 14px;
  margin-bottom: 18px;
}

.access-button {
  width: 100%;
  margin-top: 14px;
}

.access-hint {
  color: #64748b;
  font-size: 12px;
  margin-top: 14px;
  text-align: center;
}
</style>
