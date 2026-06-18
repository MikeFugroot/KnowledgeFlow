<template>
  <div class="search-result-detail" v-if="result">
    <div class="detail-header mb-4">
      <h3 class="text-base font-semibold text-gray-200 mb-2">
        {{ result.doc_title }}
      </h3>
      <div class="flex items-center gap-3 text-xs text-gray-500">
        <el-tag size="small" effect="plain" type="info">
          {{ DOC_TYPE_LABELS[result.doc_type] || result.doc_type }}
        </el-tag>
        <span v-if="result.section_title">{{ result.section_title }}</span>
        <span v-if="result.location">{{ result.location }}</span>
      </div>
    </div>

    <div class="mb-4 flex gap-2">
      <el-button
        type="primary"
        size="small"
        :loading="openingFile"
        @click="handleOpenFile"
      >
        <el-icon class="mr-1"><FolderOpened /></el-icon>
        打开文档
      </el-button>
      <el-button
        v-if="result.source && result.source.startsWith('http')"
        size="small"
        @click="openUrl(result.source)"
      >
        <el-icon class="mr-1"><Link /></el-icon>
        访问来源
      </el-button>
    </div>

    <div class="detail-section mb-4">
      <h4 class="text-sm text-gray-400 mb-2">命中文本</h4>
      <div class="hit-text rounded-lg p-3 bg-gray-800/40 text-sm text-gray-300 leading-relaxed border border-gray-700/30">
        <span v-html="highlightedText"></span>
      </div>
    </div>

    <div v-if="result.hit_terms && result.hit_terms.length > 0" class="detail-section mb-4">
      <h4 class="text-sm text-gray-400 mb-2">命中关键词</h4>
      <div class="flex flex-wrap gap-2">
        <el-tag
          v-for="term in result.hit_terms"
          :key="term"
          size="small"
          effect="dark"
          type="warning"
        >
          {{ term }}
        </el-tag>
      </div>
    </div>

    <div class="detail-section mb-4">
      <h4 class="text-sm text-gray-400 mb-2">评分详情</h4>
      <div class="grid grid-cols-3 gap-3">
        <div class="score-item rounded-lg p-3 bg-gray-800/30 border border-gray-700/30 text-center">
          <div class="text-xs text-gray-500 mb-1">综合分</div>
          <div class="text-lg font-bold text-primary-400">{{ result.score.toFixed(3) }}</div>
        </div>
        <div class="score-item rounded-lg p-3 bg-gray-800/30 border border-gray-700/30 text-center">
          <div class="text-xs text-gray-500 mb-1">语义分</div>
          <div class="text-lg font-bold text-green-400">{{ result.dense_score.toFixed(3) }}</div>
        </div>
        <div class="score-item rounded-lg p-3 bg-gray-800/30 border border-gray-700/30 text-center">
          <div class="text-xs text-gray-500 mb-1">词面分</div>
          <div class="text-lg font-bold text-yellow-400">{{ result.lexical_score.toFixed(3) }}</div>
        </div>
      </div>
    </div>

    <div v-if="result.match_reason" class="detail-section mb-4">
      <h4 class="text-sm text-gray-400 mb-2">命中原因</h4>
      <p class="text-sm text-gray-400 leading-relaxed">{{ result.match_reason }}</p>
    </div>

    <div v-if="result.source" class="detail-section">
      <h4 class="text-sm text-gray-400 mb-2">来源</h4>
      <a
        v-if="result.source.startsWith('http')"
        :href="result.source"
        target="_blank"
        class="text-sm text-primary-400 hover:underline break-all"
      >
        {{ result.source }}
      </a>
      <span v-else class="text-sm text-gray-500 break-all">{{ result.source }}</span>
    </div>
  </div>

  <div v-else class="text-center py-12 text-gray-500 text-sm">
    点击左侧搜索结果查看详情
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { FolderOpened, Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useSearchStore } from '@/stores/search'
import { getDocumentFileUrl, openDocumentLocally } from '@/api/document'
import { DOC_TYPE_LABELS } from '@/utils/constants'
import { appendAccessCode } from '@/utils/accessCode'

