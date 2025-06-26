<template>
  <div class="reports">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title gradient-text">
          <el-icon class="title-icon"><PieChart /></el-icon>
          报告中心
        </h1>
        <p class="page-subtitle">测试报告与分析</p>
      </div>
      <div class="header-actions">
        <el-button @click="openAllureReport">
          <el-icon><View /></el-icon>
          查看 Allure 报告
        </el-button>
        <el-button @click="refreshReports">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    
    <div class="reports-content">
      <!-- 报告概览 -->
      <div class="overview-section">
        <div class="overview-card sketch-card">
          <h3>最新报告</h3>
          <div class="report-summary">
            <div class="summary-item">
              <span class="item-label">执行时间:</span>
              <span class="value">{{ latestReport.executionTime }}</span>
            </div>
            <div class="summary-item">
              <span class="item-label">总用例数:</span>
              <span class="value">{{ latestReport.totalCases }}</span>
            </div>
            <div class="summary-item">
              <span class="item-label">成功率:</span>
              <span class="value success">{{ latestReport.successRate }}%</span>
            </div>
            <div class="summary-item">
              <span class="item-label">执行时长:</span>
              <span class="value">{{ latestReport.duration }}</span>
            </div>
          </div>
        </div>
        
        <div class="chart-card sketch-card">
          <h3>测试结果分布</h3>
          <div v-if="chartLoading" class="chart-loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>图表加载中...</span>
          </div>
          <div v-else class="simple-chart">
            <div class="chart-legend">
              <div
                v-for="item in chartData"
                :key="item.name"
                class="legend-item"
              >
                <div
                  class="legend-color"
                  :style="{ backgroundColor: item.color }"
                ></div>
                <span class="legend-name">{{ item.name }}</span>
                <span class="legend-value">{{ item.value }} ({{ item.percentage }}%)</span>
              </div>
            </div>
            <div class="chart-bars">
              <div
                v-for="item in chartData"
                :key="item.name"
                class="chart-bar"
              >
                <div class="bar-label">{{ item.name }}</div>
                <div class="bar-container">
                  <div
                    class="bar-fill"
                    :style="{
                      width: item.percentage + '%',
                      backgroundColor: item.color
                    }"
                  ></div>
                </div>
                <div class="bar-value">{{ item.percentage }}%</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 历史报告列表 -->
      <div class="history-section sketch-card">
        <div class="section-header">
          <h3>历史报告</h3>
          <el-button size="small" @click="exportReports">
            <el-icon><Download /></el-icon>
            导出
          </el-button>
        </div>
        
        <el-table :data="reportHistory" style="width: 100%">
          <el-table-column prop="id" label="报告ID" width="120" />
          <el-table-column prop="executionTime" label="执行时间" width="180" />
          <el-table-column prop="totalCases" label="总用例" width="100" align="center" />
          <el-table-column prop="passedCases" label="成功" width="80" align="center">
            <template #default="{ row }">
              <span class="success-text">{{ row.passedCases }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="failedCases" label="失败" width="80" align="center">
            <template #default="{ row }">
              <span class="error-text">{{ row.failedCases }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="skippedCases" label="跳过" width="80" align="center">
            <template #default="{ row }">
              <span class="warning-text">{{ row.skippedCases }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="successRate" label="成功率" width="100" align="center">
            <template #default="{ row }">
              <el-progress
                :percentage="row.successRate"
                :stroke-width="6"
                :show-text="false"
                :status="row.successRate >= 80 ? 'success' : row.successRate >= 60 ? 'warning' : 'exception'"
              />
              <span class="rate-text">{{ row.successRate }}%</span>
            </template>
          </el-table-column>
          <el-table-column prop="duration" label="执行时长" width="120" align="center" />
          <el-table-column label="操作" width="150" align="center">
            <template #default="{ row }">
              <el-button size="small" type="primary" @click="viewReport(row)">
                查看
              </el-button>
              <el-button size="small" @click="downloadReport(row)">
                下载
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  PieChart,
  View,
  Refresh,
  Loading,
  Download
} from '@element-plus/icons-vue'

// 简化的图表数据，不使用 ECharts
const chartData = computed(() => {
  if (!latestReport.value) return []

  return [
    {
      name: '成功',
      value: latestReport.value.passedCases || 0,
      color: '#00d4aa',
      percentage: Math.round((latestReport.value.passedCases / latestReport.value.totalCases) * 100) || 0
    },
    {
      name: '失败',
      value: latestReport.value.failedCases || 0,
      color: '#ff5722',
      percentage: Math.round((latestReport.value.failedCases / latestReport.value.totalCases) * 100) || 0
    },
    {
      name: '跳过',
      value: latestReport.value.skippedCases || 0,
      color: '#ffb74d',
      percentage: Math.round((latestReport.value.skippedCases / latestReport.value.totalCases) * 100) || 0
    }
  ]
})

// 响应式数据
const loading = ref(false)
const chartLoading = ref(true)

// 最新报告数据
const latestReport = ref({
  executionTime: '2024-01-15 14:30:25',
  totalCases: 156,
  passedCases: 136,
  failedCases: 15,
  skippedCases: 5,
  successRate: 87.2,
  duration: '6.59s'
})

// 历史报告数据
const reportHistory = ref([
  {
    id: 'RPT-20240115-001',
    executionTime: '2024-01-15 14:30:25',
    totalCases: 156,
    passedCases: 136,
    failedCases: 15,
    skippedCases: 5,
    successRate: 87.2,
    duration: '6.59s'
  },
  {
    id: 'RPT-20240115-002',
    executionTime: '2024-01-15 10:15:10',
    totalCases: 156,
    passedCases: 142,
    failedCases: 10,
    skippedCases: 4,
    successRate: 91.0,
    duration: '5.23s'
  },
  {
    id: 'RPT-20240114-001',
    executionTime: '2024-01-14 16:45:30',
    totalCases: 150,
    passedCases: 125,
    failedCases: 20,
    skippedCases: 5,
    successRate: 83.3,
    duration: '7.12s'
  }
])

// 图表相关函数已移至上方的 chartData computed

// 方法
const openAllureReport = () => {
  // 打开 Allure 报告
  window.open('http://localhost:9999', '_blank')
  ElMessage.info('正在打开 Allure 报告...')
}

const refreshReports = () => {
  ElMessage.success('报告数据已刷新')
  // 这里可以调用 API 刷新数据
}

const viewReport = (report) => {
  ElMessage.info(`查看报告: ${report.id}`)
  // 这里可以跳转到详细报告页面
}

const downloadReport = (report) => {
  ElMessage.success(`下载报告: ${report.id}`)
  // 这里可以下载报告文件
}

const exportReports = () => {
  ElMessage.success('报告导出成功')
  // 这里可以导出所有报告
}

// 生命周期
onMounted(() => {
  // 模拟加载延迟
  setTimeout(() => {
    chartLoading.value = false
  }, 1000)
})
</script>

<style lang="scss" scoped>
.reports {
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
  
  .header-actions {
    display: flex;
    gap: $spacing-sm;
  }
}

.reports-content {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: $spacing-lg;
}

.overview-section {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: $spacing-lg;
  
  @media (max-width: $breakpoint-md) {
    grid-template-columns: 1fr;
  }
  
  .overview-card {
    padding: $spacing-lg;
    
    h3 {
      color: $text-primary;
      margin: 0 0 $spacing-lg 0;
    }
    
    .report-summary {
      .summary-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: $spacing-sm 0;
        border-bottom: 1px solid $border-light;
        
        &:last-child {
          border-bottom: none;
        }
        
        .item-label {
          color: $text-secondary;
          font-size: $font-size-sm;
        }
        
        .value {
          font-weight: 500;
          color: $text-primary;
          
          &.success {
            color: $success-color;
          }
        }
      }
    }
  }
  
  .chart-card {
    padding: $spacing-lg;

    h3 {
      color: $text-primary;
      margin: 0 0 $spacing-md 0;
    }

    .chart-loading {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 200px;
      color: $text-secondary;
      gap: $spacing-sm;

      .el-icon {
        font-size: 20px;
      }
    }

    .simple-chart {
      .chart-legend {
        display: flex;
        flex-direction: column;
        gap: $spacing-sm;
        margin-bottom: $spacing-lg;

        .legend-item {
          display: flex;
          align-items: center;
          gap: $spacing-sm;

          .legend-color {
            width: 12px;
            height: 12px;
            border-radius: 2px;
          }

          .legend-name {
            color: $text-primary;
            font-size: $font-size-sm;
            min-width: 40px;
          }

          .legend-value {
            color: $text-secondary;
            font-size: $font-size-sm;
            margin-left: auto;
          }
        }
      }

      .chart-bars {
        .chart-bar {
          display: flex;
          align-items: center;
          gap: $spacing-sm;
          margin-bottom: $spacing-sm;

          .bar-label {
            color: $text-primary;
            font-size: $font-size-sm;
            min-width: 40px;
          }

          .bar-container {
            flex: 1;
            height: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            overflow: hidden;

            .bar-fill {
              height: 100%;
              border-radius: 10px;
              transition: width 0.3s ease;
            }
          }

          .bar-value {
            color: $text-secondary;
            font-size: $font-size-sm;
            min-width: 40px;
            text-align: right;
          }
        }
      }
    }
  }
}

.history-section {
  padding: $spacing-lg;
  
  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-lg;
    
    h3 {
      color: $text-primary;
      margin: 0;
    }
  }
  
  .success-text {
    color: $success-color;
    font-weight: 500;
  }
  
  .error-text {
    color: $error-color;
    font-weight: 500;
  }
  
  .warning-text {
    color: $warning-color;
    font-weight: 500;
  }
  
  .rate-text {
    font-size: $font-size-sm;
    margin-left: $spacing-xs;
  }
}
</style>
