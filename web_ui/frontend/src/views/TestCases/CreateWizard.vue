<template>
  <div class="create-wizard">
    <div class="wizard-header">
      <h1 class="wizard-title gradient-text">
        <el-icon class="title-icon"><MagicStick /></el-icon>
        测试用例创建向导
      </h1>
      <p class="wizard-subtitle">简单几步，快速创建高质量的API测试用例</p>
    </div>
    
    <div class="wizard-content">
      <el-steps :active="currentStep" direction="horizontal" class="wizard-steps">
        <el-step title="选择类型" icon="el-icon-folder" />
        <el-step title="基础信息" icon="el-icon-document" />
        <el-step title="接口配置" icon="el-icon-setting" />
        <el-step title="断言设置" icon="el-icon-circle-check" />
        <el-step title="完成创建" icon="el-icon-success" />
      </el-steps>
      
      <div class="wizard-body">
        <!-- 步骤1: 选择类型 -->
        <div v-show="currentStep === 0" class="step-content">
          <div class="step-header">
            <h3>选择测试用例类型</h3>
            <p>请选择您要创建的测试用例类型</p>
          </div>
          
          <div class="case-types">
            <div
              v-for="type in caseTypes"
              :key="type.value"
              :class="['case-type-card', { active: wizardForm.type === type.value }]"
              @click="wizardForm.type = type.value"
            >
              <div class="type-icon">
                <el-icon><component :is="type.icon" /></el-icon>
              </div>
              <h4>{{ type.label }}</h4>
              <p>{{ type.description }}</p>
              <div class="type-features">
                <el-tag v-for="feature in type.features" :key="feature" size="small">
                  {{ feature }}
                </el-tag>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 步骤2: 基础信息 -->
        <div v-show="currentStep === 1" class="step-content">
          <div class="step-header">
            <h3>填写基础信息</h3>
            <p>设置测试用例的基本信息</p>
          </div>
          
          <el-form :model="wizardForm" label-width="120px" class="wizard-form">
            <el-form-item label="用例名称" required>
              <el-input
                v-model="wizardForm.name"
                placeholder="输入测试用例名称，如：登录接口测试"
                maxlength="50"
                show-word-limit
              />
            </el-form-item>
            
            <el-form-item label="所属模块">
              <el-select
                v-model="wizardForm.module"
                placeholder="选择模块"
                filterable
                allow-create
                style="width: 100%"
              >
                <el-option
                  v-for="module in availableModules"
                  :key="module"
                  :label="module"
                  :value="module"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="优先级">
              <el-radio-group v-model="wizardForm.priority">
                <el-radio value="high">高</el-radio>
                <el-radio value="medium">中</el-radio>
                <el-radio value="low">低</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="用例描述">
              <el-input
                v-model="wizardForm.description"
                type="textarea"
                :rows="3"
                placeholder="简要描述测试用例的目的和功能"
                maxlength="200"
                show-word-limit
              />
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 步骤3: 接口配置 -->
        <div v-show="currentStep === 2" class="step-content">
          <div class="step-header">
            <h3>配置接口信息</h3>
            <p>设置请求的详细信息</p>
          </div>
          
          <el-form :model="wizardForm.request" label-width="120px" class="wizard-form">
            <el-form-item label="请求方法" required>
              <el-select v-model="wizardForm.request.method" style="width: 150px">
                <el-option label="GET" value="GET" />
                <el-option label="POST" value="POST" />
                <el-option label="PUT" value="PUT" />
                <el-option label="DELETE" value="DELETE" />
                <el-option label="PATCH" value="PATCH" />
              </el-select>
            </el-form-item>
            
            <el-form-item label="请求URL" required>
              <el-input
                v-model="wizardForm.request.url"
                placeholder="/api/v1/login"
              />
            </el-form-item>
            
            <el-form-item label="请求头">
              <div class="headers-editor">
                <div
                  v-for="(header, index) in wizardForm.request.headers"
                  :key="index"
                  class="header-item"
                >
                  <el-input
                    v-model="header.key"
                    placeholder="Header名称"
                    style="width: 40%"
                  />
                  <el-input
                    v-model="header.value"
                    placeholder="Header值"
                    style="width: 40%"
                  />
                  <el-button
                    type="danger"
                    text
                    @click="removeHeader(index)"
                  >删除</el-button>
                </div>
                <el-button type="primary" text @click="addHeader">
                  <el-icon><Plus /></el-icon>
                  添加请求头
                </el-button>
              </div>
            </el-form-item>
            
            <el-form-item v-if="needsBody" label="请求参数">
              <el-tabs v-model="bodyType" class="body-tabs">
                <el-tab-pane label="JSON" name="json">
                  <el-input
                    v-model="wizardForm.request.data"
                    type="textarea"
                    :rows="8"
                    placeholder='{\n  "username": "admin",\n  "password": "123456"\n}'
                  />
                </el-tab-pane>
                <el-tab-pane label="表单" name="form">
                  <div class="form-editor">
                    <div
                      v-for="(param, index) in wizardForm.request.params"
                      :key="index"
                      class="param-item"
                    >
                      <el-input
                        v-model="param.key"
                        placeholder="参数名"
                        style="width: 40%"
                      />
                      <el-input
                        v-model="param.value"
                        placeholder="参数值"
                        style="width: 40%"
                      />
                      <el-button
                        type="danger"
                        text
                        @click="removeParam(index)"
                      >删除</el-button>
                    </div>
                    <el-button type="primary" text @click="addParam">
                      <el-icon><Plus /></el-icon>
                      添加参数
                    </el-button>
                  </div>
                </el-tab-pane>
              </el-tabs>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 步骤4: 断言设置 -->
        <div v-show="currentStep === 3" class="step-content">
          <div class="step-header">
            <h3>设置响应断言</h3>
            <p>定义接口响应的验证规则</p>
          </div>
          
          <div class="assertions-editor">
            <div
              v-for="(assertion, index) in wizardForm.validate"
              :key="index"
              class="assertion-item sketch-card"
            >
              <div class="assertion-header">
                <span class="assertion-title">断言 {{ index + 1 }}</span>
                <el-button
                  type="danger"
                  text
                  size="small"
                  @click="removeAssertion(index)"
                >删除</el-button>
              </div>
              
              <el-form :model="assertion" label-width="100px" size="small">
                <el-form-item label="响应字段">
                  <el-input
                    v-model="assertion.jsonpath"
                    placeholder="如：$.data.code 或 $.message"
                  />
                </el-form-item>
                
                <el-form-item label="比较方式">
                  <el-select v-model="assertion.type" style="width: 100%">
                    <el-option label="等于" value="==" />
                    <el-option label="不等于" value="!=" />
                    <el-option label="包含" value="contains" />
                    <el-option label="不包含" value="not_contains" />
                    <el-option label="大于" value=">" />
                    <el-option label="小于" value="<" />
                  </el-select>
                </el-form-item>
                
                <el-form-item label="预期值">
                  <el-input
                    v-model="assertion.value"
                    placeholder="输入预期的响应值"
                  />
                </el-form-item>
              </el-form>
            </div>
            
            <el-button type="primary" @click="addAssertion" class="add-assertion-btn">
              <el-icon><Plus /></el-icon>
              添加断言
            </el-button>
          </div>
        </div>
        
        <!-- 步骤5: 完成创建 -->
        <div v-show="currentStep === 4" class="step-content">
          <div class="completion-content">
            <div class="completion-icon">
              <el-icon><SuccessFilled /></el-icon>
            </div>
            <h3>用例创建完成！</h3>
            <p>您的测试用例已成功创建，可以选择下一步操作</p>
            
            <!-- 显示创建的用例信息 -->
            <div v-if="createdCaseInfo" class="case-info">
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="用例名称">
                  {{ wizardForm.name }}
                </el-descriptions-item>
                <el-descriptions-item label="所属模块">
                  {{ wizardForm.module || 'default' }}
                </el-descriptions-item>
                <el-descriptions-item label="文件路径">
                  {{ createdCaseInfo.file_path }}
                </el-descriptions-item>
                <el-descriptions-item label="请求方法">
                  <el-tag :type="wizardForm.request.method === 'GET' ? 'success' : 'primary'">
                    {{ wizardForm.request.method }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="请求地址">
                  {{ wizardForm.request.url }}
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <div class="completion-actions">
              <el-button type="primary" @click="runTest">
                <el-icon><VideoPlay /></el-icon>
                立即执行测试
              </el-button>
              <el-button @click="editCase">
                <el-icon><Edit /></el-icon>
                编辑用例
              </el-button>
              <el-button @click="createAnother">
                <el-icon><DocumentAdd /></el-icon>
                创建新用例
              </el-button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="wizard-footer">
        <div class="footer-left">
          <el-button v-if="currentStep > 0" @click="prevStep">
            <el-icon><ArrowLeft /></el-icon>
            上一步
          </el-button>
        </div>
        
        <div class="footer-right">
          <el-button v-if="currentStep < 4" type="primary" @click="nextStep">
            下一步
            <el-icon><ArrowRight /></el-icon>
          </el-button>
          <el-button
            v-if="currentStep === 3"
            type="success"
            @click="createCase"
            :loading="creating"
          >
            <el-icon><Check /></el-icon>
            创建用例
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'
import { apiService } from '@/services/api'
import {
  MagicStick, Plus, ArrowLeft, ArrowRight, Check, SuccessFilled,
  VideoPlay, Edit, DocumentAdd, Monitor, DataLine, Connection, Tools
} from '@element-plus/icons-vue'

const router = useRouter()

// 响应式数据
const currentStep = ref(0)
const creating = ref(false)
const bodyType = ref('json')
const createdCaseInfo = ref(null) // 存储创建成功的用例信息

// 用例类型配置
const caseTypes = ref([
  {
    value: 'api',
    label: 'API接口测试',
    description: '测试RESTful API接口的功能和性能',
    icon: Connection,
    features: ['响应验证', '性能监控', '数据依赖']
  },
  {
    value: 'workflow',
    label: '业务流程测试', 
    description: '测试多个接口组成的完整业务流程',
    icon: DataLine,
    features: ['流程编排', '数据传递', '异常处理']
  },
  {
    value: 'performance',
    label: '性能压测',
    description: '测试接口在高并发下的性能表现',
    icon: Monitor,
    features: ['并发测试', '性能分析', '负载均衡']
  },
  {
    value: 'integration',
    label: '集成测试',
    description: '测试系统间的集成和数据交互',
    icon: Tools,
    features: ['系统集成', '数据同步', '兼容性测试']
  }
])

// 可用模块 - 动态获取
const availableModules = ref([])

// 获取可用模块列表
const loadAvailableModules = async () => {
  try {
    // 从用例管理API获取实际模块列表
    const response = await apiService.getTestCases()
    const testCases = response.data || []
    
    // 提取唯一模块名
    const moduleSet = new Set()
    testCases.forEach(item => {
      if (item && item.module) {
        moduleSet.add(item.module)
      }
    })
    
    // 添加常用模块作为默认选项
    const defaultModules = ['Login', 'User', 'Order', 'Payment', 'Product', 'Category']
    defaultModules.forEach(module => moduleSet.add(module))
    
    availableModules.value = Array.from(moduleSet).sort()
    console.log('加载可用模块:', availableModules.value)
    
  } catch (error) {
    console.error('加载模块列表失败:', error)
    // 降级使用默认模块
    availableModules.value = ['Login', 'User', 'Order', 'Payment', 'Product', 'Category']
  }
}

// 向导表单数据
const wizardForm = ref({
  type: 'api',
  name: '',
  module: '',
  priority: 'medium',
  description: '',
  request: {
    method: 'POST',
    url: '',
    headers: [
      { key: 'Content-Type', value: 'application/json' }
    ],
    data: '',
    params: []
  },
  validate: []
})

// 计算属性
const needsBody = computed(() => {
  return ['POST', 'PUT', 'PATCH'].includes(wizardForm.value.request.method)
})

// 方法
const nextStep = () => {
  if (validateCurrentStep()) {
    currentStep.value++
  }
}

const prevStep = () => {
  currentStep.value--
}

const validateCurrentStep = () => {
  switch (currentStep.value) {
    case 0:
      if (!wizardForm.value.type) {
        ElMessage.warning('请选择测试用例类型')
        return false
      }
      break
    case 1:
      if (!wizardForm.value.name.trim()) {
        ElMessage.warning('请输入用例名称')
        return false
      }
      break
    case 2:
      if (!wizardForm.value.request.url.trim()) {
        ElMessage.warning('请输入请求URL')
        return false
      }
      break
  }
  return true
}

// 请求头管理
const addHeader = () => {
  wizardForm.value.request.headers.push({ key: '', value: '' })
}

const removeHeader = (index) => {
  wizardForm.value.request.headers.splice(index, 1)
}

// 参数管理
const addParam = () => {
  wizardForm.value.request.params.push({ key: '', value: '' })
}

const removeParam = (index) => {
  wizardForm.value.request.params.splice(index, 1)
}

// 断言管理
const addAssertion = () => {
  wizardForm.value.validate.push({
    jsonpath: '',
    type: '==',
    value: ''
  })
}

const removeAssertion = (index) => {
  wizardForm.value.validate.splice(index, 1)
}

// 创建用例
const createCase = async () => {
  try {
    creating.value = true
    
    // 构建YAML格式的测试用例
    const testCase = buildTestCase()
    
    // 调用API创建测试用例
    const response = await apiService.createTestCaseFile({
      module: wizardForm.value.module || 'default',
      case_name: wizardForm.value.name,
      case_data: testCase
    })
    
    // 保存创建的用例信息
    createdCaseInfo.value = response.data || {
      file_path: `${wizardForm.value.module || 'default'}/${wizardForm.value.name}.yaml`,
      name: wizardForm.value.name
    }
    
    ElMessage.success('测试用例创建成功！')
    
    // 更新模块列表，确保新模块出现在下拉框中
    await loadAvailableModules()
    
    currentStep.value = 4
  } catch (error) {
    console.error('创建用例失败:', error)
    ElMessage.error(error.message || '创建失败，请重试')
  } finally {
    creating.value = false
  }
}

const buildTestCase = () => {
  // 构建测试用例数据结构，符合项目YAML格式
  const testCase = {
    [wizardForm.value.name]: {
      name: wizardForm.value.name,
      base_url: '${base_url}',
      request: {
        url: wizardForm.value.request.url,
        method: wizardForm.value.request.method,
        headers: {}
      }
    }
  }
  
  // 添加请求头
  wizardForm.value.request.headers.forEach(header => {
    if (header.key && header.value) {
      testCase[wizardForm.value.name].request.headers[header.key] = header.value
    }
  })
  
  // 添加请求体数据
  if (needsBody.value) {
    if (wizardForm.value.request.data) {
      try {
        testCase[wizardForm.value.name].request.json = JSON.parse(wizardForm.value.request.data)
      } catch {
        testCase[wizardForm.value.name].request.data = wizardForm.value.request.data
      }
    } else if (wizardForm.value.request.params.length > 0) {
      const data = {}
      wizardForm.value.request.params.forEach(param => {
        if (param.key && param.value) {
          data[param.key] = param.value
        }
      })
      testCase[wizardForm.value.name].request.data = data
    }
  }
  
  // 添加断言
  if (wizardForm.value.validate.length > 0) {
    testCase[wizardForm.value.name].validate = wizardForm.value.validate.map(assertion => ({
      jsonpath: assertion.jsonpath,
      type: assertion.type,
      value: assertion.value
    }))
  }
  
  return testCase
}

// 完成后的操作
const runTest = () => {
  ElMessage.success('正在跳转到执行中心...')
  // 跳转到执行页面
  router.push('/execution')
}

const editCase = () => {
  if (createdCaseInfo.value) {
    ElMessage.success('正在跳转到编辑页面...')
    // 跳转到编辑页面，使用Base64编码传入用例文件路径
    const encodedPath = btoa(unescape(encodeURIComponent(createdCaseInfo.value.file_path)))
    router.push(`/test-cases/editor/${encodedPath}`)
  } else {
    ElMessage.warning('无法获取用例路径，请从用例管理页面打开编辑器')
    router.push('/test-cases')
  }
}

const createAnother = async () => {
  try {
    // 重置表单，创建新用例
    currentStep.value = 0
    createdCaseInfo.value = null
    wizardForm.value = {
      type: 'api',
      name: '',
      module: '',
      priority: 'medium',
      description: '',
      request: {
        method: 'POST',
        url: '',
        headers: [{ key: 'Content-Type', value: 'application/json' }],
        data: '',
        params: []
      },
      validate: []
    }
    
    // 重新加载模块列表，确保最新数据
    await loadAvailableModules()
    
    ElMessage.success('已重置表单，可以创建新用例')
  } catch (error) {
    console.error('重置表单失败:', error)
    ElMessage.warning('表单已重置，但模块列表更新失败')
  }
}

// 生命周期
onMounted(() => {
  // 初始化时加载可用模块
  loadAvailableModules()
})
</script>

<style lang="scss" scoped>
.create-wizard {
  padding: $spacing-lg;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

.wizard-header {
  text-align: center;
  margin-bottom: $spacing-xl;
  
  .wizard-title {
    font-size: $font-size-xxl;
    margin-bottom: $spacing-xs;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: $spacing-sm;
    
    .title-icon {
      font-size: 32px;
    }
  }
  
  .wizard-subtitle {
    color: rgba(255, 255, 255, 0.9);
    font-size: $font-size-lg;
    margin: 0;
  }
}

.wizard-content {
  flex: 1;
  background: $bg-primary;
  border-radius: $sketch-radius-lg;
  padding: $spacing-xl;
  box-shadow: $sketch-shadow-lg;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.wizard-steps {
  margin-bottom: $spacing-xl;
  
  :deep(.el-step__title) {
    font-size: $font-size-md;
    font-weight: 600;
  }
}

.wizard-body {
  flex: 1;
  overflow-y: auto;
}

.step-content {
  .step-header {
    text-align: center;
    margin-bottom: $spacing-xl;
    
    h3 {
      color: $text-primary;
      font-size: $font-size-xl;
      margin-bottom: $spacing-xs;
    }
    
    p {
      color: $text-secondary;
      margin: 0;
    }
  }
}

// 用例类型选择
.case-types {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: $spacing-lg;
  
  .case-type-card {
    padding: $spacing-lg;
    border: 2px solid $border-light;
    border-radius: $sketch-radius-lg;
    text-align: center;
    cursor: pointer;
    transition: all $transition-fast;
    background: $bg-secondary;
    
    &:hover {
      border-color: $primary-color;
      box-shadow: $sketch-shadow-md;
    }
    
    &.active {
      border-color: $primary-color;
      background: rgba($primary-color, 0.1);
      box-shadow: $sketch-shadow-md;
    }
    
    .type-icon {
      font-size: 48px;
      color: $primary-color;
      margin-bottom: $spacing-md;
    }
    
    h4 {
      color: $text-primary;
      margin-bottom: $spacing-sm;
    }
    
    p {
      color: $text-secondary;
      margin-bottom: $spacing-md;
      font-size: $font-size-sm;
    }
    
    .type-features {
      display: flex;
      flex-wrap: wrap;
      gap: $spacing-xs;
      justify-content: center;
    }
  }
}

// 表单样式
.wizard-form {
  max-width: 600px;
  margin: 0 auto;
}

.headers-editor, .form-editor {
  .header-item, .param-item {
    display: flex;
    gap: $spacing-sm;
    align-items: center;
    margin-bottom: $spacing-sm;
  }
}

// 断言编辑器
.assertions-editor {
  .assertion-item {
    padding: $spacing-lg;
    margin-bottom: $spacing-md;
    
    .assertion-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: $spacing-md;
      
      .assertion-title {
        font-weight: 600;
        color: $text-primary;
      }
    }
  }
  
  .add-assertion-btn {
    width: 100%;
    height: 60px;
    border-style: dashed;
  }
}

// 完成页面
.completion-content {
  text-align: center;
  padding: $spacing-xxl;
  
  .completion-icon {
    font-size: 80px;
    color: $success-color;
    margin-bottom: $spacing-lg;
  }
  
  h3 {
    color: $text-primary;
    margin-bottom: $spacing-md;
  }
  
  p {
    color: $text-secondary;
    margin-bottom: $spacing-xl;
  }
  
  .case-info {
    max-width: 600px;
    margin: 0 auto $spacing-xl auto;
    text-align: left;
    
    :deep(.el-descriptions) {
      background: $bg-secondary;
      border-radius: $sketch-radius;
    }
    
    :deep(.el-descriptions__label) {
      font-weight: 600;
      color: $text-primary;
    }
    
    :deep(.el-descriptions__content) {
      color: $text-secondary;
    }
  }
  
  .completion-actions {
    display: flex;
    gap: $spacing-md;
    justify-content: center;
    flex-wrap: wrap;
  }
}

// 底部导航
.wizard-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: $spacing-xl;
  padding-top: $spacing-lg;
  border-top: 1px solid $border-light;
  
  .footer-left, .footer-right {
    display: flex;
    gap: $spacing-sm;
  }
}

.body-tabs {
  width: 100%;
  
  :deep(.el-tabs__content) {
    padding-top: $spacing-md;
  }
}
</style> 