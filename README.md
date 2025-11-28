# 🧠 AI Second Brain

A professional-grade persistent memory system for AI applications. Build retrieval-first, memory-driven AI systems using Qdrant vector database and a custom Parallel LLM Workflow.

## ✨ Features

### 🚀 Core Capabilities
- **Multi-format Document Processing** - PDF, DOCX, CSV, JSON, Code files
- **Semantic Search & Retrieval** - Vector-based similarity search with session isolation
- **Parallel AI Workflow** - Simultaneous execution of multiple LLMs (Gemini, Mistral, Cohere) for enhanced accuracy
- **Smart Aggregation** - Uses Groq (Llama 3 70B) to synthesize the best answer from multiple models
- **Long-Term Memory** - Automatically extracts and stores key facts from conversations
- **Chat Session Management** - Persistent conversations with shared memory across sessions
- **Dual Storage System** - Qdrant for fast retrieval + R2 for permanent archival
- **Professional APIs** - Enterprise-grade FastAPI backend
- **Real-time Analytics** - System monitoring and insights

### 🏗️ Enterprise Architecture
- **Qdrant Vector Database** - Scalable vector storage with session filtering
- **Cloudflare R2 Storage** - Permanent conversation archival
- **Advanced Chunking** - Sentence-aware text processing
- **Background Tasks** - Non-blocking memory storage and fact extraction
- **Session Isolation** - Documents isolated by session, memories shared globally
- **Health Monitoring** - System status and performance tracking
- **Error Handling** - Comprehensive retry logic and null safety

## 🛠️ Tech Stack

- **Backend**: FastAPI, Python 3.13+
- **Vector DB**: Qdrant Cloud
- **AI Models**: 
    - **Aggregator**: Groq (Llama 3 70B)
    - **Parallel Workers**: Gemini 1.5 Flash, Mistral Small, Cohere Command
    - **Fact Extraction**: Groq (Llama 3 8B)
- **ML Models**: SentenceTransformers
- **Frontend**: Vanilla JavaScript
- **Document Processing**: PyPDF2, python-docx, pandas

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- Qdrant Cloud account
- API Keys for: Groq, Gemini, Mistral, Cohere

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd AI-Second-Brain
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
# Copy and edit .env file
QDRANT_URL=your_qdrant_url
QDRANT_API_KEY=your_qdrant_key
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
MISTRAL_API_KEY=your_mistral_key
COHERE_API_KEY=your_cohere_key
```

4. **Run the application**
```bash
cd backend
python main.py
```

5. **Access the application**
- Web Interface: `http://localhost:5300`
- API Documentation: `http://localhost:5300/docs`
- Health Check: `http://localhost:5300/api/system/health`

## 📚 API Endpoints

### Document Management
- `POST /api/ingest` - Upload and process documents
- `POST /api/search` - Semantic search across documents

### AI Interactions
- `POST /api/chat/message` - Context-aware AI conversations (Parallel Workflow)
- `POST /api/workflow/parallel` - Direct access to the parallel workflow

### Chat Management
- `POST /api/chat/start` - Create new chat session
- `GET /api/chat/sessions` - Get all chat sessions (shared)
- `GET /api/chat/history/{session_id}` - Get chat history for session
- `GET /api/chat/title/{session_id}` - Get auto-generated chat title

### System Monitoring
- `GET /api/system/health` - System health status
- `GET /api/system/analytics` - Usage analytics
- `POST /api/system/cleanup` - Data cleanup operations

## 🔧 Configuration

### Environment Variables
```env
# Required
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_api_key
GROQ_API_KEY=your_groq_key
GEMINI_API_KEY=your_gemini_key
MISTRAL_API_KEY=your_mistral_key
COHERE_API_KEY=your_cohere_key

# Optional
TF_ENABLE_ONEDNN_OPTS=0
HF_HUB_DISABLE_SYMLINKS_WARNING=1
```

### Supported File Types
- **Documents**: PDF, DOCX, TXT, MD
- **Data**: CSV, JSON
- **Code**: Python, JavaScript, HTML, XML

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI        │    │   Qdrant        │
│   (Vanilla JS)  │◄──►│   Backend        │◄──►│   Vector DB     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Parallel Workflow│    │ Cloudflare R2   │
                       │ (Groq, Gemini,   │    │ Storage         │
                       │  Mistral, Cohere)│    │ (Archival)      │
                       └──────────────────┘    └─────────────────┘
```

## 📊 Performance Features

- **Parallel Execution**: Significantly reduces latency by running models concurrently
- **Background Memory**: Fact extraction happens in the background, keeping the UI snappy
- **Session Isolation**: Documents isolated by session, memories shared globally
- **Dual Storage**: Fast retrieval (Qdrant) + permanent archival (R2)
- **Connection Pooling**: Efficient database connections
- **Quantization**: INT8 scalar quantization for memory efficiency
- **Error Recovery**: Comprehensive null safety and retry logic

## 🔍 Usage Examples

### Upload Document
```python
import requests

files = {'file': open('document.pdf', 'rb')}
response = requests.post('http://localhost:5300/api/ingest', files=files)
```

### Search Documents
```python
search_data = {
    "query": "machine learning concepts",
    "limit": 5,
    "min_score": 0.7
}
response = requests.post('http://localhost:5300/api/search', json=search_data)
```

### AI Chat (Parallel Workflow)
```python
chat_data = {
    "session_id": "unique-session-id",
    "message": "Explain the key concepts from my uploaded documents",
    "ai_provider": "parallel"
}
response = requests.post('http://localhost:5300/api/chat/message', json=chat_data)
```

### Chat Session Management
```python
# Start new chat session
response = requests.post('http://localhost:5300/api/chat/start')
session_id = response.json()['session_id']

# Get all chat sessions
response = requests.get('http://localhost:5300/api/chat/sessions')
sessions = response.json()['sessions']

# Get chat history
response = requests.get(f'http://localhost:5300/api/chat/history/{session_id}')
history = response.json()['history']
```

## 🛡️ Production Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5300
CMD ["python", "backend/main.py"]
```

### Environment Setup
- Use environment-specific `.env` files
- Configure proper logging levels
- Set up monitoring and alerting
- Implement backup strategies for vector data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the `/docs` endpoint when running
- **Issues**: Create GitHub issues for bugs or feature requests
- **Health Check**: Monitor `/api/system/health` for system status

## 🔮 Roadmap

- [ ] Multi-user support with authentication
- [ ] Advanced analytics dashboard
- [ ] Custom embedding models
- [ ] Real-time collaboration features
- [ ] Mobile application
- [ ] Advanced workflow automation

---

Built with ❤️ for the AI community. Create intelligent systems that remember, reason, and retrieve! - By Kushagra Singh