/**
 * Vue Router配置
 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue'),
    meta: { title: '首页' }
  },
  {
    path: '/upload',
    name: 'Upload',
    component: () => import('@/views/Upload.vue'),
    meta: { title: '文件上传' }
  },
  {
    path: '/processing/:taskId',
    name: 'Processing',
    component: () => import('@/views/Processing.vue'),
    meta: { title: '处理中' }
  },
  {
    path: '/report/:taskId',
    name: 'Report',
    component: () => import('@/views/Report.vue'),
    meta: { title: '验证报告' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
