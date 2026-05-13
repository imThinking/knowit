# 贡献指南

感谢你有兴趣为 KnowIt 做出贡献！🎉

## 如何贡献

### 报告问题

如果你发现了 bug 或有功能建议：

1. 先检查 [Issues](https://github.com/imThinking/knowit/issues) 是否已有相同问题
2. 如果没有，创建新的 Issue，使用适当的模板
3. 提供详细的信息复现问题

### 提交代码

#### 开发环境设置

```bash
# 1. Fork 本仓库
# 点击 GitHub 页面右上角的 "Fork" 按钮

# 2. 克隆你的 fork
git clone https://github.com/YOUR_USERNAME/knowit.git
cd knowit

# 3. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\Activate.ps1  # Windows

# 4. 安装依赖
pip install -e ".[dev]"

# 5. 创建分支
git checkout -b feature/your-feature-name

# 6. 进行开发
# 修改代码、添加功能等

# 7. 运行测试
pytest tests/

# 8. 提交代码
git add .
git commit -m "feat: add your feature"

# 9. 推送到你的 fork
git push origin feature/your-feature-name

# 10. 创建 Pull Request
# 在 GitHub 上打开你的 fork，点击 "Compare & pull request"
```

#### 代码规范

- **Python 代码**：遵循 [PEP 8](https://pep8.org/)
- **提交信息**：使用清晰的提交信息格式

**提交信息格式**：
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型 (type)**：
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 添加测试
- `chore`: 构建/工具链更新

**示例**：
```
feat(scraper): add support for WeChat article scraping

- Use Playwright for dynamic content
- Extract content from #js_content element
- Handle WeChat-specific UI elements

Closes #123
```

#### 代码格式化

在提交前，请运行：

```bash
# 代码格式化
black src/ tests/

# 代码检查
ruff check src/ tests/

# 类型检查
mypy src/
```

#### 测试

确保所有测试通过：

```bash
# 运行所有测试
pytest tests/

# 运行特定测试
pytest tests/test_scraper.py

# 带覆盖率报告
pytest --cov=kv tests/
```

### 文档

如果添加了新功能，请更新相应的文档：
- README.md - 如果是用户可见的功能
- docs/ - 技术文档
- 代码注释 - 复杂逻辑需要注释

## Pull Request 流程

1. **更新你的分支**：确保你的分支与 main 分支保持同步
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **创建 Pull Request**：
   - 在 GitHub 上创建 PR
   - 使用 PR 模板填写信息
   - 等待代码审查

3. **代码审查**：
   - 解决审查中提出的意见
   - 保持友好和开放的态度

4. **合并**：
   - 审查通过后，你的 PR 会被合并到 main 分支

## 开发指南

### 项目结构

```
knowit/
├── src/kv/
│   ├── cli.py              # CLI 入口
│   ├── core/               # 核心模块
│   ├── services/           # 业务逻辑
│   ├── algorithms/         # 算法实现
│   └── utils/              # 工具函数
├── tests/                  # 测试
├── scripts/                # 脚本工具
└── docs/                   # 文档
```

### 添加新功能

1. 在 `src/kv/services/` 或相应的模块中添加代码
2. 在 `src/kv/cli.py` 中添加 CLI 命令（如果需要）
3. 在 `tests/` 中添加测试
4. 更新文档

### 添加新命令示例

```python
@cli.command()
@click.argument("item_id")
def my_command(item_id: str):
    """命令描述"""
    item = db.get_item(item_id)
    if not item:
        click.echo(f"错误: 未找到条目 {item_id}", err=True)
        sys.exit(1)

    # 实现你的逻辑
    click.echo(f"处理条目: {item.title}")
```

## 代码审查标准

- 代码符合 PEP 8 规范
- 测试覆盖新增功能
- 文档已更新
- 提交信息清晰
- 无明显性能问题

## 获取帮助

如果你有任何问题：

- 查看 [文档](https://github.com/imThinking/knowit#readme)
- 创建 [Discussion](https://github.com/imThinking/knowit/discussions)
- 提交 [Issue](https://github.com/imThinking/knowit/issues)

## 行为准则

- 尊重所有贡献者
- 欢迎不同观点
- 建设性的反馈
- 专注于对项目最有利的事情

## 许可证

通过贡献代码，你同意你的贡献将使用 [MIT License](LICENSE) 进行许可。

---

再次感谢你的贡献！🙏
