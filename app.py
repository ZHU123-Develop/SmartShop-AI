"""Flask 主入口 - 对话系统 Web 服务。"""

import json
import os
import sqlite3
import time
import uuid
import mimetypes
from functools import wraps
from flask import Flask, request, jsonify, render_template, Response, g, send_file
from ai_client import chat_stream, _set_vector_store

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max file size

# 配置文件路径
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "chatbot.db")
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 初始化 RAG 知识库向量存储
try:
    from rag.vector_store import VectorStore
    _vector_store = VectorStore()
    _set_vector_store(_vector_store)
except ImportError:
    # chromadb 未安装时静默跳过
    pass
except Exception:
    pass

# 跟踪正在进行的流式请求，用于停止生成
active_streams = {}

# 简易速率限制
_rate_limit_store = {}
_RATE_LIMIT = 20  # 每分钟最多请求数


def rate_limit(f):
    """简易 IP 速率限制装饰器。"""
    @wraps(f)
    def decorated(*args, **kwargs):
        ip = request.remote_addr or "unknown"
        now = time.time()
        window = 60  # 1 分钟窗口

        # 清理过期记录
        _rate_limit_store[ip] = [t for t in _rate_limit_store.get(ip, []) if now - t < window]

        if len(_rate_limit_store[ip]) >= _RATE_LIMIT:
            return jsonify({"success": False, "error": "请求过于频繁，请稍后再试"}), 429

        _rate_limit_store[ip].append(now)
        return f(*args, **kwargs)
    return decorated

# 默认配置
DEFAULT_SETTINGS = {
    "api_key": "",
    "base_url": "https://api.deepseek.com/v1",
    "model": "deepseek-chat",
    "search_provider": "bing",
}

# 预定义模型列表
MODEL_PRESETS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-chat", "deepseek-coder"],
        "supports_tools": True,
    },
    "zhipu": {
        "name": "智谱 AI (GLM)",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "models": ["glm-4-flash"],
        "supports_tools": False,
    },
    "qwen": {
        "name": "通义千问 (Qwen)",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-turbo", "qwen-plus", "qwen-max", "qwen-long"],
        "supports_tools": True,
    },
    "moonshot": {
        "name": "Moonshot (Kimi)",
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "supports_tools": False,
    },
    "siliconflow": {
        "name": "硅基流动 (SiliconFlow)",
        "base_url": "https://api.siliconflow.cn/v1",
        "models": ["deepseek-ai/DeepSeek-V3", "Pro/deepseek-ai/DeepSeek-V3"],
        "supports_tools": True,
    },
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "supports_tools": True,
    },
    "custom": {
        "name": "自定义",
        "base_url": "",
        "models": [],
        "supports_tools": False,
    },
}


# ========== SQLite 数据库 ==========
def get_db():
    """获取当前请求的数据库连接。"""
    if "db" not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception):
    """关闭数据库连接。"""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """初始化数据库表。"""
    db = sqlite3.connect(DB_FILE)
    db.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL,
            title TEXT NOT NULL DEFAULT ''
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            order_index INTEGER NOT NULL,
            created_at REAL NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    db.commit()
    db.close()


def db_get_sessions():
    """获取所有会话列表。"""
    db = get_db()
    rows = db.execute(
        "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC"
    ).fetchall()
    return [dict(r) for r in rows]


def db_get_messages(session_id):
    """获取会话的所有消息。"""
    db = get_db()
    rows = db.execute(
        "SELECT role, content FROM messages WHERE session_id = ? ORDER BY order_index",
        (session_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def db_save_session(session_id, messages):
    """保存会话和消息。使用独立连接，不依赖 Flask g 对象（可能在生成器中调用）。"""
    db = sqlite3.connect(DB_FILE)
    now = time.time()

    # 获取第一条用户消息作为标题
    first_user = next((m for m in messages if m["role"] == "user"), None)
    title = (first_user["content"][:30] if first_user else "新对话").strip()

    # UPSERT 会话
    db.execute("""
        INSERT INTO sessions (id, title, created_at, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET title = excluded.title, updated_at = excluded.updated_at
    """, (session_id, title, now, now))

    # 删除旧消息
    db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))

    # 插入新消息
    for idx, m in enumerate(messages):
        db.execute(
            "INSERT INTO messages (session_id, role, content, order_index, created_at) VALUES (?, ?, ?, ?, ?)",
            (session_id, m["role"], m["content"], idx, now)
        )

    db.commit()
    db.close()


def db_delete_session(session_id):
    """删除会话。"""
    db = get_db()
    db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
    db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    db.commit()


