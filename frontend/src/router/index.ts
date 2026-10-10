import { createRouter, createWebHistory } from 'vue-router'
const routes = [
  { path: '/login', component: () => import('../views/Login.vue') },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      { path: '/dashboard', component: () => import('../views/Dashboard.vue') },
      { path: '/users', component: () => import('../views/Users.vue') },
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/login' }
]

const router = createRouter({ history: createWebHistory(), routes })

// 全局路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  if (to.path !== '/login' && !token) return next('/login')
  if (to.path === '/login' && token) return next('/')
  next()
})
export default router
