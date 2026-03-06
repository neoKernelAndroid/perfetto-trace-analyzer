# Git 提交文件清单

## ✅ 将被提交的文件（核心源码和关键脚本）

### 📁 核心 Python 源码
```
modules/
├── __init__.py
├── common/
│   ├── __init__.py
│   ├── Excel.py
│   ├── Logger.py
│   ├── Path.py
│   └── Utils.py
├── PerfettoSql/
│   ├── __init__.py
│   ├── PerfettoSqlCommon.py
│   └── TraceObj.py
├── services/
│   ├── __init__.py
│   ├── ContinusOpenTransitionPerformance.py
│   ├── Performacne.py
│   └── TraceProcessor.py
└── TraceHtml/
    ├── __init__.py
    ├── SurfaceFlingerAnalysis.py
    └── TraceHtmlCpuMcps.py
```

### 📄 主程序文件
```
run_gpu_analysis.py
export_thread_count_to_excel.py
download_trace_processor.py
run_mcps_analysis.py
run_surfaceflinger_analysis.py
```

### 🔧 关键批处理脚本
```
INSTALL.bat                          # 安装脚本
install_dependencies.bat             # 依赖安装
setup_trace_processor.bat            # 下载 trace_processor
run_cpu_gpu_analysis_quick.bat       # CPU/GPU 快速分析
run_click_to_settings.bat            # 点击到设置分析
run_openApp_Window.bat               # 打开应用分析
run_surfaceflinger_analysis.bat      # SurfaceFlinger 分析
batch_analyze_all_traces_cpu_gpu.bat # 批量分析
verify_installation.bat              # 验证安装
INIT_GIT.bat                         # Git 初始化脚本
```

### ⚙️ 配置文件
```
configs/
├── mcps_config.json
├── config_open_transition.json
└── LAUNCHER_APP_SWIPE_TO_RECENTS.json
```

### 📚 文档
```
README.md                    # 主文档
requirements.txt             # Python 依赖
.gitignore                   # Git 忽略规则
GIT_OPENSOURCE_GUIDE.md      # Git 开源指南
RELEASE_CHECKLIST.md         # 发布检查清单
```

### 📁 空目录（结构）
```
tools/          # trace_processor.exe 存放位置（用户自行下载）
output/         # 分析输出目录
logs/           # 日志目录
```

---

## ❌ 将被排除的文件（不提交）

### 🔨 构建产物
```
build/                       # PyInstaller 构建目录
dist/                        # 编译后的 exe 文件
*.spec                       # PyInstaller 配置
*.exe                        # 可执行文件
```

### 🐛 调试和测试脚本
```
test_*.py                    # 所有测试脚本
check_*.py                   # 所有检查脚本
diagnose_*.py                # 所有诊断脚本
debug_*.py                   # 所有调试脚本
fix_*.py                     # 所有修复脚本
analyze_*.py                 # 分析脚本
verify_*.py                  # 验证脚本
integrate_*.py               # 集成脚本
monitor_*.py                 # 监控脚本
analyse_trace.py             # 旧版分析脚本
start_analyse_mcps.py        # 旧版启动脚本
```

### 📝 文档草稿
```
COMPLETE_GUIDE.md                                    # 完整指南（内部用）
SURFACEFLINGER_ANALYSIS_README.md                    # 草稿文档
SURFACEFLINGER_INTEGRATION_GUIDE.md                  # 集成指南草稿
SF_INTEGRATION_README.txt                            # 集成说明草稿
Mali_GPU_Metrics实际代码分析_中断调用和进程关联.md
Mali_GPU_Metrics详解_进程关联和时间戳问题.md
如何查找kbase_gpu_metrics_ctx_end_activity.md
查找kbase_gpu_metrics_ctx_end_activity的实际步骤.md
```

### 🗑️ 临时文件
```
logs/                        # 日志目录
output/                      # 输出文件
*.log                        # 日志文件
*.xls, *.xlsx               # Excel 输出
tmp/                         # 临时目录
testResult/                  # 测试结果
result/                      # 结果目录
```

### 📦 Trace 文件（太大）
```
*.html                       # HTML trace 文件
*.perfetto-trace            # Perfetto trace 文件
*.pftrace                   # Trace 文件
```

### 🔧 临时批处理脚本
```
run_test.bat                 # 测试脚本
run_analysis_simple.bat      # 简单分析脚本
verify_installation_source.bat  # 源码验证脚本
BUILD_SOURCE_RELEASE.bat     # 打包脚本（内部用）
```

---

## 📊 统计

### 将提交的文件数量
- Python 源码: ~18 个文件
- 批处理脚本: ~11 个文件
- 配置文件: 3 个文件
- 文档: 5 个文件
- **总计: 约 37 个核心文件**

### 排除的文件数量
- 调试/测试脚本: ~30+ 个文件
- 构建产物: build/, dist/ 目录
- 文档草稿: ~8 个文件
- 临时文件: logs/, output/ 等
- **总计: 排除 50+ 个非核心文件**

---

## 🎯 验证命令

在提交前，可以使用以下命令查看将要提交的文件：

```bash
# 查看将要提交的文件列表
git status

# 查看将要提交的文件（简洁模式）
git status --short

# 查看被忽略的文件
git status --ignored

# 模拟添加，查看哪些文件会被添加
git add --dry-run .
```

---

## ✅ 确认无误后执行

```bash
# 添加文件
git add .

# 查看暂存的文件
git status

# 提交
git commit -m "Initial release v1.0 - Perfetto Trace Analyzer"
```

---

**现在 .gitignore 已更新，只会提交核心源码和关键脚本！**

