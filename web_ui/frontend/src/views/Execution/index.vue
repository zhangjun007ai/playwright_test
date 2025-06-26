<template>
  <div class="execution">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title gradient-text">
          <el-icon class="title-icon"><VideoPlay /></el-icon>
          执行中心
        </h1>
        <p class="page-subtitle">测试执行控制台</p>
      </div>
      <div class="header-actions">
        <el-button
          type="primary"
          size="large"
          @click="startExecution"
          :loading="isRunning"
          :disabled="isRunning"
          class="run-button"
        >
          <el-icon><VideoPlay /></el-icon>
          {{ isRunning ? '执行中...' : '开始执行' }}
        </el-button>
      </div>
    </div>
    
    <div class="execution-content">
      <!-- 执行状态卡片 -->
      <div class="status-cards">
        <div class="status-card sketch-card" :class="{ active: isRunning }">
          <div class="card-icon">
            <el-icon size="32" :class="{ 'pulse-animation': isRunning }">
              <component :is="statusIcon" />
            </el-icon>
          </div>
          <div class="card-content">
            <div class="status-text">{{ statusText }}</div>
            <div class="status-time" v-if="executionTime">
              执行时间: {{ executionTime }}
            </div>
          </div>
        </div>
        
        <div class="stats-cards">
          <div class="stat-item">
            <div class="stat-value">{{ executionStats.total }}</div>
            <div class="stat-label">总用例</div>
          </div>
          <div class="stat-item success">
            <div class="stat-value">{{ executionStats.passed }}</div>
            <div class="stat-label">成功</div>
          </div>
          <div class="stat-item error">
            <div class="stat-value">{{ executionStats.failed }}</div>
            <div class="stat-label">失败</div>
          </div>
          <div class="stat-item warning">
            <div class="stat-value">{{ executionStats.skipped }}</div>
            <div class="stat-label">跳过</div>
          </div>
        </div>
      </div>
      
      <!-- 日志控制台 -->
      <div class="console-section">
        <div class="console-header">
          <h3>执行日志</h3>
          <div class="console-actions">
            <el-button-group size="small">
              <el-button :type="logLevel === 'all' ? 'primary' : ''" @click="logLevel = 'all'">
                全部
              </el-button>
              <el-button :type="logLevel === 'info' ? 'primary' : ''" @click="logLevel = 'info'">
                信息
              </el-button>
              <el-button :type="logLevel === 'error' ? 'primary' : ''" @click="logLevel = 'error'">
                错误
              </el-button>
            </el-button-group>
            <el-button size="small" @click="clearLogs">
              <el-icon><Delete /></el-icon>
              清空
            </el-button>
            <el-button size="small" @click="downloadLogs">
              <el-icon><Download /></el-icon>
              下载
            </el-button>
          </div>
        </div>
        
        <div class="console-content" ref="consoleRef">
          <div class="log-container">
            <div
              v-for="(log, index) in filteredLogs"
              :key="index"
              class="log-line"
              :class="getLogClass(log)"
            >
              <span class="log-time">{{ formatTime(log.timestamp) }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
            
            <div v-if="filteredLogs.length === 0" class="empty-logs">
              <el-empty description="暂无日志" />
            </div>
          </div>
        </div>
      </div>
      
      <!-- 进度条 -->
      <div class="progress-section" v-if="isRunning || executionResults">
        <div class="progress-header">
          <h3>执行进度</h3>
          <span class="progress-text">
            {{ executionStats.completed }}/{{ executionStats.total }}
          </span>
        </div>
        <el-progress
          :percentage="progressPercentage"
          :status="progressStatus"
          :stroke-width="8"
          class="progress-bar"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { apiService } from '@/services/api'
import { ElMessage } from 'element-plus'
import dayjs from 'dayjs'
import {
  VideoPlay,
  Loading,
  CircleCheck,
  CircleClose,
  Delete,
  Download
} from '@element-plus/icons-vue'

// 响应式数据
const isRunning = ref(false)
const executionResults = ref(null)
const logs = ref([])
const logLevel = ref('all')
const consoleRef = ref()
const startTime = ref(null)
const endTime = ref(null)

// 执行统计
const executionStats = ref({
  total: 0,
  passed: 0,
  failed: 0,
  skipped: 0,
  completed: 0
})

// 轮询定时器
let statusTimer = null
let logsTimer = null

// 计算属性
const statusIcon = computed(() => {
  if (isRunning.value) return 'Loading'
  if (executionResults.value) {
    return executionResults.value.status === 'completed' ? 'CircleCheck' : 'CircleClose'
  }
  return 'VideoPlay'
})

const statusText = computed(() => {
  if (isRunning.value) return '正在执行测试...'
  if (executionResults.value) {
    return executionResults.value.status === 'completed' ? '执行完成' : '执行失败'
  }
  return '等待执行'
})

const executionTime = computed(() => {
  if (!startTime.value) return ''
  const end = endTime.value || new Date()
  const duration = dayjs(end).diff(dayjs(startTime.value), 'second')
  return `${duration}s`
})

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') return logs.value
  return logs.value.filter(log => {
    if (logLevel.value === 'error') {
      return log.message.toLowerCase().includes('error') || 
             log.message.toLowerCase().includes('failed') ||
             log.message.toLowerCase().includes('失败')
    }
    if (logLevel.value === 'info') {
      return !log.message.toLowerCase().includes('error') && 
             !log.message.toLowerCase().includes('failed') &&
             !log.message.toLowerCase().includes('失败')
    }
    return true
  })
})

