import os
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import threading

# Global cache for RAG context
_rag_cache = {
    "context": "",
    "last_modified": None,
    "directory": None,
    "loading": False
}
_rag_lock = threading.Lock()

def get_rag_context(directory: str = "files-rag", use_cache: bool = True, timeout: int = 5) -> str:
    """
    Retrieves context from files in the specified directory.
    Supports .pdf (text extraction) and .xlsx/.xls (text representation).
    Uses caching to avoid re-reading files on every request.
    Returns empty string if loading takes too long or fails.
    """
    global _rag_cache
    
    if not os.path.exists(directory):
        return ""
    
    # Check if cache is valid
    if use_cache and _rag_cache["directory"] == directory and _rag_cache["context"]:
        try:
            # Get the latest modification time of files in directory
            latest_mtime = max(
                os.path.getmtime(os.path.join(directory, f))
                for f in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, f))
            )
            
            # If cache is up-to-date, return cached context
            if _rag_cache["last_modified"] and latest_mtime <= _rag_cache["last_modified"]:
                return _rag_cache["context"]
        except:
            pass  # If there's any error checking cache, just reload
    
    # Check if already loading
    with _rag_lock:
        if _rag_cache["loading"]:
            # Return current cache if available, else empty
            return _rag_cache["context"]
        _rag_cache["loading"] = True
    
    try:
        # Load context from files with timeout protection
        context = _load_context_from_files(directory, timeout)
        
        # Update cache
        try:
            latest_mtime = max(
                os.path.getmtime(os.path.join(directory, f))
                for f in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, f))
            )
            with _rag_lock:
                _rag_cache = {
                    "context": context,
                    "last_modified": latest_mtime,
                    "directory": directory,
                    "loading": False
                }
        except:
            with _rag_lock:
                _rag_cache["loading"] = False
        
        return context
    except Exception as e:
        print(f"Error loading RAG context: {e}")
        with _rag_lock:
            _rag_cache["loading"] = False
        return ""

def _load_context_from_files(directory: str, timeout: int = 5) -> str:
    """Load context from files with timeout."""
    context_parts = []
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        
        if not os.path.isfile(filepath):
            continue
        
        try:
            if filename.lower().endswith('.pdf'):
                text = _read_pdf(filepath)
                if text and not text.startswith("[Error"):
                    context_parts.append(f"--- CONTENIDO DEL ARCHIVO: {filename} ---\n{text}\n")
            
            elif filename.lower().endswith(('.xlsx', '.xls')):
                text = _read_excel(filepath)
                if text and not text.startswith("[Error"):
                    context_parts.append(f"--- CONTENIDO DEL ARCHIVO: {filename} ---\n{text}\n")
                    
            elif filename.lower().endswith(('.txt', '.md')):
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                    context_parts.append(f"--- CONTENIDO DEL ARCHIVO: {filename} ---\n{text}\n")
                    
        except Exception as e:
            print(f"Error reading file {filename}: {str(e)}")
            continue
    
    return "\n".join(context_parts)

def _read_pdf(filepath: str) -> str:
    """Reads text from a PDF file using langchain or pypdf."""
    text = ""
    try:
        # Try using langchain loader first if available
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(filepath)
        pages = loader.load_and_split()
        text = "\n".join([p.page_content for p in pages])
    except ImportError:
        # Fallback to pypdf direct usage
        try:
            import pypdf
            reader = pypdf.PdfReader(filepath)
            text = "\n".join([page.extract_text() for page in reader.pages])
        except ImportError:
            return "[Error: No PDF reader library found (pypdf or langchain_community)]"
    except Exception as e:
        return f"[Error reading PDF: {str(e)}]"
    
    return text

def _read_excel(filepath: str) -> str:
    """Reads text from an Excel file."""
    try:
        # Read all sheets
        xls = pd.read_excel(filepath, sheet_name=None)
        text_parts = []
        
        for sheet_name, df in xls.items():
            text_parts.append(f"Sheet: {sheet_name}")
            text_parts.append(df.to_string(index=False))
            
        return "\n".join(text_parts)
    except Exception as e:
        return f"[Error reading Excel: {str(e)}]"
