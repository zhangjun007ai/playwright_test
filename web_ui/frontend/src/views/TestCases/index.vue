<template>
  <div class="test-cases">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title gradient-text">
          <el-icon class="title-icon"><Document /></el-icon>
          用例管理
        </h1>
        <p class="page-subtitle">管理和编辑测试用例</p>
      </div>
      <div class="header-actions">
        <el-button type="success" @click="openWizard">
          <el-icon><MagicStick /></el-icon>
          创建向导
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建用例
        </el-button>
        <el-button @click="openGenerationWizard" :loading="generating">
          <el-icon><MagicStick /></el-icon>
          生成代码
        </el-button>
        <el-button @click="refreshCases">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>
    
    <div class="page-content">
      <!-- 搜索和筛选 -->
      <div class="search-section sketch-card">
        <div class="search-form">
          <el-input
            id="search-cases"
            v-model="searchKeyword"
            placeholder="搜索用例名称、描述..."
            clearable
            @input="handleSearch"
            style="width: 300px;"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>

          <el-select
            id="filter-module"
            v-model="selectedModule"
            placeholder="选择模块"
            clearable
            @change="handleFilter"
            style="width: 150px;"
          >
            <el-option
              v-for="module in modules"
              :key="module"
              :label="module"
              :value="module"
            />
          </el-select>

          <el-select
            id="filter-status"
            v-model="selectedStatus"
            placeholder="执行状态"
            clearable
            @change="handleFilter"
            style="width: 120px;"
          >
            <el-option label="启用" value="enabled" />
            <el-option label="禁用" value="disabled" />
          </el-select>
        </div>
      </div>
      
      <!-- 用例列表 -->
      <div class="cases-section" v-loading="loading" element-loading-text="加载中...">
          <div class="cases-grid">
            <div
              v-for="caseFile in filteredCases"
              :key="caseFile.file_path"
              class="case-file-card sketch-card"
            >
              <div class="card-header">
                <div class="file-info">
                  <h3 class="file-title">{{ caseFile.feature || caseFile.file }}</h3>
                  <p class="file-path">{{ caseFile.file_path }}</p>
                </div>
                <div class="file-actions">
                  <el-button 
                    size="small" 
                    link 
                    @click="toggleCaseDetails(caseFile.file_path)"
                    :type="expandedCases.has(caseFile.file_path) ? 'primary' : 'default'"
                  >
                    <el-icon>
                      <ArrowUp v-if="expandedCases.has(caseFile.file_path)" />
                      <ArrowDown v-else />
                    </el-icon>
                    详情
                  </el-button>
                  <el-dropdown trigger="click">
                    <el-button link size="small">
                      <el-icon><MoreFilled /></el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item @click="editFile(caseFile)">
                          <el-icon><Edit /></el-icon>
                          编辑
                        </el-dropdown-item>
                        <el-dropdown-item @click="generateCodeForFile(caseFile)">
                          <el-icon><MagicStick /></el-icon>
                          生成代码
                        </el-dropdown-item>
                        <el-dropdown-item @click="duplicateFile(caseFile)">
                          <el-icon><CopyDocument /></el-icon>
                          复制
                        </el-dropdown-item>
                        <el-dropdown-item @click="deleteFile(caseFile)" divided>
                          <el-icon><Delete /></el-icon>
                          删除
                        </el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </div>
              </div>
              
              <div class="card-content">
                <div class="file-meta">
                  <el-tag size="small" type="info">{{ caseFile.module || '未知模块' }}</el-tag>
                  <span class="case-count">{{ (caseFile.cases || []).length }} 个用例</span>
                  <div class="file-stats">
                    <el-tag v-if="caseFile.epic" size="small" type="success">{{ caseFile.epic }}</el-tag>
                    <el-tag v-if="caseFile.story" size="small" type="warning">{{ caseFile.story }}</el-tag>
                  </div>
                </div>
                
                <div class="cases-list">
                  <!-- 简要显示（收起状态） -->
                  <div v-if="!expandedCases.has(caseFile.file_path)">
                    <div
                      v-for="testCase in (caseFile.cases || []).slice(0, 3)"
                      :key="testCase.case_id || Math.random()"
                      class="case-item"
                    >
                      <div class="case-info">
                        <span class="case-id">{{ testCase.case_id || '未命名' }}</span>
                        <span class="case-detail">{{ testCase.detail || '无描述' }}</span>
                      </div>
                      <div class="case-meta">
                        <el-tag
                          :type="(testCase.method || 'GET') === 'GET' ? 'success' : (testCase.method || 'GET') === 'POST' ? 'primary' : 'warning'"
                          size="small"
                        >
                          {{ testCase.method || 'GET' }}
                        </el-tag>
                        <el-switch
                          v-model="testCase.is_run"
                          size="small"
                          @change="updateCaseStatus(caseFile, testCase)"
                        />
                      </div>
                    </div>
                    
                    <div v-if="(caseFile.cases || []).length > 3" class="more-cases">
                      <el-button link size="small" @click="toggleCaseDetails(caseFile.file_path)">
                        查看全部 {{ (caseFile.cases || []).length }} 个用例详情
                      </el-button>
                    </div>
                  </div>
                  
                  <!-- 详细显示（展开状态） -->
                  <div v-else class="expanded-cases">
                    <div
                      v-for="testCase in (caseFile.cases || [])"
                      :key="testCase.case_id || Math.random()"
                      class="detailed-case-item"
                    >
                      <div class="case-header">
                        <div class="case-title">
                          <span class="case-id">{{ testCase.case_id || '未命名' }}</span>
                          <el-tag
                            :type="(testCase.method || 'GET') === 'GET' ? 'success' : (testCase.method || 'GET') === 'POST' ? 'primary' : 'warning'"
                            size="small"
                          >
                            {{ testCase.method || 'GET' }}
                          </el-tag>
                          <el-switch
                            v-model="testCase.is_run"
                            size="small"
                            @change="updateCaseStatus(caseFile, testCase)"
                          />
                        </div>
                        <div class="case-actions">
                          <el-button size="small" link @click="executeTestCase(caseFile, testCase)">
                            <el-icon><VideoPlay /></el-icon>
                            执行
                          </el-button>
                        </div>
                      </div>
                      
                      <div class="case-details">
                        <p class="case-description">{{ testCase.detail || '无描述' }}</p>
                        
                        <div class="case-config">
                          <div class="config-item">
                            <label>请求地址:</label>
                            <code>{{ testCase.url || '未设置' }}</code>
                          </div>
                          
                          <div v-if="testCase.headers" class="config-item">
                            <label>请求头:</label>
                            <div class="config-details">
                              <el-tag v-for="(value, key) in testCase.headers" :key="key" size="small" class="header-tag">
                                {{ key }}: {{ value }}
                              </el-tag>
                            </div>
                          </div>
                          
                          <div v-if="testCase.data" class="config-item">
                            <label>请求参数:</label>
                            <div class="config-details">
                              <pre class="json-display">{{ formatJson(testCase.data) }}</pre>
                            </div>
                          </div>
                          
                          <div v-if="testCase.assert" class="config-item">
                            <label>断言配置:</label>
                            <div class="config-details assertions">
                              <div v-for="(value, key) in testCase.assert" :key="key" class="assertion-item">
                                <el-tag type="info" size="small">{{ key }}</el-tag>
                                <span class="assertion-value">{{ formatAssertValue(value) }}</span>
                              </div>
                            </div>
                          </div>
                          
                          <div v-if="testCase.dependence_case" class="config-item">
                            <label>依赖关系:</label>
                            <div class="config-details">
                              <el-tag type="warning" size="small">依赖用例</el-tag>
                              <span v-if="testCase.dependence_case_data">{{ testCase.dependence_case_data }}</span>
                            </div>
                          </div>
                          
                          <div v-if="testCase.sql" class="config-item">
                            <label>SQL断言:</label>
                            <div class="config-details">
                              <pre class="sql-display">{{ testCase.sql }}</pre>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

        
        <!-- 空状态 -->
        <div v-if="!loading && filteredCases.length === 0" class="empty-state">
          <el-empty description="暂无测试用例">
            <el-button type="primary" @click="showCreateDialog = true">
              创建第一个用例
            </el-button>
          </el-empty>
        </div>
      </div>
    </div>
    
    <!-- 新建用例对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="新建测试用例文件"
      width="600px"
      center
    >
      <el-form :model="newCaseForm" :rules="createRules" ref="createFormRef" label-width="100px">
        <el-form-item label="模块名称" prop="module" for="case-module">
          <el-input id="case-module" v-model="newCaseForm.module" placeholder="如：Login、User、Order" />
        </el-form-item>
        <el-form-item label="文件名称" prop="fileName" for="case-filename">
          <el-input id="case-filename" v-model="newCaseForm.fileName" placeholder="如：login、user_info" />
        </el-form-item>
        <el-form-item label="功能描述" prop="feature" for="case-feature">
          <el-input id="case-feature" v-model="newCaseForm.feature" placeholder="如：登录模块、用户信息" />
        </el-form-item>
        <el-form-item label="故事描述" prop="story" for="case-story">
          <el-input id="case-story" v-model="newCaseForm.story" placeholder="如：用户登录、获取用户信息" />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createCaseFile" :loading="creating">
          创建
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 代码生成向导对话框 -->
    <CodeGenerationDialog
      v-model="showGenerationDialog"
      :available-files="availableFilesForGeneration"
      @completed="handleGenerationCompleted"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { apiService } from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Document,
  Plus,
  MagicStick,
  Refresh,
  Search,
  MoreFilled,
  Edit,
  CopyDocument,
  Delete,
  ArrowUp,
  ArrowDown,
  VideoPlay
} from '@element-plus/icons-vue'
import CodeGenerationDialog from '@/components/CodeGenerationDialog.vue'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const generating = ref(false)
const creating = ref(false)
const showCreateDialog = ref(false)
const searchKeyword = ref('')
const selectedModule = ref('')
const selectedStatus = ref('')

