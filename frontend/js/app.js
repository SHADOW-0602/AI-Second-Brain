import { api } from './api.js';
import { UI } from './ui.js';
import { AdvancedFeatures } from './advanced.js';

class App {
    constructor() {
        // Initialize modules with circular dependency resolution
        this.advancedFeatures = new AdvancedFeatures(null); // Temporary null
        this.ui = new UI(this.advancedFeatures);
        this.advancedFeatures.ui = this.ui; // Inject UI back into AdvancedFeatures

        // Expose for inline handlers in HTML
        window.app = this;

        this.initNavigation();

        // Render initial dashboard
        this.ui.renderDashboard();
    }

    initNavigation() {
        const navLinks = document.querySelectorAll(".nav-links li");
        navLinks.forEach(link => {
            link.addEventListener("click", () => {
                // Update active state
                navLinks.forEach(l => l.classList.remove("active"));
                link.classList.add("active");

                // Render page
                const page = link.dataset.page;
                if (page === "dashboard") this.ui.renderDashboard();
                if (page === "upload") this.ui.renderUpload();
                if (page === "search") this.ui.renderSearch();
                if (page === "analytics") this.ui.renderAnalyticsPage();
                if (page === "file-manager") this.ui.renderFileManagerPage();
            });
        });
    }

    async handleUpload(file) {
        if (!file) return;

        const statusDiv = document.getElementById("upload-status");
        statusDiv.textContent = "Uploading and processing...";
        statusDiv.style.color = "var(--accent-primary)";

        try {
            const result = await api.ingestFile(file);
            statusDiv.textContent = `Success! Processed ${result.chunks_count} chunks.`;
            statusDiv.style.color = "#10b981"; // Green

            // Refresh the files list
            if (this.ui.loadUploadedFiles) {
                this.ui.loadUploadedFiles();
            }
        } catch (error) {
            statusDiv.textContent = "Upload failed. Please try again.";
            statusDiv.style.color = "#ef4444"; // Red
        }
    }

    async handleMultipleUpload(files) {
        if (!files || files.length === 0) return;

        const statusDiv = document.getElementById("upload-status");
        statusDiv.textContent = `Uploading ${files.length} files...`;
        statusDiv.style.color = "var(--accent-primary)";

        let successful = 0;
        let failed = 0;

        for (let i = 0; i < files.length; i++) {
            try {
                statusDiv.textContent = `Processing ${i + 1}/${files.length}: ${files[i].name}`;
                await api.ingestFile(files[i]);
                successful++;
            } catch (error) {
                failed++;
            }
        }

        statusDiv.textContent = `Complete! ${successful} uploaded, ${failed} failed.`;
        statusDiv.style.color = failed > 0 ? "#f59e0b" : "#10b981";

        // Refresh the files list
        if (this.ui.loadUploadedFiles) {
            this.ui.loadUploadedFiles();
        }
    }

    // Legacy method - kept for compatibility
    async handleSearch(query, provider = null) {
        // Redirect to session-based chat if no active session
        if (!this.ui.currentSessionId) {
            await this.ui.createNewChat();
        }
        
        // Use session-based send
        document.getElementById('chat-input').value = query;
        await this.ui.handleSessionSend();
    }
}

// Initialize app when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    new App();
});
