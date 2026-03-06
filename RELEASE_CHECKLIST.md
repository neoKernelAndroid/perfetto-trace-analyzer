# 发布清单 - Perfetto Trace Analyzer

## 📋 发布前检查清单

### 1. 清理中间文件
- [ ] 删除所有 `__pycache__` 目录
- [ ] 删除 `build/` 和 `dist/` 目录
- [ ] 删除 `*.pyc` 文件
- [ ] 删除 `logs/` 目录下的日志文件
- [ ] 删除 `output/` 目录下的测试输出

### 2. 验证核心文件
- [ ] `modules/` 目录完整
- [ ] `configs/` 配置文件存在
- [ ] 批处理脚本可执行
- [ ] README.md 文档完整
- [ ] requirements.txt 依赖清单

### 3. 测试功能
- [ ] 运行 `INSTALL.bat` 成功
- [ ] 运行 `verify_installation.bat` 通过
- [ ] 测试单个 trace 分析
- [ ] 测试批量分析
- [ ] 检查 Excel 输出正确

---

## 🚀 发布步骤

### 方式一：使用打包脚本（推荐）

```bash
# 1. 运行打包脚本
BUILD_SOURCE_RELEASE.bat

# 2. 检查输出
# - D:\pac\PerfettoTraceAnalyzer_v1.0_Source\  (目录)
# - D:\pac\PerfettoTraceAnalyzer_v1.0_Source.zip  (压缩包)

# 3. 测试发布包
cd D:\test
tar -x -f D:\pac\PerfettoTraceAnalyzer_v1.0_Source.zip
cd PerfettoTraceAnalyzer_v1.0_Source
verify_installation.bat
```

### 方式二：Git 开源发布

#### 初始化 Git 仓库

```bash
cd D:\new\hangguan\cpu\perfettotrace\perfettotrace

# 初始化仓库
git init

# 添加文件（.gitignore 会自动排除中间文件）
git add .

# 提交
git commit -m "Initial release v1.0"
```

#### 推送到 GitHub/Gitee

```bash
# 创建远程仓库后
git remote add origin https://github.com/yourusername/perfetto-trace-analyzer.git
git branch -M main
git push -u origin main

# 创建 release tag
git tag -a v1.0 -m "Release version 1.0"
git push origin v1.0
```

---

## 📦 发布包内容

### 包含的文件

**核心模块**
- `modules/common/` - 通用工具
- `modules/PerfettoSql/` - Perfetto SQL 接口
- `modules/services/` - 分析服务
- `modules/TraceHtml/` - HTML trace 处理

**主程序**
- `run_gpu_analysis.py`
- `export_thread_count_to_excel.py`
- `download_trace_processor.py`

**批处理脚本**
- `INSTALL.bat` - 安装脚本
- `verify_installation.bat` - 验证脚本
- `setup_trace_processor.bat` - 下载 trace_processor
- `run_cpu_gpu_analysis_quick.bat` - 快速分析
- `batch_analyze_all_traces_cpu_gpu.bat` - 批量分析

**配置文件**
- `configs/mcps_config.json`
- `configs/config_open_transition.json`

**文档**
- `README.md` - 主文档
- `requirements.txt` - 依赖清单
- `DEPLOYMENT_GUIDE.md` - 部署指南（如果有）
- `COMPLETE_GUIDE.md` - 完整指南

### 排除的文件（已在 .gitignore）

**构建产物**
- `build/`
- `dist/`
- `__pycache__/`
- `*.pyc`

**调试脚本**
- `test_*.py`
- `check_*.py`
- `diagnose_*.py`
- `debug_*.py`
- `fix_*.py`
- `analyze_gpu_data.py`
- `verify_excel*.py`

**临时文件**
- `logs/`
- `output/*.xls`
- `*.log`
- Trace 文件 (`*.html`, `*.perfetto-trace`)

**文档草稿**
- `Mali_GPU_Metrics*.md`
- `*_INTEGRATION_*.md`
- `SF_INTEGRATION_README.txt`

