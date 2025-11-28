import { api } from './api.js';

export class UI {
    constructor(advancedFeatures) {
        this.mainContent = document.getElementById("main-content");
        this.pageTitle = document.getElementById("page-title");
        this.advancedFeatures = advancedFeatures;

        // Load sessions from local storage
        this.sessions = JSON.parse(localStorage.getItem('chat_sessions')) || [];
        this.currentSessionId = null;

        // Render sessions if sidebar exists
        this.renderSessions();
    }

    async renderDashboard() {
        this.pageTitle.textContent = "Dashboard";
        this.mainContent.innerHTML = `
            <div class="dashboard-view fade-in">
                <div class="stats-grid">
                    <div class="stat-card delay-100">
                        <h3>Total Documents</h3>
                        <p class="stat-value" id="total-docs"><span class="loading-spinner" style="width: 20px; height: 20px; border-width: 2px;"></span></p>
                    </div>
                    <div class="stat-card delay-200">
                        <h3>Total Chunks</h3>
                        <p class="stat-value" id="total-chunks"><span class="loading-spinner" style="width: 20px; height: 20px; border-width: 2px;"></span></p>
                    </div>
                    <div class="stat-card delay-300">
                        <h3>Storage Used</h3>
                        <p class="stat-value" id="storage-size"><span class="loading-spinner" style="width: 20px; height: 20px; border-width: 2px;"></span></p>
                    </div>
                </div>
                <div class="recent-activity glass-card fade-in delay-300">
                    <h2>Recent Files</h2>
                    <div class="activity-list" id="recent-files">
                        <div style="text-align: center; padding: 2rem;"><span class="loading-spinner"></span></div>
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

            const totalDocs = document.getElementById('total-docs');
            const totalChunks = document.getElementById('total-chunks');
            const storageSize = document.getElementById('storage-size');

            if (totalDocs) totalDocs.textContent = analytics.total_documents || 0;
            if (totalChunks) totalChunks.textContent = analytics.total_chunks || 0;
            if (storageSize) storageSize.textContent = this.formatBytes(analytics.storage_size || 0);

            // Load recent files
            const filesResponse = await fetch('/api/system/files');
            const filesData = await filesResponse.json();

            const recentFiles = document.getElementById('recent-files');
            if (recentFiles) {
                if (filesData.files && filesData.files.length > 0) {
                    const recent = filesData.files.slice(0, 5);
                    recentFiles.innerHTML = recent.map(file => `
                        <div style="padding: 1rem; border-left: 3px solid var(--accent-primary); background: rgba(255,255,255,0.03); margin-bottom: 0.75rem; border-radius: 0.5rem; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s ease;" onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='rgba(255,255,255,0.03)'">
                            <div>
                                <strong style="color: var(--text-primary); display: block; margin-bottom: 0.25rem;">${file.filename}</strong>
                                <div style="font-size: 0.85rem; color: var(--text-secondary);">${file.chunks} chunks • ${file.processed_at}</div>
                            </div>
                            <div style="font-size: 1.2rem;">📄</div>
                        </div>
                    `).join('');
                } else {
                    recentFiles.innerHTML = '<p class="empty-state">No files uploaded yet.</p>';
                }
            }
        } catch (error) {
            console.error("Error loading dashboard stats:", error);
            const els = ['total-docs', 'total-chunks', 'storage-size'];
            els.forEach(id => {
                const el = document.getElementById(id);
                if (el) el.textContent = '-';
            });
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
                    fileGrid.innerHTML = data.files.map((file, index) => `
                    <div class="file-card fade-in" style="animation-delay: ${index * 50}ms">
                        <input type="checkbox" class="file-checkbox" value="${file.filename}" 
                               onchange="window.app.advancedFeatures.updateFileSelection('${file.filename}', this.checked)"
                               style="position: absolute; top: 1rem; left: 1rem; width: 18px; height: 18px;">
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
                    fileGrid.innerHTML = '<p class="empty-state" style="grid-column: 1/-1;">No files uploaded yet.</p>';
                }
            }
        } catch (error) {
            console.error('Failed to load files:', error);
            const fileGrid = document.getElementById('file-grid');
            if (fileGrid) {
                fileGrid.innerHTML = '<p class="empty-state" style="grid-column: 1/-1; color: var(--error);">Error loading files. Please try again.</p>';
            }
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
                // Also refresh file manager if active
                if (document.getElementById('file-grid')) {
                    this.loadFileManagerData();
                }
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
                <div class="upload-container glass-card" style="max-width: 600px; margin: 0 auto; text-align: center; padding: 3rem; border-radius: 1rem; cursor: pointer;">
                    <span style="font-size: 4rem; display: block; margin-bottom: 1.5rem; filter: drop-shadow(0 0 10px var(--accent-glow));">☁️</span>
                    <h3 style="margin-bottom: 0.5rem;">Drag & Drop files here</h3>
                    <p style="color: var(--text-secondary); margin-bottom: 2rem;">Supported: PDF, DOCX, TXT, MD, CSV, JSON, PY, JS, HTML, XML</p>
                    <input type="file" id="file-input" accept=".pdf,.docx,.txt,.md,.csv,.json,.py,.js,.html,.xml" multiple style="display: none;">
                    <button class="btn-primary" onclick="document.getElementById('file-input').click()">Select Files</button>
                    <div id="upload-status" style="margin-top: 1.5rem; min-height: 1.5rem; font-weight: 500;"></div>
                </div>
                
                <div class="uploaded-files glass-card" style="margin-top: 2rem; padding: 1.5rem; border-radius: 1rem;">
                    <h3 style="margin-bottom: 1rem; border-bottom: 1px solid var(--glass-border); padding-bottom: 0.5rem;">Uploaded Files</h3>
                    <div id="files-list">
                        <div style="text-align: center; padding: 1rem;"><span class="loading-spinner"></span></div>
                    </div>
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
            uploadContainer.style.background = 'rgba(99, 102, 241, 0.1)';
        });

        uploadContainer.addEventListener('dragleave', (e) => {
            e.preventDefault();
            uploadContainer.style.borderColor = 'var(--border-color)';
            uploadContainer.style.background = 'var(--bg-card)';
        });

        uploadContainer.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadContainer.style.borderColor = 'var(--border-color)';
            uploadContainer.style.background = 'var(--bg-card)';

            const files = e.dataTransfer.files;
            if (files.length === 1) {
                window.app.handleUpload(files[0]);
            } else if (files.length > 1) {
                window.app.handleMultipleUpload(files);
            }
        });

        // Make the whole container clickable
        uploadContainer.addEventListener('click', (e) => {
            if (e.target !== fileInput && e.target.tagName !== 'BUTTON') {
                fileInput.click();
            }
        });
    }

    async loadUploadedFiles() {
        try {
            // Always filter by current session for document isolation
            if (!this.currentSessionId) {
                await this.createNewChat();
            }
            
            let url = `/api/system/files?session_id=${this.currentSessionId}`;
            const response = await fetch(url);
            const data = await response.json();
            const filesList = document.getElementById('files-list');

            if (filesList) {
                if (data.files && data.files.length > 0) {
                    filesList.innerHTML = data.files.map(file => `
                        <div style="padding: 1rem; border: 1px solid var(--glass-border); background: rgba(255,255,255,0.02); border-radius: 0.5rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center; transition: all 0.2s ease;" onmouseover="this.style.background='rgba(255,255,255,0.05)'" onmouseout="this.style.background='rgba(255,255,255,0.02)'">
                            <div>
                                <strong style="color: var(--text-primary);">${file.filename}</strong>
                                <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">
                                    ${file.file_type} • ${file.chunks} chunks • ${file.processed_at}
                                </div>
                            </div>
                            <button class="btn-delete" onclick="event.stopPropagation(); window.app.ui.deleteFile('${file.filename}')" style="padding: 0.4rem 0.8rem; font-size: 0.8rem;">Delete</button>
                        </div>
                    `).join('');
                } else {
                    filesList.innerHTML = '<p style="color: var(--text-secondary); text-align: center; padding: 1rem;">No files uploaded yet.</p>';
                }
            }
        } catch (error) {
            const list = document.getElementById('files-list');
            if (list) list.innerHTML = '<p style="color: var(--error); text-align: center;">Error loading files.</p>';
        }
    }

    renderSearch() {
        this.pageTitle.textContent = "Search & Chat";
        this.mainContent.innerHTML = `
            <div class="main-chat-area fade-in">
                <div class="chat-header">
                    <h4 id="current-session-title" style="margin: 0; font-size: 1rem; color: var(--text-primary);">Select or create a chat session</h4>
                </div>

                <div class="chat-messages" id="chat-messages">
                    <div class="welcome-screen">
                        <div class="welcome-icon">🧠</div>
                        <h2>AI Second Brain</h2>
                        <p>Select a chat session from the sidebar or start a new one to begin.</p>
                    </div>
                </div>

                <div id="search-results" class="search-results" style="display: none;"></div>

                <div class="chat-input-area">
                    <div class="input-wrapper">
                        <input type="text" id="chat-input" placeholder="Ask anything or search your brain..." autocomplete="off">
                        <button id="send-btn">
                            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="22" y1="2" x2="11" y2="13"></line>
                                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;

        this.initializeChatSessions();
    }

    async initializeChatSessions() {
        this.currentSessionId = null;

        // Load sessions from server (shared across all users)
        await this.loadSessions();

        this.renderSidebarSessions();

        const sendBtn = document.getElementById('send-btn');
        const chatInput = document.getElementById('chat-input');

        if (sendBtn) sendBtn.addEventListener('click', () => this.handleSessionSend());
        if (chatInput) chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.handleSessionSend();
        });

        // Auto-create new chat if no session is selected (New Tab behavior)
        // We check if we are in a "fresh" state. 
        // Since we don't persist currentSessionId in localStorage (only the list),
        // a refresh or new tab will always have currentSessionId = null.
        // The user wants "completely new browser tab automatically open/create new chat".
        // So we should create a new chat immediately.

        // However, we should only do this if we are on the search/chat page.
        // But initializeChatSessions is called from renderSearch.

        await this.createNewChat();
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

            this.sessions.unshift(newSession);
            this.saveSessions(); // Save after adding new session
            this.selectSession(newSession.id);
            this.renderSidebarSessions(); // Update sidebar

        } catch (error) {
            console.error('Failed to create chat:', error);
        }
    }

    async updateChatTitle(sessionId) {
        try {
            const response = await fetch(`/api/chat/title/${sessionId}`);
            const data = await response.json();

            const session = this.sessions.find(s => s.id === sessionId);
            if (session && data.title) {
                session.title = data.title;
                this.saveSessions(); // Save after updating title
                this.renderSidebarSessions(); // Update sidebar

                // Update header if this is the current session
                if (this.currentSessionId === sessionId) {
                    const titleEl = document.getElementById('current-session-title');
                    if (titleEl) titleEl.textContent = session.title;
                }
            }
        } catch (error) {
            console.error('Failed to update chat title:', error);
        }
    }

    saveSessions() {
        localStorage.setItem('chat_sessions', JSON.stringify(this.sessions));
    }

    async loadSessions() {
        try {
            const response = await fetch('/api/chat/sessions');
            const data = await response.json();
            this.sessions = data.sessions || [];
            localStorage.setItem('chat_sessions', JSON.stringify(this.sessions));
        } catch (error) {
            const saved = localStorage.getItem('chat_sessions');
            this.sessions = saved ? JSON.parse(saved) : [];
        }
    }

    async selectSession(sessionId) {
        this.currentSessionId = sessionId;

        // Update UI to show selected state
        document.querySelectorAll('.session-item').forEach(item => {
            item.classList.remove('active');
            if (item.dataset.id === sessionId) item.classList.add('active');
        });

        const session = this.sessions.find(s => s.id === sessionId);
        if (session) {
            const titleEl = document.getElementById('current-session-title');
            if (titleEl) titleEl.textContent = session.title;
        }

        await this.loadChatHistory(sessionId);
    }

    async loadChatHistory(sessionId) {
        const container = document.getElementById('chat-messages');
        if (!container) return;

        container.innerHTML = '<div class="loading-spinner"></div>';

        try {
            const response = await fetch(`/api/chat/history/${sessionId}`);
            const data = await response.json();

            container.innerHTML = '';

            if (!data.history || data.history.length === 0) {
                container.innerHTML = `
                    <div class="welcome-screen">
                        <div class="welcome-icon">💬</div>
                        <h2>Start Chatting</h2>
                        <p>Send a message to begin this conversation.</p>
                    </div>
                `;
                return;
            }

            data.history.forEach(msg => {
                this.addMessage(msg.content, msg.role, msg.metadata);
            });

        } catch (error) {
            console.error('Failed to load history:', error);
            container.innerHTML = '<div class="error-message">Failed to load chat history</div>';
        }
    }

    renderSessions() {
        this.renderSidebarSessions();
    }

    renderSidebarSessions() {
        const container = document.getElementById('chat-sessions-list');
        if (!container) return;

        if (this.sessions.length === 0) {
            container.innerHTML = `
                <div style="padding: 1rem; text-align: center; color: var(--text-muted); font-size: 0.9rem;">
                    No chats yet
                </div>
            `;
            return;
        }

        container.innerHTML = this.sessions.map(session => {
            const safeId = session.id.replace(/'/g, '&apos;');
            const safeTitle = session.title.replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return `
            <div class="session-item ${session.id === this.currentSessionId ? 'active' : ''}" 
                 data-id="${safeId}"
                 onclick="window.app.ui.selectSession('${safeId}')">
                <div class="session-title">${safeTitle}</div>
                <button class="delete-session-btn" onclick="event.stopPropagation(); window.app.ui.deleteSession('${safeId}')">
                    ×
                </button>
            </div>
            `;
        }).join('');
    }

    async handleSessionSend() {
        const input = document.getElementById('chat-input');
        const message = input.value.trim();

        if (!message) return;

        if (!this.currentSessionId) {
            await this.createNewChat();
        }

        input.value = '';
        this.addMessage(message, 'user');

        // Show loading state
        const loadingId = 'loading-' + Date.now();
        const container = document.getElementById('chat-messages');
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'message system';
        loadingDiv.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
        container.appendChild(loadingDiv);
        container.scrollTop = container.scrollHeight;

        try {
            const response = await fetch('/api/chat/message', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    message: message
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            // Remove loading indicator
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            this.addMessage(data.response, 'assistant', data.metadata);

            // Update title if it's the first message
            const session = this.sessions.find(s => s.id === this.currentSessionId);
            if (session && session.title.startsWith('Chat ')) {
                this.updateChatTitle(this.currentSessionId);
            }

        } catch (error) {
            console.error('Failed to send message:', error);
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            this.addMessage('Failed to send message. Please try again.', 'system');
        }
    }

    deleteSession(sessionId) {
        if (!confirm('Delete this chat session?')) return;

        this.sessions = this.sessions.filter(s => s.id !== sessionId);
        this.saveSessions(); // Save after deleting session

        if (this.currentSessionId === sessionId) {
            this.currentSessionId = null;
            this.renderSearch(); // Reset view
        } else {
            this.renderSidebarSessions();
        }
    }

    async performAdvancedSearch(query) {
        const resultsArea = document.getElementById('search-results');
        const chatArea = document.getElementById('chat-messages');

        if (resultsArea) {
            resultsArea.style.display = 'block';
            resultsArea.innerHTML = '<div class="loading-spinner"></div>';
        }
        if (chatArea) chatArea.style.display = 'none';

        try {
            // Ensure we have a session for search isolation
            if (!this.currentSessionId) {
                await this.createNewChat();
            }
            
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: query,
                    limit: 10,
                    include_summary: true,
                    session_id: this.currentSessionId // Always pass session_id for isolation
                })
            });

            const data = await response.json();
            this.displaySearchResults(data, query);

        } catch (error) {
            console.error('Search failed:', error);
            if (resultsArea) resultsArea.innerHTML = '<div class="error-message">Search failed</div>';
        }
    }

    displaySearchResults(data, query) {
        const resultsArea = document.getElementById('search-results');
        if (!resultsArea) return;

        if (!data.results || data.results.length === 0) {
            resultsArea.innerHTML = '<p class="no-results" style="text-align: center; padding: 2rem;">No results found</p>';
            return;
        }

        let html = `
            <div class="results-header" style="padding: 1rem; border-bottom: 1px solid var(--glass-border); display: flex; justify-content: space-between; align-items: center;">
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
                <div class="glass-card fade-in" style="padding: 1.5rem; margin-bottom: 2rem; border-radius: 1rem; border-left: 4px solid var(--accent-primary);">
                    <div class="summary-header" style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 1rem;">
                        <span style="font-size: 1.5rem;">✨</span>
                        <h3 style="margin: 0;">AI Summary</h3>
                    </div>
                    <div class="summary-content" style="line-height: 1.6; color: var(--text-primary);">
                        ${data.ai_summary.replace(/\n/g, '<br>')}
                    </div>
                </div>
            `;
        }

        // Results Cards
        html += data.results.map((result, index) => {
            const scorePercent = Math.round(result.combined_score * 100);
            const scoreClass = scorePercent > 80 ? 'var(--success)' : scorePercent > 50 ? 'var(--warning)' : 'var(--error)';

            return `
                <div class="glass-card fade-in" style="padding: 1.5rem; margin-bottom: 1.5rem; border-radius: 1rem; animation-delay: ${index * 100}ms;">
                    <div class="result-header" style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                        <div class="file-info" style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-size: 1.2rem;">📄</span>
                            <span class="filename" style="font-weight: 600;">${result.filename}</span>
                        </div>
                        <div class="score-badge" style="background: ${scoreClass}; color: white; padding: 0.2rem 0.6rem; border-radius: 1rem; font-size: 0.8rem; font-weight: 600;">
                            ${scorePercent}% Match
                        </div>
                    </div>

                    <div class="result-body" style="margin-bottom: 1rem; color: var(--text-secondary); line-height: 1.6;">
                        <p>${this.highlightQuery(result.text, query)}</p>
                    </div>

                    <div class="result-footer" style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85rem; color: var(--text-muted);">
                        <div class="meta-info">
                            <span class="meta-tag">${result.file_type}</span>
                            <span class="meta-tag" style="margin-left: 0.5rem;">Chunk ${result.chunk_index}</span>
                        </div>
                        <button class="btn-copy" style="background: none; border: 1px solid var(--glass-border); color: var(--text-secondary); padding: 0.2rem 0.6rem; border-radius: 0.25rem; cursor: pointer;" onclick="navigator.clipboard.writeText(this.parentElement.previousElementSibling.textContent).then(() => { this.textContent = 'Copied!'; setTimeout(() => this.textContent = 'Copy', 2000); })">
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
        if (!query || !text) return text;
        try {
            const words = query.toLowerCase().split(/\s+/).filter(w => w.length > 2);
            let highlightedText = text;

            words.forEach(word => {
                const escapedWord = word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
                const regex = new RegExp(`(${escapedWord})`, 'gi');
                highlightedText = highlightedText.replace(regex, '<mark style="background: rgba(99, 102, 241, 0.3); color: white; padding: 0 2px; border-radius: 2px;">$1</mark>');
            });

            return highlightedText;
        } catch (error) {
            console.error('Error highlighting query:', error);
            return text;
        }
    }

    addMessage(text, type, metadata = null) {
        try {
            const container = document.getElementById("chat-messages");
            if (!container) return;

            const msgDiv = document.createElement("div");
            msgDiv.className = `message ${type || 'user'}`;

            // Style system messages differently
            if (type === "system") {
                msgDiv.style.cssText = "background: rgba(99, 102, 241, 0.1); border-left: 3px solid var(--accent-primary); font-size: 0.9rem; font-style: italic; color: var(--text-secondary);";
            }

            // Add provider badge if metadata is provided
            if (metadata && metadata.ai_provider) {
                const badge = document.createElement("div");
                badge.className = "provider-badge";

                const providerIcon = "🚀";
                const providerName = "Parallel Workflow";
                const modelInfo = metadata.model_used ? ` • ${metadata.model_used}` : "";

                badge.innerHTML = `<span>${providerIcon} ${providerName}${modelInfo}</span>`;
                msgDiv.appendChild(badge);
            }

            const textDiv = document.createElement("div");
            const safeText = (text || '').replace(/\n/g, '<br>');
            textDiv.innerHTML = safeText;
            msgDiv.appendChild(textDiv);

            container.appendChild(msgDiv);
            container.scrollTop = container.scrollHeight;
        } catch (error) {
            console.error('Error adding message:', error);
        }
    }
}
