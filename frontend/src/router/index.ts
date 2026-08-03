import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/login' },
    { path: '/login', component: () => import('@/views/auth/Login.vue'), meta: { public: true } },
    { path: '/register', component: () => import('@/views/auth/Register.vue'), meta: { public: true } },

    // 管理员端
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { role: 'admin' },
      children: [
        { path: '', redirect: '/admin/review' },
        { path: 'review', component: () => import('@/views/admin/UserReview.vue') },
        { path: 'overview', component: () => import('@/views/admin/Overview.vue') },
      ],
    },

    // 医生端
    {
      path: '/doctor',
      component: () => import('@/layouts/DoctorLayout.vue'),
      meta: { role: 'doctor' },
      children: [
        { path: 'students', component: () => import('@/views/doctor/StudentManage.vue') },
        { path: 'intervene', component: () => import('@/views/doctor/Intervene.vue') },
        { path: 'records', component: () => import('@/views/doctor/ChatRecords.vue') },
        { path: 'reviews', component: () => import('@/views/doctor/Reviews.vue') },
        { path: 'stats', component: () => import('@/views/doctor/Stats.vue') },
      ],
    },

    // 医学生端
    {
      path: '/student',
      component: () => import('@/layouts/StudentLayout.vue'),
      meta: { role: 'student' },
      children: [
        { path: '', redirect: '/student/dashboard' },
        { path: 'dashboard', component: () => import('@/views/student/Dashboard.vue') },
        { path: 'chat', component: () => import('@/views/student/Chat.vue') },
        { path: 'plans', component: () => import('@/views/student/Plan.vue') },
        { path: 'summaries', component: () => import('@/views/student/Summaries.vue') },
        { path: 'records', component: () => import('@/views/student/Records.vue') },
      ],
    },

    // 患者端
    {
      path: '/patient',
      component: () => import('@/layouts/PatientLayout.vue'),
      meta: { role: 'patient' },
      children: [
        { path: '', redirect: '/patient/home' },
        { path: 'home', component: () => import('@/views/patient/Home.vue') },
        { path: 'chat', component: () => import('@/views/patient/Chat.vue') },
        { path: 'profile', component: () => import('@/views/patient/Profile.vue') },
        { path: 'health', component: () => import('@/views/patient/HealthData.vue') },
        { path: 'reminders', component: () => import('@/views/patient/Reminders.vue') },
        { path: 'voice', component: () => import('@/views/patient/Voice.vue') },
      ],
    },

    { path: '/:pathMatch(.*)*', redirect: '/login' },
  ],
})

router.beforeEach((to) => {
  const store = useUserStore()
  if (to.meta.public) return true
  if (!store.token) return '/login'
  if (to.meta.role && to.meta.role !== store.role) {
    return `/${store.role}`
  }
  return true
})

export default router