const searchStore = useSearchStore()
const result = computed(() => searchStore.selectedResult)
const openingFile = ref(false)

const highlightedText = computed(() => {
  if (!result.value) return ''
  let text = result.value.chunk_text || ''

  for (const term of result.value.hit_terms || []) {
    const regex = new RegExp(`(${escapeRegExp(term)})`, 'gi')
    text = text.replace(regex, '<mark class="bg-yellow-500/30 text-yellow-200 px-0.5 rounded">$1</mark>')
  }

  return text
})

async function handleOpenFile(): Promise<void> {
  if (!result.value) return

  const documentId = result.value.document_id
  const location = result.value.location || undefined
  const source = result.value.source

  if (!documentId) {
    if (source?.startsWith('http')) {
      window.open(source, '_blank')
    } else {
      ElMessage.warning('当前搜索结果没有关联到文档记录，请重建搜索索引后再试。')
    }
    return
  }

  openingFile.value = true
  try {
    const localResult = await openDocumentLocally(documentId, location)
    if (localResult.opened) {
      if (localResult.method === 'sumatra_pdf' && !localResult.page_number && location) {
        ElMessage.warning(`PDF 已用 SumatraPDF 打开，但未从位置“${location}”解析到页码`)
      } else {
        const pageText = localResult.page_number ? `到第 ${localResult.page_number} 页` : ''
        ElMessage.success(`文档已打开${pageText}`)
      }
    } else if (localResult.url) {
      window.open(toPositionedUrl(localResult.url, {
        doc_type: localResult.doc_type,
        page_number: localResult.page_number ?? null,
        video_start: localResult.video_start ?? null,
        video_end: localResult.video_end ?? null,
      }), '_blank')
    } else {
      ElMessage.warning('文档存在记录，但没有可打开的文件路径或来源链接。')
    }
  } catch (error) {
    try {
      const fileInfo = await getDocumentFileUrl(documentId, location)
      if (fileInfo.file_url) {
        window.open(toPositionedUrl(fileInfo.file_url, fileInfo), '_blank')
        return
      }
      if (fileInfo.source_url) {
        window.open(toPositionedUrl(fileInfo.source_url, fileInfo), '_blank')
        return
      }
      ElMessage.error('打开文档失败')
    } catch (fallbackError) {
      ElMessage.error('打开文档失败')
      console.error('打开文档失败:', error, fallbackError)
    }
  } finally {
    openingFile.value = false
  }
}

function openUrl(url: string): void {
  window.open(url, '_blank')
}

function toPositionedUrl(url: string, fileInfo: {
  doc_type: string
  page_number: number | null
  video_start: number | null
  video_end: number | null
}): string {
  const [baseUrl] = appendAccessCode(url).split('#')
  const separator = baseUrl.includes('?') ? '&' : '?'
  const cacheBustedUrl = `${baseUrl}${separator}kf_open=${Date.now()}`
  const lowerUrl = baseUrl.toLowerCase()

  if (fileInfo.page_number && (fileInfo.doc_type === 'pdf' || lowerUrl.endsWith('.pdf'))) {
    return `${cacheBustedUrl}#page=${fileInfo.page_number}`
  }

  const isMedia = ['video', 'audio'].includes(fileInfo.doc_type) ||
    /\.(mp4|mov|avi|mkv|m4a|mp3|wav)(\?|$)/i.test(baseUrl)
  if (fileInfo.video_start !== null && isMedia) {
    const start = Math.max(0, fileInfo.video_start)
    const end = fileInfo.video_end !== null ? `,${Math.max(start, fileInfo.video_end)}` : ''
    return `${cacheBustedUrl}#t=${start}${end}`
  }

  return cacheBustedUrl
}

function escapeRegExp(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}
</script>
