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
        <el-button @click="formatCode" :disabled="!hasContent">
          <el-icon><MagicStick /></el-icon>
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
      
      <!-- 右侧预览和工具 -->
      <div class="preview-panel" v-if="!isFullscreen">
        <!-- 用例预览 -->
        <div class="preview-section">
          <div class="section-header">
            <h3>用例预览</h3>
            <el-button size="small" @click="refreshPreview">
              <el-icon><Refresh /></el-icon>
            </el-button>
          </div>
          <div class="preview-content">
            <el-loading v-loading="parsing" element-loading-text="解析中...">
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
                        :type="caseData.method === 'GET' ? 'success' : caseData.method === 'POST' ? 'primary' : 'warning'"
                        size="small"
                      >
                        {{ caseData.method }}
                      </el-tag>
                    </div>
                    <div class="case-detail">{{ caseData.detail }}</div>
                    <div class="case-url">{{ caseData.url }}</div>
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
            </el-loading>
          </div>
        </div>
        
        <!-- 快速插入 -->
        <div class="tools-section">
          <div class="section-header">
            <h3>快速插入</h3>
          </div>
          <div class="tools-content">
            <div class="tool-group">
              <h5>用例模板</h5>
              <el-button-group size="small">
                <el-button @click="insertTemplate('get')">GET</el-button>
                <el-button @click="insertTemplate('post')">POST</el-button>
                <el-button @click="insertTemplate('put')">PUT</el-button>
                <el-button @click="insertTemplate('delete')">DELETE</el-button>
              </el-button-group>
            </div>
            
            <div class="tool-group">
              <h5>断言模板</h5>
              <el-button-group size="small">
                <el-button @click="insertAssert('status')">状态码</el-button>
                <el-button @click="insertAssert('response')">响应断言</el-button>
                <el-button @click="insertAssert('sql')">SQL断言</el-button>
              </el-button-group>
            </div>
            
            <div class="tool-group">
              <h5>依赖配置</h5>
              <el-button size="small" @click="insertDependency">添加依赖</el-button>
            </div>
          </div>
        </div>
      </div>
    </div>
    
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
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
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
  FullScreen,
  Refresh
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()

// 响应式数据
const content = ref('')
const originalContent = ref('')
const saving = ref(false)
const parsing = ref(false)
const showSaveDialog = ref(false)
const isFullscreen = ref(false)
const editorContainer = ref()

const parsedData = ref(null)
const parseError = ref('')

// 编辑器配置
const extensions = [
  yaml(),
  EditorView.theme({
    '&': {
      fontSize: '14px',
      fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace'
    },
    '.cm-content': {
      padding: '16px',
      minHeight: '400px'
    },
    '.cm-focused': {
      outline: 'none'
    }
  })
]

// 计算属性
const filePath = computed(() => {
  return decodeURIComponent(route.params.path || '')
})

const fileName = computed(() => {
  const path = filePath.value
  return path.split('/').pop() || ''
})

const hasContent = computed(() => {
  return content.value.trim().length > 0
})

const hasChanges = computed(() => {
  return content.value !== originalContent.value
})

const editorHeight = computed(() => {
  return isFullscreen.value ? 'calc(100vh - 120px)' : 'calc(100vh - 200px)'
})

const testCases = computed(() => {
  if (!parsedData.value) return {}
  const { case_common, ...cases } = parsedData.value
  return cases
})

const caseCount = computed(() => {
  return Object.keys(testCases.value).length
})

// 方法
const loadFileContent = async () => {
  try {
    const response = await apiService.getTestCaseContent(filePath.value)
    content.value = response.data.content
    originalContent.value = response.data.content
    parseYaml()
  } catch (error) {
    console.error('加载文件内容失败:', error)
    ElMessage.error('加载文件内容失败')
  }
}

const parseYaml = () => {
  if (!content.value.trim()) {
    parsedData.value = null
    parseError.value = ''
    return
  }
  
  try {
    parsing.value = true
    parsedData.value = yamlParser.load(content.value)
    parseError.value = ''
  } catch (error) {
    parsedData.value = null
    parseError.value = error.message
  } finally {
    parsing.value = false
  }
}

const handleContentChange = () => {
  // 延迟解析，避免频繁解析
  clearTimeout(window.parseTimer)
  window.parseTimer = setTimeout(parseYaml, 500)
}

const handleEditorReady = () => {
  // 编辑器准备就绪
}

const saveFile = async () => {
  try {
    saving.value = true
    await apiService.saveTestCaseContent(filePath.value, content.value)
    originalContent.value = content.value
    ElMessage.success('文件保存成功')
  } catch (error) {
    console.error('保存文件失败:', error)
    ElMessage.error('保存文件失败')
  } finally {
    saving.value = false
  }
}

const formatCode = () => {
  try {
    const parsed = yamlParser.load(content.value)
    content.value = yamlParser.dump(parsed, {
      indent: 2,
      lineWidth: 120,
      noRefs: true
    })
    ElMessage.success('代码格式化成功')
  } catch (error) {
    ElMessage.error('格式化失败：YAML 语法错误')
  }
}

