<template>
  <section class="container">
    <header class="flex items-center justify-between mb-8">
      <h1 class="text-2xl font-bold">커뮤니티</h1>
      <button class="text-sm hover:underline" @click="logout">로그아웃</button>
    </header>

    <!-- 글 작성 -->
    <form @submit.prevent="mutate()" class="space-y-4 mb-10">
      <input v-model="title" type="text" placeholder="제목" class="w-full p-2 border rounded" required />
      <textarea v-model="content" placeholder="본문" rows="5" class="w-full p-2 border rounded" required />
      <input v-model="password" type="password" placeholder="비밀번호" class="w-full p-2 border rounded" required />

      <button type="submit"
              class="px-4 py-2 rounded bg-blue-600 text-white"
              :disabled="isCreating">
        {{ isCreating ? '등록 중…' : '글 등록' }}
      </button>
      <p v-if="createError" class="text-red-500">
        오류: {{ createErrorObj.message }}
      </p>
    </form>

    <!-- 게시글 목록 -->
    <div v-if="loadingPosts">불러오는 중…</div>
    <div v-else-if="postsError">
      문제가 발생했습니다: {{ postsErrorObj.message }}
    </div>
    <article
      v-else
      v-for="post in posts"
      :key="post.id"
      class="post border p-4 rounded shadow-sm hover:shadow-md transition mb-6 cursor-pointer"
      @click="toDetail(post.id)"
    >
      <h2 class="text-xl font-semibold mb-2">{{ post.title }}</h2>
      <p class="line-clamp-3">{{ post.content }}</p>
      <footer class="text-xs text-gray-500 mt-2">
        {{ post.user_id }} · {{ formatDate(post.created_at) }}
      </footer>
    </article>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { api } from '@/lib/axios'
import { useAuthStore } from '@/store/authStore'

interface Post {
  id: string
  user_id: string
  title: string
  content: string
  created_at: string
}

const router = useRouter()
const qc = useQueryClient()
const auth = useAuthStore()

// 1) 게시글 목록
const {
  data: posts = [],
  isLoading: loadingPosts,
  isError: postsError,
  error: postsErrorObj
} = useQuery<Post[], Error>(
  ['posts'],
  () => api.get('/community/posts').then(r => r.data)
)

// 2) 글 등록 뮤테이션
const title = ref('')
const content = ref('')
const password = ref('')

const {
  mutate,
  isLoading: isCreating,
  isError: createError,
  error: createErrorObj
} = useMutation<Post, Error>(
  () =>
    api.post('/community/post', {
      user_id: auth.uuid,
      title: title.value,
      content: content.value,
      password: password.value,
    }).then(r => r.data),
  {
    onSuccess: () => {
      qc.invalidateQueries(['posts'])
      title.value = ''
      content.value = ''
      password.value = ''
    }
  }
)

// 라우팅·유틸
function toDetail(id: string) {
  router.push({ name: 'PostDetail', params: { id } })
}
function logout() {
  auth.logout()
  router.replace({ name: 'Login' })
}
function formatDate(s: string) {
  return new Date(s).toLocaleString()
}
</script>

<style scoped>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 2rem;
}
</style>