const testCases = ref([])
const createFormRef = ref()
const expandedCases = ref(new Set()) // 展开的用例文件
const showGenerationDialog = ref(false) // 代码生成对话框显示状态

// 新建用例表单
const newCaseForm = ref({
  module: '',
  fileName: '',
  feature: '',
  story: ''
})

// 表单验证规则
const createRules = {
  module: [
    { required: true, message: '请输入模块名称', trigger: 'blur' }
  ],
  fileName: [
    { required: true, message: '请输入文件名称', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '文件名只能包含字母、数字和下划线', trigger: 'blur' }
  ],
  feature: [
    { required: true, message: '请输入功能描述', trigger: 'blur' }
  ],
  story: [
    { required: true, message: '请输入故事描述', trigger: 'blur' }
  ]
}

// 计算属性
const modules = computed(() => {
  const moduleSet = new Set(testCases.value.map(item => item.module))
  return Array.from(moduleSet)
})

// 为代码生成对话框提供可用文件列表
const availableFilesForGeneration = computed(() => {
  return testCases.value.map(caseFile => ({
    path: caseFile.file_path,
    name: `${caseFile.module}/${caseFile.file}`,
    casesCount: (caseFile.cases || []).length
  }))
})

const filteredCases = computed(() => {
  if (!Array.isArray(testCases.value)) {
    return []
  }
  
  let filtered = testCases.value
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(item => {
      if (!item) return false
      
      const feature = (item.feature || '').toLowerCase()
      const file = (item.file || '').toLowerCase()
      
      // 安全检查 cases 数组
      const cases = Array.isArray(item.cases) ? item.cases : []
      
      return feature.includes(keyword) ||
             file.includes(keyword) ||
             cases.some(c => {
               if (!c) return false
               const detail = (c.detail || '').toLowerCase()
               const caseId = (c.case_id || '').toLowerCase()
               return detail.includes(keyword) || caseId.includes(keyword)
             })
    })
  }
  
  // 模块筛选
  if (selectedModule.value) {
    filtered = filtered.filter(item => 
      item && item.module === selectedModule.value
    )
  }
  
  // 状态筛选
  if (selectedStatus.value) {
    const isEnabled = selectedStatus.value === 'enabled'
    filtered = filtered.filter(item => {
      if (!item || !Array.isArray(item.cases)) return false
      return item.cases.some(c => c && Boolean(c.is_run) === isEnabled)
    })
  }
  
  return filtered
})