const validateYaml = () => {
  try {
    yamlParser.load(content.value)
    ElMessage.success('YAML 语法验证通过')
  } catch (error) {
    ElMessage.error(`YAML 语法错误：${error.message}`)
  }
}

const refreshPreview = () => {
  parseYaml()
}

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value
  nextTick(() => {
    // 触发编辑器重新计算大小
    window.dispatchEvent(new Event('resize'))
  })
}

const goBack = () => {
  if (hasChanges.value) {
    showSaveDialog.value = true
  } else {
    router.back()
  }
}

const confirmSave = async () => {
  await saveFile()
  showSaveDialog.value = false
  router.back()
}

const discardChanges = () => {
  showSaveDialog.value = false
  router.back()
}

// 模板插入方法
const insertTemplate = (method) => {
  const templates = {
    get: `
test_case_01:
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
    dependence_case_data:
    assert:
      status_code: 200
    sql:`,
    post: `
test_case_01:
    host: \${{host()}}
    url: /api/example
    method: POST
    detail: POST请求示例
    headers:
      Content-Type: application/json
    requestType: json
    is_run: true
    data:
      field1: value1
      field2: value2
    dependence_case: false
    dependence_case_data:
    assert:
      status_code: 200
    sql:`,
    put: `
test_case_01:
    host: \${{host()}}
    url: /api/example
    method: PUT
    detail: PUT请求示例
    headers:
      Content-Type: application/json
    requestType: json
    is_run: true
    data:
      id: 1
      field1: updated_value
    dependence_case: false
    dependence_case_data:
    assert:
      status_code: 200
    sql:`,
    delete: `
test_case_01:
    host: \${{host()}}
    url: /api/example
    method: DELETE
    detail: DELETE请求示例
    headers:
      Content-Type: application/json
    requestType: params
    is_run: true
    data:
      id: 1
    dependence_case: false
    dependence_case_data:
    assert:
      status_code: 200
    sql:`
  }
  
  content.value += templates[method]
  ElMessage.success(`${method.toUpperCase()} 模板已插入`)
}

const insertAssert = (type) => {
  const assertions = {
    status: `
    assert:
      status_code: 200`,
    response: `
    assert:
      errorCode:
        jsonpath: $.errorCode
        type: ==
        value: 0
        AssertType:`,
    sql: `
    assert:
      count:
        jsonpath: $.data.count
        type: ==
        value: $.total_count
        AssertType: SQL
    sql:
      - SELECT COUNT(*) as total_count FROM table_name`
  }
  
  content.value += assertions[type]
  ElMessage.success('断言模板已插入')
}

const insertDependency = () => {
  const dependency = `
    dependence_case: true
    dependence_case_data:
      - case_id: dependent_case_01
        dependent_data:
          - dependent_type: response
            jsonpath: $.data.id
            set_cache: cached_id`
  
  content.value += dependency
  ElMessage.success('依赖配置模板已插入')
}

// 生命周期
onMounted(() => {
  loadFileContent()
})

onBeforeUnmount(() => {
  clearTimeout(window.parseTimer)
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

.preview-panel {
  width: 400px;
  display: flex;
  flex-direction: column;
  background: $bg-primary;
}

.preview-section,
.tools-section {
  .section-header {
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
}

.preview-section {
  flex: 1;
  overflow: hidden;
  
  .preview-content {
    height: calc(100% - 40px);
    overflow-y: auto;
    padding: $spacing-md;
    
    .case-preview {
      .common-info {
        margin-bottom: $spacing-lg;
        
        h4 {
          font-size: $font-size-md;
          color: $text-primary;
          margin: 0 0 $spacing-sm 0;
        }
      }
      
      .cases-list {
        h4 {
          font-size: $font-size-md;
          color: $text-primary;
          margin: 0 0 $spacing-sm 0;
        }
        
        .case-item {
          padding: $spacing-sm;
          border: 1px solid $border-light;
          border-radius: $sketch-radius;
          margin-bottom: $spacing-sm;
          
          .case-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: $spacing-xs;
            
            .case-id {
              font-family: $font-family-mono;
              font-weight: 500;
              color: $primary-color;
            }
          }
          
          .case-detail {
            color: $text-primary;
            font-size: $font-size-sm;
            margin-bottom: $spacing-xs;
          }
          
          .case-url {
            color: $text-secondary;
            font-size: $font-size-xs;
            font-family: $font-family-mono;
          }
        }
      }
    }
    
    .parse-error,
    .empty-preview {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 200px;
    }
  }
}

.tools-section {
  height: 300px;
  border-top: 1px solid $border-color;
  
  .tools-content {
    padding: $spacing-md;
    height: calc(100% - 40px);
    overflow-y: auto;
    
    .tool-group {
      margin-bottom: $spacing-lg;
      
      h5 {
        font-size: $font-size-sm;
        color: $text-secondary;
        margin: 0 0 $spacing-sm 0;
      }
    }
  }
}
</style>
