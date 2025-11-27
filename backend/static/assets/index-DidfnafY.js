(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const a of document.querySelectorAll('link[rel="modulepreload"]'))t(a);new MutationObserver(a=>{for(const n of a)if(n.type==="childList")for(const r of n.addedNodes)r.tagName==="LINK"&&r.rel==="modulepreload"&&t(r)}).observe(document,{childList:!0,subtree:!0});function s(a){const n={};return a.integrity&&(n.integrity=a.integrity),a.referrerPolicy&&(n.referrerPolicy=a.referrerPolicy),a.crossOrigin==="use-credentials"?n.credentials="include":a.crossOrigin==="anonymous"?n.credentials="omit":n.credentials="same-origin",n}function t(a){if(a.ep)return;a.ep=!0;const n=s(a);fetch(a.href,n)}})();class g{constructor(e){if(this.name="Lamatic SDK",this.endpoint="",this.projectId="",!e)throw new Error("Configuration object is required");if(!e.endpoint)throw new Error("Endpoint URL is required");if(!e.projectId)throw new Error("Project ID is required");if(!e.apiKey&&!e.accessToken)throw new Error("API key or Access Token is required");this.endpoint=e.endpoint,this.projectId=e.projectId,this.apiKey=e.apiKey,this.accessToken=e.accessToken}async executeFlow(e,s){try{const t={query:`query ExecuteWorkflow(
                $workflowId: String!  
                $payload: JSON!
              ) 
              {   
                executeWorkflow( 
                  workflowId: $workflowId   
                  payload: $payload
                ) 
                {  
                  status       
                  result   
                } 
              }`,variables:{workflowId:e,payload:s}},n={method:"POST",headers:this.getHeaders(),body:JSON.stringify(t)},r=await fetch(this.endpoint,n),i=await r.text();let o=JSON.parse(i);return o.errors?{status:"error",result:null,message:o.errors[0].message,statusCode:r.status}:{...o.data.executeWorkflow,statusCode:r.status}}catch(t){throw console.error("[Lamatic SDK Error] : ",t.message),new Error(t.message)}}async executeAgent(e,s){try{const t={query:`query ExecuteAgent(
                $agentId: String!  
                $payload: JSON!
              ) 
              {   
                executeAgent( 
                  agentId: $agentId   
                  payload: $payload
                ) 
                {  
                  status       
                  result   
                } 
              }`,variables:{agentId:e,payload:s}},n={method:"POST",headers:this.getHeaders(),body:JSON.stringify(t)},r=await fetch(this.endpoint,n),i=await r.text();let o=JSON.parse(i);return o.errors?{status:"error",result:null,message:o.errors[0].message,statusCode:r.status}:{...o.data.executeAgent,statusCode:r.status}}catch(t){throw console.error("[Lamatic SDK Error] : ",t.message),new Error(t.message)}}async checkStatus(e,s=15,t=900){const a=Date.now(),n=t*1e3,r=s*1e3;for(;Date.now()-a<n;)try{const i={query:`query CheckStatus(
                  $requestId: String!
                ) {
                  checkStatus(
                    requestId: $requestId
                  )
                }`,variables:{requestId:e}},c={method:"POST",headers:this.getHeaders(),body:JSON.stringify(i)},u=await fetch(this.endpoint,c),v=await u.text();let p=JSON.parse(v);if(p.errors)return{status:"error",result:null,message:p.errors[0].message,statusCode:u.status};const d={...p.data.checkStatus,statusCode:u.status};if(d.status==="success"||d.status==="error"||d.status==="failed")return d;Date.now()-a+r<n&&await new Promise(y=>setTimeout(y,r))}catch(i){return console.error("[Lamatic SDK Error] : ",i.message),{status:"error",result:null,message:i.message,statusCode:500}}return{status:"error",result:null,message:`Request checkStatus timedout after ${t} seconds, your request may still be executing in the background and you can check after few minutes`,statusCode:408}}getHeaders(){return this.accessToken?{"Content-Type":"application/json","X-Lamatic-Signature":this.accessToken,"x-project-id":this.projectId}:{"Content-Type":"application/json",Authorization:`Bearer ${this.apiKey}`,"x-project-id":this.projectId}}updateAccessToken(e){this.accessToken=e}}const m="/api";class f{constructor(){this.lamatic=new g({apiKey:"lt-7136f2df4d8be90dfa98e9b2b104f2d7",projectId:"default"})}async ingestFile(e){const s=new FormData;s.append("file",e);try{const t=await fetch(`${m}/ingest`,{method:"POST",body:s});if(!t.ok)throw new Error("Ingestion failed");return await t.json()}catch(t){throw console.error("Error ingesting file:",t),t}}async search(e){try{const s=await fetch(`${m}/search`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:e,limit:5,include_metadata:!0})});if(!s.ok)throw new Error("Search failed");return await s.json()}catch(s){throw console.error("Error searching:",s),s}}async chat(e,s="default"){try{const t=await this.search(e),a=t.results.map(n=>n.text);console.log("Executing Lamatic Flow:",s);try{const n=await this.lamatic.executeFlow(s,{user_message:e,context:a,memory_chunks:a.length});if(n.status==="success"&&n.result)return{response:n.result.output||n.result.text||"I processed that but got no text response.",context_used:t.results};throw new Error("Lamatic flow execution failed or returned no result")}catch(n){return console.error("Lamatic SDK Error:",n),{response:"I found relevant memories but couldn't generate a new answer (AI Error). See sources below.",context_used:t.results}}}catch(t){throw console.error("Error in chat:",t),t}}async summarize(){return{summary:"Summarization not yet migrated to SDK."}}}const h=new f;class w{constructor(e){this.mainContent=document.getElementById("main-content"),this.pageTitle=document.getElementById("page-title"),this.advancedFeatures=e}async renderDashboard(){this.pageTitle.textContent="Dashboard",this.mainContent.innerHTML=`
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
        `,this.loadDashboardStats()}async loadDashboardStats(){try{const s=await(await fetch("/api/system/analytics")).json();document.getElementById("total-docs").textContent=s.total_documents||0,document.getElementById("total-chunks").textContent=s.total_chunks||0,document.getElementById("storage-size").textContent=this.formatBytes(s.storage_size||0);const a=await(await fetch("/api/system/files")).json(),n=document.getElementById("recent-files");if(a.files&&a.files.length>0){const r=a.files.slice(0,5);n.innerHTML=r.map(i=>`
                    <div style="padding: 0.75rem; border-left: 3px solid var(--accent-primary); background: var(--bg-card); margin-bottom: 0.5rem; border-radius: 0.5rem;">
                        <strong>${i.filename}</strong>
                        <div style="font-size: 0.9rem; color: var(--text-secondary);">${i.chunks} chunks • ${i.processed_at}</div>
                    </div>
                `).join("")}else n.innerHTML='<p class="empty-state">No files uploaded yet.</p>'}catch{document.getElementById("total-docs").textContent="Error",document.getElementById("total-chunks").textContent="Error",document.getElementById("storage-size").textContent="Error"}}formatBytes(e){if(e===0)return"0 B";const s=1024,t=["B","KB","MB","GB"],a=Math.floor(Math.log(e)/Math.log(s));return parseFloat((e/Math.pow(s,a)).toFixed(2))+" "+t[a]}renderAdvancedSearchPage(){this.pageTitle.textContent="Advanced Search",this.mainContent.innerHTML=this.advancedFeatures.renderAdvancedSearch(),this.advancedFeatures.initializeEventListeners(),this.advancedFeatures.updateSearchHistory()}renderAnalyticsPage(){this.pageTitle.textContent="Analytics Dashboard",this.mainContent.innerHTML=this.advancedFeatures.renderAnalyticsDashboard(),this.advancedFeatures.loadAnalytics()}renderFileManagerPage(){this.pageTitle.textContent="File Manager",this.mainContent.innerHTML=this.advancedFeatures.renderFileManager(),this.loadFileManagerData()}async loadFileManagerData(){try{const s=await(await fetch("/api/system/files")).json(),t=document.getElementById("file-grid");s.files&&s.files.length>0?t.innerHTML=s.files.map(a=>`
                    <div class="file-card">
                        <input type="checkbox" class="file-checkbox" value="${a.filename}" 
                               onchange="window.app.advancedFeatures.updateFileSelection('${a.filename}', this.checked)">
                        <div class="file-icon">📄</div>
                        <div class="file-info">
                            <div class="file-name">${a.filename}</div>
                            <div class="file-meta">${a.file_type} • ${a.chunks} chunks</div>
                        </div>
                        <div class="file-actions">
                            <button onclick="window.app.advancedFeatures.previewFile('${a.filename}')" class="btn-preview">Preview</button>
                            <button onclick="window.app.ui.deleteFile('${a.filename}')" class="btn-delete">Delete</button>
                        </div>
                    </div>
                `).join(""):t.innerHTML='<p class="empty-state">No files uploaded yet.</p>'}catch(e){console.error("Failed to load files:",e)}}async deleteFile(e){if(confirm(`Delete "${e}"? This will remove all chunks and cannot be undone.`))try{(await fetch(`/api/system/files/${encodeURIComponent(e)}`,{method:"DELETE"})).ok?(this.loadUploadedFiles(),document.querySelector(".dashboard-view")&&this.loadDashboardStats()):alert("Failed to delete file")}catch{alert("Error deleting file")}}renderUpload(){this.pageTitle.textContent="Upload Knowledge",this.mainContent.innerHTML=`
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
        `,document.getElementById("file-input").addEventListener("change",t=>{t.target.files.length===1?window.app.handleUpload(t.target.files[0]):window.app.handleMultipleUpload(t.target.files)}),this.loadUploadedFiles();const s=document.querySelector(".upload-container");s.addEventListener("dragover",t=>{t.preventDefault(),s.style.borderColor="var(--accent-primary)",s.style.backgroundColor="rgba(59, 130, 246, 0.1)"}),s.addEventListener("dragleave",t=>{t.preventDefault(),s.style.borderColor="var(--border-color)",s.style.backgroundColor="transparent"}),s.addEventListener("drop",t=>{t.preventDefault(),s.style.borderColor="var(--border-color)",s.style.backgroundColor="transparent";const a=t.dataTransfer.files;a.length===1?window.app.handleUpload(a[0]):a.length>1&&window.app.handleMultipleUpload(a)})}async loadUploadedFiles(){try{const s=await(await fetch("/api/system/files")).json(),t=document.getElementById("files-list");s.files&&s.files.length>0?t.innerHTML=s.files.map(a=>`
                    <div style="padding: 1rem; border: 1px solid var(--border-color); border-radius: 0.5rem; margin-bottom: 0.5rem; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${a.filename}</strong>
                            <div style="font-size: 0.9rem; color: var(--text-secondary);">
                                ${a.file_type} • ${a.chunks} chunks • ${a.processed_at}
                            </div>
                        </div>
                        <button class="btn-delete" onclick="window.app.ui.deleteFile('${a.filename}')" style="background: #ef4444; color: white; border: none; padding: 0.5rem 1rem; border-radius: 0.25rem; cursor: pointer; font-size: 0.9rem;">Delete</button>
                    </div>
                `).join(""):t.innerHTML='<p style="color: var(--text-secondary); text-align: center;">No files uploaded yet.</p>'}catch{document.getElementById("files-list").innerHTML='<p style="color: #ef4444;">Error loading files.</p>'}}renderSearch(){this.pageTitle.textContent="Search & Chat",this.mainContent.innerHTML=`
            <div class="chat-container fade-in">
                <div class="chat-messages" id="chat-messages">
                    <div class="message ai">
                        Hello! I'm your Second Brain. Ask me anything about your stored notes and files.
                    </div>
                </div>
                <div class="chat-input-area">
                    <input type="text" id="chat-input" placeholder="Ask a question...">
                    <button class="btn-primary" id="send-btn">Send</button>
                </div>
            </div>
        `;const e=document.getElementById("send-btn"),s=document.getElementById("chat-input"),t=()=>{const a=s.value.trim();a&&(window.app.handleSearch(a),s.value="")};e.addEventListener("click",t),s.addEventListener("keypress",a=>{a.key==="Enter"&&t()})}addMessage(e,s){const t=document.getElementById("chat-messages");if(!t)return;const a=document.createElement("div");a.className=`message ${s} fade-in`,a.textContent=e,t.appendChild(a),t.scrollTop=t.scrollHeight}}class b{constructor(e){this.ui=e,this.searchHistory=[],this.selectedFiles=new Set}renderAdvancedSearch(){return`
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
        `}renderFileManager(){return`
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
        `}renderAnalyticsDashboard(){return`
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
        `}async performAdvancedSearch(){const e=document.getElementById("advanced-query").value,s=document.getElementById("search-type").value;if(!e.trim())return;const t=Array.from(document.querySelectorAll(".checkbox-group input:checked")).map(o=>o.value),a=parseFloat(document.getElementById("min-score").value),n=document.getElementById("date-from").value,r=document.getElementById("date-to").value,i={file_types:t.length>0?t:null,min_score:a,date_from:n||null,date_to:r||null};try{const c=await(await fetch("/api/advanced/search/advanced",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({query:e,search_type:s,filters:i,limit:20,save_to_history:!0})})).json();this.displayAdvancedResults(c),this.updateSearchHistory()}catch(o){console.error("Advanced search failed:",o)}}displayAdvancedResults(e){const s=document.getElementById("advanced-results"),t=document.getElementById("results-count"),a=document.getElementById("search-time");if(t.textContent=`${e.total_found} results`,a.textContent=`${Math.round(e.response_time*1e3)}ms`,e.results.length===0){s.innerHTML='<p class="no-results">No results found</p>';return}s.innerHTML=e.results.map(n=>`
            <div class="advanced-result-item">
                <div class="result-header">
                    <span class="filename">${n.filename}</span>
                    <div class="scores">
                        <span class="score semantic">S: ${n.semantic_score.toFixed(3)}</span>
                        <span class="score keyword">K: ${n.keyword_score.toFixed(3)}</span>
                        <span class="score combined">C: ${n.combined_score.toFixed(3)}</span>
                    </div>
                </div>
                <div class="result-content">
                    <p>${this.highlightQuery(n.text,e.query)}</p>
                </div>
                <div class="result-meta">
                    <span>${n.file_type}</span>
                    <span>Chunk ${n.chunk_index}</span>
                    <button onclick="window.app.advancedFeatures.previewFile('${n.filename}')">Preview</button>
                </div>
            </div>
        `).join("")}highlightQuery(e,s){const t=s.toLowerCase().split(" ");let a=e;return t.forEach(n=>{const r=new RegExp(`(${n})`,"gi");a=a.replace(r,"<mark>$1</mark>")}),a}async updateSearchHistory(){try{const s=await(await fetch("/api/advanced/search/history")).json(),t=document.getElementById("search-history-list");t.innerHTML=s.history.slice(0,10).map(a=>`
                <div class="history-item" onclick="window.app.advancedFeatures.loadHistorySearch('${a.query}')">
                    <div class="history-query">${a.query}</div>
                    <div class="history-meta">
                        ${a.results_count} results • ${Math.round(a.response_time*1e3)}ms
                    </div>
                </div>
            `).join("")}catch(e){console.error("Failed to load search history:",e)}}async loadAnalytics(){try{const[e,s,t]=await Promise.all([fetch("/api/advanced/analytics/search").then(a=>a.json()),fetch("/api/advanced/analytics/files").then(a=>a.json()),fetch("/api/advanced/analytics/content-gaps").then(a=>a.json())]);this.displayAnalytics(e,s,t)}catch(e){console.error("Failed to load analytics:",e)}}displayAnalytics(e,s,t){document.getElementById("avg-response-time").textContent=`${Math.round(e.avg_response_time*1e3)}ms`;const a=document.getElementById("popular-queries-list");a.innerHTML=e.popular_queries.slice(0,5).map(i=>`
            <div class="query-item">
                <span class="query-text">${i.query}</span>
                <span class="query-count">${i.count}</span>
            </div>
        `).join("");const n=document.getElementById("file-usage-chart");n.innerHTML=s.popular_files.slice(0,5).map(i=>`
            <div class="file-usage-item">
                <span class="file-name">${i.filename}</span>
                <span class="access-count">${i.access_count} accesses</span>
            </div>
        `).join("");const r=document.getElementById("content-gaps");r.innerHTML=t.suggested_research.slice(0,3).map(i=>`
            <div class="gap-item">${i}</div>
        `).join("")}async previewFile(e){try{const t=await(await fetch(`/api/advanced/content/auto-analyze/${encodeURIComponent(e)}`)).json(),a=document.getElementById("file-preview"),n=document.getElementById("preview-content"),r=document.getElementById("preview-filename");r.textContent=e,n.innerHTML=`
                <div class="preview-section">
                    <h4>Summary</h4>
                    <p>${t.analysis?.summary||"No summary available"}</p>
                </div>
                
                <div class="preview-section">
                    <h4>Key Entities</h4>
                    <div class="entities-grid">
                        ${t.analysis?.entities?Object.entries(t.analysis.entities).map(([i,o])=>o.length>0?`
                                <div class="entity-group">
                                    <strong>${i}:</strong>
                                    ${o.slice(0,3).join(", ")}
                                </div>
                            `:"").join(""):"No entities found"}
                    </div>
                </div>
                
                <div class="preview-section">
                    <h4>Keywords</h4>
                    <div class="keywords-list">
                        ${t.analysis?.keywords?t.analysis.keywords.slice(0,10).map(i=>`<span class="keyword-tag">${i.term}</span>`).join(""):"No keywords found"}
                    </div>
                </div>
                
                <div class="preview-section">
                    <h4>Generated Questions</h4>
                    <ul>
                        ${t.analysis?.questions?t.analysis.questions.slice(0,5).map(i=>`<li>${i}</li>`).join(""):"<li>No questions generated</li>"}
                    </ul>
                </div>
            `,a.style.display="block"}catch(s){console.error("Failed to preview file:",s)}}initializeEventListeners(){document.addEventListener("click",e=>{e.target.id==="advanced-search-btn"&&this.performAdvancedSearch(),e.target.id==="close-preview"&&(document.getElementById("file-preview").style.display="none"),e.target.id==="select-all"&&this.toggleSelectAll(),e.target.id==="bulk-delete"&&this.bulkDeleteFiles()}),document.addEventListener("input",e=>{e.target.id==="min-score"&&(document.getElementById("score-value").textContent=e.target.value)}),document.addEventListener("keypress",e=>{e.target.id==="advanced-query"&&e.key==="Enter"&&this.performAdvancedSearch()})}toggleSelectAll(){const e=document.querySelectorAll(".file-checkbox"),s=Array.from(e).every(t=>t.checked);e.forEach(t=>{t.checked=!s,this.updateFileSelection(t.value,t.checked)}),this.updateBulkActions()}updateFileSelection(e,s){s?this.selectedFiles.add(e):this.selectedFiles.delete(e),this.updateBulkActions()}updateBulkActions(){const e=document.getElementById("bulk-delete"),s=document.getElementById("bulk-analyze"),t=this.selectedFiles.size>0;e&&(e.disabled=!t),s&&(s.disabled=!t)}async bulkDeleteFiles(){if(!(this.selectedFiles.size===0||!confirm(`Delete ${this.selectedFiles.size} selected files?`)))try{for(const s of this.selectedFiles)await fetch(`/api/system/files/${encodeURIComponent(s)}`,{method:"DELETE"});this.selectedFiles.clear(),this.ui.loadUploadedFiles()}catch(s){console.error("Bulk delete failed:",s)}}}class k{constructor(){this.advancedFeatures=new b(null),this.ui=new w(this.advancedFeatures),this.advancedFeatures.ui=this.ui,window.app=this,this.initNavigation(),this.ui.renderDashboard()}initNavigation(){const e=document.querySelectorAll(".nav-links li");e.forEach(s=>{s.addEventListener("click",()=>{e.forEach(a=>a.classList.remove("active")),s.classList.add("active");const t=s.dataset.page;t==="dashboard"&&this.ui.renderDashboard(),t==="upload"&&this.ui.renderUpload(),t==="search"&&this.ui.renderSearch(),t==="advanced-search"&&this.ui.renderAdvancedSearchPage(),t==="analytics"&&this.ui.renderAnalyticsPage(),t==="file-manager"&&this.ui.renderFileManagerPage()})})}async handleUpload(e){if(!e)return;const s=document.getElementById("upload-status");s.textContent="Uploading and processing...",s.style.color="var(--accent-primary)";try{const t=await h.ingestFile(e);s.textContent=`Success! Processed ${t.chunks_count} chunks.`,s.style.color="#10b981",this.ui.loadUploadedFiles&&this.ui.loadUploadedFiles()}catch{s.textContent="Upload failed. Please try again.",s.style.color="#ef4444"}}async handleMultipleUpload(e){if(!e||e.length===0)return;const s=document.getElementById("upload-status");s.textContent=`Uploading ${e.length} files...`,s.style.color="var(--accent-primary)";let t=0,a=0;for(let n=0;n<e.length;n++)try{s.textContent=`Processing ${n+1}/${e.length}: ${e[n].name}`,await h.ingestFile(e[n]),t++}catch{a++}s.textContent=`Complete! ${t} uploaded, ${a} failed.`,s.style.color=a>0?"#f59e0b":"#10b981",this.ui.loadUploadedFiles&&this.ui.loadUploadedFiles()}async handleSearch(e){this.ui.addMessage(e,"user"),this.ui.addMessage("Thinking...","ai");try{const s=await h.chat(e),t=document.querySelectorAll(".message.ai");if(t.length>0&&t[t.length-1].remove(),this.ui.addMessage(s.response,"ai"),s.context_used&&s.context_used.length>0){const a=`📚 Sources: ${s.context_used.map(n=>n.filename).join(", ")}`;this.ui.addMessage(a,"context")}}catch{const t=document.querySelectorAll(".message.ai");t.length>0&&t[t.length-1].remove(),this.ui.addMessage("Sorry, I encountered an error. Please try again.","ai")}}}document.addEventListener("DOMContentLoaded",()=>{new k});
