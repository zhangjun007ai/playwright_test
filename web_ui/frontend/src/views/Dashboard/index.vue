<template>
  <div class="dashboard">
    <div class="dashboard-header">
      <h1 class="page-title gradient-text">
        <el-icon class="title-icon"><DataAnalysis /></el-icon>
        测试仪表板
      </h1>
      <p class="page-subtitle">项目概览与测试统计</p>
    </div>
    
    <div class="dashboard-content">
      <!-- 统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card sketch-card" v-for="stat in stats" :key="stat.key">
          <div class="stat-icon" :style="{ color: stat.color }">
            <el-icon :size="32"><component :is="stat.icon" /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
          <div class="stat-trend" :class="stat.trend">
            <el-icon><component :is="stat.trendIcon" /></el-icon>
            <span>{{ stat.change }}</span>
          </div>
        </div>
      </div>
      
      <!-- 图表区域 -->
      <div class="charts-grid">
        <!-- 测试趋势图 -->
        <div class="chart-card sketch-card">
          <div class="chart-header">
            <h3>测试执行趋势</h3>
            <el-button-group size="small">
              <el-button :type="trendPeriod === '7d' ? 'primary' : ''" @click="trendPeriod = '7d'">7天</el-button>
              <el-button :type="trendPeriod === '30d' ? 'primary' : ''" @click="trendPeriod = '30d'">30天</el-button>
            </el-button-group>
          </div>
          <div class="chart-content">
            <v-chart :option="trendChartOption" style="height: 300px;" />
          </div>
        </div>
        
        <!-- 用例分布图 -->
        <div class="chart-card sketch-card">
          <div class="chart-header">
            <h3>用例模块分布</h3>
          </div>
          <div class="chart-content">
            <v-chart :option="pieChartOption" style="height: 300px;" />
          </div>
        </div>
      </div>
      
      <!-- 最近活动 -->
      <div class="activity-section">
        <div class="activity-card sketch-card">
          <div class="activity-header">
            <h3>最近执行记录</h3>
            <el-button type="primary" size="small" @click="refreshActivity">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
          </div>
          <div class="activity-content">
            <el-timeline>
              <el-timeline-item
                v-for="activity in recentActivities"
                :key="activity.id"
                :timestamp="activity.timestamp"
                :type="activity.type"
                :icon="activity.icon"
              >
                <div class="activity-item">
                  <div class="activity-title">{{ activity.title }}</div>
                  <div class="activity-description">{{ activity.description }}</div>
                  <div class="activity-meta">
                    <el-tag :type="activity.status === 'success' ? 'success' : activity.status === 'error' ? 'danger' : 'warning'" size="small">
                      {{ activity.statusText }}
                    </el-tag>
                    <span class="activity-duration">耗时: {{ activity.duration }}</span>
                  </div>
                </div>
              </el-timeline-item>
            </el-timeline>
          </div>
        </div>
        
        <!-- 快速操作 -->
        <div class="quick-actions sketch-card">
          <h3>快速操作</h3>
          <div class="action-buttons">
            <el-button
              v-for="action in quickActions"
              :key="action.key"
              :type="action.type"
              :icon="action.icon"
              @click="handleQuickAction(action.key)"
              class="action-button"
            >
              {{ action.label }}
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
} from 'echarts/components'
import VChart from 'vue-echarts'
import { apiService } from '@/services/api'
import { ElMessage } from 'element-plus'
import {
  DataAnalysis,
  Document,
  SuccessFilled,
  VideoPlay,
  Timer,
  ArrowUp,
  ArrowDown,
  Refresh
} from '@element-plus/icons-vue'

// 注册 ECharts 组件
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent
])

const router = useRouter()

// 响应式数据
const loading = ref(false)
const trendPeriod = ref('7d')

// 统计数据
const stats = ref([
  {
    key: 'total_cases',
    label: '总用例数',
    value: '156',
    icon: 'Document',
    color: '#667eea',
    trend: 'up',
    trendIcon: 'ArrowUp',
    change: '+12'
  },
  {
    key: 'success_rate',
    label: '成功率',
    value: '87.5%',
    icon: 'SuccessFilled',
    color: '#00d4aa',
    trend: 'up',
    trendIcon: 'ArrowUp',
    change: '+2.3%'
  },
  {
    key: 'total_executions',
    label: '总执行次数',
    value: '1,234',
    icon: 'VideoPlay',
    color: '#4facfe',
    trend: 'up',
    trendIcon: 'ArrowUp',
    change: '+45'
  },
  {
    key: 'avg_duration',
    label: '平均耗时',
    value: '2.3s',
    icon: 'Timer',
    color: '#ffb74d',
    trend: 'down',
    trendIcon: 'ArrowDown',
    change: '-0.5s'
  }
])

