import { defineStore } from 'pinia'
import { ref } from 'vue'
import { apiService } from '@/services/api'

export const useConfigStore = defineStore('config', () => {
  // 状态
  const config = ref({
    project_name: '',
    env: '',
    tester_name: '',
    host: '',
    notification_type: 0,
    mysql_switch: false
  })
  
  const loading = ref(false)
  const error = ref(null)
  
  // 动作
  const fetchConfig = async () => {
    try {
      loading.value = true
      error.value = null
      const response = await apiService.getConfig()
      config.value = response.data
    } catch (err) {
      error.value = err.message || '获取配置失败'
      console.error('获取配置失败:', err)
    } finally {
      loading.value = false
    }
  }
  
  const updateConfig = async (newConfig) => {
    try {
      loading.value = true
      error.value = null
      await apiService.updateConfig(newConfig)
      config.value = { ...config.value, ...newConfig }
      return true
    } catch (err) {
      error.value = err.message || '更新配置失败'
      console.error('更新配置失败:', err)
      return false
    } finally {
      loading.value = false
    }
  }
  
  return {
    config,
    loading,
    error,
    fetchConfig,
    updateConfig
  }
})
