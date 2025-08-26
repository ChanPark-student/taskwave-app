import { ref } from 'vue';
import { useRoute } from 'vue-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query';
import { api } from '@/lib/axios';
import { useAuthStore } from '@/store/authStore';
const route = useRoute();
const postId = route.params.id;
const qc = useQueryClient();
const auth = useAuthStore();
// 1) 게시글 단건
const { data: post } = useQuery(['post', postId], () => api.get('/community/posts').then(r => {
    const found = r.data.find(p => p.id === postId);
    if (!found)
        throw new Error('게시글 없음');
    return found;
}));
// 2) 댓글 목록
const { data: comments = [], isLoading: loadingComments, isError: commentsError, error: commentsErrorObj } = useQuery(['comments', postId], () => api.get(`/community/comments?post_id=${postId}`).then(r => r.data));
// 3) 댓글 등록
const commentContent = ref('');
const commentPassword = ref('');
const { mutate: mutateComment, isLoading: isCommenting, isError: commentError, error: commentErrorObj } = useMutation(() => api
    .post('/community/comment', {
    post_id: postId,
    content: commentContent.value,
    password: commentPassword.value,
    user_id: auth.uuid,
})
    .then(r => r.data), {
    onSuccess: () => {
        qc.invalidateQueries(['comments', postId]);
        commentContent.value = '';
        commentPassword.value = '';
    }
});
function formatDate(s) {
    return new Date(s).toLocaleString();
}
debugger; /* PartiallyEnd: #3632/scriptSetup.vue */
const __VLS_ctx = {};
let __VLS_components;
let __VLS_directives;
// CSS variable injection 
// CSS variable injection end 
__VLS_asFunctionalElement(__VLS_intrinsicElements.section, __VLS_intrinsicElements.section)({
    ...{ class: "container" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    ...{ onClick: (...[$event]) => {
            __VLS_ctx.$router.back();
        } },
    ...{ class: "mb-4 text-blue-600 hover:underline" },
});
if (__VLS_ctx.post) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.article, __VLS_intrinsicElements.article)({
        ...{ class: "mb-10" },
    });
    __VLS_asFunctionalElement(__VLS_intrinsicElements.h1, __VLS_intrinsicElements.h1)({
        ...{ class: "text-2xl font-bold mb-4" },
    });
    (__VLS_ctx.post.title);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "whitespace-pre-line mb-4" },
    });
    (__VLS_ctx.post.content);
    __VLS_asFunctionalElement(__VLS_intrinsicElements.footer, __VLS_intrinsicElements.footer)({
        ...{ class: "text-xs text-gray-500" },
    });
    (__VLS_ctx.post.user_id);
    (__VLS_ctx.formatDate(__VLS_ctx.post.created_at));
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.form, __VLS_intrinsicElements.form)({
    ...{ onSubmit: (...[$event]) => {
            __VLS_ctx.mutateComment();
        } },
    ...{ class: "space-y-4 mb-8" },
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.textarea)({
    value: (__VLS_ctx.commentContent),
    placeholder: "댓글 내용",
    rows: "3",
    ...{ class: "w-full p-2 border rounded" },
    required: true,
});
__VLS_asFunctionalElement(__VLS_intrinsicElements.input)({
    type: "password",
    placeholder: "댓글 비밀번호",
    ...{ class: "w-full p-2 border rounded" },
    required: true,
});
(__VLS_ctx.commentPassword);
__VLS_asFunctionalElement(__VLS_intrinsicElements.button, __VLS_intrinsicElements.button)({
    type: "submit",
    ...{ class: "px-4 py-2 rounded bg-green-600 text-white" },
    disabled: (__VLS_ctx.isCommenting),
});
(__VLS_ctx.isCommenting ? '등록 중…' : '댓글 등록');
if (__VLS_ctx.commentError) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
        ...{ class: "text-red-500" },
    });
    (__VLS_ctx.commentErrorObj.message);
}
__VLS_asFunctionalElement(__VLS_intrinsicElements.h2, __VLS_intrinsicElements.h2)({
    ...{ class: "text-lg font-semibold mb-4" },
});
if (__VLS_ctx.loadingComments) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
}
else if (__VLS_ctx.commentsError) {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({});
    (__VLS_ctx.commentsErrorObj.message);
}
else {
    __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
        ...{ class: "space-y-6" },
    });
    for (const [c] of __VLS_getVForSourceType((__VLS_ctx.comments))) {
        __VLS_asFunctionalElement(__VLS_intrinsicElements.div, __VLS_intrinsicElements.div)({
            key: (c.id),
            ...{ class: "border p-3 rounded" },
        });
        __VLS_asFunctionalElement(__VLS_intrinsicElements.p, __VLS_intrinsicElements.p)({
            ...{ class: "whitespace-pre-line mb-1" },
        });
        (c.content);
        __VLS_asFunctionalElement(__VLS_intrinsicElements.footer, __VLS_intrinsicElements.footer)({
            ...{ class: "text-xs text-gray-500" },
        });
        (c.user_id);
        (__VLS_ctx.formatDate(c.created_at));
    }
}
/** @type {__VLS_StyleScopedClasses['container']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-4']} */ ;
/** @type {__VLS_StyleScopedClasses['text-blue-600']} */ ;
/** @type {__VLS_StyleScopedClasses['hover:underline']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-10']} */ ;
/** @type {__VLS_StyleScopedClasses['text-2xl']} */ ;
/** @type {__VLS_StyleScopedClasses['font-bold']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-4']} */ ;
/** @type {__VLS_StyleScopedClasses['whitespace-pre-line']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-4']} */ ;
/** @type {__VLS_StyleScopedClasses['text-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['text-gray-500']} */ ;
/** @type {__VLS_StyleScopedClasses['space-y-4']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-8']} */ ;
/** @type {__VLS_StyleScopedClasses['w-full']} */ ;
/** @type {__VLS_StyleScopedClasses['p-2']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded']} */ ;
/** @type {__VLS_StyleScopedClasses['w-full']} */ ;
/** @type {__VLS_StyleScopedClasses['p-2']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded']} */ ;
/** @type {__VLS_StyleScopedClasses['px-4']} */ ;
/** @type {__VLS_StyleScopedClasses['py-2']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded']} */ ;
/** @type {__VLS_StyleScopedClasses['bg-green-600']} */ ;
/** @type {__VLS_StyleScopedClasses['text-white']} */ ;
/** @type {__VLS_StyleScopedClasses['text-red-500']} */ ;
/** @type {__VLS_StyleScopedClasses['text-lg']} */ ;
/** @type {__VLS_StyleScopedClasses['font-semibold']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-4']} */ ;
/** @type {__VLS_StyleScopedClasses['space-y-6']} */ ;
/** @type {__VLS_StyleScopedClasses['border']} */ ;
/** @type {__VLS_StyleScopedClasses['p-3']} */ ;
/** @type {__VLS_StyleScopedClasses['rounded']} */ ;
/** @type {__VLS_StyleScopedClasses['whitespace-pre-line']} */ ;
/** @type {__VLS_StyleScopedClasses['mb-1']} */ ;
/** @type {__VLS_StyleScopedClasses['text-xs']} */ ;
/** @type {__VLS_StyleScopedClasses['text-gray-500']} */ ;
var __VLS_dollars;
const __VLS_self = (await import('vue')).defineComponent({
    setup() {
        return {
            post: post,
            comments: comments,
            loadingComments: loadingComments,
            commentsError: commentsError,
            commentsErrorObj: commentsErrorObj,
            commentContent: commentContent,
            commentPassword: commentPassword,
            mutateComment: mutateComment,
            isCommenting: isCommenting,
            commentError: commentError,
            commentErrorObj: commentErrorObj,
            formatDate: formatDate,
        };
    },
});
export default (await import('vue')).defineComponent({
    setup() {
        return {};
    },
});
; /* PartiallyEnd: #4569/main.vue */
