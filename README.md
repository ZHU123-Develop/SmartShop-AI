<div align="center">

# 🤖 SmartShop-AI

**AI 智能电商客服系统** — 多模型 · 工具调用 · RAG 知识库

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&style=flat)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-black?logo=flask&style=flat)](https://flask.palletsprojects.com)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-API-4F6BFF?style=flat)](https://deepseek.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-vector-yellow?style=flat)](https://www.trychroma.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

---

**一个开箱即用的 AI 电商客服聊天机器人，支持 7 大 AI 模型、9 种工具调用、RAG 知识库检索，并提供 ChatGPT 风格的前端界面。**

</div>

## ✨ 核心功能

### 🧠 多模型驱动
支持 **DeepSeek**、**OpenAI**、**通义千问**、**智谱 GLM**、**Moonshot**、**硅基流动** 等 7 大 AI 提供商，一键切换。

### 🛠️ 9 种智能工具
| 工具 | 说明 | 数据源 |
|------|------|--------|
| 📦 订单查询 | 订单状态、商品信息、物流单号 | 模拟数据 |
| 📬 物流追踪 | 物流轨迹、进度时间线 | 模拟数据 |
| 🔄 退换货查询 | 退货进度、退款金额 | 模拟数据 |
| 👤 会员查询 | 会员等级、积分、升级进度 | 模拟数据 |
| 🌤️ 天气查询 | 实时天气、温度湿度 | wttr.in 免费 API |
| 🔢 数学计算 | 安全 AST 解析计算器 | - |
| ⏰ 日期时间 | 当前时间、时区转换 | - |
| 🔍 网页搜索 | Bing / DuckDuckGo | 无需 API Key |
| 🦆 DuckDuckGo | 备选搜索引擎 | JSON API |

### 📚 RAG 知识库
- 基于 **ChromaDB** 向量检索
- 支持 TXT / PDF / DOCX 导入
- 智能文档分块（重叠 + 段落感知）
- **启动自动加载** 29 条电商 FAQ 样本数据

### 💬 对话体验
- ⚡ **SSE 流式输出** — 实时逐字显示 AI 回复
- 🌙 **暗色/亮色主题** — 一键切换，柔和护眼色
- 📋 **侧边栏折叠** — 桌面折叠 / 手机滑出
- 📎 **文件上传** — 支持 TXT/PDF/图片/DOCX
- 🛑 **停止生成** — 随时中断 AI 回复
- 📱 **移动端适配** — 响应式设计

---

## 🚀 快速开始

### 前提条件
- Python 3.10+
- 一个 AI 模型的 API Key（推荐 [DeepSeek](https://platform.deepseek.com/)）

### 一键安装 + 启动（推荐 uv）

```bash
# 1. 安装 uv（如未安装）
pip install uv

# 2. 克隆并进入项目
cd SmartShop-AI

# 3. 安装全部依赖（核心 + RAG + 文档解析）
uv sync --extra all

# 4. 配置 API Key（推荐环境变量方式，更安全）
# Windows PowerShell:
$env:LLM_API_KEY="sk-your-key-here"
$env:LLM_BASE_URL="https://api.deepseek.com/v1"
$env:LLM_MODEL="deepseek-chat"

# Linux/Mac:
export LLM_API_KEY="sk-your-key-here"

# 5. 启动服务
uv run python app.py
```

### 使用 pip 安装

```bash
pip install -r requirements.txt
pip install chromadb PyMuPDF pdfplumber python-docx tzdata
python app.py
```

启动后访问 **http://localhost:5000** 🎉

> ⚠️ **安全提示**: 强烈建议通过环境变量 `LLM_API_KEY` 配置 API Key，而不是写入 `settings.json`。  
> 如果使用 `settings.json`，请确保该文件已被 `.gitignore` 忽略，避免误提交到 GitHub。

---

## 🖥️ 使用指南

### 配置模型
1. 点击左下角 **⚙️ 设置** 按钮
2. 选择 AI 提供商（DeepSeek / OpenAI / 通义千问等）
3. 输入 API Key 和 API 地址
4. 选择模型，点击保存

### 快速开始
点击欢迎页面的功能卡片，或直接输入问题：

```
# 订单查询
查询订单 ORD20240101001

# 物流追踪
查一下物流单号 SF1234567890

# 会员查询
查询手机号 13800000001 的会员信息

# 天气查询
北京今天天气怎么样？

# 知识库查询
你们有什么退换货政策？
会员等级怎么升级？
```

### 设置项说明
| 设置项 | 说明 | 默认值 |
|--------|------|--------|
| 客服名称 | AI 自我介绍时的店铺名 | SmartShop |
| 营业时间 | 自动回复中的营业时段 | 9:00-21:00 |
| 知识库返回数量 | 每次检索的片段数 | 3 |
| 知识库相似度阈值 | 结果相关性过滤 | 0.5 |

---

## 📝 最近更新

### v1.1.0 (2026-07-28)
- 🔒 **安全增强**: 启动时检测 API Key 来源，提示使用环境变量替代 settings.json
- 🔄 **工具调用优化**: 添加去重检测，防止 AI 重复调用同一工具导致无限循环
- 🎯 **搜索提供商生效**: 修复 `search_provider` 配置项未生效的问题（现在 bing/duckduckgo 二选一）
- 🧠 **模型配置统一**: `_supports_tool_calling` 改用 `MODEL_PRESETS` 配置，消除硬编码
- 🏷️ **类型注解**: 核心函数添加完整类型注解（`Generator`, `Optional`, `Callable` 等）
- ⚡ **线程安全**: 速率限制器添加 `threading.Lock()` 保护
- 📦 **数据库性能**: 会话列表查询添加 `LIMIT 100` 分页
- 🧹 **清理**: 删除空目录 `docs/` 和构建产物 `__pycache__/`、`smartshop_ai.egg-info/`

---

## 📁 项目结构

```
SmartShop-AI/
├── app.py                 # Flask 入口（路由/数据库/设置）
├── ai_client.py           # AI 客户端（对话/工具/RAG）
├── settings.json          # 运行时配置（已 .gitignore，建议用环境变量）
├── templates/
│   └── index.html         # 页面模板
├── static/
│   ├── app.js             # 前端逻辑（SSE/会话/主题）
│   └── style.css          # 全局样式（暗色/亮色双主题）
├── tools/                 # Function Calling 工具集
│   ├── registry.py        # 工具注册中心
│   ├── order_query.py     # 订单查询（模拟）
│   ├── logistics_track.py # 物流追踪（模拟）
│   ├── return_refund.py   # 退换货查询（模拟）
│   ├── member_info.py     # 会员信息查询（模拟）
│   ├── weather.py         # 天气查询（wttr.in 免费 API）
│   ├── calculator.py      # 安全计算器（AST 解析）
│   ├── datetime_tool.py   # 日期时间（时区支持）
│   ├── bing_search.py     # Bing 网页搜索（HTML 解析）
│   └── duckduckgo_search.py # DuckDuckGo 搜索（JSON API）
├── rag/                   # RAG 知识库模块
│   ├── vector_store.py    # ChromaDB 封装
│   ├── document_processor.py # 文档解析与分块
│   └── sample_kb.txt      # 电商 FAQ 样本（自动加载）
├── pyproject.toml         # 项目元数据
├── CLAUDE.md              # AI 辅助开发配置
└── LICENSE                # MIT 许可证
```

---

## 🔌 API 接口

| 方法 | 路径 | 说明 | 限流 |
|------|------|------|------|
| GET | `/` | Web 主页面 | - |
| GET | `/settings` | 获取配置 | - |
| PUT | `/settings` | 更新配置 | - |
| GET | `/sessions` | 会话列表 | - |
| GET | `/sessions/<id>` | 会话消息 | - |
| DELETE | `/sessions/<id>` | 删除会话 | - |
| POST | `/chat` | 发送消息（SSE 流式） | 20次/分钟 |
| POST | `/stop/<key>` | 停止生成 | - |
| POST | `/upload` | 上传文件 | - |

### 聊天 API 调用示例

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "北京今天天气怎么样？"}'

# 响应（SSE 流式）：
# data: {"type":"chunk","content":"您好"}
# data: {"type":"chunk","content":"！"}
# data: {"type":"done","session_id":"abc123"}
```

---

## 🧪 测试数据（模拟）

| 订单号 | 状态 | 快递单号 | 会员手机号 | 退货单号 |
|--------|------|----------|-----------|----------|
| ORD20240101001 | 已发货 | SF1234567890 | 13800000001 | RET20240101001 |
| ORD20240102002 | 待付款 | YZ9876543210 | 13800000002 | RET20240102002 |
| ORD20240103003 | 已签收 | SF5566778899 | 13800000003 | RET20240103003 |
| ORD20240104004 | 已付款 | YZ1122334455 | 13800000004 | RET20240104004 |
| ORD20240105005 | 已退货 | - | 13800000005 | RET20240104004 |
| ORD20240106006 | 已发货 | - | - | - |

---

## 🔒 安全

- ✅ API Key 仅存于 `settings.json`（被 `.gitignore` 忽略）或环境变量
- ✅ 前端 Markdown 渲染经 **DOMPurify** 过滤 XSS
- ✅ 数学计算使用 **AST 解析**，非 `eval()`
- ✅ 聊天接口 **20 次/分钟** 速率限制
- ✅ 文件上传 **白名单** 过滤
- ✅ SQLite **参数化查询** 防注入

---

## 📊 项目统计

- **总代码量**: ~5,400 行
- **Python**: ~1,900 行（16 个模块）
- **JavaScript**: ~1,100 行
- **CSS**: ~2,200 行（暗色/亮色双主题）

---

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">
  <sub>Built with ❤️ by ZHU123-Develop — 多模型 AI 电商客服系统</sub>
</div>