// 最近活动
const recentActivities = ref([
  {
    id: 1,
    title: '登录模块测试',
    description: '执行了 8 个登录相关的测试用例',
    timestamp: '2024-01-15 14:30:25',
    type: 'success',
    icon: 'SuccessFilled',
    status: 'success',
    statusText: '成功',
    duration: '2.1s'
  },
  {
    id: 2,
    title: '收藏功能测试',
    description: '执行了 5 个收藏功能测试用例',
    timestamp: '2024-01-15 14:25:10',
    type: 'warning',
    icon: 'Warning',
    status: 'warning',
    statusText: '部分失败',
    duration: '3.5s'
  },
  {
    id: 3,
    title: '用户信息测试',
    description: '执行了 3 个用户信息相关测试用例',
    timestamp: '2024-01-15 14:20:45',
    type: 'danger',
    icon: 'CircleCloseFilled',
    status: 'error',
    statusText: '失败',
    duration: '1.8s'
  }
])

// 快速操作
const quickActions = ref([
  {
    key: 'run_all',
    label: '执行全部测试',
    type: 'primary',
    icon: 'VideoPlay'
  },
  {
    key: 'create_case',
    label: '新建用例',
    type: 'success',
    icon: 'Plus'
  },
  {
    key: 'view_reports',
    label: '查看报告',
    type: 'info',
    icon: 'PieChart'
  },
  {
    key: 'settings',
    label: '系统设置',
    type: 'warning',
    icon: 'Setting'
  }
])

// 图表配置
const trendChartOption = computed(() => ({
  title: {
    show: false
  },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#667eea',
    textStyle: {
      color: '#2c3e50'
    }
  },
  grid: {
    left: '3%',
    right: '4%',
    bottom: '3%',
    containLabel: true
  },
  xAxis: {
    type: 'category',
    data: ['01-09', '01-10', '01-11', '01-12', '01-13', '01-14', '01-15'],
    axisLine: {
      lineStyle: {
        color: '#e1e8ed'
      }
    },
    axisLabel: {
      color: '#7f8c8d'
    }
  },
  yAxis: {
    type: 'value',
    axisLine: {
      lineStyle: {
        color: '#e1e8ed'
      }
    },
    axisLabel: {
      color: '#7f8c8d'
    },
    splitLine: {
      lineStyle: {
        color: '#f0f3f4'
      }
    }
  },
  series: [
    {
      name: '成功',
      type: 'line',
      data: [45, 52, 48, 61, 55, 67, 58],
      smooth: true,
      lineStyle: {
        color: '#00d4aa',
        width: 3
      },
      itemStyle: {
        color: '#00d4aa'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(0, 212, 170, 0.3)' },
            { offset: 1, color: 'rgba(0, 212, 170, 0.05)' }
          ]
        }
      }
    },
    {
      name: '失败',
      type: 'line',
      data: [8, 12, 7, 15, 9, 11, 13],
      smooth: true,
      lineStyle: {
        color: '#ff5722',
        width: 3
      },
      itemStyle: {
        color: '#ff5722'
      },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(255, 87, 34, 0.3)' },
            { offset: 1, color: 'rgba(255, 87, 34, 0.05)' }
          ]
        }
      }
    }
  ]
}))

const pieChartOption = computed(() => ({
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderColor: '#667eea',
    textStyle: {
      color: '#2c3e50'
    }
  },
  legend: {
    orient: 'vertical',
    left: 'left',
    textStyle: {
      color: '#7f8c8d'
    }
  },
  series: [
    {
      type: 'pie',
      radius: '50%',
      data: [
        { value: 45, name: '登录模块' },
        { value: 32, name: '收藏功能' },
        { value: 28, name: '用户信息' },
        { value: 25, name: '其他接口' }
      ],
      emphasis: {
        itemStyle: {
          shadowBlur: 10,
          shadowOffsetX: 0,
          shadowColor: 'rgba(0, 0, 0, 0.5)'
        }
      },
      itemStyle: {
        borderRadius: 5,
        borderColor: '#fff',
        borderWidth: 2
      }
    }
  ]
}))

