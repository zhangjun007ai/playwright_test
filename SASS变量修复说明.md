# SASS变量修复说明

## 问题描述

在前端编译过程中遇到了SASS变量未定义的错误：

```
[plugin:vite:css] [sass] Undefined variable.
border-radius: $sketch-radius-lg;
```

错误位置：`web_ui/frontend/src/views/TestCases/CreateWizard.vue`

## 问题原因

在`CreateWizard.vue`文件中使用了以下SASS变量，但这些变量在`variables.scss`文件中没有定义：

- `$sketch-radius-lg`
- `$sketch-shadow-md` 
- `$sketch-shadow-lg`

## 修复方案

### 1. 添加缺失的变量定义

在 `web_ui/frontend/src/styles/variables.scss` 文件的"手绘风格"部分添加了以下变量：

```scss
// 手绘风格
$sketch-border: 2px solid $primary-color;
$sketch-radius: 8px;
$sketch-radius-lg: 12px;              // 新增
$sketch-shadow: 0 3px 15px rgba(102, 126, 234, 0.2);
$sketch-shadow-md: 0 4px 20px rgba(102, 126, 234, 0.15);  // 新增
$sketch-shadow-lg: 0 6px 30px rgba(102, 126, 234, 0.25);  // 新增
```

### 2. 变量含义说明

- `$sketch-radius-lg`: 大尺寸圆角半径，用于卡片和容器
- `$sketch-shadow-md`: 中等强度阴影效果
- `$sketch-shadow-lg`: 强阴影效果，用于突出显示

### 3. 自动检测工具

创建了 `fix_sass_variables.bat` 脚本，可以：
- 自动检测变量文件是否存在
- 检查常用变量是否已定义
- 运行编译测试验证修复效果

## 使用说明

### 手动修复
直接编辑 `web_ui/frontend/src/styles/variables.scss` 文件，添加缺失的变量定义。

### 自动检测
运行 `fix_sass_variables.bat` 脚本进行自动检测和验证。

## 验证修复

修复完成后，运行以下命令验证：

```bash
cd web_ui/frontend
npm run dev
```

如果没有SASS编译错误，说明修复成功。

## 预防措施

1. **变量规范**: 在使用新的SASS变量前，确保在 `variables.scss` 中定义
2. **命名约定**: 遵循现有的变量命名规范
3. **编译测试**: 每次添加新样式后运行编译测试

## 相关文件

- 变量定义：`web_ui/frontend/src/styles/variables.scss`
- 使用位置：`web_ui/frontend/src/views/TestCases/CreateWizard.vue`
- 检测工具：`fix_sass_variables.bat`

## 修复历史

- **2024-12-30**: 修复 `$sketch-radius-lg`、`$sketch-shadow-md`、`$sketch-shadow-lg` 变量未定义问题
- **版本**: v1.0
- **状态**: ✅ 已解决 