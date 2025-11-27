export class AdvancedFeatures {
    constructor(ui) {
        this.ui = ui;
        this.searchHistory = [];
        this.selectedFiles = new Set();
    }

    // Advanced Search Interface
    renderAdvancedSearch() {
        return `
            <div class="advanced-search-container">
                <div class="search-controls">
                    <div class="search-input-group">
                        <input type="text" id="advanced-query" placeholder="Enter your search query..." class="search-input">
                        <select id="search-type" class="search-type-select">
                            <option value="hybrid">Hybrid Search</option>
                            <option value="semantic">Semantic Only</option>
                            <option value="keyword">Keyword Only</option>
                            <option value="boolean">Boolean (AND/OR/NOT)</option>
                        </select>
                        <button id="advanced-search-btn" class="btn-primary">Search</button>
                    </div>
                    
                    <div class="search-filters">
                        <div class="filter-group">
                            <label>File Types:</label>
                            <div class="checkbox-group">
                                <label><input type="checkbox" value=".pdf"> PDF</label>
                                <label><input type="checkbox" value=".docx"> DOCX</label>
                                <label><input type="checkbox" value=".txt"> TXT</label>
                                <label><input type="checkbox" value=".md"> MD</label>
                            </div>
                        </div>
                        
                        <div class="filter-group">
                            <label>Min Score:</label>
                            <input type="range" id="min-score" min="0" max="1" step="0.1" value="0.3">
                            <span id="score-value">0.3</span>
                        </div>
                        
                        <div class="filter-group">
                            <label>Date Range:</label>
                            <input type="date" id="date-from">
                            <input type="date" id="date-to">
                        </div>
                    </div>
                </div>
                
                <div class="search-results-container">
                    <div class="results-header">
                        <div class="results-info">
                            <span id="results-count">0 results</span>
                            <span id="search-time">0ms</span>
                        </div>
                        <div class="results-actions">
                            <button id="save-search" class="btn-secondary">Save Search</button>
                            <button id="export-results" class="btn-secondary">Export</button>
                        </div>
                    </div>
                    
                    <div id="advanced-results" class="results-list">
                        <!-- Results will be populated here -->
                    </div>
                </div>
                
                <div class="search-history-panel">
                    <h3>Search History</h3>
                    <div id="search-history-list">
                        <!-- History items will be populated here -->
                    </div>
                </div>
            </div>
        `;
    }

    // File Management Interface
    renderFileManager() {
        return `
            <div class="file-manager-container">
                <div class="file-actions-bar">
                    <div class="bulk-actions">
                        <button id="select-all" class="btn-secondary">Select All</button>
                        <button id="bulk-delete" class="btn-danger" disabled>Delete Selected</button>
                        <button id="bulk-analyze" class="btn-primary" disabled>Analyze Selected</button>
                    </div>
                    
                    <div class="view-options">
                        <button id="grid-view" class="view-btn active">Grid</button>
                        <button id="list-view" class="view-btn">List</button>
                    </div>
                </div>
                
                <div class="file-grid" id="file-grid">
                    <!-- Files will be populated here -->
                </div>
                
                <div class="file-preview-panel" id="file-preview" style="display: none;">
                    <div class="preview-header">
                        <h3 id="preview-filename">File Preview</h3>
                        <button id="close-preview">×</button>
                    </div>
                    <div class="preview-content" id="preview-content">
                        <!-- Preview content -->
                    </div>
                </div>
            </div>
        `;
    }

    // Analytics Dashboard
    renderAnalyticsDashboard() {
        return `
            <div class="analytics-dashboard">
                <div class="analytics-grid">
                    <div class="analytics-card">
                        <h3>Search Performance</h3>
                        <div class="metric-value" id="avg-response-time">0ms</div>
                        <div class="metric-label">Average Response Time</div>
                    </div>
                    
                    <div class="analytics-card">
                        <h3>Popular Queries</h3>
                        <div id="popular-queries-list">
                            <!-- Popular queries -->
                        </div>
                    </div>
                    
                    <div class="analytics-card">
                        <h3>File Usage</h3>
                        <div id="file-usage-chart">
                            <!-- File usage stats -->
                        </div>
                    </div>
                    
                    <div class="analytics-card">
                        <h3>Content Gaps</h3>
                        <div id="content-gaps">
                            <!-- Knowledge gaps analysis -->
                        </div>
                    </div>
                </div>
                
                <div class="analytics-charts">
                    <div class="chart-container">
                        <h3>Search Volume Over Time</h3>
                        <canvas id="search-volume-chart"></canvas>
                    </div>
                    
                    <div class="chart-container">
                        <h3>File Type Distribution</h3>
                        <canvas id="file-type-chart"></canvas>
                    </div>
                </div>
            </div>
        `;
    }

    // Advanced Search Functionality
    async performAdvancedSearch() {
        const query = document.getElementById('advanced-query').value;
        const searchType = document.getElementById('search-type').value;

        if (!query.trim()) return;

        // Get filters
        const fileTypes = Array.from(document.querySelectorAll('.checkbox-group input:checked'))
            .map(cb => cb.value);
        const minScore = parseFloat(document.getElementById('min-score').value);
        const dateFrom = document.getElementById('date-from').value;
        const dateTo = document.getElementById('date-to').value;

        const filters = {
            file_types: fileTypes.length > 0 ? fileTypes : null,
            min_score: minScore,
            date_from: dateFrom || null,
            date_to: dateTo || null
        };

        try {
            const response = await fetch('/api/advanced/search/advanced', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query,
                    search_type: searchType,
                    filters,
                    limit: 20,
                    save_to_history: true
                })
            });

            const data = await response.json();
            this.displayAdvancedResults(data);
            this.updateSearchHistory();

        } catch (error) {
            console.error('Advanced search failed:', error);
        }
    }

    displayAdvancedResults(data) {
        const resultsContainer = document.getElementById('advanced-results');
        const resultsCount = document.getElementById('results-count');
        const searchTime = document.getElementById('search-time');

        resultsCount.textContent = `${data.total_found} results`;
        searchTime.textContent = `${Math.round(data.response_time * 1000)}ms`;

        if (data.results.length === 0) {
            resultsContainer.innerHTML = '<p class="no-results">No results found</p>';
            return;
        }

        resultsContainer.innerHTML = data.results.map(result => `
            <div class="advanced-result-item">
                <div class="result-header">
                    <span class="filename">${result.filename}</span>
                    <div class="scores">
                        <span class="score semantic">S: ${result.semantic_score.toFixed(3)}</span>
                        <span class="score keyword">K: ${result.keyword_score.toFixed(3)}</span>
                        <span class="score combined">C: ${result.combined_score.toFixed(3)}</span>
                    </div>
                </div>
                <div class="result-content">
                    <p>${this.highlightQuery(result.text, data.query)}</p>
                </div>
                <div class="result-meta">
                    <span>${result.file_type}</span>
                    <span>Chunk ${result.chunk_index}</span>
                    <button onclick="window.app.advancedFeatures.previewFile('${result.filename}')">Preview</button>
                </div>
            </div>
        `).join('');
    }

    highlightQuery(text, query) {
        const words = query.toLowerCase().split(' ');
        let highlightedText = text;

        words.forEach(word => {
            const regex = new RegExp(`(${word})`, 'gi');
            highlightedText = highlightedText.replace(regex, '<mark>$1</mark>');
        });

        return highlightedText;
    }

    async updateSearchHistory() {
        try {
            const response = await fetch('/api/advanced/search/history');
            const data = await response.json();

            const historyList = document.getElementById('search-history-list');
            historyList.innerHTML = data.history.slice(0, 10).map(item => `
                <div class="history-item" onclick="window.app.advancedFeatures.loadHistorySearch('${item.query}')">
                    <div class="history-query">${item.query}</div>
                    <div class="history-meta">
                        ${item.results_count} results • ${Math.round(item.response_time * 1000)}ms
                    </div>
                </div>
            `).join('');

        } catch (error) {
            console.error('Failed to load search history:', error);
        }
    }

    async loadAnalytics() {
        try {
            const response = await fetch('/api/system/analytics');
            const analytics = await response.json();
            
            const searchAnalytics = {
                avg_response_time: 0.5,
                popular_queries: []
            };
            
            const fileAnalytics = {
                popular_files: analytics.file_type_distribution ? 
                    Object.entries(analytics.file_type_distribution).map(([type, count]) => ({
                        filename: `${type} files`,
                        access_count: count
                    })) : []
            };
            
            const contentGaps = {
                suggested_research: [
                    "Upload more documents for better analysis",
                    "Add diverse file types for comprehensive coverage",
                    "Consider adding recent research papers"
                ]
            };

            this.displayAnalytics(searchAnalytics, fileAnalytics, contentGaps);

        } catch (error) {
            console.error('Failed to load analytics:', error);
        }
    }

    displayAnalytics(searchAnalytics, fileAnalytics, contentGaps) {
        // Update response time
        const avgResponseTime = document.getElementById('avg-response-time');
        if (avgResponseTime) {
            avgResponseTime.textContent = `${Math.round((searchAnalytics?.avg_response_time || 0) * 1000)}ms`;
        }

        // Popular queries
        const queriesList = document.getElementById('popular-queries-list');
        if (queriesList) {
            queriesList.innerHTML = (searchAnalytics?.popular_queries || []).slice(0, 5).map(q => `
                <div class="query-item">
                    <span class="query-text">${q.query}</span>
                    <span class="query-count">${q.count}</span>
                </div>
            `).join('') || '<p>No data available</p>';
        }

        // File usage
        const fileUsage = document.getElementById('file-usage-chart');
        if (fileUsage) {
            fileUsage.innerHTML = (fileAnalytics?.popular_files || []).slice(0, 5).map(f => `
                <div class="file-usage-item">
                    <span class="file-name">${f.filename}</span>
                    <span class="access-count">${f.access_count} accesses</span>
                </div>
            `).join('') || '<p>No data available</p>';
        }

        // Content gaps
        const gaps = document.getElementById('content-gaps');
        if (gaps) {
            gaps.innerHTML = (contentGaps?.suggested_research || []).slice(0, 3).map(suggestion => `
                <div class="gap-item">${suggestion}</div>
            `).join('') || '<p>No gaps identified</p>';
        }
    }

    async previewFile(filename) {
        try {
            const response = await fetch(`/api/advanced/content/auto-analyze/${encodeURIComponent(filename)}`);
            const data = await response.json();

            const previewPanel = document.getElementById('file-preview');
            const previewContent = document.getElementById('preview-content');
            const previewFilename = document.getElementById('preview-filename');

            previewFilename.textContent = filename;
            previewContent.innerHTML = `
                <div class="preview-section">
                    <h4>Summary</h4>
                    <p>${data.analysis?.summary || 'No summary available'}</p>
                </div>
                
                <div class="preview-section">
                    <h4>Key Entities</h4>
                    <div class="entities-grid">
                        ${data.analysis?.entities ? Object.entries(data.analysis.entities).map(([type, entities]) =>
                entities.length > 0 ? `
                                <div class="entity-group">
                                    <strong>${type}:</strong>
                                    ${entities.slice(0, 3).join(', ')}
                                </div>
                            ` : ''
            ).join('') : 'No entities found'}
                    </div>
                </div>
                
                <div class="preview-section">
                    <h4>Keywords</h4>
                    <div class="keywords-list">
                        ${data.analysis?.keywords ? data.analysis.keywords.slice(0, 10).map(kw =>
                `<span class="keyword-tag">${kw.term}</span>`
            ).join('') : 'No keywords found'}
                    </div>
                </div>
                
                <div class="preview-section">
                    <h4>Generated Questions</h4>
                    <ul>
                        ${data.analysis?.questions ? data.analysis.questions.slice(0, 5).map(q =>
                `<li>${q}</li>`
            ).join('') : '<li>No questions generated</li>'}
                    </ul>
                </div>
            `;

            previewPanel.style.display = 'block';

        } catch (error) {
            console.error('Failed to preview file:', error);
        }
    }

    initializeEventListeners() {
        // Advanced search
        document.addEventListener('click', (e) => {
            if (e.target.id === 'advanced-search-btn') {
                this.performAdvancedSearch();
            }

            if (e.target.id === 'close-preview') {
                document.getElementById('file-preview').style.display = 'none';
            }

            if (e.target.id === 'select-all') {
                this.toggleSelectAll();
            }

            if (e.target.id === 'bulk-delete') {
                this.bulkDeleteFiles();
            }
        });

        // Score slider
        document.addEventListener('input', (e) => {
            if (e.target.id === 'min-score') {
                document.getElementById('score-value').textContent = e.target.value;
            }
        });

        // Enter key for search
        document.addEventListener('keypress', (e) => {
            if (e.target.id === 'advanced-query' && e.key === 'Enter') {
                this.performAdvancedSearch();
            }
        });
    }

    toggleSelectAll() {
        const checkboxes = document.querySelectorAll('.file-checkbox');
        const allChecked = Array.from(checkboxes).every(cb => cb.checked);

        checkboxes.forEach(cb => {
            cb.checked = !allChecked;
            this.updateFileSelection(cb.value, cb.checked);
        });

        this.updateBulkActions();
    }

    updateFileSelection(filename, selected) {
        if (selected) {
            this.selectedFiles.add(filename);
        } else {
            this.selectedFiles.delete(filename);
        }
        this.updateBulkActions();
    }

    updateBulkActions() {
        const bulkDelete = document.getElementById('bulk-delete');
        const bulkAnalyze = document.getElementById('bulk-analyze');
        const hasSelection = this.selectedFiles.size > 0;

        if (bulkDelete) bulkDelete.disabled = !hasSelection;
        if (bulkAnalyze) bulkAnalyze.disabled = !hasSelection;
    }

    async bulkDeleteFiles() {
        if (this.selectedFiles.size === 0) return;

        const confirmed = confirm(`Delete ${this.selectedFiles.size} selected files?`);
        if (!confirmed) return;

        try {
            for (const filename of this.selectedFiles) {
                await fetch(`/api/system/files/${encodeURIComponent(filename)}`, {
                    method: 'DELETE'
                });
            }

            this.selectedFiles.clear();
            this.ui.loadUploadedFiles(); // Refresh file list

        } catch (error) {
            console.error('Bulk delete failed:', error);
        }
    }
}