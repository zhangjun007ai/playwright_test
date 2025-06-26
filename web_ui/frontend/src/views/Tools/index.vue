<template>
  <div class="tools">
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title gradient-text">
          <el-icon class="title-icon"><Tools /></el-icon>
          工具箱
        </h1>
        <p class="page-subtitle">实用工具与辅助功能</p>
      </div>
    </div>
    
    <div class="tools-content">
      <div class="tools-grid">
        <!-- 代码生成器 -->
        <div class="tool-card sketch-card">
          <div class="tool-icon">
            <el-icon size="48" color="#667eea"><MagicStick /></el-icon>
          </div>
          <div class="tool-info">
            <h3>代码生成器</h3>
            <p>根据 YAML 用例自动生成 pytest 测试代码</p>
          </div>
          <div class="tool-actions">
            <el-button type="primary" @click="generateCode" :loading="generating">
              生成代码
            </el-button>
          </div>
        </div>
        
        <!-- 数据清理 -->
        <div class="tool-card sketch-card">
          <div class="tool-icon">
            <el-icon size="48" color="#00d4aa"><Delete /></el-icon>
          </div>
          <div class="tool-info">
            <h3>数据清理</h3>
            <p>清理测试数据、日志文件和临时文件</p>
          </div>
          <div class="tool-actions">
            <el-button @click="showCleanDialog = true">
              清理数据
            </el-button>
          </div>
        </div>
        
        <!-- 用例导入 -->
        <div class="tool-card sketch-card">
          <div class="tool-icon">
            <el-icon size="48" color="#4facfe"><Upload /></el-icon>
          </div>
          <div class="tool-info">
            <h3>用例导入</h3>
            <p>从 Excel、Postman 等格式导入测试用例</p>
          </div>
          <div class="tool-actions">
            <el-button @click="showImportDialog = true">
              导入用例
            </el-button>
          </div>
        </div>
        
        <!-- 用例导出 -->
        <div class="tool-card sketch-card">
          <div class="tool-icon">
            <el-icon size="48" color="#ffb74d"><Download /></el-icon>
          </div>
          <div class="tool-info">
            <h3>用例导出</h3>
            <p>导出测试用例为 Excel、PDF 等格式</p>
          </div>
          <div class="tool-actions">
            <el-button @click="showExportDialog = true">
              导出用例
            </el-button>
          </div>
        </div>
        
        <!-- 环境检查 -->
        <div class="tool-card sketch-card">
          <div class="tool-icon">
            <el-icon size="48" color="#f093fb"><CircleCheck /></el-icon>
          </div>
          <div class="tool-info">
            <h3>环境检查</h3>
            <p>检查 Python、pytest、allure 等环境依赖</p>
          </div>
          <div class="tool-actions">
            <el-button @click="checkEnvironment" :loading="checking">
              检查环境
            </el-button>
          </div>
        </div>
        
        <!-- 依赖管理 -->
        <div class="tool-card sketch-card">
          <div class="tool-icon">
            <el-icon size="48" color="#ff5722"><Box /></el-icon>
          </div>
          <div class="tool-info">
            <h3>依赖管理</h3>
            <p>管理 Python 包依赖，更新 requirements.txt</p>
          </div>
          <div class="tool-actions">
            <el-button @click="showDependencyDialog = true">
              管理依赖
            </el-button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 数据清理对话框 -->
    <el-dialog v-model="showCleanDialog" title="数据清理" width="500px" center>
      <div class="clean-options">
        <el-checkbox-group id="clean-options" v-model="cleanOptions">
          <el-checkbox id="clean-logs" label="logs">清理日志文件</el-checkbox>
          <el-checkbox id="clean-reports" label="reports">清理测试报告</el-checkbox>
          <el-checkbox id="clean-cache" label="cache">清理缓存文件</el-checkbox>
          <el-checkbox id="clean-temp" label="temp">清理临时文件</el-checkbox>
        </el-checkbox-group>
      </div>
      <template #footer>
        <el-button @click="showCleanDialog = false">取消</el-button>
        <el-button type="danger" @click="cleanData" :loading="cleaning">
          确认清理
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 用例导入对话框 -->
    <el-dialog v-model="showImportDialog" title="用例导入" width="600px" center>
      <el-form :model="importForm" label-width="100px">
        <el-form-item label="导入格式" prop="format" for="import-format">
          <el-radio-group id="import-format" v-model="importFormat">
            <el-radio id="import-excel" label="excel">Excel 文件</el-radio>
            <el-radio id="import-postman" label="postman">Postman Collection</el-radio>
            <el-radio id="import-swagger" label="swagger">Swagger JSON</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="选择文件" prop="file">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :limit="1"
            accept=".xlsx,.json"
            drag
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              将文件拖到此处，或<em>点击上传</em>
            </div>
          </el-upload>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showImportDialog = false">取消</el-button>
        <el-button type="primary" @click="importCases" :loading="importing">
          开始导入
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 用例导出对话框 -->
    <el-dialog v-model="showExportDialog" title="用例导出" width="500px" center>
      <el-form :model="exportForm" label-width="100px">
        <el-form-item label="导出格式" prop="format" for="export-format">
          <el-radio-group id="export-format" v-model="exportFormat">
            <el-radio id="export-excel" label="excel">Excel 文件</el-radio>
            <el-radio id="export-pdf" label="pdf">PDF 文档</el-radio>
            <el-radio id="export-word" label="word">Word 文档</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="导出范围" prop="scope" for="export-scope">
          <el-radio-group id="export-scope" v-model="exportScope">
            <el-radio id="export-all" label="all">全部用例</el-radio>
            <el-radio id="export-module" label="module">按模块导出</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showExportDialog = false">取消</el-button>
        <el-button type="primary" @click="exportCases" :loading="exporting">
          开始导出
        </el-button>
      </template>
    </el-dialog>
    
    <!-- 依赖管理对话框 -->
    <el-dialog v-model="showDependencyDialog" title="依赖管理" width="700px" center>
      <div class="dependency-content">
        <div class="dependency-actions">
          <el-button @click="installDependencies" :loading="installing">
            <el-icon><Download /></el-icon>
            安装依赖
          </el-button>
          <el-button @click="updateDependencies" :loading="updating">
            <el-icon><Refresh /></el-icon>
            更新依赖
          </el-button>
          <el-button @click="generateRequirements">
            <el-icon><DocumentAdd /></el-icon>
            生成 requirements.txt
          </el-button>
        </div>
        
        <div class="dependency-list">
          <h4>当前依赖包</h4>
          <el-table :data="dependencies" style="width: 100%" size="small">
            <el-table-column prop="name" label="包名" />
            <el-table-column prop="version" label="版本" />
            <el-table-column prop="status" label="状态">
              <template #default="{ row }">
                <el-tag :type="row.status === 'installed' ? 'success' : 'warning'" size="small">
                  {{ row.status === 'installed' ? '已安装' : '待安装' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { apiService } from '@/services/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Tools,
  MagicStick,
  Delete,
  Upload,
  Download,
  CircleCheck,
  Box,
  UploadFilled,
  Refresh,
  DocumentAdd
} from '@element-plus/icons-vue'

// 响应式数据
const generating = ref(false)
const checking = ref(false)
const cleaning = ref(false)
const importing = ref(false)
const exporting = ref(false)
const installing = ref(false)
const updating = ref(false)

const showCleanDialog = ref(false)
const showImportDialog = ref(false)
const showExportDialog = ref(false)
const showDependencyDialog = ref(false)

const cleanOptions = ref(['logs'])

// 表单数据模型
const importForm = ref({
  format: 'excel',
  file: null
})

const exportForm = ref({
  format: 'excel',
  scope: 'all'
})

// 保持向后兼容的响应式变量
const importFormat = computed({
  get: () => importForm.value.format,
  set: (value) => { importForm.value.format = value }
})

const exportFormat = computed({
  get: () => exportForm.value.format,
  set: (value) => { exportForm.value.format = value }
})

const exportScope = computed({
  get: () => exportForm.value.scope,
  set: (value) => { exportForm.value.scope = value }
})

const uploadRef = ref()

// 依赖包列表
const dependencies = ref([
  { name: 'pytest', version: '7.1.3', status: 'installed' },
  { name: 'allure-pytest', version: '2.9.45', status: 'installed' },
  { name: 'requests', version: '2.26.0', status: 'installed' },
  { name: 'PyYAML', version: '6.0.2', status: 'installed' },
  { name: 'jsonpath', version: '0.82', status: 'installed' }
])

// 方法
const generateCode = async () => {
  try {
    generating.value = true
    await apiService.generateCode()
    ElMessage.success('代码生成成功')
  } catch (error) {
    console.error('代码生成失败:', error)
  } finally {
    generating.value = false
  }
}

const checkEnvironment = async () => {
  try {
    checking.value = true
    // 模拟环境检查
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessageBox.alert(
      `
      Python: ✅ 3.10.18
      pytest: ✅ 7.1.3
      allure: ✅ 2.9.45
      依赖包: ✅ 全部已安装
      `,
      '环境检查结果',
      {
        confirmButtonText: '确定',
        type: 'success'
      }
    )
  } catch (error) {
    ElMessage.error('环境检查失败')
  } finally {
    checking.value = false
  }
}

const cleanData = async () => {
  try {
    cleaning.value = true
    // 模拟数据清理
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    ElMessage.success(`已清理: ${cleanOptions.value.join(', ')}`)
    showCleanDialog.value = false
    cleanOptions.value = ['logs']
  } catch (error) {
    ElMessage.error('数据清理失败')
  } finally {
    cleaning.value = false
  }
}

const importCases = async () => {
  try {
    importing.value = true
    // 模拟用例导入
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    ElMessage.success(`从 ${importFormat.value} 格式导入用例成功`)
    showImportDialog.value = false
  } catch (error) {
    ElMessage.error('用例导入失败')
  } finally {
    importing.value = false
  }
}

const exportCases = async () => {
  try {
    exporting.value = true
    // 模拟用例导出
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    ElMessage.success(`导出为 ${exportFormat.value} 格式成功`)
    showExportDialog.value = false
  } catch (error) {
    ElMessage.error('用例导出失败')
  } finally {
    exporting.value = false
  }
}

const installDependencies = async () => {
  try {
    installing.value = true
    await new Promise(resolve => setTimeout(resolve, 3000))
    ElMessage.success('依赖安装成功')
  } catch (error) {
    ElMessage.error('依赖安装失败')
  } finally {
    installing.value = false
  }
}

const updateDependencies = async () => {
  try {
    updating.value = true
    await new Promise(resolve => setTimeout(resolve, 2500))
    ElMessage.success('依赖更新成功')
  } catch (error) {
    ElMessage.error('依赖更新失败')
  } finally {
    updating.value = false
  }
}

const generateRequirements = () => {
  ElMessage.success('requirements.txt 生成成功')
}
</script>

<style lang="scss" scoped>
.tools {
  padding: $spacing-lg;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.page-header {
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
}

.tools-content {
  flex: 1;
  overflow-y: auto;
}

.tools-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: $spacing-lg;
}

.tool-card {
  padding: $spacing-lg;
  text-align: center;
  transition: transform $transition-normal;
  
  &:hover {
    transform: translateY(-4px);
  }
  
  .tool-icon {
    margin-bottom: $spacing-md;
  }
  
  .tool-info {
    margin-bottom: $spacing-lg;
    
    h3 {
      color: $text-primary;
      margin: 0 0 $spacing-sm 0;
      font-size: $font-size-lg;
    }
    
    p {
      color: $text-secondary;
      margin: 0;
      font-size: $font-size-sm;
      line-height: 1.5;
    }
  }
  
  .tool-actions {
    display: flex;
    justify-content: center;
  }
}

.clean-options {
  padding: $spacing-md 0;
  
  .el-checkbox {
    display: block;
    margin-bottom: $spacing-sm;
  }
}

.dependency-content {
  .dependency-actions {
    display: flex;
    gap: $spacing-sm;
    margin-bottom: $spacing-lg;
    flex-wrap: wrap;
  }
  
  .dependency-list {
    h4 {
      color: $text-primary;
      margin: 0 0 $spacing-md 0;
    }
  }
}
</style>