// 方法
const handleQuickAction = (actionKey) => {
  switch (actionKey) {
    case 'run_all':
      router.push('/execution')
      break
    case 'create_case':
      router.push('/test-cases')
      break
    case 'view_reports':
      router.push('/reports')
      break
    case 'settings':
      router.push('/configuration')
      break
  }
}

const refreshActivity = () => {
  ElMessage.success('活动记录已刷新')
  // 这里可以调用 API 刷新数据
}

const loadDashboardData = async () => {
  try {
    loading.value = true
    // 这里可以调用 API 获取仪表板数据
    // const response = await apiService.getDashboardData()
    // 更新统计数据
  } catch (error) {
    console.error('加载仪表板数据失败:', error)
  } finally {
    loading.value = false
  }
}

// 生命周期
onMounted(() => {
  loadDashboardData()
})
</script>

<style lang="scss" scoped>
.dashboard {
  padding: $spacing-lg;
  height: 100%;
  overflow-y: auto;
}

.dashboard-header {
  margin-bottom: $spacing-xl;
  text-align: center;
  
  .page-title {
    font-size: $font-size-xxl;
    margin-bottom: $spacing-sm;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: $spacing-sm;
    
    .title-icon {
      font-size: 28px;
    }
  }
  
  .page-subtitle {
    color: rgba(255, 255, 255, 0.8);
    font-size: $font-size-md;
  }
}

.dashboard-content {
  max-width: $container-max-width;
  margin: 0 auto;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: $spacing-lg;
  margin-bottom: $spacing-xl;
}

.stat-card {
  padding: $spacing-lg;
  display: flex;
  align-items: center;
  gap: $spacing-md;
  transition: transform $transition-normal;
  
  &:hover {
    transform: translateY(-4px);
  }
  
  .stat-icon {
    flex-shrink: 0;
  }
  
  .stat-content {
    flex: 1;
    
    .stat-value {
      font-size: $font-size-xl;
      font-weight: 600;
      color: $text-primary;
      margin-bottom: $spacing-xs;
    }
    
    .stat-label {
      color: $text-secondary;
      font-size: $font-size-sm;
    }
  }
  
  .stat-trend {
    display: flex;
    align-items: center;
    gap: $spacing-xs;
    font-size: $font-size-sm;
    font-weight: 500;
    
    &.up {
      color: $success-color;
    }
    
    &.down {
      color: $error-color;
    }
  }
}

.charts-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: $spacing-lg;
  margin-bottom: $spacing-xl;
  
  @media (max-width: $breakpoint-md) {
    grid-template-columns: 1fr;
  }
}

.chart-card {
  padding: $spacing-lg;
  
  .chart-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-lg;
    
    h3 {
      color: $text-primary;
      font-size: $font-size-lg;
      margin: 0;
    }
  }
}

.activity-section {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: $spacing-lg;
  
  @media (max-width: $breakpoint-md) {
    grid-template-columns: 1fr;
  }
}

.activity-card {
  padding: $spacing-lg;
  
  .activity-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: $spacing-lg;
    
    h3 {
      color: $text-primary;
      font-size: $font-size-lg;
      margin: 0;
    }
  }
  
  .activity-content {
    max-height: 400px;
    overflow-y: auto;
  }
  
  .activity-item {
    .activity-title {
      font-weight: 500;
      color: $text-primary;
      margin-bottom: $spacing-xs;
    }
    
    .activity-description {
      color: $text-secondary;
      font-size: $font-size-sm;
      margin-bottom: $spacing-sm;
    }
    
    .activity-meta {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      
      .activity-duration {
        color: $text-light;
        font-size: $font-size-xs;
      }
    }
  }
}

.quick-actions {
  padding: $spacing-lg;
  
  h3 {
    color: $text-primary;
    font-size: $font-size-lg;
    margin: 0 0 $spacing-lg 0;
  }
  
  .action-buttons {
    display: flex;
    flex-direction: column;
    gap: $spacing-sm;
    
    .action-button {
      justify-content: flex-start;
      width: 100%;
    }
  }
}
</style>
