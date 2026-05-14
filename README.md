# KnowIt

<div align="center">

**个人知识库管理工具**

优雅地收集、组织和搜索网页内容

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Based on Kami](https://img.shields.io/badge/Design-Kami-important)](https://github.com/tw93/Kami)

[功能特性](#特性) • [快速开始](#快速开始) • [使用指南](#使用指南) • [开发文档](#开发)

</div>

---

<div align="center">

**设计灵感**：基于 [Kami](https://github.com/tw93/Kami) 的优雅设计系统和 [clip-to-kami](https://github.com/Anarcadia/clip-to-kami) 的内容转换实现

</div>

---

## 简介

KnowIt 是一个命令行工具，用于收集、组织和搜索网页内容。它帮助你构建个人知识库，支持智能去重、全文搜索和精美导出。

### 为什么选择 KnowIt？

- **本地优先**：所有数据存储在本地，完全掌控你的知识库
- **智能去重**：基于 simhash 算法自动检测相似和重复内容
- **灵活组织**：支持标签和层级化合集，轻松管理大量内容
- **精美导出**：采用 [Kami](https://github.com/tw93/Kami) 设计系统，输出专业级 HTML/PDF
- **命令行友好**：简洁高效的 CLI，适合工作流集成

### 设计灵感

KnowIt 的设计灵感来源于以下优秀项目：

- 🎨 **[Kami](https://github.com/tw93/Kami)** - 采用其温暖优雅的设计系统
- 📄 **[clip-to-kami](https://github.com/Anarcadia/clip-to-kami)** - 参考其内容转换实现

## 特性

### 核心功能

- **智能内容抓取**
  - 支持静态网页和微信公众号文章
  - 自动提取标题、作者、正文内容
  - 智能处理图片和代码块

- **智能去重**
  - 基于 simhash 算法的相似度检测
  - 可配置的去重阈值
  - 支持手动合并相似内容

- **强大搜索**
  - 全文搜索支持
  - 按状态、标签、合集筛选
  - 按作者、日期范围过滤

- **灵活组织**
  - 标签系统：多标签支持，便于分类
  - 合集系统：层级化组织，结构清晰
  - 状态管理：inbox、archived、starred、merged

- **自动导出**
  - 添加知识后自动生成 HTML 和 PDF
  - 按合集自动组织文件结构
  - 类似 Obsidian 的知识管理体验

- **精美导出**
  - Kami 设计系统：专业排版
  - HTML/PDF 双格式支持
  - 内容清理：移除冗余代码
  - 可选封面页

- **数据安全**
  - 自动备份功能
  - 一键恢复数据
  - 本地 SQLite 数据库

- **测试覆盖**
  - 17+ 单元测试覆盖核心功能
  - 持续集成质量保障

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/knowit.git
cd knowit

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -e .

# 初始化数据库
python scripts/init_db.py
```

### 系统要求

- Python 3.8 或更高版本
- Windows / Linux / macOS
- 可选：WeasyPrint（用于 PDF 生成）

### 基础使用

```bash
# 添加网页（自动导出 HTML 和 PDF）
kv add https://example.com/article

# 添加到指定合集
kv add https://example.com/article -c "Python 学习"

# 搜索内容
kv search "关键词"

# 导出为 HTML
kv export <item_id>

# 查看详情
kv show <item_id>
```

## 使用指南

### 添加内容

#### 添加网页

```bash
# 基础用法
kv add https://example.com/article

# 自定义标题
kv add https://example.com/article -t "我的标题"

# 添加到合集
kv add https://example.com/article -c "Python 学习"

# 跳过去重检测
kv add https://example.com/article --no-dedup
```

#### 添加微信公众号文章

```bash
# 自动识别并处理微信文章
kv add https://mp.weixin.qq.com/s/xxxxx
```

#### 添加本地文件

```bash
# 支持 Markdown、HTML 等格式
kv add /path/to/file.md
```

### 搜索内容

#### 基础搜索

```bash
# 全文搜索
kv search "Python 异步"

# 限制结果数量
kv search "Python" -l 10
```

#### 高级搜索

```bash
# 按状态筛选
kv search "Python" -s archived

# 按标签筛选
kv search "Python" -t "教程"

# 按合集筛选
kv search "Python" -c "学习笔记"

# 按作者筛选
kv search "Python" -a "作者名"

# 按日期范围筛选
kv search "Python" --after 2024-01-01
kv search "Python" --before 2024-12-31

# 组合筛选
kv search "Python" -s archived -t "教程" -c "学习笔记"
```

#### 搜索格式

```bash
# 列表格式（默认）
kv search "Python"

# 表格格式
kv search "Python" -f table
```

### 导出内容

#### 导出格式选项

```bash
# HTML 简单格式（默认）
kv export <item_id>

# HTML Kami 格式（带封面页）
kv export <item_id> --kami

# 清理 HTML 内容（推荐）
kv export <item_id> --clean

# 导出为 PDF
kv export <item_id> --format pdf

# 同时生成 HTML 和 PDF
kv export <item_id> --format both
```

#### 导出后操作

```bash
# 导出后自动打开
kv export <item_id> --open

# 打开打印对话框
kv export <item_id> --print
```

#### 导出组织方式

```bash
# 按日期组织（默认）
kv export <item_id> --organize-by date

# 按合集组织
kv export <item_id> --organize-by collection

# 不使用目录组织
kv export <item_id> --organize-by none

# 自定义输出路径
kv export <item_id> -o /path/to/output.html
```

### 管理内容

#### 查看内容

```bash
# 列出所有条目
kv list

# 按状态筛选
kv list -s archived

# 按合集筛选
kv list -c "Python 学习"

# 限制结果数量
kv list -l 20

# 查看详情
kv show <item_id>
```

#### 更改状态

```bash
# 归档
kv status <item_id> archived

# 标记为星标
kv status <item_id> starred

# 恢复到 inbox
kv status <item_id> --undo
```

### 标签管理

```bash
# 添加标签
kv tag add <item_id> "Python"

# 移除标签
kv tag remove <item_id> "Python"

# 列出所有标签
kv tag list
```

### 合集管理

```bash
# 创建合集
kv collection create "技术学习"

# 列出合集
kv collection list

# 添加到合集
kv collection add <item_id> "技术学习"

# 从合集移除
kv collection remove <item_id> "技术学习"
```

### 自动导出

KnowIt 支持在添加知识后自动导出，类似 Obsidian 的知识管理体验。

```bash
# 自动导出在添加知识后自动触发
kv add https://example.com/article
# 输出：[导出] 已自动导出: HTML, PDF
#       - by-collection/Inbox/文章标题.html
#       - by-collection/Inbox/文章标题.pdf

# 添加到合集时自动组织
kv add https://example.com/article -c "Python 学习"
# 输出：[导出] 已自动导出: HTML, PDF
#       - by-collection/Python学习/文章标题.html
#       - by-collection/Python学习/文章标题.pdf

# 临时跳过自动导出
kv add https://example.com/article --no-export
```

#### 自动导出配置

```bash
# 查看自动导出配置
kv config get auto_export

# 禁用自动导出
kv config set auto_export.enabled false

# 只导出 HTML
kv config set auto_export.formats '["html"]'

# 按日期组织
kv config set auto_export.organize_by date

# 使用简化格式（无封面页）
kv config set auto_export.use_kami false
```

#### 自动导出目录结构

```
~/KnowIt/exports/
├── by-collection/
│   ├── Python学习/
│   │   ├── 2024-01-15_装饰器详解.html
│   │   └── 2024-01-15_装饰器详解.pdf
│   ├── 前端开发/
│   │   └── CSS_Grid布局指南.html
│   └── Inbox/                    # 未分类文章
│       └── 随笔一则.html
```

### 导出管理

```bash
# 手动导出单个条目
kv export <item_id>

# 列出导出文件
kv exports list

# 导出统计
kv exports stats

# 清理旧导出
kv exports clean --days 30

# 打开导出目录
kv exports open
```

### 备份与恢复

```bash
# 创建备份
kv backup create

# 列出备份
kv backup list

# 恢复备份
kv backup restore <backup_file>
```

### 配置管理

```bash
# 查看配置
kv config list

# 获取配置项
kv config get dedup.threshold

# 设置配置项
kv config set dedup.threshold 0.8

# 编辑配置文件
kv config edit
```

### 系统状态

```bash
# 查看系统状态
kv status

# 显示统计信息
kv stats
```

## 配置

配置文件位置：`~/KnowIt/config/config.yaml`

### 示例配置

```yaml
# 去重设置
dedup:
  threshold: 0.75  # 相似度阈值（0-1）
  enabled: true    # 是否启用去重

# 自动导出设置 ⭐
auto_export:
  enabled: true                    # 是否启用自动导出
  directory: null                  # 自定义导出目录（null = 默认）
  formats:                          # 导出格式列表
    - html
    - pdf
  clean_html: true                 # 是否清理 HTML
  use_kami: true                   # 是否使用 Kami 完整格式
  organize_by: collection           # 组织方式：date | collection | none
  on_error: warn                   # 错误处理：warn | ignore

# 手动导出设置
export:
  default_format: html             # 默认导出格式
  open_in_browser: false           # 是否在浏览器中打开
  organize_by: date                # 导出目录组织方式

# 抓取设置
scraper:
  timeout: 30                      # 请求超时时间（秒）
  user_agent: 'Mozilla/5.0...'     # 用户代理

# 搜索设置
search:
  limit: 20                        # 搜索结果数量
  preview_length: 200              # 预览长度

# 显示设置
display:
  date_format: '%Y-%m-%d %H:%M'    # 日期格式
  max_preview_length: 500         # 最大预览长度
```

## 导出格式

### HTML 格式

KnowIt 支持两种 HTML 格式：

1. **简单格式**（默认）
   - 单页文档
   - 标题 + 元数据 + 内容
   - 适合快速预览

2. **Kami 格式**（`--kami`）
   - 封面页（标题、作者、来源、日期）
   - 正文内容
   - 页码和页脚
   - 适合正式文档和打印

### 内容清理

使用 `--clean` 选项可以：
- 移除内联样式和冗余属性
- 清理 WeChat 特有元素（QR 码、赞赏按钮等）
- 优化图片加载（使用 data-src）
- 过滤代码块噪音

推荐对微信公众号文章使用 `--clean` 选项。

### PDF 生成

PDF 生成需要安装 WeasyPrint：

```bash
pip install weasyprint
```

**注意**：Windows 用户可能需要安装 GTK 库。

## 技术架构

### 技术栈

**核心框架**
- **[Python](https://www.python.org/)** 3.8+ - 编程语言
- **[Click](https://github.com/pallets/click)** - CLI 框架
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - ORM
- **[SQLite](https://www.sqlite.org/)** - 数据库

**内容处理**
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** - HTML 解析
- **[simhash](https://github.com/seomoz/simhash-py)** - 相似度检测
- **[jieba](https://github.com/fxsjy/jieba)** - 中文分词

**导出功能**
- **[WeasyPrint](https://weasyprint.org/)** - PDF 生成（可选）
- 基于 **[Kami](https://github.com/tw93/Kami)** 设计系统
- 参考 **[clip-to-kami](https://github.com/Anarcadia/clip-to-kami)** 实现

### 项目结构

```
knowit/
├── src/kv/
│   ├── __init__.py
│   ├── cli.py              # CLI 入口
│   ├── commands/           # CLI 命令模块（规划中）
│   │   └── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py       # 配置管理
│   │   └── database.py     # 数据库模型
│   ├── services/
│   │   ├── __init__.py
│   │   ├── database.py          # 数据库服务
│   │   ├── scraper.py           # 网页抓取
│   │   ├── pdf_export.py        # PDF/HTML 导出（基于 Kami）
│   │   ├── html_cleaner.py      # HTML 清理（参考 clip-to-kami）
│   │   ├── kami_template.html   # Kami 设计模板
│   │   ├── backup_service.py    # 备份服务
│   │   ├── export_manager.py    # 导出管理
│   │   ├── config_service.py    # 配置服务
│   │   ├── auto_export.py       # 自动导出服务 ⭐
│   │   └── playwright_scraper.py # 动态内容抓取
│   ├── algorithms/
│   │   ├── __init__.py
│   │   └── dedup.py        # 去重算法
│   └── utils/              # 工具函数
├── tests/                  # 测试套件 ⭐
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_auto_export.py
│   ├── test_dedup.py
│   └── test_database_service.py
├── scripts/                # 脚本工具
│   ├── init_db.py         # 初始化数据库
│   └── test_setup.py      # 测试环境
├── docs/                   # 文档
├── config/                 # 配置目录 ⭐
│   └── README.md
├── data/                   # 数据目录 ⭐
│   └── README.md
├── pyproject.toml         # 项目配置
├── pytest.ini             # Pytest 配置 ⭐
├── requirements.txt        # 依赖列表
└── README.md              # 本文件
```

### 数据库模型

- **Item** - 知识条目
- **Collection** - 合集
- **Tag** - 标签
- **ItemTag** - 条目标签关联
- **ItemSimilarity** - 相似度缓存

## 开发

### 设置开发环境

```bash
# 克隆仓库
git clone https://github.com/yourusername/knowit.git
cd knowit

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\Activate.ps1  # Windows

# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest tests/

# 代码格式化
black src/ tests/
ruff check src/ tests/

# 类型检查
mypy src/
```

### 运行测试

```bash
# 所有测试
pytest tests/

# 特定测试
pytest tests/test_dedup.py

# 带详细输出
pytest tests/ -v

# 带覆盖率
pytest --cov=kv tests/

# 当前测试覆盖：17 个测试全部通过 ✅
```

## 设计系统

KnowIt 采用以下开源项目的设计和实现：

### Kami - 设计系统

> [Kami](https://github.com/tw93/Kami) by [@tw93](https://github.com/tw93)

KnowIt 完全遵循 Kami 设计规范，提供专业的文档排版：

- **字体**：TsangerJinKai02（书法楷体）
- **颜色**：温暖羊皮纸主题（#f5f4ed）
- **布局**：A4 页面，专业排版
- **风格**：优雅的中式美学

### clip-to-kami - 内容转换引擎

> [clip-to-kami](https://github.com/Anarcadia/clip-to-kami) by [Anarcadia](https://github.com/Anarcadia)

KnowIt 的 HTML 清理和 PDF 导出功能基于 clip-to-kami 实现：

- HTML 内容清理（特别是微信公众号文章）
- 图片处理和优化
- WeasyPrint PDF 生成
- WeChat 文章特殊处理

### 字体系统

- **主要字体**：TsangerJinKai02（书法楷体）
- **Fallback 链**：Source Han Serif SC → Noto Serif CJK SC → Songti SC → STSong → FangSong → Georgia → serif

### 颜色系统

- `--parchment: #f5f4ed` - 羊皮纸背景
- `--ivory: #faf9f5` - 象牙白
- `--near-black: #141413` - 深黑文本
- `--brand: #1B365D` - 品牌墨蓝色
- `--border: #e8e6dc` - 边框色

### 布局

- **页面尺寸**：A4
- **边距**：20mm (top), 22mm (right/bottom/left)
- **页脚**：页码 + 文档标题

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 开发指南

- 遵循 PEP 8 代码风格
- 添加测试覆盖新功能
- 更新文档
- 保持提交信息清晰

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 致谢

KnowIt 的实现得益于以下优秀的开源项目：

### 核心依赖

- **[Kami](https://github.com/tw93/Kami)** by [@tw93](https://github.com/tw93)
  - 优雅的文档设计系统
  - 温暖的羊皮纸配色
  - 专业的中文字体排版

- **[clip-to-kami](https://github.com/Anarcadia/clip-to-kami)** by [Anarcadia](https://github.com/Anarcadia)
  - HTML 内容清理算法
  - 微信公众号文章处理
  - PDF 导出实现参考

### 技术栈

- **[Click](https://github.com/pallets/click)** - 优雅的 CLI 框架
- **[SQLAlchemy](https://www.sqlalchemy.org/)** - Python SQL 工具包和 ORM
- **[BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)** - HTML 解析库
- **[simhash](https://github.com/seomoz/simhash-py)** - 相似度检测算法
- **[jieba](https://github.com/fxsjy/jieba)** - 中文分词
- **[WeasyPrint](https://weasyprint.org/)** - HTML 到 PDF 转换
- **[Pytest](https://docs.pytest.org/)** - 测试框架

### 特别感谢

感谢以上项目的所有贡献者和维护者！🙏

KnowIt 站在巨人的肩膀上，为个人知识管理提供了一套完整的解决方案。

## 联系方式

- **Issues**: [GitHub Issues](https://github.com/yourusername/knowit/issues)
- **文档**: [docs/](docs/)

---

<div align="center">

**KnowIt** - 你的第二大脑

Made with ❤️ for personal knowledge management

</div>
