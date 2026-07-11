import axios from 'axios'

const uniAdapter = config => new Promise((resolve, reject) => {
  uni.request({
    url: `${config.baseURL || ''}${config.url || ''}`,
    method: (config.method || 'get').toUpperCase(),
    data: typeof config.data === 'string' ? JSON.parse(config.data) : (config.data || config.params),
    header: config.headers?.toJSON ? config.headers.toJSON() : config.headers,
    timeout: config.timeout,
    success(response) {
      const result = {
        data: response.data,
        status: response.statusCode,
        statusText: String(response.statusCode),
        headers: response.header,
        config,
        request: null
      }
      if (response.statusCode >= 200 && response.statusCode < 300) resolve(result)
      else reject(Object.assign(new Error(`请求失败: ${response.statusCode}`), { response: result, config }))
    },
    fail(error) {
      reject(Object.assign(new Error(error.errMsg || '网络请求失败'), { config }))
    }
  })
})

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000',
  timeout: Number(import.meta.env.VITE_API_TIMEOUT || 8000),
  headers: { 'Content-Type': 'application/json' },
  adapter: uniAdapter
})

client.interceptors.response.use(
  response => response.data,
  error => Promise.reject(new Error(error.response?.data?.error?.message || error.message || '网络请求失败'))
)

export default client
