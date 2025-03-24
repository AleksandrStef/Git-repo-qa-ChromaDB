import os
import time
from typing import Dict, List, Optional, Any
import numpy as np
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter
# Import our mock embeddings instead of Azure OpenAI
from app.indexing.mock_embeddings import MockEmbeddings
# Try to import from langchain_chroma first, fall back to community if not available
try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
from app.config import (
    AZURE_OPENAI_API_KEY, 
    AZURE_OPENAI_ENDPOINT, 
    AZURE_OPENAI_API_VERSION,
    EMBEDDING_MODEL,
    CHROMA_PERSIST_DIRECTORY,
)
from app.utils.logger import logger
from app.indexing.github_repo import GitHubRepoHandler

class RepositoryIndexer:
    """
    Class to handle the indexing of GitHub repository files into a vector store
    """
    
    def __init__(self, 
                 chunk_size: int = 1000, 
                 chunk_overlap: int = 200,
                 persist_directory: str = CHROMA_PERSIST_DIRECTORY,
                 use_mock: bool = False):  # Changed default to use real embeddings
        """
        Initialize the repository indexer
        
        Args:
            chunk_size (int): Size of text chunks for splitting documents
            chunk_overlap (int): Overlap between text chunks
            persist_directory (str): Directory to persist the vector store
            use_mock (bool): Whether to use mock embeddings instead of Azure OpenAI
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.persist_directory = persist_directory
        self.use_mock = use_mock
        
        # Create embeddings model - either mock or real
        if self.use_mock:
            self.embeddings = MockEmbeddings(dimension=1536)  # Same dimension as text-embedding-ada-002
            logger.info("Using mock embeddings for testing")
        else:
            try:
                from langchain_openai import AzureOpenAIEmbeddings
                self.embeddings = AzureOpenAIEmbeddings(
                    azure_deployment=EMBEDDING_MODEL,
                    openai_api_version=AZURE_OPENAI_API_VERSION,
                    azure_endpoint=AZURE_OPENAI_ENDPOINT,
                    api_key=AZURE_OPENAI_API_KEY,
                )
                logger.info("Using Azure OpenAI embeddings")
            except Exception as e:
                logger.error(f"Error initializing Azure OpenAI embeddings: {str(e)}")
                logger.info("Falling back to mock embeddings")
                self.embeddings = MockEmbeddings(dimension=1536)
        
        # Create text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
        )
        
        # Initialize vector store
        self._initialize_vector_store()
    
    def _initialize_vector_store(self):
        """
        Initialize the vector store
        """
        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        try:
            self.vector_store = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )
            logger.info(f"Vector store initialized at {self.persist_directory}")
        except Exception as e:
            logger.error(f"Error initializing Chroma: {str(e)}")
            # Try initializing without persistence
            self.vector_store = Chroma(
                embedding_function=self.embeddings,
            )
            logger.info("Vector store initialized in memory (no persistence)")
    
    def index_repository(self, repo_handler: GitHubRepoHandler) -> Dict[str, Any]:
        """
        Index all files in the repository
        
        Args:
            repo_handler (GitHubRepoHandler): Handler for the GitHub repository
            
        Returns:
            Dict[str, Any]: Statistics about the indexing process
        """
        start_time = time.time()
        logger.info("Starting repository indexing...")
        
        # Get all repository files
        repo_files = repo_handler.get_repo_files()
        
        # Process each file
        total_chunks = 0
        total_files = len(repo_files)
        processed_files = 0
        
        for file_path, file_info in repo_files.items():
            try:
                # Get file content and metadata
                content = file_info["content"]
                github_url = file_info["github_url"]
                
                # Get additional metadata
                metadata = repo_handler.get_file_metadata(file_path)
                
                # Split text into chunks
                chunks = self.text_splitter.create_documents(
                    texts=[content],
                    metadatas=[{
                        "source": file_path,
                        "github_url": github_url,
                        **metadata
                    }]
                )
                
                # Add chunks to vector store
                self.vector_store.add_documents(chunks)
                
                total_chunks += len(chunks)
                processed_files += 1
                
                if processed_files % 10 == 0:
                    logger.info(f"Processed {processed_files}/{total_files} files...")
                
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
        
        # Try to persist the vector store if it has the persist method
        try:
            if hasattr(self.vector_store, 'persist'):
                self.vector_store.persist()
                logger.info("Vector store persisted to disk")
            else:
                logger.info("Vector store does not support persistence, keeping in memory")
        except Exception as e:
            logger.error(f"Error persisting vector store: {str(e)}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Compile statistics
        stats = {
            "total_files": total_files,
            "processed_files": processed_files,
            "total_chunks": total_chunks,
            "duration_seconds": duration,
            "chunks_per_second": total_chunks / duration if duration > 0 else 0,
            "files_per_second": processed_files / duration if duration > 0 else 0,
        }
        
        logger.info(f"Repository indexing completed in {duration:.2f} seconds")
        logger.info(f"Indexed {total_chunks} chunks from {processed_files} files")
        
        return stats
    
    def search(self, 
              query: str, 
              k: int = 5, 
              filter: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search the vector store for relevant documents
        
        Args:
            query (str): Query string
            k (int): Number of results to return
            filter (Dict[str, Any]): Filter to apply to the search
            
        Returns:
            List[Dict[str, Any]]: List of relevant documents with metadata
        """
        start_time = time.time()
        
        try:
            # Search vector store
            docs = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter
            )
            
            # Format results
            results = []
            for doc in docs:
                results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "source": doc.metadata.get("source", "Unknown"),
                    "github_url": doc.metadata.get("github_url", "Unknown"),
                })
            
            duration = time.time() - start_time
            logger.info(f"Search completed in {duration:.4f} seconds, found {len(results)} results")
            
            return results
        except Exception as e:
            logger.error(f"Error searching vector store: {str(e)}")
            # Return empty results if search fails
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store
        
        Returns:
            Dict[str, Any]: Statistics about the vector store
        """
        try:
            # Get collection info
            if hasattr(self.vector_store, '_collection'):
                collection = self.vector_store._collection
                count = collection.count()
            else:
                count = 0  # Default if we can't access the collection
            
            return {
                "document_count": count,
                "persist_directory": self.persist_directory,
                "chunk_size": self.chunk_size,
                "chunk_overlap": self.chunk_overlap,
                "using_mock_embeddings": self.use_mock,
            }
        except Exception as e:
            logger.error(f"Error getting vector store stats: {str(e)}")
            return {
                "document_count": 0,
                "error": str(e)
            }
