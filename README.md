# SmartShop-AI

> 多模型 AI 电商智能客服助手 — 支持工具调用与 RAG 知识库检索

一个基于 Python Flask 的 AI 客服聊天机器人，可对接多种大语言模型（DeepSeek、OpenAI、智谱 GLM、通义千问等），通过工具调用提供订单查询、物流追踪、天气查询等实用功能，并支持上传文档构建 RAG 知识库。

## ✨ 功能特性

- **多模型支持** — 兼容 DeepSeek、OpenAI、智谱 GLM、通义千问、Moonshot、SiliconFlow 及任意 OpenAI 兼容 API
- **工具调用 (Function Calling)** — AI 可动态调用搜索、天气、计算器、订单查询、物流追踪、退换货、会员信息等工具
- **RAG 知识库** — 上传 PDF/DOCX/TXT 文档，自动向量化后用于智能客服问答，优先引用店铺政策
- **流式响应** — SSE 实时 token 流式输出，支持暂停生成
- **会话管理** — 多会话创建/切换/删除，数据持久化到 SQLite
- **文件上传** — 拖拽和粘贴上传文本、图片、PDF、DOCX 文件
- **深色/浅色主题** — ChatGPT 风格的响应式 UI，支持自动主题切换
- **Markdown 渲染** — 代码块、表格、任务列表等完整支持

## 📦 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.10 + Flask |
| AI 客户端 | OpenAI SDK（通用兼容层） |
| 向量库 | ChromaDB |
| 数据库 | SQLite |
| 前端 | 原生 HTML/CSS/JS + marked.js |

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

如需使用 RAG 知识库（文档上传 + 向量化检索），额外安装：

```bash
pip install chromadb python-docx PyMuPDF pdfplumber
```

### 2. 配置 API

编辑 `settings.json`（或直接在页面设置中配置）：

```json
{
  "api_key": "your-api-key-here",
  "base_url": "https://api.deepseek.com/v1",
  "model": "deepseek-chat",
  "search_provider": "bing",
  "customer_service_name": "SmartShop",
  "business_hours": "9:00-21:00",
  "kb_top_k": 3,
  "kb_similarity_threshold": 0.5
}
```

| 字段 | 说明 |
|------|------|
| `api_key` | 你的 LLM API 密钥（必填） |
| `base_url` | API 端点地址 |
| `model` | 模型名称 |
| `search_provider` | 搜索工具：`bing` 或 `duckduckgo` |
| `customer_service_name` | 店铺名称（用于客服人设） |
| `business_hours` | 营业时间 |

### 3. 启动服务

```bash
python app.py
```

访问 `http://localhost:5000`。

## 🛠️ 可用工具

| 工具 | 说明 |
|------|------|
| `calculator` | 安全数学计算器（AST 解析） |
| `datetime` | 当前日期时间查询 |
| `weather` | 天气查询（wttr.in） |
| `bing_search` | Bing 网页搜索 |
| `duckduckgo_search` | DuckDuckGo 网页搜索 |
| `query_order` | 订单状态查询 |
| `query_logistics` | 物流追踪 |
| `query_return_refund` | 退换货状态查询 |
| `query_member_info` | 会员信息查询 |

> 订单/物流/退换货/会员工具当前使用模拟数据，实际部署时替换为真实数据库接口。

## 📚 RAG 知识库

1. 在设置中配置 API 并上传文档（TXT / PDF / DOCX）
2. 系统自动解析文档、分块、向量化并存储到 ChromaDB
3. 对话时自动检索相关知识库片段，优先基于文档内容回答

知识库配置文件：`rag/sample_kb.txt` 包含示例售后政策文档。

## 🏗️ 项目结构

```
app.py                  # Flask 主入口，路由与会话管理
deepseek_client.py      # AI 客户端（RAG + 工具调用 + 流式对话）
tools/                  # 工具注册中心与各工具实现
  registry.py           # 工具注册与执行中心
  calculator.py         # 数学计算器
  datetime_tool.py      # 日期时间
  weather.py            # 天气查询
  bing_search.py        # Bing 搜索
  duckduckgo_search.py  # DuckDuckGo 搜索
  order_query.py        # 订单查询
  logistics_track.py    # 物流追踪
  return_refund.py      # 退换货
  member_info.py        # 会员信息
rag/                    # RAG 知识库
  vector_store.py       # ChromaDB 向量存储
  document_processor.py # 文档解析与分块
  sample_kb.txt         # 示例知识库文档
static/                 # 前端 JS/CSS
templates/              # HTML 模板
rag_data/               # ChromaDB 持久化存储（运行时生成）
uploads/                # 上传文件存储（运行时生成）
settings.json           # API 配置（不提交到版本控制）
```

## ⚙️ 支持的模型提供商

| 提供商 | base_url |
|--------|----------|
| DeepSeek | `https://api.deepseek.com/v1` |
| 智谱 GLM | `https://open.bigmodel.cn/api/paas/v4` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` |
| Moonshot | `https://api.moonshot.cn/v1` |
| SiliconFlow | `https://api.siliconflow.cn/v1` |
| OpenAI | `https://api.openai.com/v1` |
| 自定义 | 任意 OpenAI 兼容端点 |

## 📄 License

[MIT License](LICENSE)
