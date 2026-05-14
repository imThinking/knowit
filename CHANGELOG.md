# Changelog

All notable changes to KnowIt will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Meilisearch 全文搜索集成
- Playwright 动态内容抓取
- CLI 模块化重构

## [0.2.0] - 2025-01-14

### Added
- **自动导出功能** - 添加知识后自动生成 HTML 和 PDF
  - 支持按合集自动组织文件结构
  - 可配置导出格式（HTML/PDF/两者）
  - 错误隔离：导出失败不影响添加操作
  - `--no-export` 选项可临时跳过导出
- **测试套件** - 完整的单元测试覆盖
  - 17 个测试用例全部通过
  - 覆盖自动导出、去重算法、数据库服务
  - Pytest 配置和测试夹具
- **项目结构优化**
  - 添加 `config/README.md` 和 `data/README.md`
  - 创建 `src/kv/commands/` 目录结构
  - 在 `cli.py` 添加重构规划文档

### Changed
- 改进配置系统，支持 `auto_export` 配置项
- 更新 README 文档，添加自动导出使用说明
- 添加项目路线图 `docs/ROADMAP.md`

### Fixed
- 修复空目录问题（config/, data/）
- 修复测试覆盖率从 0% 到 ~15%

### Technical Debt
- 识别并记录 cli.py 过大问题（1648 行）
- 识别 database.py 命名混淆问题
- 规划 services/ 目录重组

## [0.1.0] - 2024-12-XX

### Added
- **核心功能**
  - 网页内容抓取（静态页面、微信公众号）
  - Simhash 智能去重算法
  - SQLite 数据库存储
  - 全文搜索和多条件筛选
  - 标签和层级化合集系统
  - 基于 Kami 设计系统的 HTML/PDF 导出
  - 自动备份和恢复功能

- **CLI 命令**
  - `add` - 添加网页/本地文件
  - `search` - 搜索知识库
  - `list` - 列出所有条目
  - `show` - 查看详情
  - `export` - 导出 HTML/PDF
  - `collection` - 合集管理
  - `tag` - 标签管理
  - `backup` - 备份与恢复
  - `config` - 配置管理
  - `status` - 系统状态

- **设计系统**
  - 基于 Kami 的温暖羊皮纸主题
  - TsangerJinKai02 书法楷体
  - 专业排版和布局

### Dependencies
- Python 3.8+
- Click 8.0+
- SQLAlchemy 2.0+
- BeautifulSoup4 4.9+
- simhash 2.0+
- jieba 0.42+
- WeasyPrint 60+ (可选)

### Documentation
- README.md - 项目说明
- CLAUDE.md - Claude Code 指令
- CONTRIBUTING.md - 贡献指南
- docs/GITHUB_SETUP.md - GitHub 设置指南
- docs/EXPORT_FEATURES.md - 导出功能说明

---

## 版本号说明

- **Major (X.0.0)**：重大功能变更、架构重构、不兼容改动
- **Minor (0.X.0)**：新功能添加、向后兼容的改进
- **Patch (0.0.X)**：Bug 修复、文档更新、小改进

## 分类说明

- **Added** - 新增功能
- **Changed** - 功能变更
- **Deprecated** - 即将移除的功能
- **Removed** - 已移除的功能
- **Fixed** - Bug 修复
- **Security** - 安全相关修复
