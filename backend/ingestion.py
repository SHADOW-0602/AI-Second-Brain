import os
import re
import hashlib
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from io import BytesIO
from sentence_transformers import SentenceTransformer
import PyPDF2
import docx
import pandas as pd
import json
from pathlib import Path

HTML_EXT = '.html'

class DocumentProcessor:
    def __init__(self, model_name: str = None):
        from config import EMBEDDING_MODEL
        if model_name is None:
            model_name = EMBEDDING_MODEL
        self.model = SentenceTransformer(model_name)
        self.supported_formats = {'.txt', '.md', '.pdf', '.docx', '.csv', '.json', '.py', '.js', HTML_EXT, '.xml'}
        self.model = SentenceTransformer(model_name)
        self.supported_formats = {'.txt', '.md', '.pdf', '.docx', '.csv', '.json', '.py', '.js', '.html', '.xml'}
    
    def get_embedding(self, text: str) -> List[float]:
        """Generate embeddings with preprocessing."""
        if not text or not text.strip():
            from config import VECTOR_SIZE
            return [0.0] * VECTOR_SIZE
        
        # Clean and normalize text
        cleaned_text = self._clean_text(text)
        return self.model.encode(cleaned_text, normalize_embeddings=True).tolist()
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better embeddings."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation
        text = re.sub(r'[^\w\s.,!?;:()-]', '', text)
        return text.strip()
    
    def chunk_text(self, text: str, chunk_size: int = None, overlap: int = None, min_chunk_size: int = None) -> List[Dict]:
        from config import CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE
        if chunk_size is None:
            chunk_size = CHUNK_SIZE
        if overlap is None:
            overlap = CHUNK_OVERLAP
        if min_chunk_size is None:
            min_chunk_size = MIN_CHUNK_SIZE
        """Advanced text chunking with metadata."""
        if not text or len(text) < min_chunk_size:
            return []
        
        chunks = []
        sentences = self._split_into_sentences(text)
        
        current_chunk = ""
        current_size = 0
        
        for i, sentence in enumerate(sentences):
            sentence_size = len(sentence)
            
            if current_size + sentence_size > chunk_size and current_chunk:
                # Create chunk with metadata
                chunk_data = {
                    'text': current_chunk.strip(),
                    'size': len(current_chunk),
                    'sentence_count': len(current_chunk.split('.')),
                    'chunk_index': len(chunks),
                    'hash': hashlib.md5(current_chunk.encode()).hexdigest()[:8]
                }
                chunks.append(chunk_data)
                
                # Start new chunk with overlap
                overlap_text = self._get_overlap_text(current_chunk, overlap)
                current_chunk = overlap_text + sentence
                current_size = len(current_chunk)
            else:
                current_chunk += " " + sentence if current_chunk else sentence
                current_size += sentence_size
        
        # Add final chunk
        if current_chunk.strip() and len(current_chunk) >= min_chunk_size:
            chunk_data = {
                'text': current_chunk.strip(),
                'size': len(current_chunk),
                'sentence_count': len(current_chunk.split('.')),
                'chunk_index': len(chunks),
                'hash': hashlib.md5(current_chunk.encode()).hexdigest()[:8]
            }
            chunks.append(chunk_data)
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using regex."""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _get_overlap_text(self, text: str, overlap_size: int) -> str:
        """Get overlap text from the end of current chunk."""
        if len(text) <= overlap_size:
            return text
        return text[-overlap_size:]
    
    def parse_file(self, file_content: bytes, filename: str) -> Tuple[str, Dict]:
        """Extract text and metadata from various file formats."""
        file_ext = Path(filename).suffix.lower()
        
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}")
        
        metadata = {
            'filename': filename,
            'file_size': len(file_content),
            'file_type': file_ext,
            'processed_at': datetime.utcnow().isoformat(),
            'content_hash': hashlib.sha256(file_content).hexdigest()[:16]
        }
        
        try:
            if file_ext == '.pdf':
                text = self._parse_pdf(file_content)
            elif file_ext == '.docx':
                text = self._parse_docx(file_content)
            elif file_ext == '.csv':
                text = self._parse_csv(file_content)
            elif file_ext in {'.py', '.js', HTML_EXT, '.xml'}:
                text = self._parse_code(file_content, file_ext)
            elif file_ext in {'.py', '.js', '.html', '.xml'}:
                text = self._parse_code(file_content, file_ext)
            else:  # .txt, .md
                text = file_content.decode('utf-8', errors='ignore')
            
            metadata['char_count'] = len(text)
            metadata['word_count'] = len(text.split())
            
            return text, metadata
            
        except Exception as e:
            raise ValueError(f"Error parsing {filename}: {str(e)}")
    
    def _parse_pdf(self, content: bytes) -> str:
        """Extract text from PDF files."""
        pdf_reader = PyPDF2.PdfReader(BytesIO(content))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()
    
    def _parse_docx(self, content: bytes) -> str:
        """Extract text from DOCX files."""
        doc = docx.Document(BytesIO(content))
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text.strip()
    
    def _parse_csv(self, content: bytes) -> str:
        """Convert CSV to readable text format."""
        df = pd.read_csv(BytesIO(content))
        # Convert to structured text
        text = f"CSV Data with {len(df)} rows and {len(df.columns)} columns:\n"
        text += f"Columns: {', '.join(df.columns)}\n\n"
        
        # Add sample data and summary
        text += "Sample data:\n"
        text += df.head().to_string(index=False)
        text += "\n\nData summary:\n"
        text += df.describe(include='all').to_string()
        
        return text
    
    def _parse_json(self, content: bytes) -> str:
        """Convert JSON to readable text format."""
        data = json.loads(content.decode('utf-8'))
        
        def json_to_text(obj, level=0):
            indent = "  " * level
            if isinstance(obj, dict):
                text = ""
                for key, value in obj.items():
                    text += f"{indent}{key}: "
                    if isinstance(value, (dict, list)):
                        text += "\n" + json_to_text(value, level + 1)
                    else:
                        text += f"{value}\n"
                return text
            elif isinstance(obj, list):
                text = ""
                for i, item in enumerate(obj):
                    text += f"{indent}[{i}]: "
                    if isinstance(item, (dict, list)):
                        text += "\n" + json_to_text(item, level + 1)
                    else:
                        text += f"{item}\n"
                return text
            else:
                return f"{indent}{obj}\n"
        
        return json_to_text(data)
    
    def _parse_code(self, content: bytes, file_ext: str) -> str:
        """Parse code files with structure preservation."""
        code = content.decode('utf-8', errors='ignore')
        lang_map = {'.py': 'Python', '.js': 'JavaScript', HTML_EXT: 'HTML', '.xml': 'XML'}
        # Add file type context
        lang_map = {'.py': 'Python', '.js': 'JavaScript', '.html': 'HTML', '.xml': 'XML'}
        language = lang_map.get(file_ext, 'Code')
        
        # Extract functions, classes, and comments for better searchability
        structured_text = f"{language} code file:\n\n"
        
        if file_ext == '.py':
            # Extract Python functions and classes
            functions = re.findall(r'def\s+(\w+)\s*\([^)]*\):', code)
            classes = re.findall(r'class\s+(\w+)\s*[\(:]', code)
            
            if classes:
                structured_text += f"Classes: {', '.join(classes)}\n"
            if functions:
                structured_text += f"Functions: {', '.join(functions)}\n"
        
        # Add the actual code
        structured_text += "\nCode content:\n" + code
        
        return structured_text

# Global instance
processor = DocumentProcessor()

# Backward compatibility functions
def get_embedding(text: str) -> List[float]:
    return processor.get_embedding(text)

def chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> List[str]:
    chunks = processor.chunk_text(text, chunk_size, overlap)
    return [chunk['text'] for chunk in chunks]

def parse_file(file_content: bytes, filename: str) -> str:
    text, _ = processor.parse_file(file_content, filename)
    return text