const progressPercentage = computed(() => {
  if (executionStats.value.total === 0) return 0
  return Math.round((executionStats.value.completed / executionStats.value.total) * 100)
})

const progressStatus = computed(() => {
  if (isRunning.value) return 'active'
  if (executionResults.value) {
    return executionResults.value.status === 'completed' ? 'success' : 'exception'
  }
  return ''
})

// 方法
const startExecution = async () => {
  try {
    await apiService.startExecution()
    isRunning.value = true
    startTime.value = new Date()
    endTime.value = null
    logs.value = []
    executionResults.value = null
    
    // 重置统计
    executionStats.value = {
      total: 0,
      passed: 0,
      failed: 0,
      skipped: 0,
      completed: 0
    }
    
    ElMessage.success('测试执行已开始')
    
    // 开始轮询状态和日志
    startPolling()
    
  } catch (error) {
    console.error('启动测试执行失败:', error)
    ElMessage.error('启动测试执行失败')
  }
}

const startPolling = () => {
  // 轮询执行状态
  statusTimer = setInterval(async () => {
    try {
      const response = await apiService.getExecutionStatus()
      const status = response.data
      
      isRunning.value = status.running
      
      if (status.results) {
        executionResults.value = status.results
        endTime.value = new Date()
        
        // 解析执行结果
        parseExecutionResults(status.results)
      }
      
      if (!status.running) {
        stopPolling()
      }
    } catch (error) {
      console.error('获取执行状态失败:', error)
    }
  }, 2000)
  
  // 轮询日志
  logsTimer = setInterval(async () => {
    try {
      const response = await apiService.getExecutionLogs(1000)
      logs.value = response.data || []
      
      // 自动滚动到底部
      nextTick(() => {
        scrollToBottom()
      })
      
    } catch (error) {
      console.error('获取执行日志失败:', error)
    }
  }, 1000)
}

const stopPolling = () => {
  if (statusTimer) {
    clearInterval(statusTimer)
    statusTimer = null
  }
  if (logsTimer) {
    clearInterval(logsTimer)
    logsTimer = null
  }
}

const parseExecutionResults = (results) => {
  // 从日志中解析统计信息
  const logText = logs.value.map(log => log.message).join('\n')
  
  // 简单的正则匹配，实际项目中可能需要更复杂的解析
  const totalMatch = logText.match(/用例总数[:\s]*(\d+)/)
  const failedMatch = logText.match(/失败用例数[:\s]*(\d+)/)
  const passedMatch = logText.match(/成功用例数[:\s]*(\d+)/)
  const skippedMatch = logText.match(/跳过用例数[:\s]*(\d+)/)
  
  if (totalMatch) executionStats.value.total = parseInt(totalMatch[1])
  if (failedMatch) executionStats.value.failed = parseInt(failedMatch[1])
  if (passedMatch) executionStats.value.passed = parseInt(passedMatch[1])
  if (skippedMatch) executionStats.value.skipped = parseInt(skippedMatch[1])
  
  executionStats.value.completed = executionStats.value.passed + 
                                   executionStats.value.failed + 
                                   executionStats.value.skipped
}

const scrollToBottom = () => {
  if (consoleRef.value) {
    const container = consoleRef.value
    container.scrollTop = container.scrollHeight
  }
}

const clearLogs = () => {
  logs.value = []
  ElMessage.success('日志已清空')
}

