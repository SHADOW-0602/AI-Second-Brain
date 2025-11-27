import { api } from './api.js';

export class UI {
    constructor(advancedFeatures) {
        this.mainContent = document.getElementById("main-content");
        this.pageTitle = document.getElementById("page-title");
        this.advancedFeatures = advancedFeatures;
    }

    async renderDashboard() {
        this.pageTitle.textContent = "Dashboard";
        this.mainContent.innerHTML = `
            <div class="dashboard-view fade-in">
                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>Total Documents</h3>
                        <p class="stat-value" id="total-docs">Loading...</p>
                    </div>
                    <div class="stat-card">
                        <h3>Total Chunks</h3>
                        <p class="stat-value" id="total-chunks">Loading...</p>
                    </div>
                    <div class="stat-card">
                        <h3>Storage Used</h3>
                        <p class="stat-value" id="storage-size">Loading...</p>
                    </div>
                </div>
                <div class="recent-activity">
                    <h2>Recent Files</h2>
                    <div class="activity-list" id="recent-files">
                        <p class="empty-state">Loading...</p>
                    </div>
                </div>
            </div>
        `;

        // Load real stats
        this.loadDashboardStats();
    }

    async loadDashboardStats() {
        try {
            // Load analytics
            const analyticsResponse = await fetch('/api/system/analytics');
            const analytics = await analyticsResponse.json();

            document.getElementById('total-docs').textContent = analytics.total_documents || 0;
            document.getElementById('total-chunks').textContent = analytics.total_chunks || 0;
            document.getElementById('storage-size').textContent = this.formatBytes(analytics.storage_size || 0);

            // Load recent files
            const filesResponse = await fetch('/api/system/files');
            const filesData = await filesResponse.json();

            const recentFiles = document.getElementById('recent-files');
            if (filesData.files && filesData.files.length > 0) {
                const recent = filesData.files.slice(0, 5);
                recentFiles.innerHTML = recent.map(file => `
                    <div style="padding: 0.75rem; border-left: 3px solid var(--accent-primary); background: var(--bg-card); margin-bottom: 0.5rem; border-radius: 0.5rem;">
                        <strong>${file.filename}</strong>
                        <div style="font-size: 0.9rem; color: var(--text-secondary);">${file.chunks} chunks • ${file.processed_at}</div>
                    </div>
                `).join('');
            } else {
                recentFiles.innerHTML = '<p class="empty-state">No files uploaded yet.</p>';
            }
        } catch (error) {
            document.getElementById('total-docs').textContent = 'Error';
            document.getElementById('total-chunks').textContent = 'Error';
            document.getElementById('storage-size').textContent = 'Error';
        }
    }

    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    renderAdvancedSearchPage() {
        this.pageTitle.textContent = "Advanced Search";
        this.mainContent.innerHTML = this.advancedFeatures.renderAdvancedSearch();
        this.advancedFeatures.initializeEventListeners();
        this.advancedFeatures.updateSearchHistory();
    }

    renderAnalyticsPage() {
        this.pageTitle.textContent = "Analytics Dashboard";
        this.mainContent.innerHTML = this.advancedFeatures.renderAnalyticsDashboard();
        this.advancedFeatures.loadAnalytics();
    }

    renderFileManagerPage() {
        this.pageTitle.textContent = "File Manager";
        this.mainContent.innerHTML = this.advancedFeatures.renderFileManager();
        this.loadFileManagerData();
    }

    async loadFileManagerData() {
        try {
            const response = await fetch('/api/system/files');
            const data = await response.json();
            const fileGrid = document.getElementById('file-grid');

            if (data.files && data.files.length > 0) {
                if (fileGrid) {
                    fileGrid.innerHTML = data.files.map(file => `
                    <div class="file-card">
                        <input type="checkbox" class="file-checkbox" value="${file.filename}" 
                               onchange="window.app.advancedFeatures.updateFileSelection('${file.filename}', this.checked)">
                        <div class="file-icon">📄</div>
                        <div class="file-info">
                            <div class="file-name">${file.filename}</div>
                            <div class="file-meta">${file.file_type} • ${file.chunks} chunks</div>
                        </div>
                        <div class="file-actions">
                            <button onclick="window.app.advancedFeatures.previewFile('${file.filename}')" class="btn-preview">Preview</button>
                            <button onclick="window.app.ui.deleteFile('${file.filename}')" class="btn-delete">Delete</button>
                        </div>
                    </div>
                    `).join('');
                }
            } else {
                if (fileGrid) {
                    fileGrid.innerHTML = '<p class="empty-state">No files uploaded yet.</p>';
                }
            }
        } catch (error) {
            console.error('Failed to load files:', error);
        }
    }

