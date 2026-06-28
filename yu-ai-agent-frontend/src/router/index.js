import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { guest: true }
  },
  {
    path: '/',
    component: () => import('@/components/AppLayout.vue'),
    children: [
      {
        path: '',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'love',
        name: 'LoveMaster',
        component: () => import('@/views/LoveMaster.vue'),
        meta: { title: '恋爱大师', accent: 'coral' }
      },
      {
        path: 'agent',
        name: 'SuperAgent',
        component: () => import('@/views/SuperAgent.vue'),
        meta: { title: '超级智能体', accent: 'indigo' }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/Knowledge.vue'),
        meta: { title: '知识库' }
      },
      {
        path: 'friend',
        name: 'DigitalFriend',
        component: () => import('@/views/DigitalFriend.vue'),
        meta: { title: '数字朋友', accent: 'violet' }
      }
    ]
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// Auth guard
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (!to.meta.guest && !token) {
    next('/login')
  } else if (to.meta.guest && token) {
    next('/')
  } else {
    next()
  }
})

export default router