const downloadLogs = () => {
  const logText = logs.value.map(log => 
    `[${formatTime(log.timestamp)}] ${log.message}`
  ).join('\n')
  
  const blob = new Blob([logText], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `execution-logs-${dayjs().format('YYYY-MM-DD-HH-mm-ss')}.txt`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
  
  ElMessage.success('日志下载成功')
}

const getLogClass = (log) => {
  const message = log.message.toLowerCase()
  if (message.includes('error') || message.includes('failed') || message.includes('失败')) {
    return 'log-error'
  }
  if (message.includes('warning') || message.includes('warn')) {
    return 'log-warning'
  }
  if (message.includes('success') || message.includes('passed') || message.includes('成功')) {
    return 'log-success'
  }
  return 'log-info'
}

const formatTime = (timestamp) => {
  return dayjs(timestamp).format('HH:mm:ss')
}

// 生命周期
onMounted(() => {
  // 检查是否有正在执行的任务
  checkExecutionStatus()
})

onUnmounted(() => {
  stopPolling()
})

const checkExecutionStatus = async () => {
  try {
    const response = await apiService.getExecutionStatus()
    const status = response.data
    
    if (status.running) {
      isRunning.value = true
      startTime.value = new Date() // 这里应该从服务器获取实际开始时间
      startPolling()
    }
    
    if (status.results) {
      executionResults.value = status.results
    }
    
    // 加载现有日志
    const logsResponse = await apiService.getExecutionLogs(1000)
    logs.value = logsResponse.data || []
    
  } catch (error) {
    console.error('检查执行状态失败:', error)
  }
}
</script>

<style lang="scss" scoped>
.execution {
  padding: $spacing-lg;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: $spacing-xl;
  
  .header-left {
    .page-title {
      font-size: $font-size-xxl;
      margin-bottom: $spacing-xs;
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      
      .title-icon {
        font-size: 28px;
      }
    }
    
    .page-subtitle {
      color: rgba(255, 255, 255, 0.8);
      font-size: $font-size-md;
      margin: 0;
    }
  }
  
  .run-button {
    font-size: $font-size-md;
    padding: $spacing-md $spacing-xl;
    border-radius: $sketch-radius;
    
    &:hover {
      transform: translateY(-2px);
      box-shadow: $glow-primary;
    }
  }
}

.execution-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
  overflow: hidden;
}

.status-cards {
  display: flex;
  gap: $spacing-lg;
  
  .status-card {
    flex: 1;
    padding: $spacing-lg;
    display: flex;
    align-items: center;
    gap: $spacing-md;
    transition: all $transition-normal;
    
    &.active {
      border-color: $primary-color;
      box-shadow: $glow-primary;
    }
    
    .card-icon {
      color: $primary-color;
      
      .pulse-animation {
        animation: pulse 2s infinite;
      }
    }
    
    .card-content {
      .status-text {
        font-size: $font-size-lg;
        font-weight: 500;
        color: $text-primary;
        margin-bottom: $spacing-xs;
      }
      
      .status-time {
        color: $text-secondary;
        font-size: $font-size-sm;
      }
    }
  }
  
  .stats-cards {
    display: flex;
    gap: $spacing-md;
    
    .stat-item {
      background: $bg-card;
      border: $sketch-border;
      border-radius: $sketch-radius;
      padding: $spacing-md;
      text-align: center;
      min-width: 80px;
      
      .stat-value {
        font-size: $font-size-xl;
        font-weight: 600;
        margin-bottom: $spacing-xs;
      }
      
      .stat-label {
        font-size: $font-size-sm;
        color: $text-secondary;
      }
      
      &.success .stat-value {
        color: $success-color;
      }
      
      &.error .stat-value {
        color: $error-color;
      }
      
      &.warning .stat-value {
        color: $warning-color;
      }
    }
  }
}

.console-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: $bg-card;
  border: $sketch-border;
  border-radius: $sketch-radius;
  overflow: hidden;
  
  .console-header {
    height: 50px;
    background: $bg-secondary;
    border-bottom: 1px solid $border-color;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 $spacing-md;
    
    h3 {
      font-size: $font-size-md;
      color: $text-primary;
      margin: 0;
    }
    
    .console-actions {
      display: flex;
      gap: $spacing-sm;
      align-items: center;
    }
  }
  
  .console-content {
    flex: 1;
    overflow-y: auto;
    background: #1e1e1e;
    color: #d4d4d4;
    font-family: $font-family-mono;
    font-size: $font-size-sm;
    
    .log-container {
      padding: $spacing-sm;
      
      .log-line {
        padding: 2px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        
        .log-time {
          color: #569cd6;
          margin-right: $spacing-sm;
        }
        
        .log-message {
          white-space: pre-wrap;
          word-break: break-all;
        }
        
        &.log-error {
          .log-message {
            color: #f44747;
          }
        }
        
        &.log-warning {
          .log-message {
            color: #ffcc02;
          }
        }
        
        &.log-success {
          .log-message {
            color: #4ec9b0;
          }
        }
        
        &.log-info {
          .log-message {
            color: #d4d4d4;
          }
        }
      }
      
      .empty-logs {
        display: flex;
        align-items: center;
        justify-content: center;
        height: 200px;
        color: #666;
      }
    }
  }
}

.progress-section {
  background: $bg-card;
  border: $sketch-border;
  border-radius: $sketch-radius;
  padding: $spacing-lg;
  
  .progress-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-md;
    
    h3 {
      font-size: $font-size-md;
      color: $text-primary;
      margin: 0;
    }
    
    .progress-text {
      color: $text-secondary;
      font-size: $font-size-sm;
      font-family: $font-family-mono;
    }
  }
  
  .progress-bar {
    margin-bottom: $spacing-sm;
  }
}
</style>
