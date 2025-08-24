import { defineStore } from 'pinia';
export const useAuthStore = defineStore('auth', {
    state: () => ({
        uuid: localStorage.getItem('uuid') ?? '',
        username: localStorage.getItem('username') ?? '',
    }),
    actions: {
        login(id, name) {
            this.uuid = id;
            this.username = name;
            localStorage.setItem('uuid', id);
            localStorage.setItem('username', name);
        },
        logout() {
            this.uuid = '';
            this.username = '';
            localStorage.removeItem('uuid');
            localStorage.removeItem('username');
        },
        isAuthed() {
            return !!this.uuid;
        },
    },
});
