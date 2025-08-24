import { createApp } from 'vue';
import { createPinia } from 'pinia';
import { QueryClient, VueQueryPlugin, useQuery /* … */ } from '@tanstack/vue-query';
import App from '@/App.vue';
import router from '@/router';

const queryClient = new QueryClient();

createApp(App)
  .use(router)
  .use(createPinia())
  .use(VueQueryPlugin, { queryClient })
  .mount('#app');
import.meta.glob
? Object.keys(import.meta.glob('/node_modules/@tanstack/query-core/**'))
: []