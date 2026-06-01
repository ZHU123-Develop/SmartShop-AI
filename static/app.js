// ========== 核心应用模块 ==========
const App = {
    state: {
        sessions: JSON.parse(localStorage.getItem("chat_sessions") || "{}"),
        currentSessionId: null,
        isStreaming: false,
        currentStopKey: null,
        modelPresets: {},
        currentSettings: {},
        ui: {
            theme: localStorage.getItem('theme') || 'dark',
            showTime: false,
            autoScroll: true
        }
    },

    elements: {},

    // ========== 初始化 ==========
    init() {
        try {
            this.cacheElements();
            this.setupEventListeners();
            this.applyTheme();
            this.renderHistoryList();
            this.updatePageTitle();
            // Async operations - fire and forget with error handling
            this.loadSettings().catch(e => console.error("加载设置失败:", e));
            this.loadSessionsFromServer().catch(e => console.error("加载会话失败:", e));
        } catch (e) {
            console.error("App 初始化失败:", e);
        }
    },

    cacheElements() {
        const ids = [
            'sidebar', 'sidebar-overlay', 'history-list',
            'welcome-screen', 'chat-container', 'chat-box',
            'user-input', 'send-btn', 'stop-btn',
            'input-wrapper', 'scroll-indicator', 'page-title',
            'settings-modal', 'settings-overlay', 'settings-info',
            'custom-model-section',
            'suggestions', 'char-count', 'file-input', 'attach-btn'
        ];
        ids.forEach(id => {
            this.elements[id] = document.getElementById(id);
        });
    },

    setupEventListeners() {
        // 输入框
        const input = this.elements['user-input'];
        if (input) {
            input.addEventListener("input", (e) => {
                this.autoResizeTextarea(e.target);
                this.updateCharCount();
                this.updateSuggestions();
            });
            input.addEventListener("keydown", (e) => this.handleKeyDown(e));
        }

        // 聊天容器滚动
        const chatContainer = this.elements['chat-container'];
        if (chatContainer) {
            chatContainer.addEventListener('scroll', () => this.handleScroll());
        }

        // 设置遮罩关闭
        const settingsOverlay = this.elements['settings-overlay'];
        if (settingsOverlay) {
            settingsOverlay.addEventListener('click', () => this.closeSettings());
        }

        // 侧边栏遮罩关闭
        const sidebarOverlay = this.elements['sidebar-overlay'];
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', () => this.toggleSidebar());
        }

        // 拖放支持
        this.setupDragAndDrop();

        // 窗口大小变化
        window.addEventListener('resize', () => this.handleResize());

        // 粘贴图片
        document.addEventListener('paste', (e) => this.handlePaste(e));
    },

    // ========== 服务器会话加载 ==========
    async loadSessionsFromServer() {
        try {
            const resp = await fetch("/sessions");
            const data = await resp.json();
            if (data.success) {
                for (const sess of data.sessions) {
                    if (!this.state.sessions[sess.id]) {
                        const msgs = await this.fetchMessagesFromServer(sess.id);
                        if (msgs.length) {
                            this.state.sessions[sess.id] = msgs;
                        }
                    }
                }
                this.saveState();
                this.renderHistoryList();
            }
        } catch (e) {
            console.error("加载会话失败:", e);
        }
    },

    async fetchMessagesFromServer(sessionId) {
        try {
            const resp = await fetch("/sessions/" + sessionId);
            const data = await resp.json();
            return data.success ? data.messages : [];
        } catch (e) {
            return [];
        }
    },

    // ========== 状态持久化 ==========
    saveState() {
        localStorage.setItem("chat_sessions", JSON.stringify(this.state.sessions));
        localStorage.setItem("app_state", JSON.stringify({
            theme: this.state.ui.theme,
            showTime: this.state.ui.showTime
        }));
    },

    // ========== 侧边栏 ==========
    toggleSidebar() {
        const sidebar = this.elements['sidebar'];
        const overlay = this.elements['sidebar-overlay'];

        if (window.innerWidth <= 768) {
            sidebar.classList.toggle('open');
            overlay.classList.toggle('show');
        }
    },

    newChat() {
        this.state.currentSessionId = null;
        this.elements['welcome-screen'].classList.remove("hidden");
        this.elements['chat-container'].classList.add("hidden");
        this.elements['chat-box'].innerHTML = "";
        this.elements['user-input'].focus();
        this.updatePageTitle();

        if (window.innerWidth <= 768) this.toggleSidebar();
    },

    loadSession(id) {
        this.state.currentSessionId = id;
        const msgs = this.state.sessions[id] || [];
        this.elements['welcome-screen'].classList.add("hidden");
        this.elements['chat-container'].classList.remove("hidden");
        this.elements['chat-box'].innerHTML = "";

        msgs.forEach(m => this.addMessage(m.role, m.content, false));
        this.elements['user-input'].focus();
        this.renderHistoryList();
        this.updatePageTitle();

        if (window.innerWidth <= 768) this.toggleSidebar();
    },

    renderHistoryList() {
        const list = this.elements['history-list'];
        list.innerHTML = "";
        const ids = Object.keys(this.state.sessions).reverse();

        ids.forEach(id => {
            const msgs = this.state.sessions[id];
            if (!msgs || !msgs.length) return;

            const first = msgs.find(m => m.role === "user");
            const title = first ? this.truncateText(first.content, 28) : "新对话";

            const div = document.createElement("div");
            div.className = "history-item" + (id === this.state.currentSessionId ? " active" : "");
            div.innerHTML = `
                <span class="history-text">${this.escapeHtml(title)}</span>
                <span class="delete-btn" data-action="delete" data-id="${id}">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
                    </svg>
                </span>
            `;

            div.addEventListener('click', (e) => {
                if (e.target.closest('[data-action="delete"]')) {
                    e.stopPropagation();
                    this.deleteSession(id);
                    return;
                }
                this.loadSession(id);
            });

            list.appendChild(div);
        });
    },

    async deleteSession(id) {
        try { await fetch("/sessions/" + id, { method: "DELETE" }); } catch(e) {}

        delete this.state.sessions[id];
        this.saveState();

        if (id === this.state.currentSessionId) this.newChat();
        this.renderHistoryList();
        showToast('对话已删除', 'success');
    },

    // ========== 页面标题 ==========
    updatePageTitle() {
        const el = this.elements['page-title'];
        if (!el) return;

        if (this.state.currentSessionId) {
            const session = this.state.sessions[this.state.currentSessionId];
            const firstMessage = session && session.find(m => m.role === 'user');
            el.textContent = firstMessage ? this.truncateText(firstMessage.content, 30) : "AI 对话助手";
        } else {
            el.textContent = "AI 对话助手";
        }
    },

    // ========== 输入处理 ==========
    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
    },

    updateCharCount() {
        const el = this.elements['char-count'];
        if (!el) return;
        const count = this.elements['user-input'].value.length;
        el.textContent = count > 0 ? `${count} 字符` : '';
        el.classList.toggle('visible', count > 0);
        el.classList.toggle('warning', count > 3000);
    },

    updateSuggestions() {
        const el = this.elements['suggestions'];
        if (!el) return;

        const value = this.elements['user-input'].value.trim();
        if (value.length === 0) {
            this.showSuggestions(el);
        } else {
            el.classList.remove('show');
        }
    },

    showSuggestions(el) {
        const items = ['帮我总结一下', '解释一下这个概念', '写一段代码', '分析一下这个问题'];
        el.innerHTML = items
            .map(s => `<span class="suggestion-tag" onclick="useSuggestion('${this.escapeHtml(s)}')">${this.escapeHtml(s)}</span>`)
            .join('');
        el.classList.add('show');
    },

    useSuggestion(text) {
        const input = this.elements['user-input'];
        input.value = text;
        this.autoResizeTextarea(input);
        const el = this.elements['suggestions'];
        if (el) el.classList.remove('show');
        input.focus();
    },

    handleKeyDown(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            this.sendMessage();
        }
        if (e.key === "Escape") {
            if (this.elements['settings-modal'] && !this.elements['settings-modal'].classList.contains('hidden')) {
                this.closeSettings();
            } else {
                const sidebar = this.elements['sidebar'];
                if (sidebar && sidebar.classList.contains('open')) {
                    this.toggleSidebar();
                }
            }
        }
    },

    // ========== 消息发送 ==========
    sendMessage() {
        const message = this.elements['user-input'].value.trim();
        if (!message || this.state.isStreaming) return;

        // 检查 API Key 是否配置
        if (!this.state.currentSettings.api_key) {
            showToast("请先在设置中配置 API Key", "error");
            this.openSettings();
            return;
        }

        this.sendChatMessage(message, false);
    },

    async sendChatMessage(message, isRegeneration) {
        this.state.isStreaming = true;
        this.elements['send-btn'].classList.add('hidden');
        this.elements['stop-btn'].classList.remove('hidden');
        this.elements['user-input'].value = "";
        this.autoResizeTextarea(this.elements['user-input']);
        this.updateCharCount();

        const el = this.elements['suggestions'];
        if (el) el.classList.remove('show');

        // 切换到聊天视图
        this.elements['welcome-screen'].classList.add("hidden");
        this.elements['chat-container'].classList.remove("hidden");
        this.updatePageTitle();

        // 添加用户消息
        this.addMessage("user", message);

        // 创建助手消息占位
        const assistantContent = this.addMessage("assistant", "");
        assistantContent.classList.add("loading-cursor");

        // 生成停止键
        const stopKey = crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2);
        this.state.currentStopKey = stopKey;

        try {
            const response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: message,
                    session_id: this.state.currentSessionId,
                    stop_key: stopKey,
                }),
            });

            if (!response.ok) {
                throw new Error("服务器响应错误: " + response.status);
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = "";
            let fullContent = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split("\n");
                buffer = lines.pop() || "";

                for (const line of lines) {
                    if (!line.startsWith("data: ")) continue;
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === "chunk") {
                            fullContent += data.content;
                            assistantContent.innerHTML = this.renderMarkdown(fullContent);
                            this.scrollToBottom();
                        } else if (data.type === "done") {
                            this.handleMessageComplete(message, fullContent, data.session_id);
                        } else if (data.type === "stopped") {
                            fullContent += "\n\n*[生成已停止]*";
                            assistantContent.innerHTML = this.renderMarkdown(fullContent);
                            this.state.currentSessionId = data.session_id;
                        } else if (data.type === "error") {
                            fullContent += "\n\n*[错误: " + this.escapeHtml(data.content) + "]*";
                            assistantContent.innerHTML = this.renderMarkdown(fullContent);
                        }
                    } catch (e) {
                        // 忽略解析失败的 JSON
                    }
                }
            }
        } catch (err) {
            assistantContent.innerHTML = this.renderMarkdown("*连接出错: " + this.escapeHtml(err.message) + "*");
        } finally {
            assistantContent.classList.remove("loading-cursor");
            this.state.isStreaming = false;
            this.state.currentStopKey = null;
            this.elements['send-btn'].classList.remove('hidden');
            this.elements['stop-btn'].classList.add('hidden');
            this.elements['user-input'].focus();
        }
    },

    handleMessageComplete(message, fullContent, sessionId) {
        this.state.currentSessionId = sessionId;

        if (!this.state.sessions[sessionId]) {
            this.state.sessions[sessionId] = [];
        }

        this.state.sessions[sessionId].push({ role: "user", content: message });
        this.state.sessions[sessionId].push({ role: "assistant", content: fullContent });

        this.saveState();
        this.renderHistoryList();
    },

    // ========== 停止生成 ==========
    stopGeneration() {
        if (!this.state.currentStopKey) return;

        fetch("/stop/" + this.state.currentStopKey, { method: "POST" }).catch(() => {});
        // SSE 流会自行结束并触发 finally 清理
    },

    // ========== 消息渲染 ==========
    addMessage(role, content, scroll = true) {
        const div = document.createElement("div");
        div.className = "message " + role;

        const timestamp = new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });

        const avatarLabel = role === "user" ? "我" : "AI";
        const avatarSvg = role === "assistant"
            ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="1"/><line x1="12" y1="1" x2="12" y2="23"/></svg>'
            : null;

        const timeHtml = this.state.ui.showTime
            ? `<span class="message-time">${timestamp}</span>`
            : '';

        const actionsHtml = role === "assistant"
            ? `<div class="message-actions">
                 <button class="msg-action-btn" onclick="copyMessage(this)" title="复制">
                   <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                     <rect x="9" y="9" width="13" height="13" rx="2"/>
                     <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
                   </svg>
                 </button>
                 <button class="msg-action-btn" onclick="regenerateMessage(this)" title="重新生成">
                   <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                     <polyline points="23 4 23 10 17 10"/>
                     <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
                   </svg>
                 </button>
               </div>`
            : '';

        div.innerHTML = `
            <div class="avatar">${avatarSvg || avatarLabel}</div>
            <div class="message-body">
                <div class="content">${this.renderMarkdown(content)}</div>
                ${timeHtml}
                ${actionsHtml}
            </div>
        `;

        this.elements['chat-box'].appendChild(div);

        if (scroll && this.state.ui.autoScroll) {
            this.scrollToBottom();
        }

        return div.querySelector(".content");
    },

    // ========== 消息操作 ==========
    copyMessage(btn) {
        const msgBody = btn.closest(".message-body");
        if (!msgBody) return;
        const content = msgBody.querySelector(".content").innerText;
        navigator.clipboard.writeText(content).then(() => {
            const orig = btn.innerHTML;
            btn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#4caf50" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
            setTimeout(() => { btn.innerHTML = orig; }, 1500);
        }).catch(() => {});
    },

    async regenerateMessage(btn) {
        const msgDiv = btn.closest(".message");
        const allMsgs = Array.from(this.elements['chat-box'].querySelectorAll(".message"));
        const idx = allMsgs.indexOf(msgDiv);

        const userMsg = allMsgs.slice(0, idx).reverse().find(m => m.classList.contains("user"));
        if (!userMsg) return;

        const userContent = userMsg.querySelector(".content").innerText.trim();

        for (let i = allMsgs.length - 1; i >= idx; i--) {
            allMsgs[i].remove();
        }

        await this.sendChatMessage(userContent, true);
    },

    // ========== 滚动控制 ==========
    handleScroll() {
        this.updateScrollIndicator();
    },

    updateScrollIndicator() {
        const el = this.elements['scroll-indicator'];
        if (!el) return;

        const container = this.elements['chat-container'];
        const isNearBottom = container.scrollHeight - container.scrollTop <= container.clientHeight + 100;
        el.classList.toggle('hidden', isNearBottom);
    },

    scrollToBottom() {
        const container = this.elements['chat-container'];
        container.scrollTop = container.scrollHeight;

        const el = this.elements['scroll-indicator'];
        if (el) el.classList.add('hidden');
    },

    // ========== 设置管理 ==========
    async loadSettings() {
        try {
            const resp = await fetch("/settings");
            const data = await resp.json();
            if (data.success) {
                this.state.currentSettings = data.settings;
                this.state.modelPresets = data.model_presets || {};
                this.populateProviderSelect();
                this.populateFormFromSettings();
            }
        } catch (e) {
            console.error("加载设置失败:", e);
        }
    },

    /** 记录 onProviderChange 重建前的原始模型值，用于保存时回退 */
    _pendingModelValue: "",

    openSettings() {
        const modal = this.elements['settings-modal'];
        const overlay = this.elements['settings-overlay'];
        if (modal) modal.classList.remove("hidden");
        if (overlay) overlay.classList.remove("hidden");
        this.populateFormFromSettings();
    },

    closeSettings() {
        const modal = this.elements['settings-modal'];
        const overlay = this.elements['settings-overlay'];
        if (modal) modal.classList.add("hidden");
        if (overlay) overlay.classList.add("hidden");
    },

    populateProviderSelect() {
        const select = document.getElementById("setting-provider");
        if (!select) return;

        select.innerHTML = '<option value="">-- 请选择 --</option>';
        for (const [key, preset] of Object.entries(this.state.modelPresets)) {
            const opt = document.createElement("option");
            opt.value = key;
            opt.textContent = preset.name;
            select.appendChild(opt);
        }
    },

    populateFormFromSettings() {
        const apiKey = document.getElementById("setting-api-key");
        const baseUrl = document.getElementById("setting-base-url");
        const model = document.getElementById("setting-model");
        const search = document.getElementById("setting-search");
        const provider = document.getElementById("setting-provider");

        // 先保存原始模型值（onProviderChange 会重建 dropdown）
        this._pendingModelValue = this.state.currentSettings.model || "";

        if (apiKey) apiKey.value = this.state.currentSettings.api_key || "";
        if (baseUrl) baseUrl.value = this.state.currentSettings.base_url || "";
        if (search) search.value = this.state.currentSettings.search_provider || "bing";

        // 根据 base_url 检测提供商
        let detectedProvider = "";
        for (const [key, p] of Object.entries(this.state.modelPresets)) {
            if (p.base_url === this.state.currentSettings.base_url) {
                detectedProvider = key;
                break;
            }
        }

        if (detectedProvider && provider) {
            provider.value = detectedProvider;
            this.onProviderChange();
        }

        // 回填自定义模型输入框
        const customModelInput = document.getElementById("setting-custom-model");
        if (customModelInput) {
            const dp = detectedProvider || (provider ? provider.value : "");
            const preset = this.state.modelPresets[dp];
            // 如果提供商是自定义，或当前模型不在该预设的列表中 → 填入自定义输入框
            if ((dp === "custom" || !preset || !preset.models.includes(this._pendingModelValue)) && this._pendingModelValue) {
                customModelInput.value = this._pendingModelValue;
            }
        }

        // 根据提供商决定是否显示自定义模型输入框
        const customSection = this.elements['custom-model-section'];
        if (customSection) {
            customSection.classList.toggle('hidden', detectedProvider !== 'custom');
        }
    },

    onProviderChange() {
        const provider = document.getElementById("setting-provider");
        if (!provider) return;

        const preset = this.state.modelPresets[provider.value];
        const baseUrlEl = document.getElementById("setting-base-url");
        const modelEl = document.getElementById("setting-model");
        const infoEl = this.elements['settings-info'];
        const customSection = this.elements['custom-model-section'];
        const customModelInput = document.getElementById("setting-custom-model");

        // 自定义提供商：显示自定义模型输入框
        if (provider.value === "custom") {
            if (customSection) customSection.classList.remove('hidden');
            if (modelEl) {
                modelEl.innerHTML = '<option value="">-- 请在下方输入自定义模型 --</option>';
                modelEl.disabled = true;
            }
            if (customModelInput) customModelInput.focus();
        } else {
            if (customSection) customSection.classList.add('hidden');
        }

        if (!preset) {
            if (baseUrlEl) baseUrlEl.value = "";
            if (modelEl && provider.value !== "custom") {
                modelEl.innerHTML = '<option value="">-- 请先选择提供商 --</option>';
                modelEl.disabled = true;
            }
            if (infoEl) infoEl.textContent = "选择 AI 提供商后，将显示工具调用支持状态。";
            return;
        }

        if (preset.base_url && baseUrlEl) {
            baseUrlEl.value = preset.base_url;
        }

        if (modelEl) {
            modelEl.innerHTML = "";
            if (preset.models && preset.models.length) {
                modelEl.disabled = false;
                preset.models.forEach(m => {
                    const opt = document.createElement("option");
                    opt.value = m;
                    opt.textContent = m;
                    modelEl.appendChild(opt);
                });
                const customOpt = document.createElement("option");
                customOpt.value = "__custom__";
                customOpt.textContent = "-- 自定义 --";
                modelEl.appendChild(customOpt);
            } else {
                modelEl.disabled = true;
                const opt = document.createElement("option");
                opt.value = "";
                opt.textContent = "-- 请输入自定义模型名 --";
                modelEl.appendChild(opt);
            }
        }

        if (infoEl) {
            infoEl.textContent = preset.supports_tools
                ? "支持工具调用（天气、计算、搜索、时间）"
                : "不支持工具调用，仅提供对话功能";
        }
    },

    async saveSettings() {
        const provider = document.getElementById("setting-provider");
        const apiKey = document.getElementById("setting-api-key");
        const baseUrl = document.getElementById("setting-base-url");
        const model = document.getElementById("setting-model");
        const search = document.getElementById("setting-search");
        const customModelInput = document.getElementById("setting-custom-model");

        let base_url = baseUrl ? baseUrl.value.trim() : "";
        let modelValue = "";

        // 优先使用自定义模型输入框（当有值时）
        if (customModelInput && customModelInput.value.trim()) {
            modelValue = customModelInput.value.trim();
        } else if (model) {
            modelValue = model.value;
            // __custom__ 走原来的 prompt 流程（兼容老用户）
            if (modelValue === "__custom__") {
                const customModel = prompt("请输入自定义模型名称:");
                if (!customModel) return;
                modelValue = customModel.trim();
            }
        }
        // 如果 select 为空且没有自定义输入（可能是 onProviderChange 重建了选项），回退到保存时的值
        if (!modelValue && this._pendingModelValue) {
            modelValue = this._pendingModelValue;
        }

        const settings = {
            api_key: apiKey ? apiKey.value.trim() : "",
            base_url: base_url,
            model: modelValue,
            search_provider: search ? search.value : "bing",
        };

        try {
            const resp = await fetch("/settings", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(settings),
            });
            const data = await resp.json();
            if (data.success) {
                this.state.currentSettings = settings;
                this.closeSettings();
                showToast("设置已保存", "success");
            } else {
                showToast("保存失败: " + (data.error || "未知错误"), "error");
            }
        } catch (e) {
            showToast("网络错误: " + e.message, "error");
        }
    },

    // ========== 主题 ==========
    applyTheme() {
        document.body.setAttribute('data-theme', this.state.ui.theme);
    },

    toggleTheme() {
        this.state.ui.theme = this.state.ui.theme === 'light' ? 'dark' : 'light';
        this.applyTheme();
        this.saveState();
    },

    // ========== Markdown 渲染 (marked.js) ==========
    _markedConfigured: false,

    _configureMarked() {
        if (this._markedConfigured || typeof marked === "undefined") return;

        const renderer = new marked.Renderer();

        // 代码块：添加包裹容器和复制按钮
        renderer.code = function(code, language) {
            const langAttr = language ? ' class="language-' + language + '"' : '';
            const escaped = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return '<div class="code-block-wrapper">'
                + '<button class="code-copy-btn" onclick="copyCodeBlock(this)" title="复制代码">'
                + '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
                + '<rect x="9" y="9" width="13" height="13" rx="2"/>'
                + '<path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>'
                + '</svg></button>'
                + '<pre><code' + langAttr + '>' + escaped + '</code></pre>'
                + '</div>';
        };

        // 表格：添加响应式包裹
        renderer.table = function(header, body) {
            return '<div class="table-wrapper"><table>'
                + '<thead>' + header + '</thead>'
                + '<tbody>' + body + '</tbody>'
                + '</table></div>';
        };

        // 任务列表
        renderer.list = function(body) {
            // 检测是否包含任务列表项
            if (typeof body === 'string' && /<input type="checkbox"/.test(body)) {
                return '<ul class="task-list">' + body + '</ul>';
            }
            return '<ul>' + body + '</ul>';
        };

        renderer.listitem = function(text) {
            // 任务列表项
            if (/^\[x\]\s/i.test(text) || /^\[x\]/.test(text)) {
                const content = text.replace(/^\[[xX]\]\s?/, '');
                return '<li class="task-list-item"><input type="checkbox" checked disabled> ' + content + '</li>';
            }
            if (/^\[ \]\s/i.test(text) || /^\[ \]/.test(text)) {
                const content = text.replace(/^\[ \]\s?/, '');
                return '<li class="task-list-item"><input type="checkbox" disabled> ' + content + '</li>';
            }
            return '<li>' + text + '</li>';
        };

        // 删除线
        renderer.del = function(text) {
            return '<del>' + text + '</del>';
        };

        marked.setOptions({
            renderer: renderer,
            gfm: true,
            breaks: true,
        });

        this._markedConfigured = true;
    },

    renderMarkdown(text) {
        if (!text) return "";
        if (typeof marked === "undefined") {
            // marked.js 未加载时回退到纯文本
            return this.escapeHtml(text).replace(/\n/g, '<br>');
        }
        this._configureMarked();
        return marked.parse(text);
    },

    escapeHtml(text) {
        const div = document.createElement("div");
        div.textContent = text;
        return div.innerHTML;
    },

    truncateText(text, length) {
        if (text.length <= length) return text;
        return text.substring(0, length) + '...';
    },

    // ========== 文件上传 ==========
    setupDragAndDrop() {
        const wrapper = this.elements['input-wrapper'];
        if (!wrapper) return;

        wrapper.addEventListener('dragover', (e) => {
            e.preventDefault();
            wrapper.classList.add('dragging');
        });
        wrapper.addEventListener('dragleave', () => {
            wrapper.classList.remove('dragging');
        });
        wrapper.addEventListener('drop', (e) => {
            e.preventDefault();
            wrapper.classList.remove('dragging');
            const files = e.dataTransfer.files;
            if (files.length > 0) this.handleFiles(files);
        });
    },

    handlePaste(e) {
        const items = e.clipboardData && e.clipboardData.items;
        if (!items) return;

        for (const item of items) {
            if (item.type.startsWith('image/')) {
                e.preventDefault();
                showToast('图片粘贴功能开发中，请使用文件上传', 'info');
                return;
            }
        }
    },

    async handleFiles(files) {
        const file = files[0];
        if (!file) return;

        // Check file size (16MB max)
        if (file.size > 16 * 1024 * 1024) {
            showToast('文件大小超过 16MB 限制', 'error');
            return;
        }

        const ext = file.name.split('.').pop().toLowerCase();
        const allowedExts = ['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'];
        if (!allowedExts.includes(ext)) {
            showToast(`不支持的文件类型: ${file.name}`, 'error');
            return;
        }

        // Text files: read locally and put content in input
        if (ext === 'txt') {
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target.result;
                const input = this.elements['user-input'];
                input.value = text.slice(0, 4000);
                this.autoResizeTextarea(input);
                this.updateCharCount();
                showToast(`已加载文本文件: ${file.name}`, 'success');
            };
            reader.readAsText(file);
            return;
        }

        // Upload other file types to server
        showToast('正在上传文件...', 'info');
        try {
            const formData = new FormData();
            formData.append('file', file);

            const resp = await fetch('/upload', {
                method: 'POST',
                body: formData,
            });
            const data = await resp.json();

            if (data.success) {
                if (data.file_type === 'text' && data.content) {
                    // Text content returned from server
                    const input = this.elements['user-input'];
                    input.value = data.content.slice(0, 4000);
                    this.autoResizeTextarea(input);
                    this.updateCharCount();
                    showToast(`已加载文件: ${data.filename}`, 'success');
                } else {
                    // Binary file uploaded, show info message
                    const msg = data.message || `文件 '${data.filename}' 已上传`;
                    showToast(msg, 'success');
                    // Add file info to input as a reference
                    const input = this.elements['user-input'];
                    const fileRef = `[已上传文件: ${data.filename} (${data.size} 字节)] `;
                    input.value = fileRef + input.value;
                    this.updateCharCount();
                    input.focus();
                }
            } else {
                showToast(data.error || '上传失败', 'error');
            }
        } catch (e) {
            showToast('上传出错: ' + e.message, 'error');
        }
    },

    // ========== 窗口调整 ==========
    handleResize() {
        if (window.innerWidth > 768) {
            const overlay = this.elements['sidebar-overlay'];
            if (overlay) overlay.classList.remove('show');
        }
    }
};

