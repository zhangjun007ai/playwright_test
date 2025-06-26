<template>
  <div class="not-found">
    <div class="not-found-content">
      <div class="error-illustration">
        <svg viewBox="0 0 200 200" width="200" height="200">
          <!-- 手绘风格的 404 插图 -->
          <path 
            d="M50,50 Q60,40 70,50 L130,50 Q140,40 150,50 L150,150 Q140,160 130,150 L70,150 Q60,160 50,150 Z" 
            fill="none" 
            stroke="#667eea" 
            stroke-width="3"
            class="sketch-line"
          />
          <text x="100" y="110" text-anchor="middle" fill="#667eea" font-size="36" font-weight="bold">404</text>
          <circle cx="80" cy="80" r="3" fill="#667eea" />
          <circle cx="120" cy="80" r="3" fill="#667eea" />
          <path 
            d="M85,130 Q100,120 115,130" 
            fill="none" 
            stroke="#667eea" 
            stroke-width="2"
            class="sketch-line"
          />
        </svg>
      </div>
      
      <div class="error-text">
        <h1 class="gradient-text">页面未找到</h1>
        <p class="error-description">
          抱歉，您访问的页面不存在或已被移动。
        </p>
        <p class="error-suggestion">
          请检查 URL 是否正确，或返回首页继续浏览。
        </p>
      </div>
      
      <div class="error-actions">
        <el-button type="primary" size="large" @click="goHome">
          <el-icon><HomeFilled /></el-icon>
          返回首页
        </el-button>
        <el-button size="large" @click="goBack">
          <el-icon><ArrowLeft /></el-icon>
          返回上页
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { HomeFilled, ArrowLeft } from '@element-plus/icons-vue'

const router = useRouter()

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}
</script>

<style lang="scss" scoped>
.not-found {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, $primary-color 0%, $primary-light 100%);
  padding: $spacing-lg;
}

.not-found-content {
  text-align: center;
  max-width: 500px;
  
  .error-illustration {
    margin-bottom: $spacing-xl;
    
    svg {
      filter: drop-shadow(0 4px 20px rgba(102, 126, 234, 0.3));
    }
  }
  
  .error-text {
    margin-bottom: $spacing-xl;
    
    h1 {
      font-size: 3rem;
      margin-bottom: $spacing-lg;
    }
    
    .error-description {
      color: rgba(255, 255, 255, 0.9);
      font-size: $font-size-lg;
      margin-bottom: $spacing-md;
      line-height: 1.6;
    }
    
    .error-suggestion {
      color: rgba(255, 255, 255, 0.7);
      font-size: $font-size-md;
      margin: 0;
      line-height: 1.5;
    }
  }
  
  .error-actions {
    display: flex;
    gap: $spacing-md;
    justify-content: center;
    flex-wrap: wrap;
  }
}
</style>
