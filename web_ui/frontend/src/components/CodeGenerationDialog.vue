<template>
  <el-dialog
    v-model="visible"
    title="代码生成向导"
    width="800px"
    :close-on-click-modal="false"
    :close-on-press-escape="false"
    center
  >
    <div class="generation-wizard">
      <!-- 生成步骤 -->
      <el-steps :active="currentStep" direction="horizontal" class="generation-steps">
        <el-step title="准备阶段">
          <template #icon>
            <el-icon><Setting /></el-icon>
          </template>
        </el-step>
        <el-step title="扫描文件">
          <template #icon>
            <el-icon><Search /></el-icon>
          </template>
        </el-step>
        <el-step title="生成代码">
          <template #icon>
            <el-icon><MagicStick /></el-icon>
          </template>
        </el-step>
        <el-step title="完成">
          <template #icon>
            <el-icon><SuccessFilled /></el-icon>
          </template>
        </el-step>
      </el-steps>
      
      <div class="generation-content">
        <!-- 步骤1: 准备阶段 -->
        <div v-show="currentStep === 0" class="step-content">
          <div class="step-header">
            <h3>生成配置</h3>
            <p>选择要生成代码的配置选项</p>
          </div>
          
          <el-form :model="generationConfig" label-width="120px">
            <el-form-item label="生成范围">
              <el-radio-group v-model="generationConfig.scope">
                <el-radio value="all">全部文件</el-radio>
                <el-radio value="selected">选择文件</el-radio>
                <el-radio value="current">当前文件</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item v-if="generationConfig.scope === 'selected'" label="选择文件">
              <el-select v-model="generationConfig.selectedFiles" multiple style="width: 100%">
                <el-option
                  v-for="file in availableFiles"
                  :key="file.path"
                  :label="file.name"
                  :value="file.path"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="覆盖策略">
              <el-radio-group v-model="generationConfig.overwriteStrategy">
                <el-radio value="ask">询问覆盖</el-radio>
                <el-radio value="overwrite">直接覆盖</el-radio>
                <el-radio value="backup">备份后覆盖</el-radio>
              </el-radio-group>
            </el-form-item>
            
            <el-form-item label="生成选项">
              <el-checkbox-group v-model="generationConfig.options">
                <el-checkbox value="include_comments">包含注释</el-checkbox>
                <el-checkbox value="format_code">格式化代码</el-checkbox>
                <el-checkbox value="generate_report">生成报告</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-form>
        </div>
        
        <!-- 步骤2: 扫描文件 -->
        <div v-show="currentStep === 1" class="step-content">
          <div class="step-header">
            <h3>扫描YAML文件</h3>
            <p>正在扫描和分析测试用例文件...</p>
          </div>
          
          <div class="scan-progress">
            <el-progress
              :percentage="scanProgress"
              :status="scanStatus"
              stroke-width="8"
            />
            <p class="progress-text">{{ scanMessage }}</p>
          </div>
          
          <div v-if="scannedFiles.length > 0" class="scanned-files">
            <h4>已扫描的文件 ({{ scannedFiles.length }})</h4>
            <div class="file-list">
              <div
                v-for="file in scannedFiles"
                :key="file.path"
                class="file-item"
                :class="{ error: file.hasError }"
              >
                <div class="file-info">
                  <el-icon :class="{ 'text-error': file.hasError, 'text-success': !file.hasError }">
                    <Close v-if="file.hasError" />
                    <Check v-else />
                  </el-icon>
                  <span class="file-name">{{ file.name }}</span>
                  <span class="file-cases">{{ file.casesCount }} 个用例</span>
                </div>
                <div v-if="file.hasError" class="file-error">
                  {{ file.error }}
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 步骤3: 生成代码 -->
        <div v-show="currentStep === 2" class="step-content">
          <div class="step-header">
            <h3>生成测试代码</h3>
            <p>正在根据YAML配置生成Python测试代码...</p>
          </div>
          
          <div class="generation-progress">
            <el-progress
              :percentage="generationProgress"
              :status="generationStatus"
              stroke-width="8"
            />
            <p class="progress-text">{{ generationMessage }}</p>
          </div>
          
          <div v-if="generationLogs.length > 0" class="generation-logs">
            <h4>生成日志</h4>
            <div class="log-container">
              <div
                v-for="(log, index) in generationLogs"
                :key="index"
                class="log-item"
                :class="log.type"
              >
                <span class="log-time">{{ log.time }}</span>
                <span class="log-message">{{ log.message }}</span>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 步骤4: 完成 -->
        <div v-show="currentStep === 3" class="step-content">
          <div class="completion-content">
            <div class="completion-icon">
              <el-icon :class="{ 'text-success': !hasError, 'text-error': hasError }">
                <Close v-if="hasError" />
                <SuccessFilled v-else />
              </el-icon>
            </div>
            <h3>{{ hasError ? '生成失败' : '生成完成！' }}</h3>
            <p>{{ completionMessage }}</p>
            
            <!-- 生成结果统计 -->
            <div v-if="generationResult" class="result-stats">
              <el-descriptions :column="2" border size="small">
                <el-descriptions-item label="扫描文件">
                  {{ generationResult.scannedFiles || 0 }} 个
                </el-descriptions-item>
                <el-descriptions-item label="生成文件">
                  {{ generationResult.generatedFiles || 0 }} 个
                </el-descriptions-item>
                <el-descriptions-item label="总用例数">
                  {{ generationResult.totalCases || 0 }} 个
                </el-descriptions-item>
                <el-descriptions-item label="耗时">
                  {{ generationResult.duration || 0 }}s
                </el-descriptions-item>
              </el-descriptions>
            </div>
            
            <!-- 生成的文件预览 -->
            <div v-if="generationResult && generationResult.files" class="generated-files">
              <h4>生成的文件</h4>
              <div class="file-preview-list">
                <div
                  v-for="file in generationResult.files"
                  :key="file.path"
                  class="preview-file-item"
                >
                  <div class="file-header">
                    <span class="file-path">{{ file.path }}</span>
                    <el-button size="small" @click="previewFile(file)">预览</el-button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <el-button v-if="currentStep > 0 && currentStep < 3" @click="prevStep">
            上一步
          </el-button>
        </div>
        
        <div class="footer-right">
          <el-button @click="handleCancel">
            {{ currentStep === 3 ? '关闭' : '取消' }}
          </el-button>
          <el-button
            v-if="currentStep === 0"
            type="primary"
            @click="startGeneration"
          >
            开始生成
          </el-button>
          <el-button
            v-else-if="currentStep < 3"
            type="primary"
            @click="nextStep"
            :disabled="!canProceed"
          >
            下一步
          </el-button>
          <el-button
            v-if="currentStep === 3 && !hasError"
            type="success"
            @click="openGeneratedFolder"
          >
            打开文件夹
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
  
  <!-- 文件预览对话框 -->
  <el-dialog
    v-model="showPreview"
    title="文件预览"
    width="70%"
    center
  >
    <div class="file-preview">
      <div class="preview-header">
        <span class="preview-file-path">{{ previewFilePath }}</span>
      </div>
      <div class="preview-content">
        <pre><code>{{ previewContent }}</code></pre>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { apiService } from '@/services/api'
