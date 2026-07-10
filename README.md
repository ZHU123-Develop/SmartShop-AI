# 🤖 SmartShop-AI — AI 智能电商客服系统

> 一个支持多模型、工具调用和 RAG 知识库检索的 AI 电商智能客服助手。

[![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-black?logo=flask)](https://flask.palletsprojects.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-API-412991?logo=openai)](https://openai.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## ✨ 功能特性

### 🧠 多模型支持
| 提供商 | 模型 | 工具调用 |
|--------|------|---------|
| **DeepSeek** | deepseek-chat, deepseek-coder | ✅ |
| **智谱 AI (GLM)** | glm-4-flash | ❌ |
| **通义千问 (Qwen)** | qwen-turbo, qwen-plus, qwen-max, qwen-long | ✅ |
| **Moonshot (Kimi)** | moonshot-v1-8k ~ 128k | ❌ |
| **硅基流动** | DeepSeek-V3, Pro/DeepSeek-V3 | ✅ |
| **OpenAI** | gpt-4o, gpt-4o-mini, gpt-3.5-turbo | ✅ |
| **自定义** | 任意兼容 OpenAI API 的模型 | 按需 |

### 🛠️ 工具调用（Function Calling）
| 工具 | 功能 | 数据 |
|------|------|------|
| 📦 `query_order` | 订单查询 | 模拟数据（6个示例订单） |
| 📬 `query_logistics` | 物流追踪 | 模拟数据（4条物流单号） |
| 🔄 `query_return_refund` | 退换货查询 | 模拟数据（4个退换货记录） |
| 👤 `query_member_info` | 会员信息查询 | 模拟数据（5个会员） |
| 🌤️ `get_weather` | 实时天气查询 | wttr.in 免费 API |
| 🔢 `calculate` | 数学计算（安全 AST） | 支持四则运算和幂运算 |
| ⏰ `get_current_time` | 日期时间查询 | 支持多时区 |
| 🔍 `web_search` | Bing 网页搜索 | 无需 API Key（HTML 解析） |
| 🦆 `duckduckgo_search` | DuckDuckGo 搜索 | 无需 API Key（JSON API） |

### 📚 RAG 知识库
- 基于 **ChromaDB** 的向量检索
- 智能文档分块（支持重叠、段落边界感知）
- 支持 TXT / PDF / DOCX 格式导入
- 相似度阈值过滤，确保结果相关性
- 29 条电商售后 FAQ 内置知识库

### 💬 对话体验
- **SSE 流式输出** — 实时显示 AI 回复
- **会话管理** — 多会话切换、历史持久化
- **Markdown 渲染** — 使用 marked.js + DOMPurify
- **暗色/亮色主题** — 一键切换
- **文件上传** — 支持 TXT/PDF/图片/DOCX
- **停止生成** — 随时中断 AI 回复
- **移动端适配** — 响应式侧边栏

---

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **后端** | Python 3.10+, Flask 3.1, OpenAI SDK |
| **数据库** | SQLite（会话/消息持久化） |
| **向量存储** | ChromaDB（RAG 知识库） |
| **前端** | 原生 HTML/CSS/JS (Fetch API, SSE) |
| **Markdown** | marked.js + DOMPurify（XSS 防护） |
| **文档解析** | PyMuPDF / pdfplumber / python-docx |
| **搜索** | Bing / DuckDuckGo（无需 API Key） |
| **天气** | wttr.in（免费，无需 API Key） |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 基础依赖
pip install flask openai requests

# 安装 RAG 知识库支持（可选）
pip install chromadb

# 安装文档解析支持（可选）
pip install PyMuPDF pdfplumber python-docx

# 或一键安装全部
pip install -r requirements.txt
```

### 2. 配置 API Key

通过环境变量设置（推荐，避免明文存储）：

```bash
# Windows (PowerShell)
$env:LLM_API_KEY="your-api-key-here"
$env:LLM_BASE_URL="https://api.deepseek.com/v1"
$env:LLM_MODEL="deepseek-chat"

# Linux/Mac
export LLM_API_KEY="your-api-key-here"
export LLM_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"
```

或通过网页界面「设置」面板配置。

### 3. 启动服务

```bash
# 生产模式
python app.py

# 调试模式
python app.py --debug
# 或
$env:FLASK_DEBUG=1; python app.py
```

访问 **http://localhost:5000** 🎉

---

## 📖 使用指南

### 选择模型
1. 点击左下角⚙️设置按钮
2. 选择 AI 提供商（如 DeepSeek、OpenAI、智谱等）
3. 输入 API Key 和 API 地址
4. 选择模型，保存设置

### 新对话
- 点击左侧「新对话」按钮
- 或点击欢迎页面的功能卡片快速开始

### 查询订单
```
查询订单 ORD20240101001
```
```
查一下我的物流单号 SF1234567890
```

### 查询会员
```
查询手机号 13800000001 的会员信息
```

### 使用知识库
```
你们有什么退换货政策？
会员等级怎么升级？
```

---

## 📁 项目结构

```
SmartShop-AI/
├── app.py                    # Flask 主应用（路由 + 数据库 + 设置）
├── ai_client.py              # AI API 客户端（对话 + 工具调用 + RAG）
├── settings.json             # 运行时配置（.gitignore 忽略）
├── requirements.txt          # Python 依赖
├── pyproject.toml            # 项目元数据
├── CLAUDE.md                 # AI 辅助开发指南
├── LICENSE                   # MIT 许可证
├── templates/
│   └── index.html            # 主页面（聊天界面 + 设置面板）
├── static/
│   ├── style.css             # 全局样式（暗色/亮色主题）
│   └── app.js                # 前端逻辑（SSE 流式 + 会话管理）
├── tools/                    # 工具函数（Function Calling）
│   ├── registry.py           #   工具注册中心
│   ├── order_query.py        #   订单查询（模拟数据）
│   ├── logistics_track.py    #   物流追踪（模拟数据）
│   ├── return_refund.py      #   退换货查询（模拟数据）
│   ├── member_info.py        #   会员信息查询（模拟数据）
│   ├── weather.py            #   天气查询（wttr.in API）
│   ├── calculator.py         #   安全计算器（AST 解析）
│   ├── datetime_tool.py      #   日期时间工具
│   ├── bing_search.py        #   Bing 网页搜索
│   └── duckduckgo_search.py  #   DuckDuckGo 搜索
├── rag/                      # RAG 知识库模块
│   ├── vector_store.py       #   ChromaDB 向量存储封装
│   ├── document_processor.py #   文档解析与分块
│   └── sample_kb.txt         #   电商 FAQ 知识库样本
├── rag_data/                 # ChromaDB 持久化数据（.gitignore 忽略）
├── uploads/                  # 上传文件目录（.gitignore 忽略）
└── chatbot.db                # SQLite 会话数据库（.gitignore 忽略）
```

---

## 🔌 API 接口

| 方法 | 路径 | 说明 | 限流 |
|------|------|------|------|
| GET | `/` | 主页面 | - |
| GET | `/settings` | 获取配置和模型列表 | - |
| PUT | `/settings` | 更新配置 | - |
| GET | `/sessions` | 获取会话列表 | - |
| GET | `/sessions/<id>` | 获取会话消息 | - |
| DELETE | `/sessions/<id>` | 删除会话 | - |
| POST | `/chat` | 发送消息（SSE 流式） | ✅ 20次/分钟 |
| POST | `/stop/<key>` | 停止生成 | - |
| POST | `/upload` | 上传文件 | - |

### 聊天 API 示例

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "查询订单 ORD20240101001", "session_id": "abc123"}'
```

响应为 SSE 流式格式：
```
data: {"type":"chunk","content":"您好"}
data: {"type":"chunk","content":"！"}
data: {"type":"done","session_id":"abc123"}
```

---

## 🔒 安全特性

- ✅ **API Key 不硬编码** — 支持环境变量 `LLM_API_KEY` 或运行时设置
- ✅ **DOMPurify 过滤** — 前端 Markdown 渲染防 XSS
- ✅ **安全计算器** — AST 解析，非 `eval()` 执行
- ✅ **速率限制** — 聊天接口 20 次/分钟/IP
- ✅ **文件上传白名单** — 仅允许 txt/pdf/png/jpg/doc/docx
- ✅ **settings.json 被 Git 忽略** — 避免 API Key 误提交
- ✅ **SQLite 防注入** — 参数化查询，无字符串拼接

---

## 🧪 测试数据

### 订单号
| 订单号 | 状态 | 客户 |
|--------|------|------|
| ORD20240101001 | 已发货 | 张示例 |
| ORD20240102002 | 待付款 | 李示例 |
| ORD20240103003 | 已签收 | 王示例 |
| ORD20240104004 | 已付款 | 赵示例 |
| ORD20240105005 | 已退货 | 张示例 |
| ORD20240106006 | 已发货 | 孙示例 |

### 快递单号
| 单号 | 快递公司 |
|------|---------|
| SF1234567890 | 顺丰 |
| YZ9876543210 | 邮政 |
| SF5566778899 | 顺丰（退货） |
| YZ1122334455 | 邮政 |

### 会员手机号
| 手机号 | 等级 |
|--------|------|
| 13800000001 | 黄金会员 |
| 13800000002 | 普通会员 |
| 13800000003 | 白银会员 |
| 13800000004 | 钻石会员 |
| 13800000005 | 黄金会员 |

### 退货单号
| 单号 | 状态 |
|------|------|
| RET20240101001 | 退款已处理 |
| RET20240102002 | 审核中 |
| RET20240103003 | 同意换货 |
| RET20240104004 | 已退货待审核 |

---

## 📄 许可证

[MIT License](LICENSE)

---

<p align="center">
  <sub>Built with ❤️ — 多模型 AI 电商客服系统</sub>
</p>
