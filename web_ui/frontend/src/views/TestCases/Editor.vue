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
        <el-tabs v-model="activeRightTab" class="right-tabs">
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
                    <el-button @click="insertTemplate('dependency')">添加依赖</el-button>
                    <el-button @click="insertTemplate('assert')">添加断言</el-button>
                    <el-button @click="insertTemplate('sql')">SQL断言</el-button>
                  </el-button-group>
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
const filePath = computed(() => route.params.path)
const fileName = computed(() => {
  if (!filePath.value) return ''
  const parts = filePath.value.split('/')
  return parts[parts.length - 1]
})

const hasContent = computed(() => content.value.trim().length > 0)
const hasChanges = computed(() => content.value !== originalContent.value)

const editorHeight = computed(() => {
  return isFullscreen.value ? 'calc(100vh - 60px)' : '600px'
})

const extensions = computed(() => {
  const exts = [yaml()]
  if (isDark.value) {
    exts.push(oneDark)
  }
  exts.push(EditorView.lineWrapping)
  return exts
})

const testCases = computed(() => {
  if (!parsedData.value) return {}
  const cases = { ...parsedData.value }
  delete cases.case_common
  return cases
})

const caseCount = computed(() => Object.keys(testCases.value).length)

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
  if (hasChanges.value) {
    showSaveDialog.value = true
  } else {
    router.push('/test-cases')
  }
}

const loadFile = async () => {
  try {
    if (!filePath.value) return
    
    const response = await apiService.getTestCaseFile(filePath.value)
    content.value = response.data || ''
    originalContent.value = content.value
    
    // 解析YAML并提取配置
    parseYamlContent()
    
  } catch (error) {
    console.error('加载文件失败:', error)
    ElMessage.error('加载文件失败')
  }
}

const saveFile = async () => {
  try {
    saving.value = true
    
    await apiService.saveTestCaseFile(filePath.value, content.value)
    originalContent.value = content.value
    
    ElMessage.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    ElMessage.error('保存失败')
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
  // 提取依赖配置
  dependencies.value = []
  assertions.value = []
  
  Object.keys(parsed || {}).forEach(key => {
    if (key === 'case_common') return
    
    const caseData = parsed[key]
    
    // 提取依赖
    if (caseData.dependence_case_data) {
      caseData.dependence_case_data.forEach(dep => {
        if (dep.dependent_data) {
          dep.dependent_data.forEach(data => {
            dependencies.value.push({
              case_id: dep.case_id,
              type: data.dependent_type,
              jsonpath: data.jsonpath,
              cache_name: data.set_cache
            })
          })
        }
      })
    }
    
    // 提取断言
    if (caseData.assert) {
      Object.keys(caseData.assert).forEach(field => {
        const assert = caseData.assert[field]
        assertions.value.push({
          field,
          jsonpath: assert.jsonpath,
          type: assert.type,
          value: assert.value,
          assertType: assert.AssertType || ''
        })
      })
    }
  })
}

const syncConfigToYaml = () => {
  // 同步依赖和断言配置到YAML
  // 这里可以实现更智能的同步逻辑
}

const handleContentChange = () => {
  parseYamlContent()
}

const handleEditorReady = () => {
  // 编辑器就绪
}

const refreshPreview = () => {
  parseYamlContent()
}

const formatCode = () => {
  try {
    const parsed = yamlParser.load(content.value)
    content.value = yamlParser.dump(parsed, { indent: 2 })
    ElMessage.success('格式化成功')
  } catch (error) {
    ElMessage.error('格式化失败: ' + error.message)
  }
}

const validateYaml = () => {
  try {
    yamlParser.load(content.value)
    ElMessage.success('YAML格式正确')
  } catch (error) {
    ElMessage.error('YAML格式错误: ' + error.message)
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
  // 点击结构树节点的处理
  console.log('点击结构节点:', data.label)
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
  await saveFile()
  showSaveDialog.value = false
  router.push('/test-cases')
}

const discardChanges = () => {
  showSaveDialog.value = false
  router.push('/test-cases')
}

// 生命周期
onMounted(() => {
  loadFile()
})

onBeforeUnmount(() => {
  // 清理工作
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
