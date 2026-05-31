"""Flask 主入口 - 对话系统 Web 服务。"""

import json
import uuid
from flask import Flask, request, jsonify, render_template, Response
from deepseek_client import chat_stream

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

# 内存会话存储（生产环境应使用 Redis）
conversations = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """接收用户消息，SSE 流式返回 AI 回复。"""
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "请提供消息内容"}), 400

    message = data["message"].strip()
    if not message:
        return jsonify({"error": "消息不能为空"}), 400

    # 获取或创建会话
    session_id = data.get("session_id") or uuid.uuid4().hex
    if session_id not in conversations:
        conversations[session_id] = []

    history = conversations[session_id]

    def generate():
        try:
            full_reply = ""
            for chunk in chat_stream(message, history):
                full_reply += chunk
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk}, ensure_ascii=False)}\n\n"

            # 保存对话历史
            conversations[session_id].append({"role": "user", "content": message})
            conversations[session_id].append({"role": "assistant", "content": full_reply})

            yield f"data: {json.dumps({'type': 'done', 'session_id': session_id}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
