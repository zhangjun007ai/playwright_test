<template>
  <div class="layout-container">
    <!-- 侧边栏 -->
    <div class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="sidebar-header">
        <div class="logo" v-if="!sidebarCollapsed">
          <svg class="logo-icon" viewBox="0 0 100 100">
            <!-- 手绘风格的测试图标 -->
            <path 
              d="M20,20 Q25,15 30,20 L70,20 Q75,15 80,20 L80,80 Q75,85 70,80 L30,80 Q25,85 20,80 Z" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2"
              class="sketch-line"
            />
            <circle cx="35" cy="35" r="3" fill="currentColor" />
            <circle cx="50" cy="35" r="3" fill="currentColor" />
            <circle cx="65" cy="35" r="3" fill="currentColor" />
            <path 
              d="M30,50 Q50,45 70,50" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2"
              class="sketch-line"
            />
            <path 
              d="M30,65 Q50,60 70,65" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2"
              class="sketch-line"
            />
          </svg>
          <span class="logo-text gradient-text">Pytest Auto API</span>
        </div>
        <div class="logo-mini" v-else>
          <svg class="logo-icon" viewBox="0 0 100 100">
            <path 
              d="M20,20 Q25,15 30,20 L70,20 Q75,15 80,20 L80,80 Q75,85 70,80 L30,80 Q25,85 20,80 Z" 
              fill="none" 
              stroke="currentColor" 
              stroke-width="2"
            />
          </svg>
        </div>
      </div>
      
      <div class="sidebar-menu">
        <el-menu
          :default-active="$route.path"
          :collapse="sidebarCollapsed"
          :unique-opened="true"
          router
          text-color="#ffffff"
          active-text-color="#ffffff"
        >
          <el-menu-item
            v-for="route in menuRoutes"
            :key="route.path"
            :index="route.path"
            class="menu-item"
          >
            <el-icon>
              <component :is="route.iconComponent" />
            </el-icon>
            <template #title>{{ route.meta.title }}</template>
          </el-menu-item>
        </el-menu>
      </div>
    </div>
    
    <!-- 主内容区域 -->
    <div class="main-container">
      <!-- 顶部导航栏 -->
      <div class="header">
        <div class="header-left">
          <el-button
            link
            @click="toggleSidebar"
            class="sidebar-toggle"
          >
            <el-icon size="20">
              <Expand v-if="sidebarCollapsed" />
              <Fold v-else />
            </el-icon>
          </el-button>
          
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentRoute?.meta?.title || '页面' }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <div class="status-indicator" :class="{ online: isOnline }">
            <el-icon><Connection /></el-icon>
            <span>{{ isOnline ? '已连接' : '连接中' }}</span>
          </div>
          
          <el-dropdown trigger="click">
            <div class="user-info">
              <el-avatar :size="32" class="user-avatar">
                <el-icon><User /></el-icon>
              </el-avatar>
              <span class="username">{{ config.tester_name || '测试工程师' }}</span>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="showAbout = true">
                  <el-icon><InfoFilled /></el-icon>
                  关于
                </el-dropdown-item>
                <el-dropdown-item @click="refreshPage">
                  <el-icon><Refresh /></el-icon>
                  刷新页面
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      
      <!-- 页面内容 -->
      <div class="content">
        <router-view v-slot="{ Component }">
          <transition name="fade" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </div>
    </div>
    
    <!-- 关于对话框 -->
    <el-dialog
      v-model="showAbout"
      title="关于 Pytest Auto API"
      width="500px"
      center
    >
      <div class="about-content">
        <div class="about-logo">
          <svg viewBox="0 0 100 100" width="60" height="60">
            <path 
              d="M20,20 Q25,15 30,20 L70,20 Q75,15 80,20 L80,80 Q75,85 70,80 L30,80 Q25,85 20,80 Z" 
              fill="none" 
              stroke="#667eea" 
              stroke-width="2"
            />
            <circle cx="35" cy="35" r="3" fill="#667eea" />
            <circle cx="50" cy="35" r="3" fill="#667eea" />
            <circle cx="65" cy="35" r="3" fill="#667eea" />
          </svg>
        </div>
        <h3 class="gradient-text">Pytest Auto API 测试框架</h3>
        <p class="about-description">
          基于 Python + pytest + allure + yaml 的接口自动化测试框架，
          支持数据驱动、多业务依赖、数据库断言等功能。
        </p>
        <div class="about-info">
          <p><strong>版本：</strong>v2.0.0</p>
          <p><strong>作者：</strong>余少琪</p>
          <p><strong>技术栈：</strong>Vue 3 + Element Plus + Flask</p>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useConfigStore } from '@/stores/config'
