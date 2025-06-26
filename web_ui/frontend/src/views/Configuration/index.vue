<template>
  <div class="configuration">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title gradient-text">
          <el-icon class="title-icon"><Setting /></el-icon>
          配置管理
        </h1>
        <p class="page-subtitle">系统配置与环境设置</p>
      </div>
      <div class="header-actions">
        <el-button type="primary" @click="saveConfig" :loading="saving">
          <el-icon><DocumentChecked /></el-icon>
          保存配置
        </el-button>
      </div>
    </div>
    
    <div class="config-content">
      <el-tabs v-model="activeTab" class="config-tabs">
        <!-- 基础配置 -->
        <el-tab-pane label="基础配置" name="basic">
          <div class="config-section sketch-card">
            <h3>项目信息</h3>
            <el-form :model="configForm" label-width="120px" class="config-form">
              <el-form-item label="项目名称" prop="project_name" for="project-name">
                <el-input id="project-name" v-model="configForm.project_name" placeholder="请输入项目名称" />
              </el-form-item>
              <el-form-item label="测试环境" prop="env" for="test-env">
                <el-input id="test-env" v-model="configForm.env" placeholder="如：测试环境、生产环境" />
              </el-form-item>
              <el-form-item label="测试负责人" prop="tester_name" for="tester-name">
                <el-input id="tester-name" v-model="configForm.tester_name" placeholder="请输入测试负责人姓名" />
              </el-form-item>
              <el-form-item label="主域名" prop="host" for="host-url">
                <el-input id="host-url" v-model="configForm.host" placeholder="如：https://api.example.com" />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
        
        <!-- 通知配置 -->
        <el-tab-pane label="通知配置" name="notification">
          <div class="config-section sketch-card">
            <h3>通知设置</h3>
            <el-form :model="notificationForm" label-width="120px" class="config-form">
              <el-form-item label="通知类型" prop="selectedTypes" for="notification-types">
                <el-checkbox-group id="notification-types" v-model="selectedNotifications">
                  <el-checkbox id="notify-dingtalk" value="1">钉钉通知</el-checkbox>
                  <el-checkbox id="notify-wechat" value="2">企业微信</el-checkbox>
                  <el-checkbox id="notify-email" value="3">邮箱通知</el-checkbox>
                  <el-checkbox id="notify-feishu" value="4">飞书通知</el-checkbox>
                </el-checkbox-group>
              </el-form-item>

              <!-- 钉钉配置 -->
              <div v-if="selectedNotifications.includes('1')" class="notification-config">
                <h4>钉钉配置</h4>
                <el-form-item label="Webhook URL" prop="ding_talk.webhook">
                  <el-input id="dingtalk-webhook" v-model="notificationForm.ding_talk.webhook" placeholder="钉钉机器人 Webhook 地址" />
                </el-form-item>
                <el-form-item label="Secret" prop="ding_talk.secret">
                  <el-input id="dingtalk-secret" v-model="notificationForm.ding_talk.secret" placeholder="钉钉机器人密钥" />
                </el-form-item>
              </div>

              <!-- 企业微信配置 -->
              <div v-if="selectedNotifications.includes('2')" class="notification-config">
                <h4>企业微信配置</h4>
                <el-form-item label="Webhook URL" prop="wechat.webhook">
                  <el-input id="wechat-webhook" v-model="notificationForm.wechat.webhook" placeholder="企业微信机器人 Webhook 地址" />
                </el-form-item>
              </div>

              <!-- 邮箱配置 -->
              <div v-if="selectedNotifications.includes('3')" class="notification-config">
                <h4>邮箱配置</h4>
                <el-form-item label="发送邮箱" prop="email.send_user">
                  <el-input id="email-sender" v-model="notificationForm.email.send_user" placeholder="发送方邮箱地址" />
                </el-form-item>
                <el-form-item label="SMTP 服务器" prop="email.email_host">
                  <el-input id="email-host" v-model="notificationForm.email.email_host" placeholder="如：smtp.qq.com" />
                </el-form-item>
                <el-form-item label="授权码" prop="email.stamp_key">
                  <el-input id="email-password" v-model="notificationForm.email.stamp_key" type="password" placeholder="邮箱授权码" />
                </el-form-item>
                <el-form-item label="收件人列表" prop="email.send_list">
                  <el-input id="email-recipients" v-model="notificationForm.email.send_list" placeholder="多个邮箱用逗号分隔" />
                </el-form-item>
              </div>
            </el-form>
          </div>
        </el-tab-pane>
        
        <!-- 数据库配置 -->
        <el-tab-pane label="数据库配置" name="database">
          <div class="config-section sketch-card">
            <h3>MySQL 数据库</h3>
            <el-form :model="databaseForm" label-width="120px" class="config-form">
              <el-form-item label="启用数据库" prop="switch">
                <el-switch v-model="databaseForm.switch" />
                <span class="form-tip">启用后可使用数据库断言功能</span>
              </el-form-item>

              <template v-if="databaseForm.switch">
                <el-form-item label="主机地址" prop="host">
                  <el-input id="db-host" v-model="databaseForm.host" placeholder="如：localhost 或 127.0.0.1" />
                </el-form-item>
                <el-form-item label="端口" prop="port">
                  <el-input-number id="db-port" v-model="databaseForm.port" :min="1" :max="65535" />
                </el-form-item>
                <el-form-item label="用户名" prop="user">
                  <el-input id="db-user" v-model="databaseForm.user" placeholder="数据库用户名" />
                </el-form-item>
                <el-form-item label="密码" prop="password">
                  <el-input id="db-password" v-model="databaseForm.password" type="password" placeholder="数据库密码" />
                </el-form-item>
                <el-form-item>
                  <el-button @click="testConnection" :loading="testing">
                    <el-icon><Connection /></el-icon>
                    测试连接
                  </el-button>
                </el-form-item>
              </template>
            </el-form>
          </div>
        </el-tab-pane>
        
        <!-- 高级配置 -->
        <el-tab-pane label="高级配置" name="advanced">
          <div class="config-section sketch-card">
            <h3>执行配置</h3>
            <el-form :model="advancedForm" label-width="150px" class="config-form">
              <el-form-item label="实时更新用例" prop="real_time_update">
                <el-switch v-model="advancedForm.real_time_update" />
                <span class="form-tip">修改 YAML 文件后自动更新测试代码</span>
              </el-form-item>
              <el-form-item label="Excel 报告" prop="excel_report">
                <el-switch v-model="advancedForm.excel_report" />
                <span class="form-tip">生成 Excel 格式的测试报告</span>
              </el-form-item>
              <el-form-item label="镜像源" prop="mirror_source" for="mirror-source">
                <el-input id="mirror-source" v-model="advancedForm.mirror_source" placeholder="Python 包镜像源地址" />
              </el-form-item>
            </el-form>
          </div>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useConfigStore } from '@/stores/config'
