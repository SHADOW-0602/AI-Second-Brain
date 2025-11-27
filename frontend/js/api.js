const API_BASE_URL = "http://localhost:5300/api";

class ApiClient {
    constructor() {
        // Config initialized
    }

    async ingestFile(file) {
        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch(`${API_BASE_URL}/ingest`, {
                method: "POST",
                body: formData
            });
            if (!response.ok) throw new Error("Ingestion failed");
            return await response.json();
        } catch (error) {
            console.error("Error ingesting file:", error);
            throw error;
        }
    }

    async search(query) {
        try {
            const response = await fetch(`${API_BASE_URL}/search`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    query,
                    limit: 5,
                    include_metadata: true
                })
            });
            if (!response.ok) throw new Error("Search failed");
            return await response.json();
        } catch (error) {
            console.error("Error searching:", error);
            throw error;
        }
    }

    async chat(message, workflowId = null, aiProvider = "lamatic") {
        try {
            let sessionId = localStorage.getItem('chat_session_id');
            if (!sessionId) {
                sessionId = crypto.randomUUID();
                localStorage.setItem('chat_session_id', sessionId);
            }

            const response = await fetch(`${API_BASE_URL}/chat/message`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    session_id: sessionId,
                    message,
                    workflow_id: workflowId || "default",
                    ai_provider: aiProvider,
                    context_limit: 3,
                    temperature: 0.7
                })
            });

            if (!response.ok) {
                throw new Error(`Chat failed: ${response.status}`);
            }

            return await response.json();

        } catch (error) {
            console.error("Error in chat:", error);
            throw error;
        }
    }

    async summarize() {
        return { summary: "Summarization not yet migrated to SDK." };
    }

    async executeParallelWorkflow(query) {
        try {
            const response = await fetch(`${API_BASE_URL}/workflow/parallel`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query: query })
            });
            if (!response.ok) throw new Error('Workflow failed');
            return await response.json();
        } catch (error) {
            console.error('Parallel Workflow Error:', error);
            throw error;
        }
    }
}

export const api = new ApiClient();