---

## 📝 用户使用说明

### 安装步骤

1. **下载发布包**
   - 从 GitHub Releases 下载 ZIP
   - 或克隆仓库：`git clone https://github.com/yourusername/perfetto-trace-analyzer.git`

2. **解压并安装**
   ```bash
   unzip PerfettoTraceAnalyzer_v1.0_Source.zip
   cd PerfettoTraceAnalyzer_v1.0_Source
   INSTALL.bat
   ```

3. **验证安装**
   ```bash
   verify_installation.bat
   ```

### 快速开始

```bash
# 1. 复制 trace 文件到工具目录
copy "path\to\trace.html" .

# 2. 编辑配置（可选）
notepad configs\mcps_config.json

# 3. 运行分析
run_cpu_gpu_analysis_quick.bat

# 4. 查看输出
# Excel 文件在当前目录生成
```

---

## 🌐 开源发布建议

### GitHub 仓库设置

**仓库名称**: `perfetto-trace-analyzer`

**描述**: 
```
A powerful Android Perfetto trace analyzer for CPU/GPU performance metrics, 
thread analysis, and SurfaceFlinger composition statistics.
```

**Topics/Tags**:
- `perfetto`
- `android`
- `performance-analysis`
- `cpu-analysis`
- `gpu-analysis`
- `trace-analysis`
- `python`

**README 徽章**（可选）:
```markdown
![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
```

### 许可证选择

**MIT License**（推荐，最宽松）
- 允许商业使用
- 允许修改和分发
- 仅需保留版权声明

**Apache 2.0**（专利保护）
- 类似 MIT，但提供专利授权
- 适合企业使用

**GPL v3**（强制开源）
- 衍生作品必须开源
- 适合纯开源项目

### 创建 Release

在 GitHub 上创建 Release：

1. 进入仓库 → Releases → Create a new release
2. Tag: `v1.0`
3. Title: `Perfetto Trace Analyzer v1.0`
4. 描述：
   ```markdown
   ## Features
   - CPU MCPS analysis
   - GPU frequency tracking
   - SurfaceFlinger GPU composition analysis
   - Batch processing support
   - Excel report generation
   
   ## Installation
   See [README.md](README.md) for installation instructions.
   
   ## Downloads
   - Source code (zip)
   - Source code (tar.gz)
   ```
5. 上传 `PerfettoTraceAnalyzer_v1.0_Source.zip`

---

## 🔧 维护建议

### 版本管理

使用语义化版本：`MAJOR.MINOR.PATCH`

- `MAJOR`: 不兼容的 API 变更
- `MINOR`: 新功能，向后兼容
- `PATCH`: 问题修复

### 更新流程

1. 修改代码
2. 更新 `README.md` 的 Changelog
3. 更新版本号
4. 提交并打 tag
5. 创建新的 Release

### 文档维护

- 保持 README.md 更新
- 添加使用示例
- 记录已知问题
- 提供故障排除指南

---

## ✅ 发布检查表

### 发布前
- [ ] 代码测试通过
- [ ] 文档完整准确
- [ ] .gitignore 配置正确
- [ ] requirements.txt 完整
- [ ] 删除敏感信息（如个人路径）

### 发布时
- [ ] 运行 `BUILD_SOURCE_RELEASE.bat`
- [ ] 测试发布包功能
- [ ] 创建 Git tag
- [ ] 推送到远程仓库
- [ ] 创建 GitHub Release

### 发布后
- [ ] 验证下载链接
- [ ] 测试用户安装流程
- [ ] 收集用户反馈
- [ ] 准备下一版本计划

---

## 📞 支持渠道

- **Issues**: GitHub Issues 页面
- **Discussions**: GitHub Discussions（可选）
- **Email**: 提供技术支持邮箱
- **Wiki**: 详细文档和教程

---

**现在可以执行发布了！** 🎉

选择发布方式：
1. 运行 `BUILD_SOURCE_RELEASE.bat` 生成发布包
2. 或使用 `git init` 开始 Git 版本控制

