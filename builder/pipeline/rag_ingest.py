import json
from pathlib import Path
from typing import List, Dict

RAG_CACHE_DIR = Path(".rag_cache")
RAG_INDEX_FILE = RAG_CACHE_DIR / "index.json"

def ingest_docs(docs_dir: Path) -> int:
    """
    Ingest markdown files from a directory into a simple JSON index.
    """
    if not docs_dir.exists():
        raise FileNotFoundError(f"Docs directory not found: {docs_dir}")
        
    documents = []
    
    for path in docs_dir.rglob("*.md"):
        content = path.read_text()
        # Simple chunking by header could be added, for now just whole file
        # or simplified sliding window if large.
        
        doc = {
            "source": str(path),
            "content": content,
            "filename": path.name
        }
        documents.append(doc)
        
    RAG_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RAG_INDEX_FILE.write_text(json.dumps(documents, indent=2))
    return len(documents)

def retrieve_context(query: str, k: int = 3) -> str:
    """
    Retrieve relevant context for a query.
    Note: For a production system this would use embeddings.
    Here we use simple keyword matching or just return top K docs if small corpus.
    Current implementation: Returns all docs/summaries as context (assuming small corpus)
    or just a placeholder for future vector DB integration.
    """
    if not RAG_INDEX_FILE.exists():
        return ""
        
    docs = json.loads(RAG_INDEX_FILE.read_text())
    
    # Naive keyword search
    hits = []
    terms = query.lower().split()
    
    for doc in docs:
        score = sum(1 for t in terms if t in doc["content"].lower())
        if score > 0:
            hits.append((score, doc))
            
    hits.sort(key=lambda x: x[0], reverse=True)
    
    context = ""
    for _, doc in hits[:k]:
        context += f"\n--- Source: {doc['filename']} ---\n{doc['content'][:2000]}...\n"
        
    return context
