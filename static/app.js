// ========== State ==========
let sessions = JSON.parse(localStorage.getItem("chat_sessions") || "{}");
let currentSessionId = null;
let isStreaming = false;

// ========== DOM ==========
const sidebar = document.getElementById("sidebar");
const historyList = document.getElementById("history-list");
const welcomeScreen = document.getElementById("welcome-screen");
const chatContainer = document.getElementById("chat-container");
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const sidebarOverlay = document.getElementById("sidebar-overlay");

// ========== Init ==========
renderHistoryList();

// ========== Sidebar ==========
function toggleSidebar() {
    sidebar.classList.toggle("open");
    sidebarOverlay.classList.toggle("show");
}

function newChat() {
    currentSessionId = null;
    welcomeScreen.classList.remove("hidden");
    chatContainer.classList.add("hidden");
    chatBox.innerHTML = "";
    userInput.focus();
    if (window.innerWidth <= 768) toggleSidebar();
}

function renderHistoryList() {
    historyList.innerHTML = "";
    const ids = Object.keys(sessions).reverse();
    ids.forEach(id => {
        const msgs = sessions[id];
        if (!msgs || !msgs.length) return;
        const first = msgs.find(m => m.role === "user");
        const title = first ? first.content.slice(0, 28) : "新对话";
        const div = document.createElement("div");
        div.className = "history-item" + (id === currentSessionId ? " active" : "");
        div.innerHTML =
            '<span class="history-text">' + escapeHtml(title) + '</span>' +
            '<span class="delete-btn" onclick="event.stopPropagation(); deleteSession(\'' + id + '\')">' +
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
            '<line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></span>';
        div.onclick = () => loadSession(id);
        historyList.appendChild(div);
    });
}

function saveSessions() {
    localStorage.setItem("chat_sessions", JSON.stringify(sessions));
}

function deleteSession(id) {
    delete sessions[id];
    saveSessions();
    if (id === currentSessionId) newChat();
    renderHistoryList();
}

function loadSession(id) {
    currentSessionId = id;
    const msgs = sessions[id] || [];
    welcomeScreen.classList.add("hidden");
    chatContainer.classList.remove("hidden");
    chatBox.innerHTML = "";
    msgs.forEach(m => addMessage(m.role, m.content, false));
    userInput.focus();
    renderHistoryList();
    if (window.innerWidth <= 768) toggleSidebar();
}

// ========== Input ==========
userInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 150) + "px";
});

userInput.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// ========== Messages ==========
function addMessage(role, content, scroll = true) {
    const div = document.createElement("div");
    div.className = "message " + role;
    const avatarLabel = role === "user" ? "我" : "AI";
    const avatarSvg = role === "assistant"
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="1"/><line x1="12" y1="1" x2="12" y2="23"/></svg>'
        : null;
    div.innerHTML =
        '<div class="avatar">' + (avatarSvg || avatarLabel) + '</div>' +
        '<div class="content">' + formatContent(content) + '</div>';
    chatBox.appendChild(div);
    if (scroll) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    return div.querySelector(".content");
}

function formatContent(text) {
    // Basic markdown: code blocks and inline code
    let html = escapeHtml(text);
    // Code blocks
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');
    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
    return html;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ========== Send Message ==========
async function sendMessage() {
    const message = userInput.value.trim();
    if (!message || isStreaming) return;

    isStreaming = true;
    sendBtn.disabled = true;
    userInput.value = "";
    userInput.style.height = "auto";

    // Switch to chat view
    welcomeScreen.classList.add("hidden");
    chatContainer.classList.remove("hidden");

    addMessage("user", message);

    // Create assistant placeholder
    const assistantContent = addMessage("assistant", "");
    assistantContent.classList.add("loading-cursor");

    try {
        const response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message: message,
                session_id: currentSessionId,
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
                try {
                    const data = JSON.parse(line.slice(6));
                    if (data.type === "chunk") {
                        fullContent += data.content;
                        assistantContent.innerHTML = formatContent(fullContent);
                        chatContainer.scrollTop = chatContainer.scrollHeight;
                    } else if (data.type === "done") {
                        currentSessionId = data.session_id;
                        if (!sessions[currentSessionId]) {
                            sessions[currentSessionId] = [];
                        }
                        sessions[currentSessionId].push({ role: "user", content: message });
                        sessions[currentSessionId].push({ role: "assistant", content: fullContent });
                        saveSessions();
                        renderHistoryList();
                    } else if (data.type === "error") {
                        fullContent += "\n[错误: " + data.content + "]";
                        assistantContent.innerHTML = formatContent(fullContent);
                    }
                } catch (e) {
                    // skip malformed JSON
                }
            }
        }
    } catch (err) {
        assistantContent.textContent = "连接出错: " + err.message;
    } finally {
        assistantContent.classList.remove("loading-cursor");
        isStreaming = false;
        sendBtn.disabled = false;
        userInput.focus();
    }
}
