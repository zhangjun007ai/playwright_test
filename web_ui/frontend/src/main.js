import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import 'element-plus/dist/index.css'

import App from './App.vue'
import router from './router'

// 导入全局样式
import './styles/index.scss'

const app = createApp(App)

// 配置 Vue 全局属性，抑制某些开发模式警告
app.config.warnHandler = (msg, instance, trace) => {
  // 过滤掉 Element Plus 相关的某些警告
  if (msg.includes('link') && msg.includes('deprecated')) {
    return
  }
  if (msg.includes('ElFormItem') && msg.includes('label')) {
    return
  }
  // 其他警告正常显示
  console.warn(msg, trace)
}

// 注册 Element Plus 图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(createPinia())
app.use(router)

// 配置 Element Plus 全局选项
app.use(ElementPlus, {
  // 配置全局属性
  size: 'default',
  // 禁用某些开发模式下的警告
  namespace: 'el'
})

app.mount('#app')
