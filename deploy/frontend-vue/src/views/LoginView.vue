<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '@/store/authStore';
import { api } from '@/lib/axios';

const router = useRouter();
const auth = useAuthStore();

const username = ref('');
const password = ref('');    // ← password 필드 추가(단순 텍스트)

async function handleLogin() {
  try {
    /* 1️⃣  서버에 user 생성 요청 */
    // LoginView.vue (handleLogin 함수)
    const { data } = await api.post('/community/user', {
      username: username.value,
      password: password.value || 'temp',
    });


    /* 2️⃣  authStore에 id 저장 */
    auth.login(data.id, data.username);

    /* 3️⃣  커뮤니티 페이지로 이동 */
    router.push({ name: 'CommunityHome' });
  } catch (err) {
    alert('로그인(회원 생성) 실패');
    console.error(err);
  }
}
</script>

<template>
  <section class="login flex flex-col items-center justify-center h-screen">
    <h1 class="text-3xl font-bold mb-6">로그인</h1>

    <form @submit.prevent="handleLogin" class="space-y-4 w-72">
      <input
        v-model="username"
        type="text"
        placeholder="사용자 이름"
        class="w-full p-2 border rounded"
        required
      />
      <input
        v-model="password"
        type="password"
        placeholder="비밀번호(임시 가능)"
        class="w-full p-2 border rounded"
      />
      <button
        type="submit"
        class="w-full py-2 rounded bg-blue-600 text-white hover:bg-blue-700 transition"
      >
        입장
      </button>
    </form>
  </section>
</template>
