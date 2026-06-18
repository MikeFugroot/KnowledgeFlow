import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import MainLayout from '@/layouts/MainLayout.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '智能工作台', icon: 'Monitor' },
      },
      {
        path: '/import/files',
        name: 'FileImport',
        component: () => import('@/views/FileImport.vue'),
        meta: { title: '本地文件导入', icon: 'Upload' },
      },
      {
        path: '/import/web',
        name: 'WebImport',
        component: () => import('@/views/WebImport.vue'),
        meta: { title: '网页导入', icon: 'Link' },
      },
      {
        path: '/documents',
        name: 'Documents',
        component: () => import('@/views/Documents.vue'),
        meta: { title: '整理结果', icon: 'Document' },
      },
      {
        path: '/profile',
        name: 'KnowledgeProfile',
        component: () => import('@/views/KnowledgeProfile.vue'),
        meta: { title: '知识画像', icon: 'DataAnalysis' },
      },
      {
        path: '/search',
        name: 'SemanticSearch',
        component: () => import('@/views/SemanticSearch.vue'),
        meta: { title: '语义检索', icon: 'Search' },
      },
      {
        path: '/logs',
        name: 'Logs',
        component: () => import('@/views/Logs.vue'),
        meta: { title: '运行日志', icon: 'Notebook' },
      },
      {
        path: '/settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置', icon: 'Setting' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const title = to.meta.title as string | undefined
  document.title = title ? `${title} - KnowledgeFlow` : 'KnowledgeFlow Web'
  next()
})

export default router