import {
  Expand, Fold, Connection, User, InfoFilled, Refresh,
  DataAnalysis, Document, VideoPlay, PieChart, Setting, Tools
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const configStore = useConfigStore()

// 响应式数据
const sidebarCollapsed = ref(false)
const showAbout = ref(false)
const isOnline = ref(false)

// 计算属性
const config = computed(() => configStore.config)
const currentRoute = computed(() => route)

// 图标映射
const iconMap = {
  'DataAnalysis': DataAnalysis,
  'Document': Document,
  'VideoPlay': VideoPlay,
  'PieChart': PieChart,
  'Setting': Setting,
  'Tools': Tools
}

// 菜单路由（过滤掉隐藏的路由）
const menuRoutes = computed(() => {
  return router.getRoutes()
    .filter(route => route.path !== '/' && !route.meta?.hidden)
    .filter(route => route.meta?.title)
    .map(route => ({
      ...route,
      iconComponent: iconMap[route.meta?.icon] || Document
    }))
})

// 方法
const toggleSidebar = () => {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

const refreshPage = () => {
  window.location.reload()
}

const checkConnection = async () => {
  try {
    const response = await fetch('/api/health')
    isOnline.value = response.ok
  } catch (error) {
    isOnline.value = false
  }
}

// 生命周期
onMounted(async () => {
  await configStore.fetchConfig()
  await checkConnection()
  
  // 定期检查连接状态
  setInterval(checkConnection, 30000)
})
</script>

<style lang="scss" scoped>
.layout-container {
  display: flex;
  height: 100vh;
  background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);
}

.sidebar {
  width: $sidebar-width;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(255, 255, 255, 0.2);
  transition: width $transition-normal;
  
  &.collapsed {
    width: $sidebar-collapsed-width;
  }
  
  .sidebar-header {
    height: $header-height;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 $spacing-md;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    
    .logo {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      
      .logo-icon {
        width: 32px;
        height: 32px;
        color: $text-white;
      }
      
      .logo-text {
        font-size: $font-size-lg;
        font-weight: 600;
        color: $text-white;
      }
    }
    
    .logo-mini {
      .logo-icon {
        width: 28px;
        height: 28px;
        color: $text-white;
      }
    }
  }
  
  .sidebar-menu {
    padding: $spacing-md;
    height: calc(100vh - #{$header-height});
    overflow-y: auto;
    
    .menu-item {
      margin-bottom: $spacing-xs;
      border-radius: $sketch-radius;
      
      &:hover {
        background: rgba(255, 255, 255, 0.1) !important;
      }
      
      &.is-active {
        background: linear-gradient(135deg, $accent-color, $secondary-color) !important;
        box-shadow: $glow-accent;
      }
    }
  }
}

.main-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: $header-height;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid $border-light;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $spacing-lg;
  box-shadow: $shadow-light;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: $spacing-lg;
    
    .sidebar-toggle {
      color: $text-secondary;
      
      &:hover {
        color: $primary-color;
      }
    }
    
    .breadcrumb {
      font-size: $font-size-sm;
    }
  }
  
  .header-right {
    display: flex;
    align-items: center;
    gap: $spacing-lg;
    
    .status-indicator {
      display: flex;
      align-items: center;
      gap: $spacing-xs;
      color: $text-secondary;
      font-size: $font-size-sm;
      
      &.online {
        color: $success-color;
      }
    }
    
    .user-info {
      display: flex;
      align-items: center;
      gap: $spacing-sm;
      cursor: pointer;
      padding: $spacing-xs $spacing-sm;
      border-radius: $sketch-radius;
      transition: background-color $transition-fast;
      
      &:hover {
        background: rgba(102, 126, 234, 0.1);
      }
      
      .username {
        font-size: $font-size-sm;
        color: $text-primary;
      }
    }
  }
}

.content {
  flex: 1;
  overflow: auto;
  background: rgba(255, 255, 255, 0.05);
}

.about-content {
  text-align: center;
  
  .about-logo {
    margin-bottom: $spacing-lg;
  }
  
  h3 {
    margin-bottom: $spacing-md;
    font-size: $font-size-xl;
  }
  
  .about-description {
    color: $text-secondary;
    line-height: 1.6;
    margin-bottom: $spacing-lg;
  }
  
  .about-info {
    text-align: left;
    
    p {
      margin-bottom: $spacing-xs;
      color: $text-secondary;
    }
  }
}

// 页面切换动画
.fade-enter-active,
.fade-leave-active {
  transition: opacity $transition-normal;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
