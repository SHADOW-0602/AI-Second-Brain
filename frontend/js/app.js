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
        this.initSidebarNewChat();
        this.initMobileMenu();

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

                // Close mobile menu if open
                this.closeMobileMenu();
            });
        });
    }

    initMobileMenu() {
        const menuBtn = document.getElementById('mobile-menu-btn');
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');

        if (menuBtn && sidebar && overlay) {
            menuBtn.addEventListener('click', () => {
                sidebar.classList.add('open');
                overlay.classList.add('active');
            });

            overlay.addEventListener('click', () => {
                this.closeMobileMenu();
            });
        }
    }

    closeMobileMenu() {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar && overlay) {
            sidebar.classList.remove('open');
            overlay.classList.remove('active');
        }
    }

    initSidebarNewChat() {
        const newChatBtn = document.getElementById('sidebar-new-chat');
        if (newChatBtn) {
            newChatBtn.addEventListener('click', async () => {
                // Navigate to search page first
                const navLinks = document.querySelectorAll(".nav-links li");
                navLinks.forEach(l => l.classList.remove("active"));

                const searchLink = document.querySelector('[data-page="search"]');
                if (searchLink) searchLink.classList.add("active");

                this.ui.renderSearch();

                // Close mobile menu if open
                this.closeMobileMenu();

                // Wait for UI to render then create new chat
                setTimeout(async () => {
                    if (this.ui.createNewChat) {
                        await this.ui.createNewChat();
                    }
                }, 100);
            });
        }
    }

    async handleUpload(file) {
        if (!file) return;

        // Ensure we have a session for document isolation
        if (!this.ui.currentSessionId) {
            await this.ui.createNewChat();
        }

        const statusDiv = document.getElementById("upload-status");
        if (statusDiv) {
            statusDiv.textContent = "Uploading and processing...";
            statusDiv.style.color = "var(--accent-primary)";
        }

        try {
            const result = await api.ingestFile(file, this.ui.currentSessionId);
            if (statusDiv) {
                statusDiv.textContent = `Success! Processed ${result.chunks_count} chunks.`;
                statusDiv.style.color = "var(--success)";
            }

            // Refresh the files list
            if (this.ui.loadUploadedFiles) {
                this.ui.loadUploadedFiles();
            }
        } catch (error) {
            if (statusDiv) {
                statusDiv.textContent = "Upload failed. Please try again.";
                statusDiv.style.color = "var(--error)";
            }
        }
    }

    async handleMultipleUpload(files) {
        if (!files || files.length === 0) return;

        // Ensure we have a session for document isolation
        if (!this.ui.currentSessionId) {
            await this.ui.createNewChat();
        }

        const statusDiv = document.getElementById("upload-status");
        if (statusDiv) {
            statusDiv.textContent = `Uploading ${files.length} files...`;
            statusDiv.style.color = "var(--accent-primary)";
        }

        let successful = 0;
        let failed = 0;

        for (let i = 0; i < files.length; i++) {
            try {
                if (statusDiv) statusDiv.textContent = `Processing ${i + 1}/${files.length}: ${files[i].name}`;
                await api.ingestFile(files[i], this.ui.currentSessionId);
                successful++;
            } catch (error) {
                failed++;
            }
        }

        if (statusDiv) {
            statusDiv.textContent = `Complete! ${successful} uploaded, ${failed} failed.`;
            statusDiv.style.color = failed > 0 ? "var(--warning)" : "var(--success)";
        }

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
        const chatInput = document.getElementById('chat-input');
        if (chatInput) chatInput.value = query;
        await this.ui.handleSessionSend();
    }
}

// Initialize app when DOM is ready
document.addEventListener("DOMContentLoaded", () => {
    new App();
});
