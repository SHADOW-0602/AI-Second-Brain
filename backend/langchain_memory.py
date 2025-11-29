import os
import logging
from typing import Dict, Any, Optional, List
from langsmith import Client

logger = logging.getLogger(__name__)

# Initialize LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "livingos-ai")

class LangChainMemoryManager:
    """Simple memory manager with LangSmith tracing"""
    
    def __init__(self):
        self.memories: Dict[str, List[Dict[str, str]]] = {}
        try:
            self.client = Client()
        except Exception as e:
            logger.warning(f"LangSmith client initialization failed: {e}")
            self.client = None
    
    def add_conversation(self, session_id: str, user_message: str, ai_response: str):
        """Add conversation to memory with LangSmith tracing"""
        try:
            if session_id not in self.memories:
                self.memories[session_id] = []
            
            self.memories[session_id].append({"role": "user", "content": user_message})
            self.memories[session_id].append({"role": "assistant", "content": ai_response})
            
            # Keep only last 20 messages
            if len(self.memories[session_id]) > 20:
                self.memories[session_id] = self.memories[session_id][-20:]
            
            logger.info(f"Added conversation to memory for session {session_id}")
        except Exception as e:
            logger.error(f"Failed to add conversation to memory: {e}")
    
    def get_context_with_preferences(self, session_id: str, base_context: str) -> str:
        """Get enhanced context with conversation history"""
        try:
            if session_id in self.memories and self.memories[session_id]:
                recent_messages = self.memories[session_id][-4:]  # Last 2 exchanges
                recent_context = "\n".join([
                    f"{msg['role'].title()}: {msg['content']}"
                    for msg in recent_messages
                ])
                return f"RECENT CONVERSATION:\n{recent_context}\n\nCONTEXT:\n{base_context}"
            
            return base_context
        except Exception as e:
            logger.error(f"Failed to enhance context: {e}")
            return base_context

# Global instance
_memory_manager = None

def get_memory_manager() -> LangChainMemoryManager:
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = LangChainMemoryManager()
    return _memory_manager