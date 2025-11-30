# LivingOS AI

A professional-grade intelligent memory system that evolves with every interaction. Build retrieval-first, memory-driven AI systems using Qdrant vector database and a custom Parallel LLM Workflow with LangSmith integration.

## Features

### Core Capabilities

- **Multi-format Document Processing** - PDF, DOCX, CSV, JSON, Code files
- **Session-Based Document Isolation** - Each chat session has its own document workspace
- **Parallel AI Workflow** - Simultaneous execution of multiple LLMs (Gemini, Mistral, Cohere) for enhanced accuracy
- **Smart Aggregation** - Uses Groq (Llama 3.3 70B) to synthesize the best answer from multiple models
- **Memory Source Tracking** - Every AI response shows contributing sources (📄 Documents, 📧 Memories, 🧠 General Knowledge)
- **Long-Term Memory** - Automatically extracts and stores key facts from conversations (shared globally)
- **Chat Session Management** - Persistent conversations with isolated document access
- **Intent Analysis** - AI classifies user intent (Chat, Search, Summarize) for optimized responses
- **Smart Context** - Prioritizes active document content for "summarize" queries
- **Smart Notes Generation** - AI-powered note extraction from documents (multi-file support)
- **Dual Storage System** - Qdrant for fast retrieval + R2 for permanent archival
- **General Knowledge Fallback** - AI answers based on general knowledge when no documents are available
- **Professional APIs** - Enterprise-grade FastAPI backend
- **Custom Branding** - Unique favicon and polished UI

### Enterprise Architecture

- **Qdrant Vector Database** - Scalable vector storage with session filtering
- **Cloudflare R2 Storage** - Permanent conversation and file archival
- **Advanced Chunking** - Sentence-aware text processing
- **Background Tasks** - Non-blocking memory storage and fact extraction
- **Session Isolation** - Documents isolated by session, memories shared globally
- **Error Handling** - Comprehensive retry logic and null safety

## Tech Stack

- **Backend**: FastAPI, Python 3.13+
- **Vector DB**: Qdrant Cloud
- **AI Models**:
  - **Aggregator**: Groq (Llama 3.3 70B Versatile)
  - **Parallel Workers**: Gemini 2.5 Pro, Mistral Small, Cohere
  - **Fact Extraction**: Groq (Llama 3.3 8B Instant)
- **Memory System**: LangChain with LangSmith tracing
- **ML Models**: SentenceTransformers
- **Frontend**: Single-page OS-style interface
- **Document Processing**: PyPDF2, python-docx, pandas

## Quick Start

### 🚀 Deploy on Render (Recommended)

