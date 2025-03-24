import numpy as np
from typing import List, Optional, Any, Dict
from langchain_core.embeddings import Embeddings

class MockEmbeddings(Embeddings):
    """
    Mock implementation of text embeddings for testing without Azure OpenAI API
    """
    
    def __init__(self, dimension: int = 1536):
        """
        Initialize the mock embeddings
        
        Args:
            dimension (int): Dimension of the embeddings
        """
        self.dimension = dimension
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate mock embeddings for a list of texts
        
        Args:
            texts (List[str]): List of texts to embed
            
        Returns:
            List[List[float]]: List of embeddings
        """
        # Generate deterministic but pseudo-random embeddings
        embeddings = []
        
        for text in texts:
            # Use text hash as seed
            seed = hash(text) % 10000
            np.random.seed(seed)
            
            # Generate random embedding and normalize
            embedding = np.random.randn(self.dimension)
            embedding = embedding / np.linalg.norm(embedding)
            
            embeddings.append(embedding.tolist())
        
        return embeddings
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate mock embedding for a query
        
        Args:
            text (str): Query text to embed
            
        Returns:
            List[float]: Embedding
        """
        # Use same method as embed_documents for consistency
        return self.embed_documents([text])[0]