// ========== 全局工具函数 ==========
function showToast(message, type = 'info') {
    // Remove existing toasts first to prevent stacking/blocking
    document.querySelectorAll('.settings-toast').forEach(t => t.remove());

    const toast = document.createElement("div");
    toast.className = "settings-toast " + type;
    toast.textContent = message;
    toast.style.pointerEvents = 'none'; // Don't block clicks
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ========== 全局函数（HTML onclick 调用）==========
window.newChat = () => App.newChat();
window.toggleSidebar = () => App.toggleSidebar();
window.openSettings = () => App.openSettings();
window.closeSettings = () => App.closeSettings();
window.onProviderChange = () => App.onProviderChange();
window.saveSettings = () => App.saveSettings();
window.sendMessage = () => App.sendMessage();
window.sendExample = (message) => {
    App.elements['user-input'].value = message;
    App.autoResizeTextarea(App.elements['user-input']);
    App.sendMessage();
};
window.copyMessage = (btn) => App.copyMessage(btn);
window.regenerateMessage = (btn) => App.regenerateMessage(btn);
window.copyCodeBlock = (btn) => {
    const wrapper = btn.closest('.code-block-wrapper');
    if (!wrapper) return;
    const code = wrapper.querySelector('code');
    if (!code) return;
    const text = code.innerText || code.textContent;
    navigator.clipboard.writeText(text).then(() => {
        btn.classList.add('copied');
        btn.title = '已复制!';
        setTimeout(() => {
            btn.classList.remove('copied');
            btn.title = '复制代码';
        }, 1500);
    }).catch(() => {});
};
window.scrollToBottom = () => App.scrollToBottom();
window.useSuggestion = (text) => App.useSuggestion(text);
window.stopGeneration = () => App.stopGeneration();

// 文件上传
window.triggerFileUpload = () => {
    const input = App.elements['file-input'];
    if (input) input.click();
};
window.handleFileSelected = (event) => {
    if (event.target.files && event.target.files.length > 0) {
        App.handleFiles(event.target.files);
    }
    event.target.value = '';
};

// 工具
window.toggleTheme = () => App.toggleTheme();
window.clearChat = () => {
    if (confirm('确定要清空当前对话吗？')) {
        App.newChat();
        showToast('对话已清空', 'success');
    }
};
window.clearAllData = () => {
    if (confirm('确定要清除所有数据吗？这将删除所有对话记录和设置。')) {
        localStorage.clear();
        App.state.sessions = {};
        App.saveState();
        App.newChat();
        showToast('所有数据已清除', 'success');
    }
};

// ========== 启动 ==========
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});

// ========== 全局错误捕获 ==========
window.addEventListener('error', (e) => {
    console.error('全局错误:', e.message, 'at', e.filename + ':' + e.lineno);
});
window.addEventListener('unhandledrejection', (e) => {
    console.error('未处理的 Promise 拒绝:', e.reason);
});
