import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    redirect: '/friends',
  },
  {
    path: '/friends',
    name: 'Friends',
    component: () => import('../views/FriendsView.vue'),
    meta: { title: '好友', icon: 'fa-address-book' },
  },
  {
    path: '/search',
    name: 'Search',
    component: () => import('../views/SearchView.vue'),
    meta: { title: '发现用户', icon: 'fa-magnifying-glass' },
  },
  {
    path: '/recommend',
    name: 'Recommend',
    component: () => import('../views/RecommendView.vue'),
    meta: { title: '好友推荐', icon: 'fa-star' },
  },
  {
    path: '/messages/:userId?',
    name: 'Messages',
    components: {
      default: () => import('../views/MessagesView.vue'),
      detail: () => import('../views/ChatView.vue'),
    },
    meta: { title: '消息', icon: 'fa-comment' },
  },
  {
    path: '/profile/:id?',
    name: 'Profile',
    component: () => import('../views/ProfileView.vue'),
    meta: { title: '个人资料', icon: 'fa-user' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
