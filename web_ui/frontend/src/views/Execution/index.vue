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
          v-if="!isRunning"
          type="primary"
          size="large"
          @click="showExecutionDialog = true"
          class="run-button"
        >
          <el-icon><VideoPlay /></el-icon>
          开始执行
        </el-button>
        <el-button
          v-else
          type="danger"
          size="large"
          @click="stopExecution"
          class="stop-button"
        >
          <el-icon><VideoPause /></el-icon>
          停止执行
        </el-button>
        <el-button
          @click="showHistory = true"
          :disabled="isRunning"
        >
          <el-icon><Clock /></el-icon>
          执行历史
        </el-button>
      </div>
    </div>
    
    <div class="execution-content">
      <!-- 执行状态卡片 -->
      <div class="status-section">
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
            <div class="status-progress" v-if="isRunning && executionStats.total > 0">
              进度: {{ executionStats.completed }}/{{ executionStats.total }}
            </div>
          </div>
          <div class="card-actions" v-if="!isRunning && executionResults">
            <el-button size="small" @click="viewReport">
              查看报告
            </el-button>
          </div>
        </div>
        
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ executionStats.total }}</div>
            <div class="stat-label">总用例</div>
          </div>
          <div class="stat-card success">
            <div class="stat-value">{{ executionStats.passed }}</div>
            <div class="stat-label">成功</div>
          </div>
          <div class="stat-card error">
            <div class="stat-value">{{ executionStats.failed }}</div>
            <div class="stat-label">失败</div>
          </div>
          <div class="stat-card warning">
            <div class="stat-value">{{ executionStats.skipped }}</div>
            <div class="stat-label">跳过</div>
          </div>
        </div>
      </div>
      
      <!-- 进度条 -->
      <div class="progress-section" v-if="isRunning || executionResults">
        <div class="progress-header">
          <h3>执行进度</h3>
          <span class="progress-text">
            {{ progressPercentage }}% ({{ executionStats.completed }}/{{ executionStats.total }})
          </span>
        </div>
        <el-progress
          :percentage="progressPercentage"
          :status="progressStatus"
          :stroke-width="8"
          class="progress-bar"
        />
      </div>
      
      <!-- 日志控制台 -->
      <div class="console-section">
        <div class="console-header">
          <h3>执行日志</h3>
          <div class="console-controls">
            <div class="log-filters">
              <el-button-group size="small">
                <el-button 
                  :type="logLevel === 'all' ? 'primary' : ''" 
                  @click="logLevel = 'all'"
                >
                  全部 ({{ logs.length }})
                </el-button>
                <el-button 
                  :type="logLevel === 'info' ? 'primary' : ''" 
                  @click="logLevel = 'info'"
                >
                  信息 ({{ infoLogCount }})
                </el-button>
                <el-button 
                  :type="logLevel === 'error' ? 'primary' : ''" 
                  @click="logLevel = 'error'"
                >
                  错误 ({{ errorLogCount }})
                </el-button>
              </el-button-group>
            </div>
            
            <div class="console-actions">
              <el-switch
                v-model="autoScroll"
                active-text="自动滚动"
                inactive-text=""
                size="small"
              />
              <el-button size="small" @click="clearLogs" :disabled="isRunning">
                <el-icon><Delete /></el-icon>
                清空
              </el-button>
              <el-button size="small" @click="downloadLogs" :disabled="logs.length === 0">
                <el-icon><Download /></el-icon>
                下载
              </el-button>
            </div>
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
              <span class="log-level">{{ getLogLevel(log) }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
            
            <div v-if="filteredLogs.length === 0" class="empty-logs">
              <el-empty 
                :description="logs.length === 0 ? '暂无日志' : '暂无匹配的日志'" 
                :image-size="60"
              />
            </div>
            
            <!-- 实时日志指示器 -->
            <div v-if="isRunning" class="log-indicator">
              <el-icon class="loading-icon"><Loading /></el-icon>
              <span>实时接收日志中...</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 执行配置对话框 -->
    <el-dialog
      v-model="showExecutionDialog"
      title="执行配置"
      width="600px"
      center
    >
      <el-form :model="executionConfig" label-width="120px">
        <el-form-item label="执行范围">
          <el-radio-group v-model="executionConfig.scope">
            <el-radio value="all">全部用例</el-radio>
            <el-radio value="module">按模块执行</el-radio>
            <el-radio value="custom">自定义用例</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="选择模块" v-if="executionConfig.scope === 'module'">
          <el-select v-model="executionConfig.modules" multiple placeholder="选择要执行的模块">
            <el-option
              v-for="module in availableModules"
              :key="module"
              :label="module"
              :value="module"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="自定义用例" v-if="executionConfig.scope === 'custom'">
          <el-input
            v-model="executionConfig.customCases"
            type="textarea"
            rows="3"
            placeholder="输入要执行的用例文件路径，每行一个"
          />
        </el-form-item>
        
        <el-form-item label="并发数">
          <el-slider
            v-model="executionConfig.workers"
            :min="1"
            :max="10"
            show-input
            :show-input-controls="false"
          />
        </el-form-item>
        
        <el-form-item label="失败后处理">
          <el-radio-group v-model="executionConfig.failureAction">
            <el-radio value="continue">继续执行</el-radio>
            <el-radio value="stop">立即停止</el-radio>
          </el-radio-group>
        </el-form-item>
        
        <el-form-item label="生成报告">
          <el-checkbox v-model="executionConfig.generateReport">生成Allure报告</el-checkbox>
        </el-form-item>
        
        <el-form-item label="通知设置">
          <el-checkbox v-model="executionConfig.sendNotification">执行完成后发送通知</el-checkbox>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showExecutionDialog = false">取消</el-button>
        <el-button type="primary" @click="startExecution" :loading="isRunning">
          开始执行
        </el-button>
      </template>
    </el-dialog>

    <!-- 执行历史对话框 -->
    <el-dialog
      v-model="showHistory"
      title="执行历史"
      width="900px"
      center
    >
      <div class="history-content">
        <div class="history-header">
          <el-button @click="loadExecutionHistory" :loading="historyLoading">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
        
        <el-table :data="executionHistory" v-loading="historyLoading">
          <el-table-column prop="id" label="ID" width="100" />
          <el-table-column prop="startTime" label="开始时间" width="180">
            <template #default="{ row }">
              {{ formatDateTime(row.startTime) }}
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="耗时" width="100" />
          <el-table-column prop="totalCases" label="总用例" width="80" />
          <el-table-column prop="passedCases" label="成功" width="80">
            <template #default="{ row }">
              <span class="success-text">{{ row.passedCases }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="failedCases" label="失败" width="80">
            <template #default="{ row }">
              <span class="error-text">{{ row.failedCases }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="successRate" label="成功率" width="100">
            <template #default="{ row }">
              <el-tag :type="row.successRate >= 90 ? 'success' : row.successRate >= 70 ? 'warning' : 'danger'">
                {{ row.successRate }}%
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="getStatusType(row.status)">
                {{ getStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="viewHistoryReport(row)">
                查看报告
              </el-button>
              <el-button size="small" @click="viewHistoryLogs(row)">
                查看日志
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { apiService } from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import dayjs from 'dayjs'
import {
  VideoPlay,
  VideoPause,
  Loading,
  CircleCheck,
  CircleClose,
  Delete,
  Download,
  Clock,
  Refresh
} from '@element-plus/icons-vue'

// 响应式数据
const isRunning = ref(false)
const executionResults = ref(null)
const logs = ref([])
const logLevel = ref('all')
const autoScroll = ref(true)
const consoleRef = ref()
const startTime = ref(null)
const endTime = ref(null)

// 对话框控制
const showExecutionDialog = ref(false)
const showHistory = ref(false)
const historyLoading = ref(false)

// 执行配置
const executionConfig = ref({
  scope: 'all',
  modules: [],
  customCases: '',
  workers: 2,
  failureAction: 'continue',
  generateReport: true,
  sendNotification: false
})

// 可用模块列表
const availableModules = ref(['Login', 'UserInfo', 'Collect'])

// 执行统计
const executionStats = ref({
  total: 0,
  passed: 0,
  failed: 0,
  skipped: 0,
  completed: 0
})

// 执行历史
const executionHistory = ref([])

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
      return isErrorLog(log)
    }
    if (logLevel.value === 'info') {
      return !isErrorLog(log)
    }
    return true
  })
})

