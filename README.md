# KnowIt

> 你的第二大脑，优雅地归集网络碎片。

KnowIt 是一个开源的个人知识库收集整理工具，专注于**主动收集**和**智能合并**。

## 核心特性

- 📥 **主动收集**：CLI 命令收集网页、微信文章、本地文件
- 🤖 **智能合并**：自动识别并合并重复/相似内容
- 🔍 **强大搜索**：Meilisearch 全文索引，毫秒级响应
- 📄 **优雅输出**：基于 Kami 排版的精美 PDF
- 💾 **本地优先**：数据存储在本地，隐私安全

## 快速开始

```bash
# 安装
pip install -e .

# 添加内容
kv add https://example.com/article

# 搜索
kv search "Python 异步"

# 导出
kv export "Python 学习" --pdf
```

## 基于

- [Kami](https://github.com/tw93/kami) - 设计系统
- [clip-to-kami](https://github.com/Anarcadia/clip-to-kami) - 内容转换引擎

## 开源协议

MIT License
