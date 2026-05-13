# KnowIt Windows 开发指南

## 在 PowerShell 中设置开发环境

### 前置要求

1. **安装 Python 3.10+**
   - 访问 https://www.python.org/downloads/
   - 下载 Windows installer
   - 安装时勾选 "Add Python to PATH"

2. **安装 Git**（可选）
   - 访问 https://git-scm.com/download/win
   - 使用默认设置安装

### 快速开始

#### 方法 1：使用自动安装脚本（推荐）

```powershell
# 进入项目目录
cd E:\PROJECTS\knowit

# 运行自动安装脚本
.\setup.bat
```

脚本会自动：
- ✅ 检查 Python 版本
- ✅ 安装核心依赖
- ✅ 创建虚拟环境
- ✅ 初始化数据库

#### 方法 2：手动安装

```powershell
# 1. 进入项目目录
cd E:\PROJECTS\knowit

# 2. 安装依赖
pip install click sqlalchemy beautifulsoup4 lxml simhash

# 3. 创建虚拟环境（推荐）
python -m venv venv

# 4. 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 5. 初始化数据库
python scripts\init_db.py
```

### 开发工作流

#### 日常开发

```powershell
# 1. 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 2. 测试 CLI 命令
python -m kv.cli --help

# 3. 运行 CLI
python -m kv.cli add https://example.com

# 4. 运行测试
pytest tests/
```

#### VS Code 配置

1. 安装 **Python** 扩展
2. 打开项目文件夹：`File -> Open Folder`
3. 选择解释器：`Ctrl+Shift+P -> Python: Select Interpreter`
   - 选择 `./venv/Scripts/python.exe`

### 依赖说明

**核心依赖**（必须安装）：
- `click` - CLI 框架
- `sqlalchemy` - ORM
- `beautifulsoup4` - HTML 解析
- `simhash` - 相似度计算

**可选依赖**（按需安装）：
- `jieba` - 中文分词
- `scikit-learn` - 聚类算法
- `weasyprint` - PDF 生成

### 常见问题

#### Q: pip 安装失败？
A: 使用国内镜像源
```powershell
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple click sqlalchemy
```

#### Q: 虚拟环境激活失败？
A: PowerShell 执行策略限制，运行：
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Q: 找不到模块？
A: 确保已激活虚拟环境，提示符应该显示 `(venv)`

### 项目目录说明

```
knowit/
├── src/kv/              # 源代码
├── scripts/            # 工具脚本
├── tests/              # 测试
├── data/               # 数据目录（SQLite 数据库）
├── config/             # 配置文件
└── venv/               # 虚拟环境（自动生成）
```

### 下一步

安装完成后，查看：
- `README.md` - 项目说明
- `KnowIt-技术设计文档.html` - 技术设计
- `KnowIt-项目计划书.html` - 项目计划

开始开发：
```powershell
# 激活虚拟环境
.\venv\Scripts\Activate.ps1

# 测试 CLI
python -m kv.cli --help
```
