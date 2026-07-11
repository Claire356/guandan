import { defineConfig, loadEnv } from 'vite'
import uni from '@dcloudio/vite-plugin-uni'

const browserPageFallback = () => ({
  name: 'browser-page-fallback',
  configureServer(server) {
    server.middlewares.use((request, response, next) => {
      const acceptsHtml = request.headers.accept?.includes('text/html')
      if (acceptsHtml && /^\/pages\/[^/?]+\/index\/?(?:\?.*)?$/.test(request.url || '')) {
        request.url = '/'
      }
      next()
    })
  }
})

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  return {
    base: env.VITE_PUBLIC_BASE || '/',
    plugins: [browserPageFallback(), uni()],
    server: {
      host: '0.0.0.0',
      port: Number(env.VITE_DEV_PORT || 5173),
      proxy: {
        '/api': {
          target: env.VITE_API_PROXY_TARGET || 'http://127.0.0.1:8000',
          changeOrigin: true,
          rewrite: path => path.replace(/^\/api/, '')
        }
      }
    }
  }
})