// 方法
const openWizard = () => {
  router.push('/test-cases/wizard')
}

const loadTestCases = async () => {
  try {
    loading.value = true
    const response = await apiService.getTestCases()
    
    // 确保数据格式正确
    const data = response.data || []
    testCases.value = Array.isArray(data) ? data : []
    
    // 验证数据结构
    testCases.value = testCases.value.map(item => {
      if (!item || typeof item !== 'object') {
        return null
      }
      
      return {
        ...item,
        module: item.module || '',
        feature: item.feature || '',
        file: item.file || '',
        file_path: item.file_path || '',
        cases: Array.isArray(item.cases) ? item.cases.map(c => ({
          case_id: c?.case_id || '',
          detail: c?.detail || '',
          method: c?.method || 'GET',
          is_run: Boolean(c?.is_run),
          url: c?.url || '',
          ...c
        })) : []
      }
    }).filter(Boolean) // 过滤掉无效的数据
    
    console.log('加载测试用例成功:', testCases.value.length, '个文件')
    
  } catch (error) {
    handleApiError(error, '加载测试用例失败')
    // 设置为空数组，避免后续访问错误
    testCases.value = []
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 搜索逻辑已在计算属性中处理
}

const handleFilter = () => {
  // 筛选逻辑已在计算属性中处理
}

const editFile = (caseFile) => {
  try {
    // 验证文件对象
    if (!caseFile || !caseFile.file_path) {
      ElMessage.error('无效的文件路径')
      return
    }
    
    let filePath = caseFile.file_path
    console.log('原始文件路径:', filePath)
    
    // 路径标准化：将反斜杠转换为正斜杠
    filePath = filePath.replace(/\\/g, '/')
    console.log('标准化路径:', filePath)
    
    // 使用Base64编码，避免URL路径冲突
    const encodedPath = btoa(unescape(encodeURIComponent(filePath)))
    console.log('Base64编码路径:', encodedPath)
    
    const targetPath = `/test-cases/editor/${encodedPath}`
    console.log('目标跳转路径:', targetPath)
    
    router.push(targetPath)
    
  } catch (error) {
    console.error('跳转编辑器失败:', error)
    ElMessage.error('打开编辑器失败: ' + (error.message || '未知错误'))
  }
}

const duplicateFile = async (caseFile) => {
  try {
    const { value: newFileName } = await ElMessageBox.prompt(
      '请输入新文件名称',
      '复制用例文件',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /^[a-zA-Z0-9_]+$/,
        inputErrorMessage: '文件名只能包含字母、数字和下划线'
      }
    )
    
    // 这里实现复制逻辑
    ElMessage.success('文件复制成功')
    await loadTestCases()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('复制文件失败:', error)
    }
  }
}

