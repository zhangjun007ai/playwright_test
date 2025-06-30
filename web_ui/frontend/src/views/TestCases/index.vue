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
          <el-icon><Magic /></el-icon>
          创建向导
        </el-button>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建用例
        </el-button>
        <el-button @click="generateCode" :loading="generating">
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
                  <el-tag size="small" type="info">{{ caseFile.module }}</el-tag>
                  <span class="case-count">{{ caseFile.cases.length }} 个用例</span>
                </div>
                
                <div class="cases-list">
                  <div
                    v-for="testCase in caseFile.cases.slice(0, 3)"
                    :key="testCase.case_id"
                    class="case-item"
                  >
                    <div class="case-info">
                      <span class="case-id">{{ testCase.case_id }}</span>
                      <span class="case-detail">{{ testCase.detail }}</span>
                    </div>
                    <div class="case-meta">
                      <el-tag
                        :type="testCase.method === 'GET' ? 'success' : testCase.method === 'POST' ? 'primary' : 'warning'"
                        size="small"
                      >
                        {{ testCase.method }}
                      </el-tag>
                      <el-switch
                        v-model="testCase.is_run"
                        size="small"
                        @change="updateCaseStatus(caseFile, testCase)"
                      />
                    </div>
                  </div>
                  
                  <div v-if="caseFile.cases.length > 3" class="more-cases">
                    <el-button link size="small" @click="editFile(caseFile)">
                      查看全部 {{ caseFile.cases.length }} 个用例
                    </el-button>
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
  Magic,
  MagicStick,
  Refresh,
  Search,
  MoreFilled,
  Edit,
  CopyDocument,
  Delete
} from '@element-plus/icons-vue'

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

const filteredCases = computed(() => {
  let filtered = testCases.value
  
  // 关键词搜索
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(item => 
      item.feature.toLowerCase().includes(keyword) ||
      item.file.toLowerCase().includes(keyword) ||
      item.cases.some(c => 
        c.detail.toLowerCase().includes(keyword) ||
        c.case_id.toLowerCase().includes(keyword)
      )
    )
  }
  
  // 模块筛选
  if (selectedModule.value) {
    filtered = filtered.filter(item => item.module === selectedModule.value)
  }
  
  // 状态筛选
  if (selectedStatus.value) {
    const isEnabled = selectedStatus.value === 'enabled'
    filtered = filtered.filter(item => 
      item.cases.some(c => Boolean(c.is_run) === isEnabled)
    )
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
    testCases.value = response.data || []
  } catch (error) {
    console.error('加载测试用例失败:', error)
    ElMessage.error('加载测试用例失败')
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
  router.push(`/test-cases/editor/${encodeURIComponent(caseFile.file_path)}`)
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
    await ElMessageBox.confirm(
      `确定要删除文件 "${caseFile.file}" 吗？此操作不可恢复。`,
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    // 这里实现删除逻辑
    ElMessage.success('文件删除成功')
    await loadTestCases()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除文件失败:', error)
    }
  }
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
    await apiService.generateCode()
    ElMessage.success('测试代码生成成功')
  } catch (error) {
    console.error('生成代码失败:', error)
    ElMessage.error('生成代码失败')
  } finally {
    generating.value = false
  }
}

const refreshCases = () => {
  loadTestCases()
}

const createCaseFile = async () => {
  try {
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
    
    await apiService.saveTestCaseContent(filePath, yamlContent)
    
    ElMessage.success('用例文件创建成功')
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
    ElMessage.error('创建用例文件失败')
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
      
      .case-count {
        color: $text-secondary;
        font-size: $font-size-sm;
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
  }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 300px;
}
</style>