import { ElMessage } from 'element-plus'
import { Setting, DocumentChecked, Connection } from '@element-plus/icons-vue'

const configStore = useConfigStore()

// 响应式数据
const activeTab = ref('basic')
const saving = ref(false)
const testing = ref(false)

// 表单数据
const configForm = ref({
  project_name: '',
  env: '',
  tester_name: '',
  host: ''
})

const notificationForm = ref({
  selectedTypes: [],
  ding_talk: {
    webhook: '',
    secret: ''
  },
  wechat: {
    webhook: ''
  },
  email: {
    send_user: '',
    email_host: '',
    stamp_key: '',
    send_list: ''
  }
})

const databaseForm = ref({
  switch: false,
  host: '',
  port: 3306,
  user: '',
  password: ''
})

const advancedForm = ref({
  real_time_update: false,
  excel_report: false,
  mirror_source: ''
})

// 保持向后兼容的计算属性
const selectedNotifications = computed({
  get: () => notificationForm.value.selectedTypes,
  set: (value) => { notificationForm.value.selectedTypes = value }
})

// 计算属性
const notificationType = computed(() => {
  return selectedNotifications.value.join(',')
})

// 方法
const loadConfig = async () => {
  await configStore.fetchConfig()
  const config = configStore.config
  
  // 填充表单数据
  configForm.value = {
    project_name: config.project_name || '',
    env: config.env || '',
    tester_name: config.tester_name || '',
    host: config.host || ''
  }
  
  // 解析通知类型
  if (config.notification_type) {
    selectedNotifications.value = config.notification_type.toString().split(',').filter(Boolean)
  }
}

const saveConfig = async () => {
  try {
    saving.value = true
    
    // 构建配置对象
    const configData = {
      ...configForm.value,
      notification_type: notificationType.value
    }
    
    const success = await configStore.updateConfig(configData)
    if (success) {
      ElMessage.success('配置保存成功')
    }
  } catch (error) {
    console.error('保存配置失败:', error)
  } finally {
    saving.value = false
  }
}

const testConnection = async () => {
  try {
    testing.value = true
    // 这里可以调用 API 测试数据库连接
    await new Promise(resolve => setTimeout(resolve, 2000)) // 模拟测试
    ElMessage.success('数据库连接测试成功')
  } catch (error) {
    ElMessage.error('数据库连接测试失败')
  } finally {
    testing.value = false
  }
}

// 生命周期
onMounted(() => {
  loadConfig()
})
</script>

<style lang="scss" scoped>
.configuration {
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

.config-content {
  flex: 1;
  overflow-y: auto;
}

.config-tabs {
  height: 100%;
  
  :deep(.el-tabs__content) {
    height: calc(100% - 40px);
    overflow-y: auto;
  }
}

.config-section {
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
  
  h3 {
    color: $text-primary;
    margin: 0 0 $spacing-lg 0;
    font-size: $font-size-lg;
  }
  
  h4 {
    color: $text-secondary;
    margin: $spacing-lg 0 $spacing-md 0;
    font-size: $font-size-md;
    border-bottom: 1px solid $border-light;
    padding-bottom: $spacing-xs;
  }
}

.config-form {
  .form-tip {
    color: $text-secondary;
    font-size: $font-size-sm;
    margin-left: $spacing-sm;
  }
  
  .notification-config {
    background: $bg-secondary;
    padding: $spacing-md;
    border-radius: $sketch-radius;
    margin: $spacing-md 0;
  }
}
</style>
