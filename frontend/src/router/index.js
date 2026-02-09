import { createRouter, createWebHistory } from 'vue-router'
import Upload from '@/pages/Upload.vue'
import Dashboard from '@/pages/Dashboard.vue'

const routes = [
  {
    path: '/',
    name: 'Upload',
    component: Upload,
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
