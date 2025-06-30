<template>
  <div class="case-editor">
    <div class="editor-header">
      <div class="header-left">
        <el-button @click="goBack" link class="back-button">
          <el-icon><ArrowLeft /></el-icon>
          返回
        </el-button>
        <div class="file-info">
          <h1 class="file-title">{{ fileName }}</h1>
          <p class="file-path">{{ filePath }}</p>
        </div>
      </div>
      <div class="header-actions">
        <el-button @click="generateCode" :loading="generating" type="success">
          <el-icon><MagicStick /></el-icon>
          生成代码
        </el-button>
        <el-button @click="formatCode" :disabled="!hasContent">
          <el-icon><DocumentCopy /></el-icon>
          格式化
        </el-button>
        <el-button @click="validateYaml" :disabled="!hasContent">
          <el-icon><CircleCheck /></el-icon>
          验证
        </el-button>
        <el-button type="primary" @click="saveFile" :loading="saving" :disabled="!hasChanges">
          <el-icon><DocumentChecked /></el-icon>
          保存
        </el-button>
      </div>
    </div>
    
    <div class="editor-content">
      <!-- 左侧编辑器 -->
      <div class="editor-panel">
        <div class="panel-header">
          <h3>YAML 编辑器</h3>
          <div class="editor-tools">
            <el-tooltip content="结构助手">
              <el-button size="small" link @click="showStructureHelper = !showStructureHelper">
                <el-icon><Guide /></el-icon>
              </el-button>
            </el-tooltip>
            <el-tooltip content="全屏编辑">
              <el-button size="small" link @click="toggleFullscreen">
                <el-icon><FullScreen /></el-icon>
              </el-button>
            </el-tooltip>
          </div>
        </div>
        <div class="editor-container" ref="editorContainer">
          <codemirror
            v-model="content"
            :style="{ height: editorHeight }"
            :extensions="extensions"
            @update="handleContentChange"
            @ready="handleEditorReady"
          />
        </div>
      </div>
      
      <!-- 右侧面板 -->
      <div class="right-panel" v-if="!isFullscreen">
        <el-tabs v-model="activeRightTab" class="right-tabs" type="border-card">
          <!-- 用例预览 -->
          <el-tab-pane label="用例预览" name="preview">
            <div class="preview-section">
              <div class="section-header">
                <h3>用例预览</h3>
                <el-button size="small" @click="refreshPreview">
                  <el-icon><Refresh /></el-icon>
                </el-button>
              </div>
              <div class="preview-content">
                <div v-loading="parsing" element-loading-text="解析中...">
                  <div v-if="parsedData" class="case-preview">
                    <!-- 公共信息 -->
                    <div v-if="parsedData.case_common" class="common-info">
                      <h4>公共配置</h4>
                      <el-descriptions :column="1" size="small" border>
                        <el-descriptions-item label="Epic">
                          {{ parsedData.case_common.allureEpic }}
                        </el-descriptions-item>
                        <el-descriptions-item label="Feature">
                          {{ parsedData.case_common.allureFeature }}
                        </el-descriptions-item>
                        <el-descriptions-item label="Story">
                          {{ parsedData.case_common.allureStory }}
                        </el-descriptions-item>
                      </el-descriptions>
                    </div>
                    
                    <!-- 测试用例列表 -->
                    <div class="cases-list">
                      <h4>测试用例 ({{ caseCount }})</h4>
                      <div
                        v-for="(caseData, caseId) in testCases"
                        :key="caseId"
                        class="case-item"
                      >
                        <div class="case-header">
                          <span class="case-id">{{ caseId }}</span>
                          <el-tag
                            :type="getMethodType(caseData.method)"
                            size="small"
                          >
                            {{ caseData.method }}
                          </el-tag>
                          <el-tag v-if="caseData.dependence_case" type="warning" size="small">
                            依赖
                          </el-tag>
                        </div>
                        <div class="case-detail">{{ caseData.detail }}</div>
                        <div class="case-url">{{ caseData.url }}</div>
                        <div v-if="caseData.assert" class="case-assertions">
                          <el-tag v-for="(assert, key) in caseData.assert" :key="key" size="small" class="assertion-tag">
                            {{ key }}
                          </el-tag>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div v-else-if="parseError" class="parse-error">
                    <el-alert
                      title="YAML 解析错误"
                      :description="parseError"
                      type="error"
                      show-icon
                      :closable="false"
                    />
                  </div>
                  
                  <div v-else class="empty-preview">
                    <el-empty description="暂无内容" />
                  </div>
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 结构助手 -->
          <el-tab-pane label="结构助手" name="structure">
            <div class="structure-helper">
              <div class="helper-section">
                <h4>快速插入</h4>
                <div class="helper-buttons">
                  <el-button-group size="small">
                    <el-button @click="insertTemplate('common')">公共配置</el-button>
                    <el-button @click="insertTemplate('get')">GET请求</el-button>
                    <el-button @click="insertTemplate('post')">POST请求</el-button>
                  </el-button-group>
                </div>
                <div class="helper-buttons">
                  <el-button-group size="small">
                    <el-button @click="insertTemplate('put')">PUT请求</el-button>
                    <el-button @click="insertTemplate('delete')">DELETE请求</el-button>
                    <el-button @click="insertTemplate('patch')">PATCH请求</el-button>
                  </el-button-group>
                </div>
                <div class="helper-buttons">
                  <el-button-group size="small">
                    <el-button @click="insertTemplate('dependency')">添加依赖</el-button>
                    <el-button @click="insertTemplate('assert')">添加断言</el-button>
                    <el-button @click="insertTemplate('sql')">SQL断言</el-button>
                  </el-button-group>
                </div>
                <div class="helper-buttons">
                  <el-button-group size="small">
                    <el-button @click="insertTemplate('complex_assert')">复杂断言</el-button>
                    <el-button @click="insertTemplate('data_extract')">数据提取</el-button>
                    <el-button @click="insertTemplate('complete_case')">完整用例</el-button>
                  </el-button-group>
                </div>
              </div>

              <div class="helper-section">
                <h4>智能提示</h4>
                <div class="smart-hints">
                  <el-alert
                    title="YAML编写提示"
                    type="info"
                    :closable="false"
                    show-icon
                  >
                    <template #default>
                      <ul class="hint-list">
                        <li>• 使用2个空格进行缩进，不要使用Tab</li>
                        <li>• 字符串值包含特殊字符时需要用引号包围</li>
                        <li>• 使用 ${{host()}} 引用全局配置的host地址</li>
                        <li>• JSONPath语法: $.data.code 获取响应中的code字段</li>
                        <li>• 依赖用例的数据缓存: $json(cache_name)$ 引用</li>
                      </ul>
                    </template>
                  </el-alert>
                </div>
              </div>

              <div class="helper-section">
                <h4>常用片段</h4>
                <div class="snippet-list">
                  <el-collapse accordion>
                    <el-collapse-item title="请求头配置" name="headers">
                      <div class="snippet-item">
                        <el-button size="small" @click="insertSnippet('auth_header')">Authorization</el-button>
                        <el-button size="small" @click="insertSnippet('content_json')">Content-Type JSON</el-button>
                        <el-button size="small" @click="insertSnippet('content_form')">Content-Type Form</el-button>
                      </div>
                    </el-collapse-item>
                    <el-collapse-item title="断言类型" name="assertions">
                      <div class="snippet-item">
                        <el-button size="small" @click="insertSnippet('status_assert')">状态码断言</el-button>
                        <el-button size="small" @click="insertSnippet('response_time')">响应时间断言</el-button>
                        <el-button size="small" @click="insertSnippet('json_schema')">JSON结构断言</el-button>
                      </div>
                    </el-collapse-item>
                    <el-collapse-item title="数据类型" name="data_types">
                      <div class="snippet-item">
                        <el-button size="small" @click="insertSnippet('login_data')">登录参数</el-button>
                        <el-button size="small" @click="insertSnippet('pagination_data')">分页参数</el-button>
                        <el-button size="small" @click="insertSnippet('upload_data')">文件上传</el-button>
                      </div>
                    </el-collapse-item>
                  </el-collapse>
                </div>
              </div>

              <div class="helper-section">
                <h4>用例结构</h4>
                <div class="structure-tree">
                  <el-tree
                    :data="yamlStructure"
                    :props="{ children: 'children', label: 'label' }"
                    @node-click="handleStructureClick"
                    class="yaml-tree"
                  />
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 依赖配置 -->
          <el-tab-pane label="依赖配置" name="dependency">
            <div class="dependency-config">
              <div class="config-header">
                <h4>业务依赖配置</h4>
                <el-button size="small" type="primary" @click="addDependency">
                  <el-icon><Plus /></el-icon>
                  添加依赖
                </el-button>
              </div>
              
              <div class="dependency-list">
                <div
                  v-for="(dep, index) in dependencies"
                  :key="index"
                  class="dependency-item"
                >
                  <el-card class="dep-card">
                    <div class="dep-header">
                      <span>依赖 {{ index + 1 }}</span>
                      <el-button size="small" type="danger" link @click="removeDependency(index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                    <el-form :model="dep" label-width="80px" size="small">
                      <el-form-item label="用例ID">
                        <el-input v-model="dep.case_id" placeholder="依赖的用例ID" />
                      </el-form-item>
                      <el-form-item label="数据类型">
                        <el-select v-model="dep.type" placeholder="选择数据类型">
                          <el-option label="响应数据" value="response" />
                          <el-option label="请求数据" value="request" />
                          <el-option label="SQL数据" value="sqlData" />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="JsonPath">
                        <el-input v-model="dep.jsonpath" placeholder="$.data.id" />
                      </el-form-item>
                      <el-form-item label="缓存名">
                        <el-input v-model="dep.cache_name" placeholder="自定义缓存名称" />
                      </el-form-item>
                    </el-form>
                  </el-card>
                </div>
                
                <div v-if="dependencies.length === 0" class="empty-deps">
                  <el-empty description="暂无依赖配置" />
                </div>
              </div>
            </div>
          </el-tab-pane>

          <!-- 断言配置 -->
          <el-tab-pane label="断言配置" name="assertion">
            <div class="assertion-config">
              <div class="config-header">
                <h4>断言配置</h4>
                <el-button size="small" type="primary" @click="addAssertion">
                  <el-icon><Plus /></el-icon>
                  添加断言
                </el-button>
              </div>
              
              <div class="assertion-list">
                <div
                  v-for="(assertion, index) in assertions"
                  :key="index"
                  class="assertion-item"
                >
                  <el-card class="assertion-card">
                    <div class="assertion-header">
                      <span>断言 {{ index + 1 }}</span>
                      <el-button size="small" type="danger" link @click="removeAssertion(index)">
                        <el-icon><Delete /></el-icon>
                      </el-button>
                    </div>
                    <el-form :model="assertion" label-width="80px" size="small">
                      <el-form-item label="字段名">
                        <el-input v-model="assertion.field" placeholder="断言字段名称" />
                      </el-form-item>
                      <el-form-item label="JsonPath">
                        <el-input v-model="assertion.jsonpath" placeholder="$.code" />
                      </el-form-item>
                      <el-form-item label="断言类型">
                        <el-select v-model="assertion.type" placeholder="选择断言类型">
                          <el-option label="等于 (==)" value="==" />
                          <el-option label="不等于 (!=)" value="!=" />
                          <el-option label="包含 (contains)" value="contains" />
                          <el-option label="大于 (>)" value=">" />
                          <el-option label="小于 (<)" value="<" />
                        </el-select>
                      </el-form-item>
                      <el-form-item label="期望值">
                        <el-input v-model="assertion.value" placeholder="期望的值" />
                      </el-form-item>
                      <el-form-item label="断言方式">
                        <el-select v-model="assertion.assertType">
                          <el-option label="接口响应" value="" />
                          <el-option label="SQL断言" value="SQL" />
                        </el-select>
                      </el-form-item>
                    </el-form>
                  </el-card>
                </div>
                
                <div v-if="assertions.length === 0" class="empty-assertions">
                  <el-empty description="暂无断言配置" />
                </div>
              </div>
            </div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>

    <!-- 代码生成进度对话框 -->
    <el-dialog
      v-model="showGenerateDialog"
      title="代码生成"
      width="500px"
      center
      :close-on-click-modal="false"
    >
      <div class="generate-content">
        <div class="generate-status">
          <el-steps :active="generateStep" finish-status="success">
            <el-step title="解析YAML" />
            <el-step title="生成代码" />
            <el-step title="写入文件" />
            <el-step title="完成" />
          </el-steps>
        </div>
        <div class="generate-message">
          <p>{{ generateMessage }}</p>
        </div>
        <div v-if="generateError" class="generate-error">
          <el-alert
            :title="generateError"
            type="error"
            show-icon
            :closable="false"
          />
        </div>
      </div>
      <template #footer>
        <el-button @click="showGenerateDialog = false" :disabled="generating">
          {{ generating ? '生成中...' : '关闭' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 保存确认对话框 -->
    <el-dialog
      v-model="showSaveDialog"
      title="保存确认"
      width="400px"
      center
    >
      <p>检测到文件内容已修改，是否保存更改？</p>
      <template #footer>
        <el-button @click="discardChanges">不保存</el-button>
        <el-button type="primary" @click="confirmSave" :loading="saving">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Codemirror } from 'vue-codemirror'
import { yaml } from '@codemirror/lang-yaml'
import { oneDark } from '@codemirror/theme-one-dark'
import { EditorView } from '@codemirror/view'
import { apiService } from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as yamlParser from 'js-yaml'
import {
  ArrowLeft,
  MagicStick,
  CircleCheck,
  DocumentChecked,
  DocumentCopy,
  FullScreen,
  Refresh,
  Guide,
  Plus,
  Delete
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const content = ref('')
const originalContent = ref('')
const saving = ref(false)
const parsing = ref(false)
const parsedData = ref(null)
const parseError = ref('')
const isFullscreen = ref(false)
const editorContainer = ref()
const showSaveDialog = ref(false)
const showStructureHelper = ref(false)
const activeRightTab = ref('preview')

// 代码生成相关
const generating = ref(false)
const showGenerateDialog = ref(false)
const generateStep = ref(0)
const generateMessage = ref('')
const generateError = ref('')

// 依赖和断言配置
const dependencies = ref([])
const assertions = ref([])

// 计算属性
const filePath = computed(() => {
  const path = route.params.path
  console.log('Editor接收到的路径参数:', path)
  
  if (!path || typeof path !== 'string') {
    console.warn('无效的路径参数')
    return ''
  }
  
  try {
    // 判断是否为Base64编码的路径
    // Base64字符串只包含字母、数字、+、/、= 字符
    const base64Regex = /^[A-Za-z0-9+/]+=*$/
    
    if (base64Regex.test(path)) {
      // Base64解码
      try {
        const decodedPath = decodeURIComponent(escape(atob(path)))
        console.log('Base64解码成功:', path, '->', decodedPath)
        
        // 路径标准化：确保使用正斜杠
        const normalizedPath = decodedPath.replace(/\\/g, '/')
        console.log('标准化后路径:', normalizedPath)
        
        return normalizedPath
      } catch (base64Error) {
        console.warn('Base64解码失败，尝试URL解码:', base64Error)
        // 如果Base64解码失败，尝试URL解码
        const urlDecodedPath = decodeURIComponent(path)
        return urlDecodedPath.replace(/\\/g, '/')
      }
    } else {
      // 兼容旧的URL编码方式
      console.log('检测为URL编码，使用URL解码:', path)
      const urlDecodedPath = decodeURIComponent(path)
      const normalizedPath = urlDecodedPath.replace(/\\/g, '/')
      console.log('URL解码并标准化后:', normalizedPath)
      return normalizedPath
    }
  } catch (error) {
    console.warn('路径解码失败:', error)
    // 返回原始路径，进行基本的路径标准化
    return String(path).replace(/\\/g, '/')
  }
})

const fileName = computed(() => {
  const path = filePath.value
  if (!path || typeof path !== 'string') return ''
  
  try {
    const parts = path.split('/')
    return parts[parts.length - 1] || ''
  } catch (error) {
    console.warn('文件名解析失败:', error)
    return ''
  }
})

const hasContent = computed(() => content.value.trim().length > 0)
const hasChanges = computed(() => content.value !== originalContent.value)

const editorHeight = computed(() => {
  return isFullscreen.value ? 'calc(100vh - 60px)' : '600px'
})

const extensions = computed(() => {
  const exts = [yaml()]
  // 可以根据用户设置或系统主题切换暗色模式
  // if (isDark.value) {
  //   exts.push(oneDark)
  // }
  exts.push(EditorView.lineWrapping)
  return exts
})

const testCases = computed(() => {
  if (!parsedData.value || typeof parsedData.value !== 'object') return {}
  
  try {
    const cases = { ...parsedData.value }
    delete cases.case_common
    return cases
  } catch (error) {
    console.warn('提取测试用例失败:', error)
    return {}
  }
})

const caseCount = computed(() => {
  try {
    return Object.keys(testCases.value || {}).length
  } catch (error) {
    console.warn('计算用例数量失败:', error)
    return 0
  }
})

const yamlStructure = computed(() => [
  {
    label: 'case_common (公共配置)',
    children: [
      { label: 'allureEpic' },
      { label: 'allureFeature' },
      { label: 'allureStory' }
    ]
  },
  {
    label: 'test_case_01 (测试用例)',
    children: [
      { label: 'host' },
      { label: 'url' },
      { label: 'method' },
      { label: 'detail' },
      { label: 'headers' },
      { label: 'requestType' },
      { label: 'data' },
      { label: 'dependence_case' },
      { label: 'dependence_case_data' },
      { label: 'assert' },
      { label: 'sql' }
    ]
  }
])

// 监听依赖和断言变化，同步到YAML
watch([dependencies, assertions], () => {
  syncConfigToYaml()
}, { deep: true })

// 方法
const goBack = () => {
  try {
    console.log('返回用例管理页面...')
    
    if (hasChanges.value) {
      // 有未保存的更改，显示保存对话框
      showSaveDialog.value = true
    } else {
      // 直接返回用例管理页面
      router.push('/test-cases').catch(err => {
        console.warn('路由跳转警告:', err)
        // 即使路由跳转失败，也尝试强制跳转
        window.location.href = '/test-cases'
      })
    }
  } catch (error) {
    console.error('返回操作失败:', error)
    ElMessage.error('返回失败，请刷新页面')
    
    // 降级方案：直接使用window.location
    try {
      window.location.href = '/test-cases'
    } catch (fallbackError) {
      console.error('降级跳转也失败:', fallbackError)
      ElMessage.error('页面跳转失败，请手动导航到用例管理页面')
    }
  }
}

const loadFile = async () => {
  try {
    const path = filePath.value
    if (!path || typeof path !== 'string') {
      console.warn('无效的文件路径:', path)
      return
    }
    
    const response = await apiService.getTestCaseFile(path)
    content.value = response.data || ''
    originalContent.value = content.value
    
    // 解析YAML并提取配置
    parseYamlContent()
    
  } catch (error) {
    console.error('加载文件失败:', error)
    
    let errorMessage = '加载文件失败'
    if (error.response) {
      errorMessage = error.response.data?.message || `HTTP ${error.response.status}: ${error.response.statusText}`
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error(errorMessage)
  }
}

const saveFile = async () => {
  try {
    saving.value = true
    
    const path = filePath.value
    if (!path || typeof path !== 'string') {
      throw new Error('无效的文件路径')
    }
    
    await apiService.saveTestCaseFile(path, content.value)
    originalContent.value = content.value
    
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    
    let errorMessage = '保存失败'
    if (error.response) {
      errorMessage = error.response.data?.message || `HTTP ${error.response.status}: ${error.response.statusText}`
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error(errorMessage)
  } finally {
    saving.value = false
  }
}

const generateCode = async () => {
  try {
    generating.value = true
    showGenerateDialog.value = true
    generateStep.value = 0
    generateError.value = ''
    
    // 步骤1: 保存文件
    generateMessage.value = '保存YAML文件...'
    await saveFile()
    generateStep.value = 1
    
    // 步骤2: 调用代码生成API
    generateMessage.value = '正在生成pytest代码...'
    await apiService.generateCode()
    generateStep.value = 2
    
    // 步骤3: 完成
    generateMessage.value = '代码生成完成！'
    generateStep.value = 3
    
    ElMessage.success('代码生成成功！')
    
  } catch (error) {
    console.error('代码生成失败:', error)
    generateError.value = error.message || '代码生成失败'
    ElMessage.error('代码生成失败')
  } finally {
    generating.value = false
  }
}

const parseYamlContent = () => {
  try {
    parsing.value = true
    parseError.value = ''
    
    if (!content.value.trim()) {
      parsedData.value = null
      return
    }
    
    const parsed = yamlParser.load(content.value)
    parsedData.value = parsed
    
    // 提取依赖和断言配置
    extractConfigFromYaml(parsed)
    
  } catch (error) {
    parseError.value = error.message
    parsedData.value = null
  } finally {
    parsing.value = false
  }
}

const extractConfigFromYaml = (parsed) => {
  try {
    // 重置配置
    dependencies.value = []
    assertions.value = []
    
    if (!parsed || typeof parsed !== 'object') {
      return
    }
    
    Object.keys(parsed).forEach(key => {
      if (key === 'case_common') return
      
      const caseData = parsed[key]
      if (!caseData || typeof caseData !== 'object') return
      
      // 提取依赖
      if (Array.isArray(caseData.dependence_case_data)) {
        caseData.dependence_case_data.forEach(dep => {
          if (dep && Array.isArray(dep.dependent_data)) {
            dep.dependent_data.forEach(data => {
              if (data && typeof data === 'object') {
                dependencies.value.push({
                  case_id: dep.case_id || '',
                  type: data.dependent_type || '',
                  jsonpath: data.jsonpath || '',
                  cache_name: data.set_cache || ''
                })
              }
            })
          }
        })
      }
      
      // 提取断言
      if (caseData.assert && typeof caseData.assert === 'object') {
        Object.keys(caseData.assert).forEach(field => {
          const assert = caseData.assert[field]
          if (assert && typeof assert === 'object') {
            assertions.value.push({
              field: field || '',
              jsonpath: assert.jsonpath || '',
              type: assert.type || '',
              value: assert.value || '',
              assertType: assert.AssertType || ''
            })
          }
        })
      }
    })
  } catch (error) {
    console.warn('提取YAML配置失败:', error)
    dependencies.value = []
    assertions.value = []
  }
}

const syncConfigToYaml = () => {
  // 同步依赖和断言配置到YAML
  // 这里可以实现更智能的同步逻辑
}

const handleContentChange = () => {
  parseYamlContent()
  // 实时验证YAML语法
  validateYamlRealtime()
}

// 实时YAML验证（不显示消息提示）
const validateYamlRealtime = () => {
  try {
    if (!content.value.trim()) {
      parseError.value = ''
      return
    }
    
    const parsed = yamlParser.load(content.value)
    parseError.value = ''
    
    // 可以在这里添加更多的实时验证逻辑
    
  } catch (error) {
    parseError.value = `语法错误: ${error.message}`
  }
}

const handleEditorReady = () => {
  // 编辑器就绪
}

const refreshPreview = () => {
  parseYamlContent()
}

const formatCode = () => {
  try {
    if (!content.value.trim()) {
      ElMessage.warning('请先输入YAML内容')
      return
    }
    
    const parsed = yamlParser.load(content.value)
    if (!parsed) {
      ElMessage.warning('YAML内容为空，无法格式化')
      return
    }
    
    const formatted = yamlParser.dump(parsed, { 
      indent: 2, 
      defaultFlowStyle: false,
      allowUnicode: true 
    })
    
    content.value = formatted
    ElMessage.success('代码格式化成功')
  } catch (error) {
    console.error('格式化失败:', error)
    const errorMessage = error.message || '未知错误'
    ElMessage.error(`格式化失败: ${errorMessage}`)
  }
}

const validateYaml = () => {
  try {
    if (!content.value.trim()) {
      ElMessage.warning('请先输入YAML内容')
      return
    }
    
    const parsed = yamlParser.load(content.value)
    
    if (!parsed) {
      ElMessage.warning('YAML内容为空')
      return
    }
    
    // 进行更详细的结构验证
    let hasTestCases = false
    Object.keys(parsed).forEach(key => {
      if (key !== 'case_common') {
        hasTestCases = true
      }
    })
    
    if (!hasTestCases) {
      ElMessage.warning('未找到有效的测试用例，请检查YAML结构')
      return
    }
    
    ElMessage.success('YAML格式正确，结构验证通过')
  } catch (error) {
    console.error('YAML验证失败:', error)
    const errorMessage = error.message || '未知错误'
    
    // 提供更友好的错误提示
    let friendlyMessage = errorMessage
    if (errorMessage.includes('duplicated mapping key')) {
      friendlyMessage = '检测到重复的键名，请检查YAML结构'
    } else if (errorMessage.includes('bad indentation')) {
      friendlyMessage = '缩进格式错误，请检查YAML缩进'
    } else if (errorMessage.includes('expected')) {
      friendlyMessage = 'YAML语法错误，请检查括号、引号等符号'
    }
    
    ElMessage.error(`YAML验证失败: ${friendlyMessage}`)
  }
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
}

const getMethodType = (method) => {
  const types = {
    'GET': 'success',
    'POST': 'primary',
    'PUT': 'warning',
    'DELETE': 'danger'
  }
  return types[method] || 'info'
}

const insertTemplate = (type) => {
  const templates = {
    common: `# 公共参数
case_common:
  allureEpic: 项目模块
  allureFeature: 功能模块
  allureStory: 用户故事

`,
    get: `test_case_01:
  host: \${{host()}}
  url: /api/example
  method: GET
  detail: GET请求示例
  headers:
    Content-Type: application/json
  requestType: params
  is_run: true
  data:
    param1: value1
  dependence_case: false
  assert:
    code:
      jsonpath: $.code
      type: ==
      value: 200
      AssertType:
  sql:

`,
    post: `test_case_01:
  host: \${{host()}}
  url: /api/example
  method: POST
  detail: POST请求示例
  headers:
    Content-Type: application/json
  requestType: json
  is_run: true
  data:
    name: example
    value: test
  dependence_case: false
  assert:
    code:
      jsonpath: $.code
      type: ==
      value: 200
      AssertType:
  sql:

`,
    put: `test_case_01:
  host: \${{host()}}
  url: /api/example/1
  method: PUT
  detail: PUT请求示例
  headers:
    Content-Type: application/json
  requestType: json
  is_run: true
  data:
    id: 1
    name: updated_example
  dependence_case: false
  assert:
    code:
      jsonpath: $.code
      type: ==
      value: 200
      AssertType:
  sql:

`,
    delete: `test_case_01:
  host: \${{host()}}
  url: /api/example/1
  method: DELETE
  detail: DELETE请求示例
  headers:
    Content-Type: application/json
  requestType: params
  is_run: true
  data:
    id: 1
  dependence_case: false
  assert:
    code:
      jsonpath: $.code
      type: ==
      value: 200
      AssertType:
  sql:

`,
    patch: `test_case_01:
  host: \${{host()}}
  url: /api/example/1
  method: PATCH
  detail: PATCH请求示例
  headers:
    Content-Type: application/json
  requestType: json
  is_run: true
  data:
    name: patched_example
  dependence_case: false
  assert:
    code:
      jsonpath: $.code
      type: ==
      value: 200
      AssertType:
  sql:

`,
    dependency: `  dependence_case: true
  dependence_case_data:
    - case_id: previous_case_id
      dependent_data:
        - dependent_type: response
          jsonpath: $.data.id
          set_cache: example_id
`,
    assert: `  assert:
    code:
      jsonpath: $.code
      type: ==
      value: 200
      AssertType:
    message:
      jsonpath: $.message
      type: contains
      value: success
      AssertType:
`,
    complex_assert: `  assert:
    status_code:
      jsonpath: $.status_code
      type: ==
      value: 200
      AssertType:
    response_time:
      jsonpath: $.response_time
      type: <
      value: 1000
      AssertType: response_time
    data_count:
      jsonpath: $.data.length
      type: >
      value: 0
      AssertType:
    user_name:
      jsonpath: $.data.user.name
      type: !=
      value: null
      AssertType:
`,
    data_extract: `  dependence_case: true
  dependence_case_data:
    - case_id: previous_case_id
      dependent_data:
        - dependent_type: response
          jsonpath: $.data.user_id
          set_cache: current_user_id
        - dependent_type: response
          jsonpath: $.data.token
          set_cache: auth_token
`,
    complete_case: `test_complete_example:
  host: \${{host()}}
  url: /api/user/profile
  method: POST
  detail: 完整用例示例 - 用户资料更新
  headers:
    Content-Type: application/json
    Authorization: Bearer \$json(auth_token)\$
  requestType: json
  is_run: true
  data:
    user_id: \$json(current_user_id)\$
    name: "新用户名"
    email: "user@example.com"
    phone: "13800138000"
  dependence_case: true
  dependence_case_data:
    - case_id: login_case
      dependent_data:
        - dependent_type: response
          jsonpath: $.data.user_id
          set_cache: current_user_id
        - dependent_type: response
          jsonpath: $.data.access_token
          set_cache: auth_token
  assert:
    status_code:
      jsonpath: $.code
      type: ==
      value: 200
      AssertType:
    success_message:
      jsonpath: $.message
      type: ==
      value: "更新成功"
      AssertType:
    updated_name:
      jsonpath: $.data.name
      type: ==
      value: "新用户名"
      AssertType:
  sql:
    - SELECT * FROM users WHERE id = \$json(current_user_id)\$ AND name = '新用户名'

`,
    sql: `  sql:
    - SELECT * FROM users WHERE id = \$json($.data.id)\$
`
  }
  
  if (templates[type]) {
    const editor = editorContainer.value?.querySelector('.cm-editor')
    if (editor) {
      const currentContent = content.value
      content.value = currentContent + (currentContent ? '\n' : '') + templates[type]
    }
  }
}

const handleStructureClick = (data) => {
  try {
    if (!data || !data.label) {
      console.warn('无效的结构节点数据:', data)
      return
    }
    
    console.log('点击结构节点:', data.label)
    
    // 根据点击的节点类型插入对应的模板代码
    const nodeTemplates = {
      'case_common (公共配置)': 'common',
      'test_case_01 (测试用例)': 'post',
      'host': () => insertAtCursor('host: ${{host()}}'),
      'url': () => insertAtCursor('url: /api/example'),
      'method': () => insertAtCursor('method: POST'),
      'headers': () => insertAtCursor('headers:\n  Content-Type: application/json'),
      'data': () => insertAtCursor('data:\n  key: value'),
      'dependence_case_data': 'dependency',
      'assert': 'assert',
      'sql': 'sql'
    }
    
    const template = nodeTemplates[data.label]
    if (typeof template === 'string') {
      insertTemplate(template)
    } else if (typeof template === 'function') {
      template()
    } else {
      ElMessage.info(`点击了: ${data.label}`)
    }
  } catch (error) {
    console.error('处理结构节点点击失败:', error)
    ElMessage.error('操作失败，请重试')
  }
}

const insertAtCursor = (text) => {
  try {
    const currentContent = content.value
    // 简单的在末尾插入，实际项目中可以实现光标位置插入
    content.value = currentContent + (currentContent && !currentContent.endsWith('\n') ? '\n' : '') + text + '\n'
    ElMessage.success('已插入代码片段')
  } catch (error) {
    console.error('插入代码片段失败:', error)
    ElMessage.error('插入失败')
  }
}

// 插入常用代码片段
const insertSnippet = (type) => {
  const snippets = {
    // 请求头配置
    auth_header: `  headers:
    Authorization: Bearer \$json(auth_token)\$`,
    content_json: `  headers:
    Content-Type: application/json`,
    content_form: `  headers:
    Content-Type: application/x-www-form-urlencoded`,
    
    // 断言类型
    status_assert: `    status_code:
      jsonpath: $.code
      type: ==
      value: 200
      AssertType:`,
    response_time: `    response_time:
      jsonpath: $.response_time
      type: <
      value: 1000
      AssertType: response_time`,
    json_schema: `    data_structure:
      jsonpath: $.data
      type: json_schema
      value: |
        {
          "type": "object",
          "properties": {
            "id": {"type": "number"},
            "name": {"type": "string"}
          },
          "required": ["id", "name"]
        }
      AssertType:`,
    
    // 数据类型
    login_data: `  data:
    username: "admin"
    password: "123456"
    remember: true`,
    pagination_data: `  data:
    page: 1
    size: 10
    sort: "id"
    order: "desc"`,
    upload_data: `  data:
    file: "@/path/to/file.jpg"
    description: "文件描述"
    category: "image"`
  }
  
  if (snippets[type]) {
    insertAtCursor(snippets[type])
  }
}

const addDependency = () => {
  dependencies.value.push({
    case_id: '',
    type: 'response',
    jsonpath: '',
    cache_name: ''
  })
}

const removeDependency = (index) => {
  dependencies.value.splice(index, 1)
}

const addAssertion = () => {
  assertions.value.push({
    field: '',
    jsonpath: '',
    type: '==',
    value: '',
    assertType: ''
  })
}

const removeAssertion = (index) => {
  assertions.value.splice(index, 1)
}

const confirmSave = async () => {
  try {
    await saveFile()
    showSaveDialog.value = false
    
    // 保存成功后返回列表页
    router.push('/test-cases').catch(err => {
      console.warn('保存后路由跳转警告:', err)
      window.location.href = '/test-cases'
    })
  } catch (error) {
    console.error('保存失败:', error)
    // 不关闭对话框，让用户重试
    ElMessage.error('保存失败，请重试')
  }
}

const discardChanges = () => {
  try {
    showSaveDialog.value = false
    
    // 放弃更改并返回列表页
    router.push('/test-cases').catch(err => {
      console.warn('放弃更改后路由跳转警告:', err)
      window.location.href = '/test-cases'
    })
  } catch (error) {
    console.error('放弃更改失败:', error)
    ElMessage.error('操作失败，请刷新页面')
    
    // 降级方案
    try {
      window.location.href = '/test-cases'
    } catch (fallbackError) {
      console.error('降级跳转也失败:', fallbackError)
    }
  }
}

// 监听路由参数变化
watch(() => route.params.path, (newPath, oldPath) => {
  if (newPath !== oldPath) {
    loadFile()
  }
}, { immediate: false })

// 生命周期
onMounted(async () => {
  try {
    // 验证路由参数
    if (!route.params.path) {
      ElMessage.error('缺少文件路径参数')
      router.push('/test-cases')
      return
    }
    
    await loadFile()
  } catch (error) {
    console.error('组件初始化失败:', error)
    ElMessage.error('页面加载失败')
  }
})

onBeforeUnmount(() => {
  // 清理工作
  if (hasChanges.value) {
    // 可以在这里保存草稿或提示用户
    console.log('页面关闭时有未保存的更改')
  }
})
</script>

<style lang="scss" scoped>
.case-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: $bg-secondary;
}

.editor-header {
  height: 60px;
  background: $bg-primary;
  border-bottom: 1px solid $border-color;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 $spacing-lg;
  
  .header-left {
    display: flex;
    align-items: center;
    gap: $spacing-md;
    
    .back-button {
      color: $text-secondary;
      
      &:hover {
        color: $primary-color;
      }
    }
    
    .file-info {
      .file-title {
        font-size: $font-size-lg;
        color: $text-primary;
        margin: 0;
      }
      
      .file-path {
        font-size: $font-size-sm;
        color: $text-secondary;
        margin: 0;
        font-family: $font-family-mono;
      }
    }
  }
  
  .header-actions {
    display: flex;
    gap: $spacing-sm;
  }
}

.editor-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.editor-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  border-right: 1px solid $border-color;
  
  .panel-header {
    height: 40px;
    background: $bg-secondary;
    border-bottom: 1px solid $border-color;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 $spacing-md;
    
    h3 {
      font-size: $font-size-sm;
      color: $text-secondary;
      margin: 0;
    }
  }
  
  .editor-container {
    flex: 1;
    overflow: hidden;
  }
}

.right-panel {
  width: 400px;
  border-left: 1px solid $border-light;
  background: rgba(255, 255, 255, 0.95);
  
  .right-tabs {
    height: 100%;
    
    :deep(.el-tabs__content) {
      height: calc(100% - 40px);
      overflow-y: auto;
      padding: $spacing-md;
    }
  }
}

.structure-helper {
  .helper-section {
    margin-bottom: $spacing-lg;
    
    h4 {
      margin-bottom: $spacing-md;
      color: $text-primary;
    }
    
    .helper-buttons {
      margin-bottom: $spacing-sm;
    }
  }
  
  .structure-tree {
    .yaml-tree {
      background: transparent;
      
      :deep(.el-tree-node__content) {
        padding: $spacing-xs 0;
        
        &:hover {
          background: rgba(102, 126, 234, 0.1);
        }
      }
    }
  }
  
  // 智能提示样式
  .smart-hints {
    .hint-list {
      margin: 0;
      padding-left: $spacing-md;
      list-style: none;
      
      li {
        margin-bottom: $spacing-xs;
        color: $text-secondary;
        font-size: $font-size-sm;
        line-height: 1.5;
      }
    }
  }
  
  // 常用片段样式
  .snippet-list {
    .snippet-item {
      display: flex;
      flex-wrap: wrap;
      gap: $spacing-xs;
      padding: $spacing-sm 0;
      
      .el-button {
        margin-bottom: $spacing-xs;
      }
    }
    
    :deep(.el-collapse-item__header) {
      font-size: $font-size-sm;
      font-weight: 500;
      color: $text-primary;
    }
    
    :deep(.el-collapse-item__content) {
      padding-bottom: $spacing-sm;
    }
  }
}

.dependency-config,
.assertion-config {
  .config-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: $spacing-md;
    
    h4 {
      margin: 0;
      color: $text-primary;
    }
  }
  
  .dependency-list,
  .assertion-list {
    .dependency-item,
    .assertion-item {
      margin-bottom: $spacing-md;
      
      .dep-card,
      .assertion-card {
        .dep-header,
        .assertion-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: $spacing-sm;
          font-weight: 500;
        }
      }
    }
  }
  
  .empty-deps,
  .empty-assertions {
    text-align: center;
    padding: $spacing-xl;
  }
}

.generate-content {
  .generate-status {
    margin-bottom: $spacing-lg;
  }
  
  .generate-message {
    text-align: center;
    margin-bottom: $spacing-md;
    color: $text-secondary;
  }
  
  .generate-error {
    margin-top: $spacing-md;
  }
}

.case-preview {
  .case-item {
    .case-assertions {
      margin-top: $spacing-xs;
      
      .assertion-tag {
        margin-right: $spacing-xs;
      }
    }
  }
}
</style>
