# GitHub 发布指南

## 推送到 GitHub

### 步骤 1：创建 GitHub 仓库

1. 访问 [GitHub](https://github.com)
2. 点击右上角的 "+" → "New repository"
3. 填写仓库信息：
   - **Repository name**: `knowit`
   - **Description**: `个人知识库管理工具 - 优雅地收集、组织和搜索网页内容`
   - **Visibility**: Public 或 Private
   - **不要**勾选 "Add a README file"（我们已经有了）
   - **不要**勾选 "Add .gitignore"
   - **不要**勾选 "Choose a license"（稍后添加）

4. 点击 "Create repository"

### 步骤 2：推送代码到 GitHub

创建仓库后，GitHub 会显示快速设置页面。选择 "push an existing repository from the command line" 部分：

```bash
# 添加远程仓库（替换 YOUR_USERNAME 为你的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/knowit.git

# 推送到 GitHub
git branch -M main
git push -u origin main
```

### 步骤 3：验证

访问你的仓库页面（如 `https://github.com/YOUR_USERNAME/knowit`），应该能看到：
- README.md 显示在首页
- 所有源代码文件
- 提交历史

### 步骤 4：添加 License（推荐）

1. 在仓库页面点击 "Create new file"
2. 文件名填：`LICENSE`
3. 选择 "MIT License"
4. 点击 "Review and commit"
5. 点击 "Commit new file"

### 步骤 5：添加仓库 Topics

在仓库页面右侧：
1. 点击 "Settings" 标签
2. 找到 "Topics" 部分
3. 添加以下 tags：
   - `knowledge-management`
   - `cli`
   - `python`
   - `web-scraping`
   - `personal-knowledge-base`
   - `note-taking`
   - `search`

### 步骤 6：完善仓库信息

#### 添加仓库描述（如果创建时未填写）

1. 点击仓库页面的 "⚙️ Settings"
2. 在 "Description" 填写：
   ```
   个人知识库管理工具 - 优雅地收集、组织和搜索网页内容
   ```
3. 在 "Website" 填写（可选）：
   ```
   https://github.com/YOUR_USERNAME/knowit
   ```

#### 设置仓库可见性

1. 在 Settings → General → Danger Zone
2. 点击 "Change visibility"
3. 选择 Public 或 Private

## 后续操作

### 发布新版本

```bash
# 更新版本号
# 编辑 pyproject.toml 中的 version = "x.y.z"

# 创建 git tag
git tag -a v0.1.0 -m "Release v0.1.0: Initial release"

# 推送 tag
git push origin v0.1.0

# 或者推送所有 tags
git push origin --tags
```

### 创建 GitHub Release

1. 访问仓库页面
2. 点击 "Releases" → "Create a new release"
3. 选择 tag：`v0.1.0`
4. Release title：`v0.1.0 - Initial Release`
5. 描述内容：
   ```markdown
   ## 功能特性

   - 智能内容抓取（网页、微信公众号文章）
   - Simhash 去重算法
   - 全文搜索与多条件筛选
   - 标签和合集管理
   - Kami 设计系统导出（HTML/PDF）
   - 数据备份与恢复

   ## 安装

   ```bash
   pip install git+https://github.com/YOUR_USERNAME/knowit.git
   ```

   ## 快速开始

   ```bash
   # 初始化数据库
   kv init

   # 添加内容
   kv add https://example.com

   # 搜索
   kv search "关键词"
   ```
   ```
6. 勾选 "Set as the latest release"
7. 点击 "Publish release"

## 仓库 URL 更新

完成上述步骤后，记得更新以下文件中的 URL：

### README.md

将以下内容：
```markdown
git clone https://github.com/yourusername/knowit.git
```

替换为：
```markdown
git clone https://github.com/YOUR_USERNAME/knowit.git
```

### pyproject.toml

确保 `project.urls` 部分正确：
```toml
[project.urls]
Homepage = "https://github.com/YOUR_USERNAME/knowit"
Repository = "https://github.com/YOUR_USERNAME/knowit"
Issues = "https://github.com/YOUR_USERNAME/knowit/issues"
```

## 发布到 PyPI（可选）

如果想将包发布到 PyPI：

```bash
# 安装构建工具
pip install build twine

# 构建
python -m build

# 上传到 PyPI（测试环境）
python -m twine upload --repository testpypi dist/*

# 上传到 PyPI（生产环境）
python -m twine upload dist/*
```

## 注意事项

1. **敏感信息**：确保没有提交敏感信息（密码、API keys 等）
2. **.gitignore**：检查 `.gitignore` 是否正确配置
3. **大文件**：GitHub 有 100MB 单文件限制
4. **依赖**：确保 `requirements.txt` 和 `pyproject.toml` 完整

## 常见问题

### 推送失败：Authentication failed

```bash
# 使用 SSH 代替 HTTPS
git remote set-url origin git@github.com:YOUR_USERNAME/knowit.git
```

### 推送失败：remote rejected

```bash
# 强制推送（谨慎使用）
git push -f origin main
```

### 更新远程仓库信息

```bash
# 查看当前远程仓库
git remote -v

# 更新远程仓库 URL
git remote set-url origin https://github.com/YOUR_USERNAME/knowit.git
```

## 下一步

- 完善 CI/CD（GitHub Actions）
- 添加更多测试
- 编写使用文档
- 创建示例视频
- 发布到 PyPI

---

祝你发布顺利！🎉