const infoLogCount = computed(() => {
  return logs.value.filter(log => !isErrorLog(log)).length
})

const errorLogCount = computed(() => {
  return logs.value.filter(log => isErrorLog(log)).length
})

const progressPercentage = computed(() => {
  if (executionStats.value.total === 0) return 0
  return Math.round((executionStats.value.completed / executionStats.value.total) * 100)
})

const progressStatus = computed(() => {
  if (isRunning.value) return ''
  if (executionResults.value) {
    return executionResults.value.status === 'completed' ? 'success' : 'exception'
  }
  return ''
})

// 监听自动滚动设置
watch(logs, () => {
  if (autoScroll.value) {
    nextTick(() => {
      scrollToBottom()
    })
  }
}, { deep: true })

// 方法
const startExecution = async () => {
  try {
    await apiService.startExecution(executionConfig.value)
    isRunning.value = true
    startTime.value = new Date()
    endTime.value = null
    logs.value = []
    executionResults.value = null
    showExecutionDialog.value = false
    
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

const stopExecution = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要停止当前执行吗？',
      '确认停止',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await apiService.stopExecution()
    isRunning.value = false
    stopPolling()
    
    ElMessage.success('测试执行已停止')
    
  } catch (error) {
    if (error !== 'cancel') {
      console.error('停止测试执行失败:', error)
      ElMessage.error('停止测试执行失败')
    }
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
        ElMessage.success('测试执行完成')
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
  // 从结果中解析统计信息
  if (results.stats) {
    executionStats.value = {
      total: results.stats.total || 0,
      passed: results.stats.passed || 0,
      failed: results.stats.failed || 0,
      skipped: results.stats.skipped || 0,
      completed: (results.stats.passed || 0) + (results.stats.failed || 0) + (results.stats.skipped || 0)
    }
  }
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
    `[${formatTime(log.timestamp)}] [${getLogLevel(log)}] ${log.message}`
  ).join('\n')
  
  const blob = new Blob([logText], { type: 'text/plain;charset=utf-8' })
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

const viewReport = () => {
  // 打开Allure报告
  window.open('http://localhost:9999', '_blank')
  ElMessage.info('正在打开测试报告...')
}

const loadExecutionHistory = async () => {
  try {
    historyLoading.value = true
    const response = await apiService.getExecutionHistory()
    executionHistory.value = response.data || []
  } catch (error) {
    console.error('加载执行历史失败:', error)
    ElMessage.error('加载执行历史失败')
  } finally {
    historyLoading.value = false
  }
}

const viewHistoryReport = (historyItem) => {
  ElMessage.info(`查看执行报告: ${historyItem.id}`)
  // 这里可以跳转到历史报告页面
}

const viewHistoryLogs = (historyItem) => {
  ElMessage.info(`查看执行日志: ${historyItem.id}`)
  // 这里可以显示历史日志
}

const getLogClass = (log) => {
  if (isErrorLog(log)) return 'log-error'
  if (isWarningLog(log)) return 'log-warning'
  if (isSuccessLog(log)) return 'log-success'
  return 'log-info'
}

const getLogLevel = (log) => {
  if (isErrorLog(log)) return 'ERROR'
  if (isWarningLog(log)) return 'WARN'
  if (isSuccessLog(log)) return 'SUCCESS'
  return 'INFO'
}

const isErrorLog = (log) => {
  const message = log.message.toLowerCase()
  return message.includes('error') || message.includes('failed') || 
         message.includes('失败') || message.includes('错误')
}

const isWarningLog = (log) => {
  const message = log.message.toLowerCase()
  return message.includes('warning') || message.includes('warn') || 
         message.includes('警告')
}

const isSuccessLog = (log) => {
  const message = log.message.toLowerCase()
  return message.includes('success') || message.includes('passed') || 
         message.includes('成功') || message.includes('通过')
}

const getStatusType = (status) => {
  const statusMap = {
    'completed': 'success',
    'failed': 'danger',
    'stopped': 'warning',
    'running': 'primary'
  }
  return statusMap[status] || 'info'
}

const getStatusText = (status) => {
  const statusMap = {
    'completed': '完成',
    'failed': '失败',
    'stopped': '已停止',
    'running': '运行中'
  }
  return statusMap[status] || status
}

const formatTime = (timestamp) => {
  return dayjs(timestamp).format('HH:mm:ss')
}

const formatDateTime = (timestamp) => {
  return dayjs(timestamp).format('YYYY-MM-DD HH:mm:ss')
}

// 生命周期
onMounted(() => {
  // 检查是否有正在执行的任务
  checkExecutionStatus()
  loadExecutionHistory()
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
      parseExecutionResults(status.results)
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
  margin-bottom: $spacing-xl;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  
  .header-left {
    flex: 1;
    
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
  
  .header-actions {
    display: flex;
    gap: $spacing-md;
    
    .run-button,
    .stop-button {
      font-size: $font-size-md;
      padding: $spacing-md $spacing-lg;
      border-radius: $sketch-radius;
    }
    
    .stop-button {
      background: linear-gradient(135deg, #ff5722, #f44336);
      
      &:hover {
        background: linear-gradient(135deg, #f44336, #e53935);
      }
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

.status-section {
  display: flex;
  gap: $spacing-lg;
  
  .status-card {
    flex: 1;
    padding: $spacing-lg;
    display: flex;
    align-items: center;
    gap: $spacing-lg;
    transition: all $transition-normal;
    
    &.active {
      background: linear-gradient(135deg, rgba(102, 126, 234, 0.1), rgba(118, 75, 162, 0.1));
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
      flex: 1;
      
      .status-text {
        font-size: $font-size-lg;
        font-weight: 600;
        color: $text-primary;
        margin-bottom: $spacing-xs;
      }
      
      .status-time,
      .status-progress {
        font-size: $font-size-sm;
        color: $text-secondary;
      }
    }
    
    .card-actions {
      display: flex;
      gap: $spacing-sm;
    }
  }
  
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: $spacing-md;
    min-width: 400px;
    
    .stat-card {
      padding: $spacing-md;
      text-align: center;
      background: rgba(255, 255, 255, 0.95);
      border-radius: $sketch-radius;
      border: 1px solid $border-light;
      
      &.success {
        border-color: $success-color;
        background: rgba(0, 212, 170, 0.1);
      }
      
      &.error {
        border-color: $error-color;
        background: rgba(255, 87, 34, 0.1);
      }
      
      &.warning {
        border-color: $warning-color;
        background: rgba(255, 183, 77, 0.1);
      }
      
      .stat-value {
        font-size: $font-size-xl;
        font-weight: 600;
        margin-bottom: $spacing-xs;
      }
      
      .stat-label {
        font-size: $font-size-sm;
        color: $text-secondary;
      }
    }
  }
}

.progress-section {
  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-md;
    
    h3 {
      margin: 0;
      color: $text-primary;
    }
    
    .progress-text {
      font-size: $font-size-sm;
      color: $text-secondary;
    }
  }
  
  .progress-bar {
    :deep(.el-progress-bar__outer) {
      background: rgba(255, 255, 255, 0.2);
    }
  }
}

.console-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.95);
  border-radius: $sketch-radius;
  border: 1px solid $border-light;
  min-height: 0;
  
  .console-header {
    padding: $spacing-md $spacing-lg;
    border-bottom: 1px solid $border-light;
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    h3 {
      margin: 0;
      color: $text-primary;
    }
    
    .console-controls {
      display: flex;
      align-items: center;
      gap: $spacing-lg;
      
      .log-filters {
        display: flex;
        align-items: center;
      }
      
      .console-actions {
        display: flex;
        align-items: center;
        gap: $spacing-sm;
      }
    }
  }
  
  .console-content {
    flex: 1;
    overflow-y: auto;
    background: #1e1e1e;
    color: #ffffff;
    font-family: $font-family-mono;
    font-size: $font-size-sm;
    
    .log-container {
      padding: $spacing-md;
      
      .log-line {
        display: flex;
        margin-bottom: $spacing-xs;
        line-height: 1.5;
        border-left: 3px solid transparent;
        padding-left: $spacing-sm;
        
        &.log-error {
          color: #ff6b6b;
          border-left-color: #ff6b6b;
        }
        
        &.log-warning {
          color: #ffa726;
          border-left-color: #ffa726;
        }
        
        &.log-success {
          color: #4caf50;
          border-left-color: #4caf50;
        }
        
        &.log-info {
          color: #ffffff;
        }
        
        .log-time {
          color: #9e9e9e;
          margin-right: $spacing-sm;
          min-width: 80px;
        }
        
        .log-level {
          color: #bb86fc;
          margin-right: $spacing-sm;
          min-width: 60px;
          font-weight: 500;
        }
        
        .log-message {
          flex: 1;
          word-break: break-all;
        }
      }
      
      .empty-logs {
        display: flex;
        justify-content: center;
        align-items: center;
        height: 200px;
        color: #9e9e9e;
      }
      
      .log-indicator {
        display: flex;
        align-items: center;
        gap: $spacing-sm;
        color: #bb86fc;
        margin-top: $spacing-md;
        padding: $spacing-sm;
        background: rgba(187, 134, 252, 0.1);
        border-radius: $sketch-radius;
        
        .loading-icon {
          animation: spin 1s linear infinite;
        }
      }
    }
  }
}

.history-content {
  .history-header {
    margin-bottom: $spacing-md;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .success-text {
    color: $success-color;
    font-weight: 500;
  }
  
  .error-text {
    color: $error-color;
    font-weight: 500;
  }
}

// 动画
@keyframes pulse {
  0% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.05); }
  100% { opacity: 1; transform: scale(1); }
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
