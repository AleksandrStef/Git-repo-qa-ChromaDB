from typing import Dict, Any
import time
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.indexing.github_repo import GitHubRepoHandler
from app.indexing.vector_store import RepositoryIndexer
from app.agents.llm import LLMHandler
from app.agents.workflow import AgentWorkflow
from app.config import REPO_URL, REPO_BRANCH
from app.api.models import (
    QueryRequest,
    QueryResponse,
    IndexingRequest,
    IndexingResponse,
    HealthResponse
)
from app.utils.logger import logger

# Create router
router = APIRouter()

# Create global instances
repo_handler = GitHubRepoHandler(REPO_URL, REPO_BRANCH)
indexer = RepositoryIndexer()
llm_handler = LLMHandler()
agent_workflow = AgentWorkflow(indexer, llm_handler)

# Indexing status
indexing_status = {
    "in_progress": False,
    "last_indexed": None,
    "stats": None,
    "error": None
}


def get_workflow() -> AgentWorkflow:
    """
    Get the agent workflow
    
    Returns:
        AgentWorkflow: Agent workflow
    """
    return agent_workflow


def perform_indexing():
    """
    Perform indexing in the background
    """
    global indexing_status
    
    if indexing_status["in_progress"]:
        logger.info("Indexing already in progress, skipping...")
        return
    
    indexing_status["in_progress"] = True
    indexing_status["error"] = None
    
    try:
        # Clone repository
        repo_handler.clone_repo()
        
        # Index repository
        start_time = time.time()
        stats = indexer.index_repository(repo_handler)
        
        # Update status
        indexing_status["last_indexed"] = time.time()
        indexing_status["stats"] = stats
        indexing_status["in_progress"] = False
        
        logger.info(f"Indexing completed in {time.time() - start_time:.2f} seconds")
    
    except Exception as e:
        error_msg = f"Error during indexing: {str(e)}"
        logger.error(error_msg)
        
        indexing_status["error"] = error_msg
        indexing_status["in_progress"] = False


@router.post("/api/query", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    workflow: AgentWorkflow = Depends(get_workflow)
) -> QueryResponse:
    """
    Query the repository
    
    Args:
        request (QueryRequest): Query request
        workflow (AgentWorkflow): Agent workflow
        
    Returns:
        QueryResponse: Query response
    """
    try:
        # Check if repository has been indexed
        if indexer.get_stats().get("document_count", 0) == 0:
            if not indexing_status["in_progress"]:
                raise HTTPException(
                    status_code=503,
                    detail="Repository has not been indexed yet. Please trigger indexing first."
                )
            else:
                raise HTTPException(
                    status_code=503,
                    detail="Repository indexing is in progress. Please try again later."
                )
        
        # Run workflow
        result = workflow.run(
            query=request.query,
            chat_history=request.chat_history
        )
        
        # Convert to response model
        response = QueryResponse(
            query=result["query"],
            answer=result["answer"],
            is_out_of_scope=result["is_out_of_scope"],
            processing_time=result["processing_time"],
            error=result.get("error")
        )
        
        # Add context if available
        if "context" in result:
            response.context = result["context"]
        
        return response
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )


@router.post("/api/index", response_model=IndexingResponse)
async def index(
    request: IndexingRequest,
    background_tasks: BackgroundTasks
) -> IndexingResponse:
    """
    Index the repository
    
    Args:
        request (IndexingRequest): Indexing request
        background_tasks (BackgroundTasks): Background tasks
        
    Returns:
        IndexingResponse: Indexing response
    """
    try:
        # Check if indexing is already in progress
        if indexing_status["in_progress"]:
            return IndexingResponse(
                success=False,
                stats={"status": "in_progress"},
                error="Indexing already in progress"
            )
        
        # Check if repository has already been indexed and force_reindex is False
        if indexer.get_stats().get("document_count", 0) > 0 and not request.force_reindex:
            return IndexingResponse(
                success=True,
                stats={
                    "status": "already_indexed",
                    "last_indexed": indexing_status.get("last_indexed"),
                    "document_count": indexer.get_stats().get("document_count", 0)
                }
            )
        
        # Start indexing in the background
        background_tasks.add_task(perform_indexing)
        
        return IndexingResponse(
            success=True,
            stats={"status": "started"}
        )
    
    except Exception as e:
        logger.error(f"Error starting indexing: {str(e)}")
        return IndexingResponse(
            success=False,
            stats={},
            error=f"Error starting indexing: {str(e)}"
        )


@router.get("/api/index/status", response_model=Dict[str, Any])
async def index_status() -> Dict[str, Any]:
    """
    Get indexing status
    
    Returns:
        Dict[str, Any]: Indexing status
    """
    status = {
        "in_progress": indexing_status["in_progress"],
        "last_indexed": indexing_status["last_indexed"],
        "document_count": indexer.get_stats().get("document_count", 0)
    }
    
    if indexing_status["stats"]:
        status["stats"] = indexing_status["stats"]
    
    if indexing_status["error"]:
        status["error"] = indexing_status["error"]
    
    return status


@router.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """
    Get service health
    
    Returns:
        HealthResponse: Health response
    """
    try:
        # Get vector store stats
        vector_store_stats = indexer.get_stats()
        
        # Get repository info
        repo_info = {
            "url": REPO_URL,
            "branch": REPO_BRANCH,
            "owner": repo_handler.owner,
            "name": repo_handler.repo_name,
            "indexed": vector_store_stats.get("document_count", 0) > 0,
            "indexing_in_progress": indexing_status["in_progress"]
        }
        
        return HealthResponse(
            status="ok",
            vector_store=vector_store_stats,
            repo_info=repo_info
        )
    
    except Exception as e:
        logger.error(f"Error checking health: {str(e)}")
        return HealthResponse(
            status="error",
            vector_store={"error": str(e)},
            repo_info={"url": REPO_URL, "branch": REPO_BRANCH}
        )