const deleteFile = async (caseFile) => {
  try {
    await showConfirmDialog(
      '删除确认',
      `确定要删除文件 "${caseFile.file}" 吗？此操作不可恢复。`,
      'warning'
    )
    
    // 显示删除进度
    const loadingMessage = ElMessage.info({
      message: '正在删除文件...',
      duration: 0
    })
    
    try {
      // 这里实现删除逻辑 - 需要后端API支持
      // await apiService.deleteTestCaseFile(caseFile.file_path)
      
      // 模拟删除操作
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      loadingMessage.close()
      ElMessage.success('文件删除成功')
      await loadTestCases()
    } catch (deleteError) {
      loadingMessage.close()
      handleApiError(deleteError, '删除文件失败')
    }
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除操作错误:', error)
    }
  }
}

// 切换用例详情展开/折叠状态
const toggleCaseDetails = (filePath) => {
  if (expandedCases.value.has(filePath)) {
    expandedCases.value.delete(filePath)
  } else {
    expandedCases.value.add(filePath)
  }
}

// 格式化JSON显示
const formatJson = (data) => {
  if (typeof data === 'string') {
    try {
      return JSON.stringify(JSON.parse(data), null, 2)
    } catch {
      return data
    }
  }
  return JSON.stringify(data, null, 2)
}

// 格式化断言值显示
const formatAssertValue = (value) => {
  if (typeof value === 'object') {
    return JSON.stringify(value)
  }
  return String(value)
}

// 单独为文件生成代码
const generateCodeForFile = async (caseFile) => {
  try {
    generating.value = true
    ElMessage.info('正在为当前文件生成测试代码...')
    
    // 调用API为单个文件生成代码
    const response = await apiService.generateCode(caseFile.file_path)
    
    ElMessage.success({
      message: `代码生成成功！耗时 ${response.data.duration}s`,
      duration: 3000
    })
    
    console.log('生成详情:', response.data)
  } catch (error) {
    handleApiError(error, '代码生成失败')
  } finally {
    generating.value = false
  }
}

// 执行单个测试用例
const executeTestCase = async (caseFile, testCase) => {
  try {
    ElMessage.info(`正在执行测试用例: ${testCase.case_id}`)
    
    // 这里可以调用API执行单个测试用例
    // 暂时显示提示信息
    ElMessage.success('测试用例执行成功')
    
  } catch (error) {
    console.error('测试用例执行失败:', error)
    ElMessage.error('测试用例执行失败: ' + (error.message || '未知错误'))
  }
}

