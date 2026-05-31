// ========== State ==========
let sessions = JSON.parse(localStorage.getItem("chat_sessions") || "{}");
let currentSessionId = null;
let isStreaming = false;
let currentRequestKey = null;
let modelPresets = {};
let currentSettings = {};

// ========== DOM ==========
const sidebar = document.getElementById("sidebar");
const historyList = document.getElementById("history-list");
const welcomeScreen = document.getElementById("welcome-screen");
const chatContainer = document.getElementById("chat-container");
const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const sendBtn = document.getElementById("send-btn");
const sidebarOverlay = document.getElementById("sidebar-overlay");

// Settings DOM
const settingsOverlay = document.getElementById("settings-overlay");
const settingsModal = document.getElementById("settings-modal");
const settingProvider = document.getElementById("setting-provider");
const settingApiKey = document.getElementById("setting-api-key");
const settingBaseUrl = document.getElementById("setting-base-url");
const settingModel = document.getElementById("setting-model");
const settingSearch = document.getElementById("setting-search");
const settingsInfo = document.getElementById("settings-info");

// ========== Init ==========
renderHistoryList();
loadSettings();
loadSessionsFromServer();
// ========== Server Sessions (SQLite) ==========
async function loadSessionsFromServer() {
    try {
        const resp = await fetch("/sessions");
        const data = await resp.json();
        if (data.success) {
            // Merge server sessions into local storage
            sessions = {};
            for (const sess of data.sessions) {
                const msgs = await fetchMessagesFromServer(sess.id);
                if (msgs.length) {
                    sessions[sess.id] = msgs;
                }
            }
            renderHistoryList();
        }
    } catch (e) {
        console.error("加载会话失败:", e);
    }
}

async function fetchMessagesFromServer(sessionId) {
    try {
        const resp = await fetch("/sessions/" + sessionId);
        const data = await resp.json();
        return data.success ? data.messages : [];
    } catch (e) {
        return [];
    }
}

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

