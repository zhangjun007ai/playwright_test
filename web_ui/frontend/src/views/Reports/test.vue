<template>
  <div class="reports-test">
    <div class="page-header">
      <h1 class="page-title gradient-text">
        <el-icon class="title-icon"><PieChart /></el-icon>
        报告中心测试
      </h1>
      <p class="page-subtitle">测试页面是否正常显示</p>
    </div>
    
    <div class="test-content">
      <div class="test-card sketch-card">
        <h3>基础测试</h3>
        <p>如果您能看到这个页面，说明基础组件正常工作。</p>
        
        <div class="test-buttons">
          <el-button type="primary" @click="testClick">
            <el-icon><Check /></el-icon>
            测试按钮
          </el-button>
          <el-button @click="showMessage">
            显示消息
          </el-button>
        </div>
      </div>
      
      <div class="test-card sketch-card">
        <h3>数据测试</h3>
        <p>计数器: {{ counter }}</p>
        <el-button @click="increment">增加</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const counter = ref(0)

const testClick = () => {
  ElMessage.success('测试按钮点击成功！')
}

const showMessage = () => {
  ElMessage.info('这是一条测试消息')
}

const increment = () => {
  counter.value++
}
</script>

<style lang="scss" scoped>
@import "@/styles/variables.scss";

.reports-test {
  padding: $spacing-lg;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
  margin-bottom: $spacing-xl;
  
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

.test-content {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: $spacing-lg;
}

.test-card {
  padding: $spacing-lg;
  
  h3 {
    color: $text-primary;
    margin: 0 0 $spacing-md 0;
  }
  
  p {
    color: $text-secondary;
    margin-bottom: $spacing-md;
  }
  
  .test-buttons {
    display: flex;
    gap: $spacing-sm;
    flex-wrap: wrap;
  }
}
</style>