1. **Fork this repository** to your GitHub account
2. **Go to [Render Dashboard](https://dashboard.render.com)**
3. **Click "New" → "Blueprint"** and connect your repository
4. **Set environment variables** (see [Environment Variables](#environment-variables))
5. **Deploy!** Your app will be live at `https://your-app-name.onrender.com`

📖 **Detailed deployment guide:** [DEPLOY.md](DEPLOY.md)

### 💻 Local Development

#### Prerequisites

- Python 3.11+
- Qdrant Cloud account
- API Keys for: Groq, Gemini, Mistral, Cohere

#### Installation

1. **Clone and setup**

```bash
git clone <repository-url>
cd AI-Second-Brain
pip install -r requirements.txt
```

2. **Configure environment**

```bash
# Copy .env.example to .env and edit
cp .env.example .env
# Edit .env with your API keys
```

3. **Run locally**

```bash
cd backend
python main.py
```

4. **Access the application**

- Web Interface: `http://localhost:5300`
- API Documentation: `http://localhost:5300/docs`
- Health Check: `http://localhost:5300/health`

## API Endpoints

### Document Management

- `POST /api/ingest` - Upload and process documents (session-isolated)
- `GET /api/system/files` - List uploaded files for current session
- `DELETE /api/system/files/{filename}` - Delete file from both Qdrant and R2

### AI Interactions

- `POST /api/chat/message` - Context-aware AI conversations (Parallel Workflow)
- `POST /api/workflow/parallel` - Direct access to the parallel workflow

### Chat Management

- `POST /api/chat/start` - Create new chat session
- `GET /api/chat/sessions` - Get all chat sessions (shared)
- `GET /api/chat/history/{session_id}` - Get chat history for session
- `GET /api/chat/title/{session_id}` - Get auto-generated chat title

### Smart Notes

- `POST /api/notes/generate` - Generate smart notes from text
- `GET /api/notes/list` - List all smart notes
- `GET /api/notes/{id}` - Get specific smart note

## Configuration

### Environment Variables

#### Required for Full Functionality

```env
QDRANT_URL=https://your-cluster.qdrant.io
QDRANT_API_KEY=your_qdrant_api_key
GROQ_API_KEY=your_groq_api_key
GEMINI_API_KEY=your_gemini_api_key
MISTRAL_API_KEY=your_mistral_api_key
COHERE_API_KEY=your_cohere_api_key
```

#### Optional (Enhanced Features)

```env
# LangSmith Tracing
LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=livingos-ai

# Cloudflare R2 Storage
R2_ENDPOINT=your_r2_endpoint
R2_BUCKET_NAME=your_bucket_name
R2_ACCESS_KEY_ID=your_access_key
R2_SECRET_ACCESS_KEY=your_secret_key

# Performance
TF_ENABLE_ONEDNN_OPTS=0
HF_HUB_DISABLE_SYMLINKS_WARNING=1
```

ℹ️ **Note:** App works with just Qdrant + AI keys. R2 storage and LangSmith are optional.

### Supported File Types

- **Documents**: PDF, DOCX, TXT, MD
- **Data**: CSV, JSON
- **Code**: Python, JavaScript, HTML, XML

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OS-Style      │    │   FastAPI        │    │   Qdrant        │
│   Frontend      │◄──►│   Backend        │◄──►│   Vector DB     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │ Parallel Workflow│    │ Cloudflare R2   │
                       │ (Groq, Gemini,   │    │ Storage         │
                       │  Mistral, Cohere)│    │ (Archival)      │
                       └──────────────────┘    └─────────────────┘
```

### Session Architecture

- **Documents**: Isolated per session (each chat sees only its own files)
- **Memories**: Shared globally (extracted facts available across all sessions)
- **Chat History**: Persistent per session with automatic title generation
- **Smart Notes**: Generated per session, stored persistently

## Performance Features

- **Parallel Execution**: Significantly reduces latency by running models concurrently
- **Background Memory**: Fact extraction happens in the background, keeping the UI snappy
- **Session Isolation**: Documents isolated by session, memories shared globally
- **Dual Storage**: Fast retrieval (Qdrant) + permanent archival (R2)
- **Optimized Loading**: Limited chat history (50 messages) and sessions (20) for faster performance
- **Mobile Responsive**: Optimized layout for mobile devices with touch-friendly interface
- **Connection Pooling**: Efficient database connections
- **Error Recovery**: Comprehensive null safety and retry logic

## Usage Examples

### Upload Document (Session-Isolated)

```python
import requests

files = {'file': open('document.pdf', 'rb')}
data = {'session_id': 'your-session-id'}
response = requests.post('http://localhost:5300/api/ingest', files=files, data=data)
```

### AI Chat (Parallel Workflow)

```python
chat_data = {
    "session_id": "unique-session-id",
    "message": "Explain the key concepts from my uploaded documents"
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

## Production Deployment

### 🌐 Render (Recommended)

**One-click deployment with automatic scaling and SSL**

1. Use the `render.yaml` blueprint in this repository
2. Set environment variables in Render dashboard
3. Deploy automatically from GitHub

📖 **Full guide:** [DEPLOY.md](DEPLOY.md)

### 🐳 Docker (Alternative)

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY . .
EXPOSE 10000
CMD ["cd", "backend", "&&", "python", "main.py"]
```

### 🔧 Production Features

- **Graceful Degradation**: Works without optional services
- **Health Monitoring**: `/health` endpoint shows service status
- **Error Recovery**: Automatic retries and fallbacks
- **Session Isolation**: Documents isolated per session
- **Background Processing**: Non-blocking memory extraction

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- **Live Demo**: Deploy on Render in 5 minutes using [DEPLOY.md](DEPLOY.md)
- **Documentation**: API docs at `/docs` endpoint
- **Health Check**: Monitor `/health` for system status
- **Issues**: Create GitHub issues for bugs or feature requests

## Deployment Status

✅ **Ready for Production**

- 🌐 **Render**: One-click deployment with `render.yaml`
- 🐳 **Docker**: Production-ready Dockerfile included
- ☁️ **Cloud**: Optimized for cloud deployment
- 🔒 **Secure**: Environment-based configuration
- 📊 **Scalable**: Built for enterprise workloads

## Current System Behavior

### Intelligent Memory System

- **Living Knowledge**: System extracts and shares useful facts from every conversation
- **Session Isolation**: Documents and chat history remain private per session
- **Global Learning**: Accumulated knowledge grows and benefits all future chats
- **LangSmith Integration**: All interactions traced for monitoring and analytics

### Session Management

- **Persistent Sessions**: Session ID persists across page refreshes for continuity
- **Document Isolation**: Files uploaded in one session are only visible in that session
- **Memory Sharing**: Extracted facts and learnings are shared across all sessions
- **Chat Continuity**: Users can switch between different chat sessions and continue conversations
- **Chat Deletion**: Users can delete individual chat histories from the interface
- **Performance Limits**: Recent 50 messages per session, 20 most recent sessions displayed
- **New Chat Detection** - Fresh sessions automatically start with clean interface
- **Smart Persistence** - Sessions persist on page reload but reset on new tab for privacy

### File Management

- **Multiple Upload**: Support for uploading multiple files simultaneously via click or drag-and-drop
- **File Exclusion**: Toggle files in/out of AI access without deleting them
- **Session Filtering**: Files are isolated per session for privacy
- **File Operations**: View, exclude/include, and delete files with visual feedback
- **Drag & Drop**: Visual feedback when dragging files over upload area

### Navigation

- **M (Memory)**: Main workspace for document viewing and chat with file management
- **C (Chat)**: Browse and switch between chat sessions with delete functionality
- **F (Files)**: View smart notes and uploaded files for current session
- **Mobile Optimized**: Responsive design with stacked layout for mobile devices
- **Session Switching**: Clicking chat history automatically loads documents and switches to Memory view

### Parallel Workflow

Every chat message automatically uses the parallel workflow:

1. **Intent Analysis**: Gemini classifies intent (Chat/Search/Summarize) and extracts keywords
2. **Context Retrieval**:
   - *Summarize*: Fetches full content of active document
   - *Search*: Uses extracted keywords to find specific facts
   - *Chat*: Checks for relevant context but prioritizes conversation
   - *Fallback*: If no documents found, explicitly uses general knowledge
3. **Parallel Processing**: Gemini + Mistral + Cohere process simultaneously
4. **Smart Aggregation**: Groq synthesizes the best response
5. **Source Attribution**: Automatically adds source information to responses
6. **Background Learning**: Extracts facts and stores memories
7. **LangSmith Tracing**: All interactions logged for analysis

## Roadmap

### ✅ Completed

- [X] **Production Deployment**: Render-ready with `render.yaml`
- [X] **Graceful Degradation**: Works without optional services
- [X] **Session Management**: Persistent chat sessions with isolation
- [X] **Parallel AI Workflow**: Multi-model processing with aggregation
- [X] **Memory Source Tracking**: Transparent source attribution for all AI responses
- [X] **Smart Notes**: AI-powered document summarization
- [X] **Mobile Responsive**: Touch-friendly interface
- [X] **File Management**: Upload, exclude, delete with visual feedback
- [X] **Intent Analysis**: Smart query classification and optimization
- [X] **Background Processing**: Non-blocking memory extraction

---

Built for the AI community. Create living, intelligent systems that evolve with every interaction! - By Kushagra Singh
