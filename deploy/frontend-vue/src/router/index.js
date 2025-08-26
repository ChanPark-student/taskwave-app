import { createRouter, createWebHistory } from 'vue-router';
import { useAuthStore } from '@/store/authStore';
const routes = [
    {
        path: '/',
        redirect: '/login',
    },
    {
        path: '/login',
        name: 'Login',
        component: () => import('@/views/LoginView.vue'),
    },
    {
        path: '/community',
        name: 'CommunityHome',
        component: () => import('@/views/CommunityHome.vue'),
        meta: { requiresAuth: true },
    },
    {
        path: '/community/:id',
        name: 'PostDetail',
        component: () => import('@/views/PostDetail.vue'),
        meta: { requiresAuth: true },
        props: true,
    },
];
const router = createRouter({
    history: createWebHistory(),
    routes,
});
/* 전역 가드 ─ 로그인 여부 체크 */
router.beforeEach((to, _from) => {
    if (to.meta.requiresAuth) {
        const auth = useAuthStore();
        if (!auth.isAuthed())
            return { name: 'Login' };
    }
    return true;
});
export default router;