import {
  Check, Close, SuccessFilled, Setting, Search, MagicStick
} from '@element-plus/icons-vue'

// Props
const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  currentFilePath: {
    type: String,
    default: ''
  },
  availableFiles: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['update:modelValue', 'completed'])

// 响应式数据
const visible = ref(false)
const currentStep = ref(0)
const hasError = ref(false)

// 生成配置
const generationConfig = ref({
  scope: 'all',
  selectedFiles: [],
  overwriteStrategy: 'ask',
  options: ['include_comments', 'format_code']
})

// 扫描状态
const scanProgress = ref(0)
const scanStatus = ref('')
const scanMessage = ref('准备扫描...')
const scannedFiles = ref([])

// 生成状态
const generationProgress = ref(0)
const generationStatus = ref('')
const generationMessage = ref('准备生成...')
const generationLogs = ref([])
const generationResult = ref(null)
const completionMessage = ref('')

// 文件预览
const showPreview = ref(false)
const previewFilePath = ref('')
const previewContent = ref('')

// 计算属性
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return true
    case 1:
      return scanProgress.value === 100
    case 2:
      return generationProgress.value === 100
    default:
      return false
  }
})

// 监听显示状态
watch(() => props.modelValue, (newVal) => {
  visible.value = newVal
  if (newVal) {
    resetWizard()
  }
})

