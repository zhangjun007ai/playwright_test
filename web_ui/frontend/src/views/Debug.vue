<template>
  <div class="debug-page">
    <div class="page-header">
      <h1 class="page-title gradient-text">
        <el-icon class="title-icon"><Tools /></el-icon>
        前后端联调测试
      </h1>
      <p class="page-subtitle">测试前后端API通信状态</p>
    </div>
    
    <div class="debug-content">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-card class="test-card">
            <template #header>
              <div class="card-header">
                <span>后端服务状态</span>
                <el-button type="primary" @click="testHealthCheck" :loading="testing.health">
                  检查连接
                </el-button>
              </div>
            </template>
            <div class="test-result">
              <div class="status-item">
                <span class="label">连接状态:</span>
                <el-tag :type="healthStatus.status ? 'success' : 'danger'">
                  {{ healthStatus.status ? '正常' : '异常' }}
                </el-tag>
              </div>
              <div class="status-item">
                <span class="label">响应时间:</span>
                <span>{{ healthStatus.responseTime }}ms</span>
              </div>
              <div class="status-item">
                <span class="label">服务信息:</span>
                <span>{{ healthStatus.message }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card class="test-card">
            <template #header>
              <div class="card-header">
                <span>配置接口测试</span>
                <el-button type="primary" @click="testConfigAPI" :loading="testing.config">
                  测试接口
                </el-button>
              </div>
            </template>
            <div class="test-result">
              <div class="status-item">
                <span class="label">接口状态:</span>
                <el-tag :type="configStatus.status ? 'success' : 'danger'">
                  {{ configStatus.status ? '正常' : '异常' }}
                </el-tag>
              </div>
              <div class="status-item">
                <span class="label">数据获取:</span>
                <span>{{ configStatus.dataReceived ? '成功' : '失败' }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-row :gutter="20" style="margin-top: 20px;">
        <el-col :span="12">
          <el-card class="test-card">
            <template #header>
              <div class="card-header">
                <span>用例接口测试</span>
                <el-button type="primary" @click="testCasesAPI" :loading="testing.cases">
                  测试接口
                </el-button>
              </div>
            </template>
            <div class="test-result">
              <div class="status-item">
                <span class="label">接口状态:</span>
                <el-tag :type="casesStatus.status ? 'success' : 'danger'">
                  {{ casesStatus.status ? '正常' : '异常' }}
                </el-tag>
              </div>
              <div class="status-item">
                <span class="label">用例数量:</span>
                <span>{{ casesStatus.count }} 个</span>
              </div>
            </div>
          </el-card>
        </el-col>
        
        <el-col :span="12">
          <el-card class="test-card">
            <template #header>
              <div class="card-header">
                <span>执行接口测试</span>
                <el-button type="primary" @click="testExecutionAPI" :loading="testing.execution">
                  测试接口
                </el-button>
              </div>
            </template>
            <div class="test-result">
              <div class="status-item">
                <span class="label">接口状态:</span>
                <el-tag :type="executionStatus.status ? 'success' : 'danger'">
                  {{ executionStatus.status ? '正常' : '异常' }}
                </el-tag>
              </div>
              <div class="status-item">
                <span class="label">执行状态:</span>
                <span>{{ executionStatus.running ? '运行中' : '空闲' }}</span>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      
      <el-card style="margin-top: 20px;">
        <template #header>
          <div class="card-header">
            <span>API响应日志</span>
            <el-button @click="clearLogs">清空日志</el-button>
          </div>
        </template>
        <div class="logs-container">
          <div v-for="(log, index) in logs" :key="index" class="log-item">
            <span class="log-time">{{ log.time }}</span>
            <el-tag :type="log.level" size="small">{{ log.level.toUpperCase() }}</el-tag>
            <span class="log-message">{{ log.message }}</span>
          </div>
          <div v-if="logs.length === 0" class="no-logs">
            暂无日志记录
          </div>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Tools } from '@element-plus/icons-vue'
import { apiService } from '@/services/api'

// 响应式数据
const testing = ref({
  health: false,
  config: false,
  cases: false,
  execution: false
})

const healthStatus = ref({
  status: false,
  responseTime: 0,
  message: '未测试'
})

const configStatus = ref({
  status: false,
  dataReceived: false
})

const casesStatus = ref({
  status: false,
  count: 0
})

const executionStatus = ref({
  status: false,
  running: false
})

const logs = ref([])

// 工具方法
const addLog = (level, message) => {
  logs.value.unshift({
    time: new Date().toLocaleTimeString(),
    level,
    message
  })
  if (logs.value.length > 100) {
    logs.value = logs.value.slice(0, 100)
  }
}

const clearLogs = () => {
  logs.value = []
}

// 测试方法
const testHealthCheck = async () => {
  testing.value.health = true
  const startTime = Date.now()
  
  try {
    addLog('info', '开始健康检查...')
    const response = await apiService.healthCheck()
    const responseTime = Date.now() - startTime
    
    healthStatus.value = {
      status: true,
      responseTime,
      message: response.message || '服务正常'
    }
    
    addLog('success', `健康检查成功 (${responseTime}ms)`)
    ElMessage.success('后端服务连接正常')
  } catch (error) {
    const responseTime = Date.now() - startTime
    healthStatus.value = {
      status: false,
      responseTime,
      message: error.message || '连接失败'
    }
    
    addLog('error', `健康检查失败: ${error.message}`)
    ElMessage.error('后端服务连接失败')
  } finally {
    testing.value.health = false
  }
}

const testConfigAPI = async () => {
  testing.value.config = true
  
  try {
    addLog('info', '测试配置接口...')
    const response = await apiService.getConfig()
    
    configStatus.value = {
      status: true,
      dataReceived: !!response.data
    }
    
    addLog('success', `配置接口测试成功，获取到配置数据`)
    ElMessage.success('配置接口正常')
  } catch (error) {
    configStatus.value = {
      status: false,
      dataReceived: false
    }
    
    addLog('error', `配置接口测试失败: ${error.message}`)
    ElMessage.error('配置接口异常')
  } finally {
    testing.value.config = false
  }
}

const testCasesAPI = async () => {
  testing.value.cases = true
  
  try {
    addLog('info', '测试用例接口...')
    const response = await apiService.getTestCases()
    
    casesStatus.value = {
      status: true,
      count: response.data ? response.data.length : 0
    }
    
    addLog('success', `用例接口测试成功，发现 ${casesStatus.value.count} 个用例`)
    ElMessage.success('用例接口正常')
  } catch (error) {
    casesStatus.value = {
      status: false,
      count: 0
    }
    
    addLog('error', `用例接口测试失败: ${error.message}`)
    ElMessage.error('用例接口异常')
  } finally {
    testing.value.cases = false
  }
}

const testExecutionAPI = async () => {
  testing.value.execution = true
  
  try {
    addLog('info', '测试执行接口...')
    const response = await apiService.getExecutionStatus()
    
    executionStatus.value = {
      status: true,
      running: response.data ? response.data.running : false
    }
    
    addLog('success', `执行接口测试成功`)
    ElMessage.success('执行接口正常')
  } catch (error) {
    executionStatus.value = {
      status: false,
      running: false
    }
    
    addLog('error', `执行接口测试失败: ${error.message}`)
    ElMessage.error('执行接口异常')
  } finally {
    testing.value.execution = false
  }
}
</script>

<style lang="scss" scoped>
.debug-page {
  padding: $spacing-lg;
  height: 100%;
}

.page-header {
  margin-bottom: $spacing-lg;
  
  .page-title {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: $spacing-xs;
    
    .title-icon {
      font-size: 2rem;
    }
  }
  
  .page-subtitle {
    color: $text-gray;
    font-size: 1rem;
    margin: 0;
  }
}

.test-card {
  @include sketch-card;
  margin-bottom: $spacing-md;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-weight: bold;
  }
}

.test-result {
  .status-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: $spacing-sm 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    &:last-child {
      border-bottom: none;
    }
    
    .label {
      font-weight: 500;
      color: $text-gray;
    }
  }
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  background: rgba(0, 0, 0, 0.2);
  border-radius: $border-radius;
  padding: $spacing-sm;
  
  .log-item {
    display: flex;
    align-items: center;
    gap: $spacing-sm;
    padding: $spacing-xs 0;
    font-size: 0.875rem;
    
    .log-time {
      color: $text-gray;
      min-width: 80px;
    }
    
    .log-message {
      color: $text-white;
    }
  }
  
  .no-logs {
    text-align: center;
    color: $text-gray;
    padding: $spacing-md 0;
    font-style: italic;
  }
}
</style> 