# ========== 配置管理 ==========
def load_settings():
    """从配置文件加载设置。"""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_SETTINGS.copy()


def save_settings(settings):
    """保存设置到配置文件。"""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


# ========== 路由 ==========
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/settings", methods=["GET"])
def get_settings():
    """获取当前配置。"""
    settings = load_settings()
    return jsonify({
        "success": True,
        "settings": settings,
        "model_presets": MODEL_PRESETS,
    })


@app.route("/settings", methods=["PUT"])
def update_settings():
    """更新配置。"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "请提供配置数据"}), 400

    settings = load_settings()
    for key in ["api_key", "base_url", "model", "search_provider"]:
        if key in data:
            settings[key] = data[key]

    save_settings(settings)
    return jsonify({"success": True})


@app.route("/sessions", methods=["GET"])
def list_sessions():
    """获取所有会话列表。"""
    sessions = db_get_sessions()
    return jsonify({"success": True, "sessions": sessions})


@app.route("/sessions/<session_id>", methods=["GET"])
def get_session(session_id):
    """获取单个会话的消息。"""
    messages = db_get_messages(session_id)
    return jsonify({"success": True, "messages": messages})


@app.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    """删除会话。"""
    db_delete_session(session_id)
    return jsonify({"success": True})


@app.route("/chat", methods=["POST"])
@rate_limit
def chat():
    """接收用户消息，SSE 流式返回 AI 回复。"""
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "请提供消息内容"}), 400

    message = data["message"].strip()
    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    session_id = data.get("session_id") or uuid.uuid4().hex

    # 从数据库加载历史
    history = db_get_messages(session_id)

    # 使用客户端提供的 stop_key，或自动生成
    request_key = data.get("stop_key") or uuid.uuid4().hex
    active_streams[request_key] = {"abort": False}

    def generate():
        stream_key = request_key
        try:
            full_reply = ""
            for chunk in chat_stream(message, history):
                # 检查是否被要求停止
                if active_streams.get(stream_key, {}).get("abort"):
                    # 如果已经收集到部分内容，发送停止事件
                    if full_reply:
                        yield f"data: {json.dumps({'type': 'stopped', 'session_id': session_id}, ensure_ascii=False)}\n\n"
                    return
                full_reply += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            # 保存对话历史到数据库
            new_messages = history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": full_reply},
            ]
            db_save_session(session_id, new_messages)

            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
        finally:
            active_streams.pop(stream_key, None)

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@app.route("/stop/<request_key>", methods=["POST"])
def stop_generation(request_key):
    """停止当前流式生成。"""
    if request_key in active_streams:
        active_streams[request_key]["abort"] = True
    return jsonify({"success": True})


# ========== 文件上传 ==========
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx"}


def allowed_file(filename):
    """检查文件扩展名是否允许。"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/upload", methods=["POST"])
def upload_file():
    """接收文件上传，返回文件信息供对话使用。"""
    if "file" not in request.files:
        return jsonify({"success": False, "error": "未找到文件"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"success": False, "error": "未选择文件"}), 400

    if not allowed_file(file.filename):
        return jsonify({"success": False, "error": f"不支持的文件类型: {file.filename}"}), 400

    try:
        # 生成安全文件名
        ext = file.filename.rsplit(".", 1)[1].lower()
        safe_name = f"{uuid.uuid4().hex}.{ext}"
        file_path = os.path.join(UPLOAD_FOLDER, safe_name)
        file.save(file_path)

        file_size = os.path.getsize(file_path)
        mime_type = mimetypes.guess_type(file_path)[0] or "application/octet-stream"

        # 对于文本文件，直接读取内容返回
        if ext == "txt":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                text = f.read()[:4000]  # 限制长度
            return jsonify({
                "success": True,
                "filename": file.filename,
                "file_type": "text",
                "content": text,
                "size": file_size,
            })

        # 对于 PDF/图片，返回文件信息（前端可以决定如何展示）
        return jsonify({
            "success": True,
            "filename": file.filename,
            "file_type": "binary",
            "mime_type": mime_type,
            "size": file_size,
            "message": f"文件 '{file.filename}' 已上传 ({file_size} 字节)，请在对话中引用。",
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"上传失败: {e}"}), 500


if __name__ == "__main__":
    import sys

    # 命令行参数支持环境切换
    debug = "--debug" in sys.argv or os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true")

    # 初始化数据库（CLI 或首次启动时使用）
    init_db()

    app.run(debug=debug, host="0.0.0.0", port=5000)
