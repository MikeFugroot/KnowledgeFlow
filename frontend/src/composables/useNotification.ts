/**
 * 通知组合式函数
 * 封装 ElNotification / ElMessage，提供统一的消息通知接口
 */
import { ElMessage, ElNotification, ElMessageBox } from 'element-plus'

/**
 * 成功消息提示
 */
export function notifySuccess(message: string, duration: number = 3000): void {
  ElMessage.success({
    message,
    duration,
    showClose: true,
  })
}

/**
 * 错误消息提示
 */
export function notifyError(message: string, duration: number = 5000): void {
  ElMessage.error({
    message,
    duration,
    showClose: true,
  })
}

/**
 * 警告消息提示
 */
export function notifyWarning(message: string, duration: number = 4000): void {
  ElMessage.warning({
    message,
    duration,
    showClose: true,
  })
}

/**
 * 信息消息提示
 */
export function notifyInfo(message: string, duration: number = 3000): void {
  ElMessage.info({
    message,
    duration,
    showClose: true,
  })
}

/**
 * 成功通知（右上角弹出）
 */
export function notifySuccessBox(title: string, message: string = '', duration: number = 4500): void {
  ElNotification.success({
    title,
    message,
    duration,
  })
}

/**
 * 错误通知（右上角弹出）
 */
export function notifyErrorBox(title: string, message: string = '', duration: number = 0): void {
  ElNotification.error({
    title,
    message,
    duration, // 默认不自动关闭
  })
}

/**
 * 警告通知（右上角弹出）
 */
export function notifyWarningBox(title: string, message: string = '', duration: number = 4500): void {
  ElNotification.warning({
    title,
    message,
    duration,
  })
}

/**
 * 信息通知（右上角弹出）
 */
export function notifyInfoBox(title: string, message: string = '', duration: number = 4500): void {
  ElNotification.info({
    title,
    message,
    duration,
  })
}

/**
 * 确认对话框
 * @param message - 确认消息
 * @param title - 标题
 * @returns 用户是否确认
 */
export async function confirmAction(
  message: string,
  title: string = '确认操作'
): Promise<boolean> {
  try {
    await ElMessageBox.confirm(message, title, {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
    return true
  } catch {
    return false
  }
}

/**
 * 删除确认对话框
 */
export async function confirmDelete(
  message: string = '此操作将永久删除该数据，是否继续？',
  title: string = '删除确认'
): Promise<boolean> {
  try {
    await ElMessageBox.confirm(message, title, {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'error',
      confirmButtonClass: 'el-button--danger',
    })
    return true
  } catch {
    return false
  }
}

/**
 * useNotification 组合式函数
 * 提供所有通知方法的 Vue 组件内使用接口
 */
export function useNotification() {
  return {
    success: notifySuccess,
    error: notifyError,
    warning: notifyWarning,
    info: notifyInfo,
    successBox: notifySuccessBox,
    errorBox: notifyErrorBox,
    warningBox: notifyWarningBox,
    infoBox: notifyInfoBox,
    confirm: confirmAction,
    confirmDelete,
  }
}
