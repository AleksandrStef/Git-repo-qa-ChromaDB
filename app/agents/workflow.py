from typing import Dict, Any, List, TypedDict, Union
import time
from typing_extensions import TypedDict
from app.utils.logger import logger
from app.indexing.vector_store import RepositoryIndexer
from app.agents.llm import LLMHandler


class AgentState(TypedDict):
    """
    State for the agent workflow
    """
    query: str
    chat_history: List[Dict[str, str]]
    context: List[Dict[str, Any]]
    answer: str
    is_out_of_scope: bool
    processing_time: Dict[str, float]
    error: Union[str, None]
    out_of_scope_answer: Union[str, None]


class AgentWorkflow:
    """
    Simplified workflow for the agent team that doesn't use LangGraph
    """
    
    def __init__(self, indexer: RepositoryIndexer, llm_handler: LLMHandler):
        """
        Initialize the agent workflow
        
        Args:
            indexer (RepositoryIndexer): Repository indexer
            llm_handler (LLMHandler): LLM handler
        """
        self.indexer = indexer
        self.llm_handler = llm_handler
    
    def run(self, query: str, chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Run the workflow manually without using LangGraph
        
        Args:
            query (str): Query from the user
            chat_history (List[Dict[str, str]]): Chat history
            
        Returns:
            Dict[str, Any]: Results
        """
        start_time = time.time()
        logger.info(f"Running workflow for query: {query}")
        
        # Initialize state
        state = {
            "query": query,
            "chat_history": chat_history or [],
            "context": [],
            "answer": "",
            "is_out_of_scope": False,
            "processing_time": {},
            "error": None,
            "out_of_scope_answer": None
        }
        
        try:
            # Step 1: Check if query is in scope
            scope_check_start = time.time()
            is_out_of_scope = self.llm_handler.detect_out_of_scope(query)
            scope_check_time = time.time() - scope_check_start
            state["processing_time"]["scope_check"] = scope_check_time
            state["is_out_of_scope"] = is_out_of_scope
            
            logger.info(f"Query scope check completed in {scope_check_time:.4f} seconds. Out of scope: {is_out_of_scope}")
            
            # Step 2a: If in scope, retrieve context and generate answer
            if not is_out_of_scope:
                # Retrieve context
                context_start = time.time()
                context = self.indexer.search(query=query, k=5)
                context_time = time.time() - context_start
                state["processing_time"]["context_retrieval"] = context_time
                state["context"] = context
                
                logger.info(f"Context retrieval completed in {context_time:.4f} seconds. Found {len(context)} results")
                
                # Generate answer
                answer_start = time.time()
                answer = self.llm_handler.generate_answer(
                    query=query,
                    context=context,
                    chat_history=chat_history
                )
                answer_time = time.time() - answer_start
                state["processing_time"]["answer_generation"] = answer_time
                state["answer"] = answer
                
                logger.info(f"Answer generation completed in {answer_time:.4f} seconds")
            
            # Step 2b: If out of scope, generate out-of-scope response
            else:
                out_of_scope_start = time.time()
                out_of_scope_answer = self.llm_handler.generate_out_of_scope_response(query)
                out_of_scope_time = time.time() - out_of_scope_start
                state["processing_time"]["out_of_scope_handling"] = out_of_scope_time
                state["out_of_scope_answer"] = out_of_scope_answer
                
                logger.info(f"Out-of-scope handling completed in {out_of_scope_time:.4f} seconds")
            
            # Calculate total processing time
            total_time = time.time() - start_time
            state["processing_time"]["total"] = total_time
            
            logger.info(f"Workflow completed in {total_time:.4f} seconds")
            
            # Format result
            if state["is_out_of_scope"]:
                answer = state["out_of_scope_answer"]
            else:
                answer = state["answer"]
            
            result = {
                "query": query,
                "answer": answer,
                "is_out_of_scope": state["is_out_of_scope"],
                "processing_time": state["processing_time"],
                "error": state["error"],
            }
            
            # Add context if in scope
            if not state["is_out_of_scope"]:
                result["context"] = state["context"]
            
            return result
        
        except Exception as e:
            error_msg = f"Error running workflow: {str(e)}"
            logger.error(error_msg)
            
            return {
                "query": query,
                "answer": "I apologize, but I encountered an error while processing your query. Please try again later.",
                "is_out_of_scope": False,
                "processing_time": {"total": time.time() - start_time},
                "error": error_msg,
            }
