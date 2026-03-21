import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', component: () => import('@/views/Home.vue') },
    { path: '/cultivate', component: () => import('@/views/Cultivate.vue') },
    { path: '/story', component: () => import('@/views/Story.vue') },
    { path: '/bag', component: () => import('@/views/Bag.vue') },
    { path: '/more', component: () => import('@/views/More.vue') },
  ],
})

export default router
