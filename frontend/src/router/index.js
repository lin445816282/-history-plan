import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/profiles' },
  { path: '/profiles', component: () => import('../views/ProfileList.vue') },
  { path: '/profiles/new', component: () => import('../views/ProfileCreate.vue') },
  { path: '/profiles/:id', component: () => import('../views/ProfileDetail.vue') },
  { path: '/profile/:id/growth', component: () => import('../views/Growth.vue') },
  { path: '/report/:snapshotId', component: () => import('../views/Report.vue') },
  { path: '/review/:snapshotId', component: () => import('../views/Review.vue') },
  { path: '/deviation', component: () => import('../views/DeviationDashboard.vue') },
  { path: '/knowledge', component: () => import('../views/KnowledgeBase.vue') },
  { path: '/settings', component: () => import('../views/Settings.vue') },
]

export default createRouter({ history: createWebHashHistory(), routes })
