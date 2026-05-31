let sessionId = localStorage.getItem("chat_session_id") || "";
let isStreaming = false;

const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");

// 自动调整 textarea 高度
userInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 120) + "px";
});

// Enter 发送，Shift+Enter 换行
userInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

function addMessage(role, content) {
    const div = document.createElement("div");
    div.className = `message ${role}`;
    const avatar = role === "user" ? "我" : "AI";
    div.innerHTML = `
        <div class="avatar">${avatar}</div>
        <div class="content">${escapeHtml(content)}</div>
    `;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
    return div.querySelector(".content");
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

async function sendMessage() {
    const message = userInput.value.trim();
    if (!message || isStreaming) return;

    isStreaming = true;
    sendBtn.disabled = true;
    userInput.value = "";
    userInput.style.height = "auto";

    addMessage("user", message);

    // 创建 AI 回复占位
    const assistantContent = addMessage("assistant", "");
    assistantContent.classList.add("loading");

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message,
                session_id: sessionId,
            }),
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let fullContent = "";

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop();

            for (const line of lines) {
                if (!line.startsWith("data: ")) continue;
                const data = JSON.parse(line.slice(6));

                if (data.type === "chunk") {
                    fullContent += data.content;
                    assistantContent.textContent = fullContent;
                    chatBox.scrollTop = chatBox.scrollHeight;
                } else if (data.type === "done") {
                    sessionId = data.session_id;
                    localStorage.setItem("chat_session_id", sessionId);
                } else if (data.type === "error") {
                    fullContent += "\n[错误: " + data.content + "]";
                    assistantContent.textContent = fullContent;
                }
            }
        }
    } catch (err) {
        assistantContent.textContent = "连接出错: " + err.message;
    } finally {
        assistantContent.classList.remove("loading");
        isStreaming = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}
