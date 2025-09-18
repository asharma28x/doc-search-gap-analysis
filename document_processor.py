import os
import pickle
import numpy as np
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer
import faiss

# Config of variables
VECTOR_STORE_PATH = "vector_store"
INDEX_FILE = os.path.join(VECTOR_STORE_PATH, "faiss_index.bin")
CHUNKS_FILE = os.path.join(VECTOR_STORE_PATH, "chunks.pkl")
EMBEDDING_MODEL = "sentence-transformers/static-retrieval-mrl-en-v1"

def get_embedding_model():
    """Loads and returns the sentence transformer model."""
    print("Loading embedding model...")
    model = SentenceTransformer(EMBEDDING_MODEL, device="cpu")
    print("Embedding model loaded.")
    return model

def load_and_chunk_pdfs(pdf_paths):
    """Loads text from PDF files and splits it into chunks."""
    all_chunks = []
    for path in pdf_paths:
        print(f"Processing PDF: {path}")
        try:
            reader = PdfReader(path)
            text = "".join(page.extract_text() for page in reader.pages)
            # Simple chunking by paragraph
            chunks = [f"Source: {os.path.basename(path)}\n\n{p.strip()}" for p in text.split('\n\n') if p.strip()]
            all_chunks.extend(chunks)
        except Exception as e:
            print(f"Error reading {path}: {e}")
    return all_chunks

def create_vector_store(doc_paths, model):
    """Creates and saves a FAISS vector store from document paths."""
    if not os.path.exists(VECTOR_STORE_PATH):
        os.makedirs(VECTOR_STORE_PATH)

    chunks = load_and_chunk_pdfs(doc_paths)
    if not chunks:
        print("No text chunks found. Aborting vector store creation.")
        return

    print(f"Creating embeddings for {len(chunks)} chunks...")
    embeddings = model.encode(chunks, show_progress_bar=True)
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index = faiss.IndexIDMap(index)
    index.add_with_ids(np.array(embeddings, dtype=np.float32), np.arange(len(chunks)))

    print(f"Saving FAISS index to {INDEX_FILE}")
    faiss.write_index(index, INDEX_FILE)

    print(f"Saving text chunks to {CHUNKS_FILE}")
    with open(CHUNKS_FILE, "wb") as f:
        pickle.dump(chunks, f)

def load_vector_store():
    """Loads a FAISS index and corresponding text chunks from disk."""
    if not os.path.exists(INDEX_FILE) or not os.path.exists(CHUNKS_FILE):
        return None, None
    
    print("Loading vector store from disk...")
    index = faiss.read_index(INDEX_FILE)
    with open(CHUNKS_FILE, "rb") as f:
        chunks = pickle.load(f)
    print("Vector store loaded.")
    return index, chunks
