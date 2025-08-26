<template>
  <section class="container">
    <button class="mb-4 text-blue-600 hover:underline" @click="$router.back()">
      ← 목록
    </button>

    <!-- 게시글 단건 -->
    <article v-if="post" class="mb-10">
      <h1 class="text-2xl font-bold mb-4">{{ post.title }}</h1>
      <p class="whitespace-pre-line mb-4">{{ post.content }}</p>
      <footer class="text-xs text-gray-500">
        작성자: {{ post.user_id }} · {{ formatDate(post.created_at) }}
      </footer>
    </article>

    <!-- 댓글 작성 -->
    <form @submit.prevent="mutateComment()" class="space-y-4 mb-8">
      <textarea
        v-model="commentContent"
        placeholder="댓글 내용"
        rows="3"
        class="w-full p-2 border rounded"
        required
      />
      <input
        v-model="commentPassword"
        type="password"
        placeholder="댓글 비밀번호"
        class="w-full p-2 border rounded"
        required
      />
      <button
        type="submit"
        class="px-4 py-2 rounded bg-green-600 text-white"
        :disabled="isCommenting"
      >
        {{ isCommenting ? '등록 중…' : '댓글 등록' }}
      </button>
      <p v-if="commentError" class="text-red-500">
        오류: {{ commentErrorObj.message }}
      </p>
    </form>

    <!-- 댓글 목록 -->
    <h2 class="text-lg font-semibold mb-4">댓글</h2>
    <div v-if="loadingComments">불러오는 중…</div>
    <div v-else-if="commentsError">
      문제가 발생했습니다: {{ commentsErrorObj.message }}
    </div>
    <div v-else class="space-y-6">
      <div v-for="c in comments" :key="c.id" class="border p-3 rounded">
        <p class="whitespace-pre-line mb-1">{{ c.content }}</p>
        <footer class="text-xs text-gray-500">
          {{ c.user_id }} · {{ formatDate(c.created_at) }}
        </footer>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
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
interface Comment {
  id: string
  post_id: string
  user_id: string
  content: string
  created_at: string
}

const route = useRoute()
const postId = route.params.id as string
const qc = useQueryClient()
const auth = useAuthStore()

// 1) 게시글 단건
const { data: post } = useQuery<Post, Error>(
  ['post', postId],
  () =>
    api.get('/community/posts').then(r => {
      const found = (r.data as Post[]).find(p => p.id === postId)
      if (!found) throw new Error('게시글 없음')
      return found
    })
)

// 2) 댓글 목록
const {
  data: comments = [],
  isLoading: loadingComments,
  isError: commentsError,
  error: commentsErrorObj
} = useQuery<Comment[], Error>(
  ['comments', postId],
  () => api.get(`/community/comments?post_id=${postId}`).then(r => r.data)
)

// 3) 댓글 등록
const commentContent = ref('')
const commentPassword = ref('')

const {
  mutate: mutateComment,
  isLoading: isCommenting,
  isError: commentError,
  error: commentErrorObj
} = useMutation<Comment, Error>(
  () =>
    api
      .post('/community/comment', {
        post_id: postId,
        content: commentContent.value,
        password: commentPassword.value,
        user_id: auth.uuid,
      })
      .then(r => r.data),
  {
    onSuccess: () => {
      qc.invalidateQueries(['comments', postId])
      commentContent.value = ''
      commentPassword.value = ''
    }
  }
)

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