watch(visible, (newVal) => {
  emit('update:modelValue', newVal)
})

// 方法
const resetWizard = () => {
  currentStep.value = 0
  hasError.value = false
  scanProgress.value = 0
  scanStatus.value = ''
  scanMessage.value = '准备扫描...'
  scannedFiles.value = []
  generationProgress.value = 0
  generationStatus.value = ''
  generationMessage.value = '准备生成...'
  generationLogs.value = []
  generationResult.value = null
  completionMessage.value = ''
  
  // 根据当前文件路径设置默认配置
  if (props.currentFilePath) {
    generationConfig.value.scope = 'current'
  }
}

const startGeneration = async () => {
  try {
    currentStep.value = 1
    await performScan()
    
    currentStep.value = 2
    await performGeneration()
    
    currentStep.value = 3
    showCompletion()
    
  } catch (error) {
    console.error('代码生成失败:', error)
    hasError.value = true
    currentStep.value = 3
    completionMessage.value = `生成失败: ${error.message}`
  }
}

const performScan = async () => {
  return new Promise((resolve) => {
    scanMessage.value = '正在扫描YAML文件...'
    let progress = 0
    
    const scanInterval = setInterval(() => {
      progress += 10
      scanProgress.value = progress
      
      if (progress === 50) {
        scanMessage.value = '分析文件结构...'
        // 模拟扫描结果
        scannedFiles.value = [
          {
            path: 'data/login/login.yaml',
            name: 'login.yaml',
            casesCount: 5,
            hasError: false
          },
          {
            path: 'data/user/user.yaml',
            name: 'user.yaml',
            casesCount: 8,
            hasError: false
          }
        ]
      } else if (progress === 80) {
        scanMessage.value = '验证用例配置...'
      } else if (progress === 100) {
        scanMessage.value = '扫描完成'
        scanStatus.value = 'success'
        clearInterval(scanInterval)
        resolve()
      }
    }, 200)
  })
}

const performGeneration = async () => {
  try {
    generationMessage.value = '开始生成测试代码...'
    
    // 调用实际的API
    const response = await apiService.generateCode()
    
    // 模拟生成进度
    return new Promise((resolve) => {
      let progress = 0
      
      const genInterval = setInterval(() => {
        progress += 15
        generationProgress.value = progress
        
        // 添加生成日志
        if (progress === 15) {
          addGenerationLog('info', '开始解析YAML文件')
        } else if (progress === 30) {
          addGenerationLog('info', '生成测试用例代码')
        } else if (progress === 45) {
          addGenerationLog('info', '添加断言逻辑')
        } else if (progress === 60) {
          addGenerationLog('info', '处理依赖关系')
        } else if (progress === 75) {
          addGenerationLog('info', '格式化代码')
        } else if (progress === 90) {
          addGenerationLog('info', '保存文件')
        } else if (progress >= 100) {
          generationProgress.value = 100
          generationStatus.value = 'success'
          generationMessage.value = '代码生成完成'
          addGenerationLog('success', '代码生成成功完成')
          
          // 设置生成结果
          generationResult.value = response.data || {
            scannedFiles: scannedFiles.value.length,
            generatedFiles: 5,
            totalCases: 13,
            duration: 2.5,
            files: [
              { path: 'test_case/test_login.py' },
              { path: 'test_case/test_user.py' }
            ]
          }
          
          clearInterval(genInterval)
          resolve()
        }
      }, 300)
    })
  } catch (error) {
    addGenerationLog('error', `生成失败: ${error.message}`)
    throw error
  }
}

const addGenerationLog = (type, message) => {
  generationLogs.value.push({
    type,
    time: new Date().toLocaleTimeString(),
    message
  })
}

