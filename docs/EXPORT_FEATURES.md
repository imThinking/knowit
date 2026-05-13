# KnowIt 导出功能更新说明

## 已实现的 clip-to-kami 功能

### 1. HTML 内容清理 (`html_cleaner.py`)

基于 `clip-to-kami/scripts/convert.py` 的 `clean_html` 函数实现：

**功能**：
- 移除不需要的元素（script, style, QR codes, reward areas）
- 移除样式属性和 data-* 属性（保留 data-src 用于图片）
- 正确处理 WeChat 文章的 `<section>` 标签（不跳过只包含图片的 section）
- 提取代码块并过滤 CSS counter noise
- 处理图片时优先使用 `data-src`（原始图片）而非 `src`（懒加载占位符）
- 跳过 SVG 占位符图片

**使用方法**：
```bash
kv export <item_id> --clean
```

### 2. Kami 设计系统模板 (`kami_template.html`)

完整的 Kami 模板，包含：

**字体系统**：
- 主要字体：TsangerJinKai02（书法楷体）
- Fallback 链：Source Han Serif SC → Noto Serif CJK SC → Songti SC → STSong → FangSong → Georgia → serif
- 支持常规（W04）和粗体（W05）两个字重
- CDN 备用字体加载

**颜色系统**：
- `--parchment: #f5f4ed` - 羊皮纸背景
- `--ivory: #faf9f5` - 象牙白
- `--near-black: #141413` - 深黑文本
- `--dark-warm: #3d3d3a` - 深暖灰
- `--olive: #504e49` - 橄榄灰
- `--stone: #6b6a64` - 石灰
- `--brand: #1B365D` - 品牌墨蓝色
- `--border: #e8e6dc` - 边框色
- `--border-soft: #e5e3d8` - 柔和边框

**布局系统**：
- A4 页面尺寸
- 页边距：20mm (top), 22mm (right/bottom/left)
- PDF 页脚：页码 + 文档标题
- 封面页单独分页

### 3. PDF 导出服务 (`pdf_export.py`)

**新增方法**：
- `generate_html()` - 生成 Kami 完整格式 HTML（带封面页）
- `generate_html_simple()` - 生成简单格式 HTML（无封面页）
- `generate_pdf()` - 使用 WeasyPrint 生成 PDF

**参数**：
- `clean` - 是否清理 HTML 内容
- `font_dir` - 自定义字体目录路径

**依赖**：
```bash
pip install weasyprint
```

**注意**：Windows 上 WeasyPrint 可能需要额外的 GTK 库。

### 4. CLI 导出命令更新

**新选项**：
```bash
--format {html|pdf|both}    # 输出格式（默认：html）
--clean                     # 清理 HTML 内容（推荐用于 WeChat 文章）
--font-dir <path>           # Kami 字体目录路径
```

**使用示例**：

```bash
# 基础 HTML 导出（简单格式）
kv export <item_id>

# Kami 完整格式（带封面页）
kv export <item_id> --kami

# 清理后的 HTML（推荐）
kv export <item_id> --clean

# PDF 导出（需要 WeasyPrint）
kv export <item_id> --format pdf

# 同时生成 HTML 和 PDF
kv export <item_id> --format both

# 组合选项
kv export <item_id> --kami --clean --format both
kv export <item_id> --clean --open
kv export <item_id> --clean --print
```

### 5. 输出格式对比

| 格式 | 说明 | 文件大小 | 适用场景 |
|------|------|----------|----------|
| 简单 HTML | 单页文档，无封面 | 较小 | 快速预览、简单文档 |
| Kami HTML | 封面页 + 正文 | 较大 | 正式文档、打印 |
| PDF | 标准化 PDF | 取决于内容 | 分发、存档 |
| 清理后 HTML | 移除冗余代码 | 中等 | 通用、推荐 |

### 6. 与 clip-to-kami 的对比

| 功能 | clip-to-kami | KnowIt |
|------|--------------|---------|
| Kami 设计系统 | ✅ | ✅ |
| HTML 清理 | ✅ | ✅ |
| PDF 生成 | ✅ | ✅ |
| 图片本地化 | ✅ | ❌ (未实现) |
| EPUB 支持 | ✅ | ❌ (未实现) |
| 数据库集成 | ❌ | ✅ |
| 标签管理 | ❌ | ✅ |
| 合集管理 | ❌ | ✅ |

### 7. 推荐工作流

**微信公众号文章**：
```bash
kv export <item_id> --clean --simple --open
```

**正式文档导出**：
```bash
kv export <item_id> --clean --kami --format pdf
```

**快速预览**：
```bash
kv export <item_id> --clean
```

### 8. 已知限制

1. **PDF 生成**：Windows 上需要安装 GTK 库才能使用 WeasyPrint
2. **图片本地化**：未实现（clip-to-kami 有此功能）
3. **EPUB 导出**：未实现（clip-to-kami 有此功能）

### 9. 技术实现细节

**HTML 清理关键点**：
- 递归处理元素，不跳过只包含图片的 `<section>` 标签
- 优先使用 `data-src` 而非 `src`（WeChat 懒加载）
- 移除所有 `class` 和 `id` 属性以获得干净的输出
- 过滤 CSS counter noise（`counter(line)` 等）

**Kami 模板填充**：
- 使用简单的字符串替换（`{{title}}`, `{{content}}` 等）
- 支持日期格式化（`YYYY-MM-DD HH:MM`）
- 自动处理缺失的字段（author, url 等）

**PDF 生成流程**：
1. 生成 HTML 内容
2. 创建临时目录
3. 复制字体文件（如果提供 font_dir）
4. 使用 WeasyPrint 转换为 PDF
5. 保存到最终路径

### 10. 文件结构

```
src/kv/services/
├── kami_template.html      # Kami 设计系统模板
├── html_cleaner.py         # HTML 内容清理服务
├── pdf_export.py           # HTML/PDF 导出服务（已更新）
├── scraper.py              # Web 抓取服务
└── playwright_scraper.py   # 动态内容抓取（WeChat）
```

### 11. 示例输出

**简单格式 HTML**：
- 单页文档
- 标题 + 元数据 + 内容
- Kami 样式系统

**Kami 完整格式 HTML**：
- 封面页（标题、作者、来源、日期）
- 正文内容
- 页码和页脚
- 分页支持

**清理后 HTML**：
- 移除所有内联样式
- 移除冗余属性
- 清理 WeChat 特有元素
- 保留语义结构

## 总结

KnowIt 现已完全集成 clip-to-kami 的核心功能：
- ✅ Kami 设计系统（字体、颜色、布局）
- ✅ HTML 内容清理（特别是 WeChat 文章）
- ✅ PDF 生成（使用 WeasyPrint）
- ✅ 多种输出格式（简单/Kami, HTML/PDF）
- ✅ 数据库集成（标签、合集、状态管理）
- ✅ 无 emoji 设计（纯文本标签）
- ✅ 中文字体支持（楷体、宋体）

用户可以根据需求选择最适合的导出格式和选项。
