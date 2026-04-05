import os
from typing import List
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.utils import embedding_functions

class RAGService:
    def __init__(self, collection_name: str = "auraflow_docs"):
        self.collection_name = collection_name
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            # Lazy initialization of ChromaDB
            CHROMA_DATA_PATH = "backend/data/chroma"
            os.makedirs(CHROMA_DATA_PATH, exist_ok=True)
            chroma_client = chromadb.PersistentClient(path=CHROMA_DATA_PATH)
            default_ef = embedding_functions.DefaultEmbeddingFunction()
            self._collection = chroma_client.get_or_create_collection(
                name=self.collection_name, 
                embedding_function=default_ef
            )
        return self._collection

    async def index_file(self, file_path: str):
        """Loads, splits, and indexes a file into ChromaDB."""
        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)
            
        documents = loader.load()
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100
        )
        chunks = text_splitter.split_documents(documents)
        
        ids = [f"{os.path.basename(file_path)}_{i}" for i in range(len(chunks))]
        texts = [chunk.page_content for chunk in chunks]
        metadatas = [{"source": file_path} for _ in chunks]
        
        self.collection.add(
            ids=ids,
            documents=texts,
            metadatas=metadatas
        )
        return len(chunks)

    def retrieve_context(self, query: str, n_results: int = 3) -> str:
        """Retrieves relevant chunks and returns them as a single context string."""
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        
        # Flatten the results
        documents = results.get("documents", [[]])[0]
        return "\n\n---\n\n".join(documents)

rag_service = RAGService()