    async deleteFile(filename) {
        if (!confirm(`Delete "${filename}"? This will remove all chunks and cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/system/files/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                // Refresh file list and dashboard
                this.loadUploadedFiles();
                if (document.querySelector('.dashboard-view')) {
                    this.loadDashboardStats();
                }
            } else {
                alert('Failed to delete file');
            }
        } catch (error) {
            alert('Error deleting file');
        }
    }

    renderUpload() {
        this.pageTitle.textContent = "Upload Knowledge";
        this.mainContent.innerHTML = `
            <div class="upload-view fade-in">
                <div class="upload-container" style="max-width: 600px; margin: 0 auto; text-align: center; padding: 3rem; border: 2px dashed var(--border-color); border-radius: 1rem;">
                    <span style="font-size: 3rem; display: block; margin-bottom: 1rem;">📄</span>
                    <h3>Drag & Drop files here (multiple files supported)</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 2rem;">Supported formats: PDF, DOCX, TXT, MD, CSV, JSON, PY, JS, HTML, XML</p>
                    <input type="file" id="file-input" accept=".pdf,.docx,.txt,.md,.csv,.json,.py,.js,.html,.xml" multiple style="display: none;">
                    <button class="btn-primary" onclick="document.getElementById('file-input').click()">Select File</button>
                    <div id="upload-status" style="margin-top: 1rem;"></div>
                </div>
                
                <div class="uploaded-files" style="margin-top: 2rem;">
                    <h3>Uploaded Files</h3>
                    <div id="files-list">Loading...</div>
                </div>
            </div>
        `;

        // Add event listeners for upload
        const fileInput = document.getElementById("file-input");
        fileInput.addEventListener("change", (e) => {
            if (e.target.files.length === 1) {
                window.app.handleUpload(e.target.files[0]);
            } else {
                window.app.handleMultipleUpload(e.target.files);
            }
        });

        // Load and display uploaded files
        this.loadUploadedFiles();

        // Add drag & drop functionality
        const uploadContainer = document.querySelector('.upload-container');

        uploadContainer.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadContainer.style.borderColor = 'var(--accent-primary)';
            uploadContainer.style.backgroundColor = 'rgba(59, 130, 246, 0.1)';
        });

        uploadContainer.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadContainer.style.borderColor = 'var(--border-color)';
            uploadContainer.style.backgroundColor = 'transparent';
        });

        uploadContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadContainer.style.borderColor = 'var(--border-color)';
            uploadContainer.style.backgroundColor = 'transparent';

            const files = e.dataTransfer.files;
            if (files.length === 1) {
                window.app.handleUpload(files[0]);
            } else if (files.length > 1) {
                window.app.handleMultipleUpload(files);
            }
        });
    }

    async loadUploadedFiles() {
        try {
            const response = await fetch('/api/system/files');
            const data = await response.json();
            const filesList = document.getElementById('files-list');

            if (data.files && data.files.length > 0) {
                filesList.innerHTML = data.files.map(file => `
                    <div style="padding: 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${file.filename}</strong>
                            <div style="font-size: 0.9rem; color: var(--text-secondary);">
                                ${file.file_type} • ${file.chunks} chunks • ${file.processed_at}
                            </div>
                        </div>
                        <button class="btn-delete" onclick="window.app.ui.deleteFile('${file.filename}')" style="background: #ef4444; color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.25rem; cursor: pointer; font-size: 0.9rem;">Delete</button>
                    </div>
                `).join('');
            } else {
                filesList.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">No files uploaded yet.</p>';
            }
        } catch (error) {
            document.getElementById('files-list').innerHTML = '<p style="color: #ef4444;">Error loading files.</p>';
        }
    }

    renderSearch() {
        this.pageTitle.textContent = "Search & Chat";
        this.mainContent.innerHTML = `
            <div class="search-chat-container fade-in">
                <!-- Chat Sessions Sidebar -->
                <div class="chat-sessions-sidebar">
                    <div class="sessions-header">
                        <h3>Chat Sessions</h3>
                        <button class="btn-primary" id="new-chat-btn">+ New Chat</button>
                    </div>
                    <div class="sessions-list" id="sessions-list">
                        <p class="empty-state">No chat sessions yet</p>
                    </div>
                </div>

                <!-- Main Chat Area -->
                <div class="main-chat-area">
                    <div class="chat-header">
                        <h4 id="current-session-title">Select or create a chat session</h4>
                        <!-- Provider selection removed, defaulting to Parallel -->
                    </div>

                    <div class="chat-messages" id="chat-messages">
                        <div class="message system">
                            Create a new chat or select an existing session to start chatting.
                        </div>
                    </div>

                    <div class="chat-input-area" id="chat-input-area" style="display: none;">
                        <input type="text" id="chat-input" placeholder="Ask a question...">
                        <button class="btn-primary" id="send-btn">Send</button>
                    </div>
                </div>
            </div>
        `;

        this.initializeChatSessions();
    }

    async initializeChatSessions() {
        this.currentSessionId = null;
        this.sessions = [];

        this.loadSessions();

        document.getElementById('new-chat-btn').addEventListener('click', () => this.createNewChat());
        document.getElementById('send-btn').addEventListener('click', () => this.handleSessionSend());
        document.getElementById('chat-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSessionSend();
        });
    }

    async createNewChat() {
        try {
            const response = await fetch('/api/chat/start', { method: 'POST' });
            const data = await response.json();

            const newSession = {
                id: data.session_id,
                title: `Chat ${this.sessions.length + 1}`,
                created: new Date().toISOString()
            };

            this.sessions.push(newSession);
            this.selectSession(newSession.id);
            this.renderSessions();
            this.saveSessions();

        } catch (error) {
            console.error('Failed to create chat:', error);
        }
    }

    selectSession(sessionId) {
        this.currentSessionId = sessionId;
        const session = this.sessions.find(s => s.id === sessionId);

        if (session) {
            document.getElementById('current-session-title').textContent = session.title;
            document.getElementById('chat-input-area').style.display = 'flex';
            this.loadChatHistory(sessionId);
            this.renderSessions();
        }
    }

    async loadChatHistory(sessionId) {
        try {
            const response = await fetch(`/api/chat/history/${sessionId}`);
            const data = await response.json();

            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = '';

            if (data.history && data.history.length > 0) {
                data.history.forEach(msg => {
                    this.addMessage(msg.content, msg.role === 'user' ? 'user' : 'ai');
                });
            } else {
                this.addMessage('Hello! How can I help you today?', 'ai');
            }

        } catch (error) {
            console.error('Failed to load chat history:', error);
        }
    }

    renderSessions() {
        const sessionsList = document.getElementById('sessions-list');

        if (this.sessions.length === 0) {
            sessionsList.innerHTML = '<p class="empty-state">No chat sessions yet</p>';
            return;
        }

        sessionsList.innerHTML = this.sessions.map(session => `
            <div class="session-item ${session.id === this.currentSessionId ? 'active' : ''}" 
                 onclick="window.app.ui.selectSession('${session.id}')">
                <div class="session-title">${session.title}</div>
                <div class="session-date">${new Date(session.created).toLocaleDateString()}</div>
                <button class="session-delete" onclick="event.stopPropagation(); window.app.ui.deleteSession('${session.id}')">&times;</button>
            </div>
        `).join('');
    }

    async handleSessionSend() {
        if (!this.currentSessionId) {
            alert('Please create or select a chat session first');
            return;
        }

        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        const provider = "parallel";

        if (!message) return;

        input.value = '';
        this.addMessage(message, 'user');
        this.addMessage('Thinking...', 'ai');

        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    message: message,
                    ai_provider: provider,
                    workflow_id: 'default'
                })
            });

            const data = await response.json();

            const messages = document.querySelectorAll('.message.ai');
            if (messages.length > 0) {
                messages[messages.length - 1].remove();
            }

            this.addMessage(data.response, 'ai', { ai_provider: data.ai_provider });

        } catch (error) {
            console.error('Chat error:', error);
            const messages = document.querySelectorAll('.message.ai');
            if (messages.length > 0) {
                messages[messages.length - 1].remove();
            }
            this.addMessage('Sorry, I encountered an error. Please try again.', 'ai');
        }
    }

    deleteSession(sessionId) {
        if (!confirm('Delete this chat session?')) return;

        this.sessions = this.sessions.filter(s => s.id !== sessionId);

        if (this.currentSessionId === sessionId) {
            this.currentSessionId = null;
            document.getElementById('chat-input-area').style.display = 'none';
            document.getElementById('current-session-title').textContent = 'Select or create a chat session';
            document.getElementById('chat-messages').innerHTML = '<div class="message system">Create a new chat or select an existing session.</div>';
        }

        this.renderSessions();
        this.saveSessions();
    }

    saveSessions() {
        localStorage.setItem('chat_sessions', JSON.stringify(this.sessions));
    }

    loadSessions() {
        const saved = localStorage.getItem('chat_sessions');
        if (saved) {
            this.sessions = JSON.parse(saved);
            this.renderSessions();
        }
    }

    async handleSend() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();
        const searchType = document.getElementById('search-type').value;

        if (!message) return;

        // Clear input
        input.value = '';

        // Add user message
        this.addMessage(message, 'user');

        // Determine mode
        if (searchType === 'auto') {
            // Simple heuristic: ? at end or "what/how/why" start -> chat, else search
            const isQuestion = message.endsWith('?') ||
                /^(what|how|why|who|when|where)/i.test(message);

            if (isQuestion) {
                await window.app.handleChat(message, "mistral"); // Default to mistral for chat
            } else {
                await this.performAdvancedSearch(message, "hybrid");
            }
        } else if (searchType === 'mistral' || searchType === 'lamatic') {
            // Explicit chat provider
            await window.app.handleChat(message, searchType);
        } else {
            // Fallback
            await this.performAdvancedSearch(message, "hybrid");
        }
    }

    async performAdvancedSearch(query, searchType) {
        // Automatic filters
        const filters = {
            file_types: null, // Search all types
            min_score: 0.0    // Default score
        };

        // Hide chat, show results
        document.getElementById('chat-messages').style.display = 'none';
        const resultsArea = document.getElementById('search-results');
        resultsArea.style.display = 'block';
        resultsArea.innerHTML = `
            <div style="text-align: center; padding: 3rem;">
                <div class="loading-spinner"></div>
                <p style="margin-top: 1rem; color: var(--text-secondary);">Searching and generating AI summary...</p>
            </div>
        `;

        try {
            const response = await fetch('/api/advanced/search/advanced', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    search_type: searchType,
                    filters,
                    limit: 10,
                    save_to_history: true,
                    summarize: true // Request AI summary
                })
            });

            const data = await response.json();
            this.displaySearchResults(data, query);

        } catch (error) {
            console.error('Advanced search failed:', error);
            resultsArea.innerHTML = '<p style="color: #ef4444; text-align: center; padding: 2rem;">Search failed. Please try again.</p>';
        }
    }

    displaySearchResults(data, query) {
        const resultsArea = document.getElementById('search-results');

        if (!data.results || data.results.length === 0) {
            resultsArea.innerHTML = '<p class="no-results" style="text-align: center; padding: 2rem;">No results found</p>';
            return;
        }

        let html = `
            <div class="results-header" style="padding: 1rem; border-bottom: 1px solid var(--border-color); display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <span style="font-weight: 600; color: var(--text-primary);">${data.total_found} results</span>
                    <span style="color: var(--text-secondary); margin-left: 0.5rem; font-size: 0.9rem;">(${Math.round(data.response_time * 1000)}ms)</span>
                </div>
                <button onclick="document.getElementById('chat-messages').style.display='flex'; document.getElementById('search-results').style.display='none';" class="btn-secondary">Back to Chat</button>
            </div>
            <div class="results-list" style="padding: 1.5rem; max-width: 900px; margin: 0 auto;">
        `;

        // AI Summary Section
        if (data.ai_summary) {
            html += `
                <div class="ai-summary-card fade-in">
                    <div class="summary-header">
                        <span class="ai-icon">✨</span>
                        <h3>AI Summary</h3>
                    </div>
                    <div class="summary-content">
                        ${data.ai_summary.replace(/\n/g, '<br>')}
                    </div>
                </div>
            `;
        }

        // Results Cards
        html += data.results.map(result => {
            const scorePercent = Math.round(result.combined_score * 100);
            const scoreClass = scorePercent > 80 ? 'high' : scorePercent > 50 ? 'medium' : 'low';

            return `
                <div class="result-card fade-in">
                    <div class="result-header">
                        <div class="file-info">
                            <span class="file-icon">📄</span>
                            <span class="filename">${result.filename}</span>
                        </div>
                        <div class="score-badge ${scoreClass}">
                            ${scorePercent}% Match
                        </div>
                    </div>
                    
                    <div class="result-body">
                        <p class="result-text">${this.highlightQuery(result.text, query)}</p>
                    </div>
                    
                    <div class="result-footer">
                        <div class="meta-info">
                            <span class="meta-tag">${result.file_type}</span>
                            <span class="meta-tag">Chunk ${result.chunk_index}</span>
                        </div>
                        <button class="btn-copy" onclick="navigator.clipboard.writeText(this.parentElement.previousElementSibling.textContent).then(() => { this.textContent = 'Copied!'; setTimeout(() => this.textContent = 'Copy', 2000); })">
                            Copy
                        </button>
                    </div>
                </div>
            `;
        }).join('');

        html += '</div>';
        resultsArea.innerHTML = html;
    }

    highlightQuery(text, query) {
        if (!query) return text;
        const words = query.toLowerCase().split(/\s+/).filter(w => w.length > 2);
        let highlightedText = text;

        words.forEach(word => {
            const regex = new RegExp(`(${word})`, 'gi');
            highlightedText = highlightedText.replace(regex, '<mark>$1</mark>');
        });

        return highlightedText;
    }

    detectSearchType(query) {
        const lowerQuery = query.toLowerCase();

        // Exact phrase patterns (keyword search)
        if (query.includes('"') || /\b(exact|exactly|phrase)\b/.test(lowerQuery)) {
            return "keyword";
        }

        // Technical terms or specific keywords
        if (/\b(function|class|method|variable|error|code|algorithm|implementation)\b/.test(lowerQuery)) {
            return "keyword";
        }

        // Conceptual queries (semantic search)
        if (/\b(concept|idea|meaning|similar|related|like|about|explain|understand)\b/.test(lowerQuery)) {
            return "semantic";
        }

        // Complex queries with multiple aspects (hybrid search)
        if (query.split(' ').length > 5 || /\b(and|or|but|however|also|including)\b/.test(lowerQuery)) {
            return "hybrid";
        }

        // Questions or conversational queries (AI chat)
        if (/^(what|how|why|when|where|who|can|could|should|would|is|are|do|does)\b/i.test(query) || query.includes('?')) {
            return "chat";
        }

        // Default to semantic for general searches
        return "semantic";
    }

    getSearchTypeLabel(type) {
        const labels = {
            "chat": "AI Chat",
            "hybrid": "Hybrid Search",
            "semantic": "Semantic Search",
            "keyword": "Keyword Search"
        };
        return labels[type] || type;
    }

    addMessage(text, type, metadata = null) {
        const container = document.getElementById("chat-messages");
        if (!container) return;

        const msgDiv = document.createElement("div");
        msgDiv.className = `message ${type} fade-in`;

        // Style system messages differently
        if (type === "system") {
            msgDiv.style.cssText = "background: rgba(59, 130, 246, 0.1); border-left: 3px solid var(--accent-primary); font-size: 0.9rem; font-style: italic;";
        }

        // Add provider badge if metadata is provided
        if (metadata && metadata.ai_provider) {
            const badge = document.createElement("div");
            badge.className = "provider-badge";
            badge.style.cssText = "font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 0.25rem; display: flex; align-items: center; gap: 0.5rem;";

            const providerIcon = "🚀";
            const providerName = "Parallel Workflow";
            const modelInfo = metadata.model_used ? ` • ${metadata.model_used}` : "";

            badge.innerHTML = `<span>${providerIcon} ${providerName}${modelInfo}</span>`;
            msgDiv.appendChild(badge);
        }

        const textDiv = document.createElement("div");
        textDiv.textContent = text;
        msgDiv.appendChild(textDiv);

        container.appendChild(msgDiv);
        container.scrollTop = container.scrollHeight;
    }
}
