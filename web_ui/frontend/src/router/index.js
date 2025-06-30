import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'Layout',
      component: () => import('@/layout/index.vue'),
      redirect: '/dashboard',
      children: [
        {
          path: '/dashboard',
          name: 'Dashboard',
          component: () => import('@/views/Dashboard/index.vue'),
          meta: {
            title: '仪表板',
            icon: 'DataAnalysis'
          }
        },
        {
          path: '/test-cases',
          name: 'TestCases',
          component: () => import('@/views/TestCases/index.vue'),
          meta: {
            title: '用例管理',
            icon: 'Document'
          }
        },
        {
          path: '/test-cases/editor/:path*',
          name: 'TestCaseEditor',
          component: () => import('@/views/TestCases/Editor.vue'),
          meta: {
            title: '用例编辑器',
            icon: 'Edit',
            hidden: true
          }
        },
        {
          path: '/test-cases/wizard',
          name: 'CreateWizard',
          component: () => import('@/views/TestCases/CreateWizard.vue'),
          meta: {
            title: '创建向导',
            icon: 'Magic',
            hidden: true
          }
        },
        {
          path: '/execution',
          name: 'Execution',
          component: () => import('@/views/Execution/index.vue'),
          meta: {
            title: '执行中心',
            icon: 'VideoPlay'
          }
        },
        {
          path: '/reports',
          name: 'Reports',
          component: () => import('@/views/Reports/index.vue'),
          meta: {
            title: '报告中心',
            icon: 'PieChart'
          }
        },
        {
          path: '/configuration',
          name: 'Configuration',
          component: () => import('@/views/Configuration/index.vue'),
          meta: {
            title: '配置管理',
            icon: 'Setting'
          }
        },
        {
          path: '/tools',
          name: 'Tools',
          component: () => import('@/views/Tools/index.vue'),
          meta: {
            title: '工具箱',
            icon: 'Tools'
          }
        }
      ]
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'NotFound',
      component: () => import('@/views/NotFound/index.vue')
    }
  ]
})

export default router