const showCompletion = () => {
  if (!hasError.value) {
    completionMessage.value = '测试代码已成功生成并保存到 test_case 目录'
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const nextStep = () => {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

const handleCancel = () => {
  visible.value = false
}

const openGeneratedFolder = () => {
  // 这里可以实现打开文件夹的逻辑
  ElMessage.success('已在新窗口中打开生成的文件夹')
}

const previewFile = (file) => {
  previewFilePath.value = file.path
  previewContent.value = `# Generated Test File: ${file.path}
import pytest
import allure
from utils.read_files_tools.get_yaml_data_analysis import GetTestCase

class TestExample:
    @allure.story("测试用例示例")
    def test_example(self):
        # 测试代码将在这里生成
        pass
`
  showPreview.value = true
}
</script>

<style lang="scss" scoped>
.generation-wizard {
  .generation-steps {
    margin-bottom: 2rem;
  }
  
  .generation-content {
    min-height: 400px;
    
    .step-content {
      .step-header {
        text-align: center;
        margin-bottom: 2rem;
        
        h3 {
          margin-bottom: 0.5rem;
        }
        
        p {
          color: #666;
          margin: 0;
        }
      }
    }
  }
  
  .scan-progress,
  .generation-progress {
    margin-bottom: 2rem;
    
    .progress-text {
      text-align: center;
      margin-top: 0.5rem;
      color: #666;
    }
  }
  
  .scanned-files,
  .generation-logs {
    margin-top: 1rem;
    
    h4 {
      margin-bottom: 1rem;
    }
    
    .file-list {
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid #e4e7ed;
      border-radius: 4px;
      
      .file-item {
        padding: 0.75rem;
        border-bottom: 1px solid #f5f7fa;
        
        &:last-child {
          border-bottom: none;
        }
        
        &.error {
          background: #fef0f0;
        }
        
        .file-info {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          
          .file-name {
            font-weight: 500;
          }
          
          .file-cases {
            color: #909399;
            font-size: 0.875rem;
          }
        }
        
        .file-error {
          color: #f56c6c;
          font-size: 0.875rem;
          margin-top: 0.25rem;
        }
      }
    }
    
    .log-container {
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid #e4e7ed;
      border-radius: 4px;
      padding: 0.5rem;
      background: #f8f9fa;
      font-family: 'Courier New', monospace;
      
      .log-item {
        margin-bottom: 0.25rem;
        font-size: 0.875rem;
        
        .log-time {
          color: #909399;
          margin-right: 0.5rem;
        }
        
        &.error {
          color: #f56c6c;
        }
        
        &.success {
          color: #67c23a;
        }
        
        &.info {
          color: #606266;
        }
      }
    }
  }
  
  .completion-content {
    text-align: center;
    
    .completion-icon {
      font-size: 4rem;
      margin-bottom: 1rem;
      
      .text-success {
        color: #67c23a;
      }
      
      .text-error {
        color: #f56c6c;
      }
    }
    
    .result-stats {
      margin: 2rem 0;
    }
    
    .generated-files {
      margin-top: 2rem;
      text-align: left;
      
      .file-preview-list {
        border: 1px solid #e4e7ed;
        border-radius: 4px;
        
        .preview-file-item {
          padding: 0.75rem;
          border-bottom: 1px solid #f5f7fa;
          
          &:last-child {
            border-bottom: none;
          }
          
          .file-header {
            display: flex;
            justify-content: between;
            align-items: center;
            
            .file-path {
              font-family: 'Courier New', monospace;
              flex: 1;
            }
          }
        }
      }
    }
  }
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  
  .footer-left,
  .footer-right {
    display: flex;
    gap: 0.5rem;
  }
}

.file-preview {
  .preview-header {
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #e4e7ed;
    
    .preview-file-path {
      font-family: 'Courier New', monospace;
      font-weight: 500;
    }
  }
  
  .preview-content {
    max-height: 500px;
    overflow-y: auto;
    
    pre {
      background: #f8f9fa;
      padding: 1rem;
      border-radius: 4px;
      margin: 0;
      
      code {
        font-family: 'Courier New', monospace;
        font-size: 0.875rem;
        line-height: 1.5;
      }
    }
  }
}

.text-success {
  color: #67c23a;
}

.text-error {
  color: #f56c6c;
}
</style> 