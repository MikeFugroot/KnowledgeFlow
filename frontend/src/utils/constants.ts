export const API_UPLOAD = {
  FILES: '/api/upload/files',
  PROCESS: '/api/upload/process',
  DOWNLOAD: (id: number) => `/api/upload/files/${id}/download`,
} as const

export const API_DOCUMENT = {
  LIST: '/api/documents',
  DETAIL: (id: number) => `/api/documents/${id}`,
  FILE_URL: (id: number) => `/api/documents/${id}/file-url`,
  OPEN_LOCALLY: (id: number) => `/api/documents/${id}/open-locally`,
  BATCH_DELETE: '/api/documents/batch',
  REORGANIZE: (id: number) => `/api/documents/${id}/reorganize`,
  EXPORT: '/api/documents/export',
} as const

export const API_WEBIMPORT = {
  URL: '/api/webimport/url',
  URLS: '/api/webimport/urls',
  BILIBILI_FOLDERS: '/api/webimport/bilibili/folders',
  BILIBILI_FAVORITES: '/api/webimport/bilibili/favorites',
  BILIBILI_TEST_COOKIE: '/api/webimport/bilibili/test-cookie',
  XIAOHONGSHU_TEST_COOKIE: '/api/webimport/xiaohongshu/test-cookie',
  BOOKMARKS: '/api/webimport/bookmarks',
} as const

export const API_SEARCH = {
  QUERY: '/api/search',
  INDEX_BUILD: '/api/search/index/build',
  INDEX_STATUS: '/api/search/index/status',
} as const

export const API_PROFILE = {
  GET: '/api/profile',
  REFRESH: '/api/profile/refresh',
  STATUS: '/api/profile/status',
} as const

export const API_TASK = {
  LIST: '/api/tasks',
  DETAIL: (id: number) => `/api/tasks/${id}`,
  CANCEL: (id: number) => `/api/tasks/${id}/cancel`,
} as const

export const API_SETTINGS = {
  GET: '/api/settings',
  UPDATE: '/api/settings',
} as const

export const API_DASHBOARD = {
  STATS: '/api/dashboard/stats',
} as const

export enum WSMessageType {
  TASK_PROGRESS = 'task_progress',
  LOG = 'log',
  INDEX_STATUS = 'index_status',
  PROFILE_STATUS = 'profile_status',
  TASK_COMPLETED = 'task_completed',
  TASK_FAILED = 'task_failed',
  PING = 'ping',
  PONG = 'pong',
}

export enum DocType {
  PDF = 'pdf',
  DOCX = 'docx',
  TXT = 'txt',
  MARKDOWN = 'markdown',
  VIDEO = 'video',
  AUDIO = 'audio',
  WEB = 'web',
  BILIBILI = 'bilibili',
  XIAOHONGSHU = 'xiaohongshu',
  PPT = 'ppt',
  PPTX = 'pptx',
}

export const FILE_TYPE_MAP: Record<string, DocType> = {
  '.pdf': DocType.PDF,
  '.docx': DocType.DOCX,
  '.doc': DocType.DOCX,
  '.txt': DocType.TXT,
  '.md': DocType.MARKDOWN,
  '.markdown': DocType.MARKDOWN,
  '.mp4': DocType.VIDEO,
  '.avi': DocType.VIDEO,
  '.mkv': DocType.VIDEO,
  '.mov': DocType.VIDEO,
  '.mp3': DocType.AUDIO,
  '.wav': DocType.AUDIO,
  '.flac': DocType.AUDIO,
  '.ppt': DocType.PPT,
  '.pptx': DocType.PPTX,
}

export const DOC_TYPE_LABELS: Record<string, string> = {
  [DocType.PDF]: 'PDF 文档',
  [DocType.DOCX]: 'Word 文档',
  [DocType.TXT]: '文本文件',
  [DocType.MARKDOWN]: 'Markdown',
  [DocType.VIDEO]: '视频',
  [DocType.AUDIO]: '音频',
  [DocType.WEB]: '网页',
  [DocType.BILIBILI]: 'B站视频',
  [DocType.XIAOHONGSHU]: '小红书笔记',
  [DocType.PPT]: 'PPT 演示',
  [DocType.PPTX]: 'PPT 演示',
}

export const DOC_TYPE_ICONS: Record<string, string> = {
  [DocType.PDF]: 'Document',
  [DocType.DOCX]: 'Document',
  [DocType.TXT]: 'Tickets',
  [DocType.MARKDOWN]: 'Tickets',
  [DocType.VIDEO]: 'VideoPlay',
  [DocType.AUDIO]: 'Headset',
  [DocType.WEB]: 'Link',
  [DocType.BILIBILI]: 'VideoCamera',
  [DocType.XIAOHONGSHU]: 'PictureFilled',
  [DocType.PPT]: 'DataBoard',
  [DocType.PPTX]: 'DataBoard',
}

export const CATEGORIES = ['学习', '技术', '生活', '其他'] as const
export type Category = (typeof CATEGORIES)[number]

export const LOG_LEVELS = ['INFO', 'WARNING', 'ERROR'] as const
export type LogLevel = (typeof LOG_LEVELS)[number]

export const LOG_LEVEL_COLORS: Record<LogLevel, string> = {
  INFO: '#67c23a',
  WARNING: '#e6a23c',
  ERROR: '#f56c6c',
}

export const DEFAULT_PAGE_SIZE = 20
export const DEFAULT_SEARCH_TOP_K = 10
export const WS_RECONNECT_INTERVAL = 3000
export const WS_MAX_RECONNECT_ATTEMPTS = 10
export const WS_HEARTBEAT_INTERVAL = 30000
export const MAX_FILE_SIZE = 500 * 1024 * 1024
export const SUPPORTED_EXTENSIONS = Object.keys(FILE_TYPE_MAP)

export const ERROR_CODE_RANGES = {
  SUCCESS: 0,
  CLIENT_ERROR: { min: 40001, max: 40099 },
  AUTH_ERROR: { min: 40101, max: 40199 },
  NOT_FOUND: { min: 40401, max: 40499 },
  SERVER_ERROR: { min: 50001, max: 50099 },
  THIRD_PARTY_ERROR: { min: 50101, max: 50199 },
  TASK_ERROR: { min: 50201, max: 50299 },
} as const
