import { defineStore } from 'pinia';
import { v4 as uuidv4 } from 'uuid';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    uuid: localStorage.getItem('uuid') ?? '',
    username: localStorage.getItem('username') ?? '',
  }),
  actions: {
    login(id: string, name: string) {
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
    isAuthed(): boolean {
      return !!this.uuid;
    },
  },
});
