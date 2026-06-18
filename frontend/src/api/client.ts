/**
 * Axios 实例 + 拦截器
 * 统一错误处理、token 预留、响应格式 {code, data, message}
 */
import axios, {
  type AxiosInstance,
  type AxiosRequestConfig,
  type AxiosResponse,
  type InternalAxiosRequestConfig,
} from 'axios'
import { ElMessage } from 'element-plus'
import { clearAccessCode, getAccessCode } from '@/utils/accessCode'

/** API 统一响应格式 */
export interface ApiResponse<T = unknown> {
  code: number
  data: T
  message: string
}

/** 分页数据格式 */
export interface PaginatedData<T = unknown> {
  items: T[]
  total: number
  page: number
  page_size: number
}

/** 创建 Axios 实例 */
const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  timeout: 60000, // 默认 60s 超时（大文件上传可能需要更长）
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * 请求拦截器
 * - 注入 token（多用户预留）
 * - 请求开始时可设置全局 loading
 */
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Token 预留：从 localStorage 读取
    const token = localStorage.getItem('kf_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    const accessCode = getAccessCode()
    if (accessCode && config.headers) {
      config.headers['X-KF-Access-Code'] = accessCode
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 * - 统一处理 {code, data, message} 格式
 * - code !== 0 时显示错误消息
 */
client.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const res = response.data

    // code === 0 表示成功，直接返回 data
    if (res.code === 0) {
      return response
    }

    // 业务错误处理
    const errorMessage = res.message || '请求失败'
    ElMessage.error(errorMessage)
    return Promise.reject(new Error(errorMessage))
  },
  (error) => {
    // HTTP 错误处理
    let message = '网络异常，请稍后重试'
    if (error.response) {
      const status = error.response.status
      const detail = error.response.data?.detail
      const serverMessage = typeof detail === 'string' ? detail : error.response.data?.message
      switch (status) {
        case 400:
          message = serverMessage || '请求参数错误'
          break
        case 401:
          message = serverMessage || '未授权，请重新登录'
          clearAccessCode()
          window.dispatchEvent(new Event('kf-access-denied'))
          break
        case 403:
          message = serverMessage || '拒绝访问'
          break
        case 404:
          message = serverMessage || '请求资源不存在'
          break
        case 500:
          message = serverMessage || '服务器内部错误'
          break
        case 502:
          message = serverMessage || '网关错误'
          break
        case 503:
          message = serverMessage || '服务不可用'
          break
        default:
          message = serverMessage || `请求失败 (${status})`
      }
    } else if (error.code === 'ECONNABORTED') {
      message = '请求超时，请稍后重试'
    } else if (error.code === 'ERR_CANCELED') {
      // 请求被取消，静默处理
      return Promise.reject(error)
    }

    ElMessage.error(message)
    return Promise.reject(error)
  }
)

/**
 * 封装 GET 请求
 */
export async function get<T = unknown>(
  url: string,
  params?: Record<string, unknown>,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await client.get<ApiResponse<T>>(url, {
    params,
    ...config,
  })
  return response.data.data
}

/**
 * 封装 POST 请求
 */
export async function post<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await client.post<ApiResponse<T>>(url, data, config)
  return response.data.data
}

/**
 * 封装 PUT 请求
 */
export async function put<T = unknown>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await client.put<ApiResponse<T>>(url, data, config)
  return response.data.data
}

/**
 * 封装 DELETE 请求
 */
export async function del<T = unknown>(
  url: string,
  params?: Record<string, unknown>,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await client.delete<ApiResponse<T>>(url, {
    params,
    ...config,
  })
  return response.data.data
}

/**
 * 上传文件（multipart/form-data）
 */
export async function upload<T = unknown>(
  url: string,
  formData: FormData,
  config?: AxiosRequestConfig
): Promise<T> {
  const response = await client.post<ApiResponse<T>>(url, formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
    timeout: 300000, // 上传超时 5 分钟
    ...config,
  })
  return response.data.data
}

export default client
