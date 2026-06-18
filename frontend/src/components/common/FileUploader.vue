<template>
  <div
    class="file-uploader"
    :class="{ 'is-dragover': isDragover, 'is-disabled': disabled }"
    @dragenter.prevent="onDragEnter"
    @dragover.prevent="onDragOver"
    @dragleave.prevent="onDragLeave"
    @drop.prevent="onDrop"
    @click="triggerFileInput"
  >
    <input
      ref="fileInputRef"
      type="file"
      :accept="acceptTypes"
      :multiple="multiple"
      class="hidden"
      @change="onFileInputChange"
    />
    <div class="upload-content flex flex-col items-center justify-center py-8">
      <el-icon :size="48" class="text-primary-400 mb-4">
        <Upload />
      </el-icon>
      <p class="text-gray-300 text-base mb-2">
        {{ isDragover ? '释放文件以上传' : '拖拽文件到此处，或点击选择' }}
      </p>
      <p class="text-gray-500 text-xs">
        支持 {{ extensionList }} 等格式，单文件最大 500MB
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { Upload } from '@element-plus/icons-vue'
import { SUPPORTED_EXTENSIONS, MAX_FILE_SIZE } from '@/utils/constants'
import { formatFileSize } from '@/utils/format'
import { useNotification } from '@/composables/useNotification'

const props = withDefaults(defineProps<{
  /** 允许的文件扩展名列表 */
  extensions?: string[]
  /** 是否多选 */
  multiple?: boolean
  /** 是否禁用 */
  disabled?: boolean
}>(), {
  extensions: () => SUPPORTED_EXTENSIONS,
  multiple: true,
  disabled: false,
})

const emit = defineEmits<{
  (e: 'select', files: File[]): void
}>()

const notification = useNotification()

const fileInputRef = ref<HTMLInputElement | null>(null)
const isDragover = ref(false)

/** 接受的文件类型字符串 */
const acceptTypes = computed(() => props.extensions.join(','))

/** 扩展名展示列表 */
const extensionList = computed(() => props.extensions.slice(0, 8).join(', '))

/** 拖拽进入 */
function onDragEnter(): void {
  if (props.disabled) return
  isDragover.value = true
}

/** 拖拽悬停 */
function onDragOver(): void {
  if (props.disabled) return
  isDragover.value = true
}

/** 拖拽离开 */
function onDragLeave(): void {
  isDragover.value = false
}

/** 文件放置 */
function onDrop(event: DragEvent): void {
  isDragover.value = false
  if (props.disabled) return

  const files = event.dataTransfer?.files
  if (!files || files.length === 0) return

  handleFiles(Array.from(files))
}

/** 触发文件选择 */
function triggerFileInput(): void {
  if (props.disabled) return
  fileInputRef.value?.click()
}

/** 文件输入框变化 */
function onFileInputChange(event: Event): void {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) return

  handleFiles(Array.from(files))
  // 清空 input 以便重复选择同一文件
  input.value = ''
}

/** 处理选中的文件 */
function handleFiles(files: File[]): void {
  const validFiles: File[] = []
  const invalidFiles: string[] = []

  for (const file of files) {
    // 检查文件大小
    if (file.size > MAX_FILE_SIZE) {
      invalidFiles.push(`${file.name} (${formatFileSize(file.size)}) 超出大小限制`)
      continue
    }

    // 检查文件扩展名
    const ext = '.' + file.name.split('.').pop()?.toLowerCase()
    if (!props.extensions.includes(ext)) {
      invalidFiles.push(`${file.name} 格式不支持`)
      continue
    }

    validFiles.push(file)
  }

  if (invalidFiles.length > 0) {
    notification.warning(`${invalidFiles.length} 个文件不合规: ${invalidFiles.slice(0, 3).join('; ')}`)
  }

  if (validFiles.length > 0) {
    emit('select', validFiles)
  }
}
</script>

<style scoped>
.file-uploader {
  border: 2px dashed #4a5568;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background-color: rgba(45, 55, 72, 0.3);
}

.file-uploader:hover {
  border-color: #3b82f6;
  background-color: rgba(59, 130, 246, 0.05);
}

.file-uploader.is-dragover {
  border-color: #3b82f6;
  background-color: rgba(59, 130, 246, 0.1);
}

.file-uploader.is-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
