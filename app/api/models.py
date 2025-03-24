from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """
    Request model for query endpoint
    """
    query: str = Field(..., description="User query about the Vanna repository")
    chat_history: Optional[List[Dict[str, str]]] = Field(
        default=None,
        description="List of previous messages, each containing 'role' and 'content'"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "How does Vanna convert natural language to SQL?",
                "chat_history": [
                    {"role": "user", "content": "What is Vanna AI?"},
                    {"role": "assistant", "content": "Vanna AI is a tool that helps convert natural language to SQL queries."}
                ]
            }
        }
    }


class QueryResponse(BaseModel):
    """
    Response model for query endpoint
    """
    query: str = Field(..., description="Original user query")
    answer: str = Field(..., description="Generated answer")
    is_out_of_scope: bool = Field(..., description="Whether the query is out of scope")
    processing_time: Dict[str, float] = Field(
        ..., 
        description="Time taken for different parts of processing (in seconds)"
    )
    context: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Relevant context used to generate the answer"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if an error occurred"
    )


class IndexingRequest(BaseModel):
    """
    Request model for indexing endpoint
    """
    force_reindex: bool = Field(
        default=False, 
        description="Whether to force reindexing of the repository"
    )


class IndexingResponse(BaseModel):
    """
    Response model for indexing endpoint
    """
    success: bool = Field(..., description="Whether indexing was successful")
    stats: Dict[str, Any] = Field(
        ..., 
        description="Statistics about the indexing process"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if an error occurred"
    )


class HealthResponse(BaseModel):
    """
    Response model for health endpoint
    """
    status: str = Field(..., description="Status of the service")
    vector_store: Dict[str, Any] = Field(
        ..., 
        description="Information about the vector store"
    )
    repo_info: Dict[str, Any] = Field(
        ..., 
        description="Information about the repository"
    )
