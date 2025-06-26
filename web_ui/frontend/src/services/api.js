import axios from 'axios'
import { ElMessage } from 'element-plus'

// 创建 axios 实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token 等认证信息
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    const { data } = response
    
    // 如果是文件下载等特殊响应，直接返回
    if (response.config.responseType === 'blob') {
      return response
    }
    
    // 检查业务状态码
    if (data.code && data.code !== 200) {
      ElMessage.error(data.message || '请求失败')
      return Promise.reject(new Error(data.message || '请求失败'))
    }
    
    return data
  },
  (error) => {
    let message = '网络错误'
    
    if (error.response) {
      const { status, data } = error.response
      switch (status) {
        case 400:
          message = data.message || '请求参数错误'
          break
        case 401:
          message = '未授权，请重新登录'
          break
        case 403:
          message = '拒绝访问'
          break
        case 404:
          message = '请求的资源不存在'
          break
        case 500:
          message = data.message || '服务器内部错误'
          break
        default:
          message = data.message || `请求失败 (${status})`
      }
    } else if (error.request) {
      message = '网络连接失败，请检查网络'
    }
    
    ElMessage.error(message)
    return Promise.reject(error)
  }
)

// API 服务对象
export const apiService = {
  // 健康检查
  healthCheck() {
    return api.get('/health')
  },
  
  // 配置管理
  getConfig() {
    return api.get('/config')
  },
  
  updateConfig(config) {
    return api.post('/config', config)
  },
  
  // 测试用例管理
  getTestCases() {
    return api.get('/test-cases')
  },
  
  getTestCaseContent(filePath) {
    return api.get(`/test-cases/${filePath}`)
  },
  
  saveTestCaseContent(filePath, content) {
    return api.post(`/test-cases/${filePath}`, { content })
  },
  
  // 代码生成
  generateCode() {
    return api.post('/generate-code')
  },
  
  // 测试执行
  startExecution() {
    return api.post('/execute/start')
  },
  
  getExecutionStatus() {
    return api.get('/execute/status')
  },
  
  getExecutionLogs(limit = 100) {
    return api.get('/execute/logs', { params: { limit } })
  }
}

export default api