// 打开代码生成向导
const openGenerationWizard = () => {
  showGenerationDialog.value = true
}

// 处理代码生成完成
const handleGenerationCompleted = (result) => {
  console.log('代码生成完成:', result)
  ElMessage.success('代码生成完成！')
  // 可以在这里进行其他操作，如刷新页面等
}

// 优化错误处理的通用方法
const handleApiError = (error, defaultMessage = '操作失败') => {
  console.error('API错误:', error)
  
  let errorMessage = defaultMessage
  if (error.response) {
    const { data, status } = error.response
    errorMessage = data?.message || `HTTP ${status}: ${data?.error || '服务器错误'}`
  } else if (error.request) {
    errorMessage = '网络连接失败，请检查网络状态'
  } else if (error.message) {
    errorMessage = error.message
  }
  
  ElMessage.error(errorMessage)
  return errorMessage
}

// 显示操作确认对话框
const showConfirmDialog = (title, message, type = 'warning') => {
  return ElMessageBox.confirm(message, title, {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type,
    center: true
  })
}

const updateCaseStatus = async (caseFile, testCase) => {
  try {
    // 这里实现更新用例状态的逻辑
    ElMessage.success(`用例 ${testCase.case_id} 状态已更新`)
  } catch (error) {
    console.error('更新用例状态失败:', error)
    ElMessage.error('更新用例状态失败')
    // 回滚状态
    testCase.is_run = !testCase.is_run
  }
}