async function deleteSession(id) {
    // Delete from server
    try { await fetch("/sessions/" + id, { method: "DELETE" }); } catch(e) {}
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
function addMessage(role, content, scroll, isRegeneration) {
    const div = document.createElement("div");
    div.className = "message " + role;
    const avatarLabel = role === "user" ? "我" : "AI";
    const avatarSvg = role === "assistant"
        ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="1"/><line x1="12" y1="1" x2="12" y2="23"/></svg>'
        : null;

    const actionsHtml = role === "assistant"
        ? '<div class="message-actions">' +
            '<button class="msg-action-btn" onclick="copyMessage(this)" title="复制">' +
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/></svg></button>' +
            '<button class="msg-action-btn" onclick="regenerateMessage(this)" title="重新生成">' +
            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg></button>' +
            '</div>'
        : '';

    div.innerHTML =
        '<div class="avatar">' + (avatarSvg || avatarLabel) + '</div>' +
        '<div class="message-body">' +
            '<div class="content">' + renderMarkdown(content) + '</div>' +
            actionsHtml +
        '</div>';
    chatBox.appendChild(div);
    if (scroll) {
        chatContainer.scrollTop = chatContainer.scrollHeight;
    }
    return div.querySelector(".content");
}

function copyMessage(btn) {
    const content = btn.closest(".message-body").querySelector(".content").innerText;
    navigator.clipboard.writeText(content).then(() => {
        const orig = btn.innerHTML;
        btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4caf50" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
        setTimeout(() => { btn.innerHTML = orig; }, 1500);
    });
}

async function regenerateMessage(btn) {
    const msgDiv = btn.closest(".message");
    const allMsgs = Array.from(chatBox.querySelectorAll(".message"));
    const idx = allMsgs.indexOf(msgDiv);

    // Find the user message before this AI message
    const userMsg = allMsgs.slice(0, idx).reverse().find(m => m.classList.contains("user"));
    if (!userMsg) return;

    const userContent = userMsg.querySelector(".content").innerText.trim();

    // Remove this AI message and everything after it
    for (let i = allMsgs.length - 1; i >= idx; i--) {
        allMsgs[i].remove();
    }

    // Resend
    await sendChatMessage(userContent, true);
}

// ========== Markdown Rendering ==========
function renderMarkdown(text) {
    if (!text) return "";
    let html = escapeHtml(text);

    // Code blocks (``` ... ```)
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, function(match, lang, code) {
        const langAttr = lang ? ' class="language-' + lang + '"' : '';
        return '<pre><code' + langAttr + '>' + code.trimEnd() + '</code></pre>';
    });

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold
    html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');

    // Headers
    html = html.replace(/^###### (.+)$/gm, '<h6>$1</h6>');
    html = html.replace(/^##### (.+)$/gm, '<h5>$1</h5>');
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
    html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');

    // Links
    html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');

    // Unordered lists
    html = html.replace(/^\s*[-*]\s+(.+)$/gm, '<li>$1</li>');
    html = html.replace(/((<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

    // Horizontal rule
    html = html.replace(/^---$/gm, '<hr>');

    // Blockquote
    html = html.replace(/^&gt;\s+(.+)$/gm, '<blockquote>$1</blockquote>');

    // Line breaks (preserve paragraphs)
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');
    html = '<p>' + html + '</p>';

    // Clean up empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>\s*(<pre|<ul|<h[1-6]|<hr|<blockquote)/g, '$1');
    html = html.replace(/(<\/pre>|<\/ul>|<\/h[1-6]>)\s*<\/p>/g, '$1');
    html = html.replace(/(<hr>)\s*<\/p>/g, '$1');
    html = html.replace(/(<blockquote>)\s*<\/p>/g, '$1');

    return html;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ========== Send Message ==========
function sendMessage() {
    const message = userInput.value.trim();
    if (!message || isStreaming) return;
    sendChatMessage(message, false);
}

async function sendChatMessage(message, isRegeneration) {
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
                        assistantContent.innerHTML = renderMarkdown(fullContent);
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
                    } else if (data.type === "stopped") {
                        fullContent += "\n[生成已停止]";
                        assistantContent.innerHTML = renderMarkdown(fullContent);
                        currentSessionId = data.session_id;
                    } else if (data.type === "error") {
                        fullContent += "\n[错误: " + data.content + "]";
                        assistantContent.innerHTML = renderMarkdown(fullContent);
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

// ========== Settings ==========
async function loadSettings() {
    try {
        const resp = await fetch("/settings");
        const data = await resp.json();
        if (data.success) {
            currentSettings = data.settings;
            modelPresets = data.model_presets || {};
            populateProviderSelect();
            populateFormFromSettings();
        }
    } catch (e) {
        console.error("加载设置失败:", e);
    }
}

function populateProviderSelect() {
    settingProvider.innerHTML = '<option value="">-- 请选择 --</option>';
    for (const [key, preset] of Object.entries(modelPresets)) {
        const opt = document.createElement("option");
        opt.value = key;
        opt.textContent = preset.name;
        settingProvider.appendChild(opt);
    }
}

function populateFormFromSettings() {
    settingApiKey.value = currentSettings.api_key || "";
    settingBaseUrl.value = currentSettings.base_url || "";
    settingModel.value = currentSettings.model || "";
    settingSearch.value = currentSettings.search_provider || "bing";

    // Try to detect provider from base_url
    let detectedProvider = "";
    for (const [key, preset] of Object.entries(modelPresets)) {
        if (preset.base_url === currentSettings.base_url) {
            detectedProvider = key;
            break;
        }
    }
    if (detectedProvider) {
        settingProvider.value = detectedProvider;
        onProviderChange();
    }
}

function onProviderChange() {
    const providerKey = settingProvider.value;
    const preset = modelPresets[providerKey];

    if (!preset) {
        settingBaseUrl.value = "";
        settingModel.innerHTML = '<option value="">-- 请先选择提供商 --</option>';
        settingModel.disabled = true;
        settingsInfo.textContent = "选择 AI 提供商后，将显示工具调用支持状态。";
        return;
    }

    // Fill base URL
    if (preset.base_url) {
        settingBaseUrl.value = preset.base_url;
    }

    // Fill model dropdown
    settingModel.innerHTML = "";
    if (preset.models && preset.models.length) {
        settingModel.disabled = false;
        preset.models.forEach(m => {
            const opt = document.createElement("option");
            opt.value = m;
            opt.textContent = m;
            settingModel.appendChild(opt);
        });
        // Keep custom input as last option
        const customOpt = document.createElement("option");
        customOpt.value = "__custom__";
        customOpt.textContent = "-- 自定义 --";
        settingModel.appendChild(customOpt);
    } else {
        settingModel.disabled = true;
        const opt = document.createElement("option");
        opt.value = "";
        opt.textContent = "-- 请输入自定义模型名 --";
        settingModel.appendChild(opt);
    }

    // Update info
    const toolStatus = preset.supports_tools
        ? "支持工具调用（天气、计算、搜索、时间）"
        : "不支持工具调用，仅提供对话功能";
    settingsInfo.textContent = toolStatus;
}

function openSettings() {
    settingsOverlay.classList.remove("hidden");
    settingsModal.classList.remove("hidden");
    populateFormFromSettings();
}

function closeSettings() {
    settingsOverlay.classList.add("hidden");
    settingsModal.classList.add("hidden");
}

async function saveSettings() {
    const providerKey = settingProvider.value;
    let base_url = settingBaseUrl.value.trim();
    let model = settingModel.value;

    // If custom model selected, treat as needing manual input
    if (model === "__custom__") {
        const customModel = prompt("请输入自定义模型名称:");
        if (!customModel) return;
        model = customModel.trim();
    }

    const settings = {
        api_key: settingApiKey.value.trim(),
        base_url: base_url,
        model: model,
        search_provider: settingSearch.value,
    };

    try {
        const resp = await fetch("/settings", {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(settings),
        });
        const data = await resp.json();
        if (data.success) {
            currentSettings = settings;
            closeSettings();
            showSettingsToast("设置已保存", "success");
        } else {
            showSettingsToast("保存失败: " + (data.error || "未知错误"), "error");
        }
    } catch (e) {
        showSettingsToast("网络错误: " + e.message, "error");
    }
}

function showSettingsToast(msg, type) {
    const toast = document.createElement("div");
    toast.className = "settings-toast " + type;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}
