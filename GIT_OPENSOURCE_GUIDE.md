# Git 开源发布指南

## 🚀 快速开始

### 前提条件
- 已安装 Git（[下载地址](https://git-scm.com/downloads)）
- 有 GitHub 或 Gitee 账号

---

## 📋 方式一：发布到 GitHub（推荐国际用户）

### 步骤 1：在 GitHub 创建仓库

1. 访问 [https://github.com/new](https://github.com/new)
2. 填写仓库信息：
   - **Repository name**: `perfetto-trace-analyzer`
   - **Description**: `A powerful Android Perfetto trace analyzer for CPU/GPU performance metrics`
   - **Public** (公开) 或 **Private** (私有)
   - ❌ 不要勾选 "Add a README file"（我们已经有了）
   - ❌ 不要勾选 "Add .gitignore"（我们已经有了）
   - ✅ 选择 License: MIT License（推荐）
3. 点击 **Create repository**

### 步骤 2：本地初始化 Git 仓库

打开命令行，执行：

```bash
# 进入项目目录
cd D:\new\hangguan\cpu\perfettotrace\perfettotrace

# 初始化 Git 仓库
git init

# 配置用户信息（如果还没配置过）
git config user.name "你的名字"
git config user.email "你的邮箱@example.com"

# 查看将要提交的文件（.gitignore 会自动排除中间文件）
git status

# 添加所有文件
git add .

# 提交
git commit -m "Initial release v1.0 - Perfetto Trace Analyzer"
```

### 步骤 3：推送到 GitHub

```bash
# 添加远程仓库（替换成你的 GitHub 用户名）
git remote add origin https://github.com/你的用户名/perfetto-trace-analyzer.git

# 设置主分支名称
git branch -M main

# 推送代码
git push -u origin main
```

如果提示需要登录，输入你的 GitHub 用户名和密码（或 Personal Access Token）。

### 步骤 4：创建 Release 版本

在 GitHub 网页上：

1. 进入你的仓库页面
2. 点击右侧 **Releases** → **Create a new release**
3. 填写信息：
   - **Tag version**: `v1.0`
   - **Release title**: `Perfetto Trace Analyzer v1.0`
   - **Description**: 
     ```markdown
     ## 🎉 首次发布
     
     ### 功能特性
     - CPU MCPS 分析
     - GPU 频率跟踪
     - SurfaceFlinger GPU 合成分析
     - 批量处理支持
     - Excel 报告生成
     
     ### 安装说明
     详见 [README.md](README.md)
     ```
4. 可选：上传 `PerfettoTraceAnalyzer_v1.0_Source.zip` 作为附件
5. 点击 **Publish release**

---

## 📋 方式二：发布到 Gitee（推荐国内用户）

### 步骤 1：在 Gitee 创建仓库

1. 访问 [https://gitee.com/projects/new](https://gitee.com/projects/new)
2. 填写仓库信息：
   - **仓库名称**: `perfetto-trace-analyzer`
   - **仓库介绍**: `Android Perfetto trace 性能分析工具，支持 CPU/GPU 指标分析`
   - **是否开源**: 选择 "开源"
   - **开源许可证**: 选择 "MIT License"
   - ❌ 不要勾选 "使用 Readme 文件初始化这个仓库"
   - ❌ 不要勾选 ".gitignore"
3. 点击 **创建**

### 步骤 2：本地初始化 Git 仓库

```bash
# 进入项目目录
cd D:\new\hangguan\cpu\perfettotrace\perfettotrace

# 初始化 Git 仓库
git init

# 配置用户信息
git config user.name "你的名字"
git config user.email "你的邮箱@example.com"

# 添加所有文件
git add .

# 提交
git commit -m "Initial release v1.0 - Perfetto Trace Analyzer"
```

### 步骤 3：推送到 Gitee

```bash
# 添加远程仓库（替换成你的 Gitee 用户名）
git remote add origin https://gitee.com/你的用户名/perfetto-trace-analyzer.git

# 推送代码
git push -u origin master
```

### 步骤 4：创建发行版

在 Gitee 网页上：

1. 进入你的仓库页面
2. 点击 **发行版** → **创建发行版**
3. 填写信息：
   - **标签名称**: `v1.0`
   - **发行版标题**: `Perfetto Trace Analyzer v1.0`
   - **发行版描述**: 
     ```markdown
     ## 首次发布
     
     ### 功能特性
     - CPU MCPS 分析
     - GPU 频率跟踪
     - SurfaceFlinger GPU 合成分析
     - 批量处理支持
     - Excel 报告生成
     ```
4. 上传 `PerfettoTraceAnalyzer_v1.0_Source.zip`
5. 点击 **发布**

---

## 📋 方式三：同时发布到 GitHub 和 Gitee

### 添加多个远程仓库

```bash
# 添加 GitHub
git remote add github https://github.com/你的用户名/perfetto-trace-analyzer.git

# 添加 Gitee
git remote add gitee https://gitee.com/你的用户名/perfetto-trace-analyzer.git

# 推送到 GitHub
git push -u github main

# 推送到 Gitee
git push -u gitee master
```

### 后续更新时同时推送

```bash
# 修改代码后
git add .
git commit -m "更新说明"

# 同时推送到两个平台
git push github main
git push gitee master
```

---

## 🔧 常见问题

### Q1: 提示 "fatal: not a git repository"

**A:** 确保在项目根目录执行 `git init`

### Q2: 推送时提示 "Permission denied"

**A:** 
- GitHub: 需要配置 Personal Access Token
  1. GitHub 设置 → Developer settings → Personal access tokens → Generate new token
  2. 勾选 `repo` 权限
  3. 使用 token 作为密码
  
- Gitee: 使用账号密码或配置 SSH 密钥

### Q3: 如何配置 SSH 密钥（避免每次输入密码）

```bash
# 生成 SSH 密钥
ssh-keygen -t rsa -C "你的邮箱@example.com"

# 查看公钥
cat ~/.ssh/id_rsa.pub

# 复制公钥内容，添加到 GitHub/Gitee 的 SSH Keys 设置中
```

然后使用 SSH 地址：
```bash
# GitHub
git remote set-url origin git@github.com:你的用户名/perfetto-trace-analyzer.git

# Gitee
git remote set-url origin git@gitee.com:你的用户名/perfetto-trace-analyzer.git
```

### Q4: 不小心提交了敏感信息怎么办？

```bash
# 从历史记录中删除文件
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch 敏感文件路径" \
  --prune-empty --tag-name-filter cat -- --all

# 强制推送
git push origin --force --all
```

### Q5: 如何忽略已经提交的文件？

```bash
# 从 Git 跟踪中移除（但保留本地文件）
git rm --cached 文件名

# 添加到 .gitignore
echo "文件名" >> .gitignore

# 提交更改
git add .gitignore
git commit -m "Update .gitignore"
git push
```

---

## 📝 后续维护

### 更新代码

```bash
# 修改代码后
git add .
git commit -m "描述你的修改"
git push
```

### 创建新版本

```bash
# 打标签
git tag -a v1.1 -m "Release version 1.1"
git push origin v1.1

# 在 GitHub/Gitee 网页上创建对应的 Release
```

### 查看提交历史

```bash
git log --oneline --graph --all
```

### 回退到之前的版本

```bash
# 查看历史
git log

# 回退到指定版本（保留修改）
git reset --soft 提交ID

# 回退到指定版本（丢弃修改）
git reset --hard 提交ID
```

---

## 🎯 推荐的 Git 工作流

### 日常开发

```bash
# 1. 创建功能分支
git checkout -b feature/新功能名称

# 2. 开发并提交
git add .
git commit -m "添加新功能"

# 3. 合并到主分支
git checkout main
git merge feature/新功能名称

# 4. 推送
git push
```

### 修复 Bug

```bash
# 1. 创建修复分支
git checkout -b fix/bug描述

# 2. 修复并提交
git add .
git commit -m "修复: bug描述"

# 3. 合并并推送
git checkout main
git merge fix/bug描述
git push
```

---

## 📚 Git 命令速查表

| 命令 | 说明 |
|------|------|
| `git init` | 初始化仓库 |
| `git status` | 查看状态 |
| `git add .` | 添加所有文件 |
| `git commit -m "消息"` | 提交 |
| `git push` | 推送到远程 |
| `git pull` | 拉取远程更新 |
| `git clone URL` | 克隆仓库 |
| `git branch` | 查看分支 |
| `git checkout -b 分支名` | 创建并切换分支 |
| `git merge 分支名` | 合并分支 |
| `git log` | 查看历史 |
| `git tag v1.0` | 创建标签 |

---

## ✅ 开源检查清单

发布前确认：

- [ ] 删除了所有敏感信息（密码、密钥、个人路径等）
- [ ] .gitignore 配置正确
- [ ] README.md 文档完整
- [ ] 选择了合适的开源许可证
- [ ] 代码可以正常运行
- [ ] 添加了使用示例
- [ ] 提供了安装说明

---

**现在可以开始开源了！选择 GitHub 或 Gitee，按照上面的步骤操作即可。** 🎉

