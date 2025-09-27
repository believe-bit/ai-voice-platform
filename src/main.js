// src/main.js
import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import io from 'socket.io-client';

const app = createApp(App);
app.use(router);
app.use(ElementPlus);
app.config.globalProperties.$socket = io('http://localhost:5000'); // 替换为你的后端 WebSocket URL
app.mount('#app');

window.addEventListener('error', (event) => {
  if (event.message.includes('ResizeObserver loop completed with undelivered notifications')) {
    event.preventDefault();
    console.warn('已忽略 ResizeObserver 错误');
  }
});