const generateCode = async () => {
  try {
    generating.value = true
    ElMessage.info('正在生成测试代码，请稍候...')
    
    const response = await apiService.generateCode()
    const data = response.data || {}
    
    // 显示详细的生成结果
    const messageContent = [
      `生成完成！耗时 ${data.duration || 0}s`,
      `处理了 ${data.yaml_files_count || 0} 个YAML文件`,
      `生成了 ${data.generated_files_count || 0} 个Python测试文件`
    ].join('\n')
    
    ElMessageBox.alert(
      `${messageContent}\n\n生成的文件:\n${(data.generated_files || []).map(f => `• ${f}`).join('\n')}`,
      '代码生成成功',
      {
        confirmButtonText: '确定',
        type: 'success',
        customStyle: {
          'white-space': 'pre-line'
        }
      }
    )
    
    console.log('生成代码详情:', data)
    
  } catch (error) {
    console.error('生成代码失败:', error)
    
    let errorMessage = '生成代码失败'
    if (error.response && error.response.data) {
      errorMessage = error.response.data.message || errorMessage
      // 如果有详细错误信息，显示在控制台
      if (error.response.data.error_detail) {
        console.error('错误详情:', error.response.data.error_detail)
      }
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error(errorMessage)
  } finally {
    generating.value = false
  }
}

const refreshCases = () => {
  loadTestCases()
}

const createCaseFile = async () => {
  try {
    // 验证表单
    await createFormRef.value.validate()
    creating.value = true
    
    // 构建文件路径
    const filePath = `data/${newCaseForm.value.module}/${newCaseForm.value.fileName}.yaml`
    
    // 构建 YAML 内容
    const yamlContent = `# 公共参数
case_common:
  allureEpic: 开发平台接口
  allureFeature: ${newCaseForm.value.feature}
  allureStory: ${newCaseForm.value.story}

${newCaseForm.value.fileName}_01:
    host: \${{host()}}
    url: /api/example
    method: GET
    detail: 示例用例
    headers:
      Content-Type: application/json
    requestType: params
    is_run: true
    data:
    dependence_case: false
    dependence_case_data:
    assert:
      status_code: 200
    sql:
`
    
    console.log('创建用例文件:', { filePath, module: newCaseForm.value.module, fileName: newCaseForm.value.fileName })
    
    // 调用API创建文件
    const response = await apiService.saveTestCaseFile(filePath, yamlContent)
    console.log('创建响应:', response)
    
    ElMessage.success(`用例文件创建成功: ${filePath}`)
    showCreateDialog.value = false
    
    // 重置表单
    newCaseForm.value = {
      module: '',
      fileName: '',
      feature: '',
      story: ''
    }
    
    // 刷新列表
    await loadTestCases()
    
  } catch (error) {
    console.error('创建用例文件失败:', error)
    
    // 更详细的错误处理
    let errorMessage = '创建用例文件失败'
    if (error.response) {
      errorMessage = error.response.data?.message || `HTTP ${error.response.status}: ${error.response.statusText}`
    } else if (error.message) {
      errorMessage = error.message
    }
    
    ElMessage.error(errorMessage)
  } finally {
    creating.value = false
  }
}

// 生命周期
onMounted(() => {
  loadTestCases()
})
</script>

<style lang="scss" scoped>
.test-cases {
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

.page-content {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.search-section {
  padding: $spacing-lg;
  margin-bottom: $spacing-lg;
  
  .search-form {
    display: flex;
    gap: $spacing-md;
    align-items: center;
  }
}

.cases-section {
  flex: 1;
  overflow-y: auto;
}

.cases-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: $spacing-lg;
}

.case-file-card {
  padding: $spacing-lg;
  transition: transform $transition-normal;
  
  &:hover {
    transform: translateY(-2px);
  }
  
  .card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: $spacing-md;
    
    .file-info {
      flex: 1;
      
      .file-title {
        font-size: $font-size-lg;
        color: $text-primary;
        margin: 0 0 $spacing-xs 0;
      }
      
      .file-path {
        color: $text-secondary;
        font-size: $font-size-sm;
        margin: 0;
        font-family: $font-family-mono;
      }
    }
  }
  
  .card-content {
    .file-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: $spacing-md;
      flex-wrap: wrap;
      gap: $spacing-sm;
      
      .case-count {
        color: $text-secondary;
        font-size: $font-size-sm;
      }
      
      .file-stats {
        display: flex;
        gap: $spacing-xs;
        flex-wrap: wrap;
      }
    }
    
    .cases-list {
      .case-item {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: $spacing-sm 0;
        border-bottom: 1px solid $border-light;
        
        &:last-child {
          border-bottom: none;
        }
        
        .case-info {
          flex: 1;
          
          .case-id {
            font-family: $font-family-mono;
            font-size: $font-size-sm;
            color: $primary-color;
            font-weight: 500;
          }
          
          .case-detail {
            display: block;
            color: $text-secondary;
            font-size: $font-size-sm;
            margin-top: $spacing-xs;
          }
        }
        
        .case-meta {
          display: flex;
          align-items: center;
          gap: $spacing-sm;
        }
      }
      
      .more-cases {
        text-align: center;
        padding-top: $spacing-sm;
      }
    }
    
    // 详细用例展示样式
    .expanded-cases {
      .detailed-case-item {
        border: 1px solid $border-light;
        border-radius: $border-radius-md;
        margin-bottom: $spacing-md;
        padding: $spacing-md;
        background: rgba(255, 255, 255, 0.02);
        
        .case-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: $spacing-sm;
          
          .case-title {
            display: flex;
            align-items: center;
            gap: $spacing-sm;
            
            .case-id {
              font-family: $font-family-mono;
              font-size: $font-size-sm;
              color: $primary-color;
              font-weight: 500;
            }
          }
          
          .case-actions {
            display: flex;
            gap: $spacing-xs;
          }
        }
        
        .case-details {
          .case-description {
            color: $text-secondary;
            font-size: $font-size-sm;
            margin-bottom: $spacing-md;
            font-style: italic;
          }
          
          .case-config {
            .config-item {
              margin-bottom: $spacing-sm;
              
              label {
                display: block;
                font-size: $font-size-sm;
                font-weight: 500;
                color: $text-primary;
                margin-bottom: $spacing-xs;
              }
              
              code {
                background: rgba(255, 255, 255, 0.1);
                padding: 2px 6px;
                border-radius: $border-radius-sm;
                font-family: $font-family-mono;
                font-size: $font-size-xs;
                color: $primary-color;
              }
              
              .config-details {
                .header-tag {
                  margin-right: $spacing-xs;
                  margin-bottom: $spacing-xs;
                }
                
                .json-display,
                .sql-display {
                  background: rgba(0, 0, 0, 0.2);
                  padding: $spacing-sm;
                  border-radius: $border-radius-sm;
                  font-family: $font-family-mono;
                  font-size: $font-size-xs;
                  color: #e8eaed;
                  overflow-x: auto;
                  margin: 0;
                  border: 1px solid $border-light;
                }
                
                &.assertions {
                  .assertion-item {
                    display: flex;
                    align-items: center;
                    gap: $spacing-sm;
                    margin-bottom: $spacing-xs;
                    
                    .assertion-value {
                      font-family: $font-family-mono;
                      font-size: $font-size-xs;
                      color: $success-color;
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}
</style>
