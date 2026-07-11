import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import uviewPlus from 'uview-plus'
import App from './App.vue'

// #ifdef H5
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(error => {
      console.warn('Service Worker 注册失败', error)
    })
  })
}
// #endif

export function createApp() {
  const app = createSSRApp(App)
  app.use(createPinia())
  app.use(uviewPlus)
  return { app }
}
