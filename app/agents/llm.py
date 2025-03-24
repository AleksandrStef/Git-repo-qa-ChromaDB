from typing import Dict, Any, Optional, List
from app.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_DEPLOYMENT_NAME,
    AZURE_OPENAI_API_VERSION,
    COMPLETION_MODEL
)
from app.agents.mock_llm import MockLLM
from app.utils.logger import logger

class LLMHandler:
    """
    Handler for LLM operations
    """
    
    def __init__(
        self,
        model_name: str = COMPLETION_MODEL,
        deployment_name: str = AZURE_OPENAI_DEPLOYMENT_NAME,
        temperature: float = 0.0,
        max_tokens: int = 2000,
        use_mock: bool = False  # Changed default to use real LLM
    ):
        """
        Initialize the LLM handler
        
        Args:
            model_name (str): Name of the model
            deployment_name (str): Name of the Azure OpenAI deployment
            temperature (float): Temperature for generation
            max_tokens (int): Maximum number of tokens to generate
            use_mock (bool): Whether to use mock LLM implementation
        """
        self.model_name = model_name
        self.deployment_name = deployment_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.use_mock = use_mock
        
        # Initialize LLM - either mock or real
        if self.use_mock:
            self.llm = MockLLM()
            logger.info("Using mock LLM for testing")
        else:
            try:
                from langchain_openai import AzureChatOpenAI
                self.llm = AzureChatOpenAI(
                    azure_deployment=deployment_name,
                    openai_api_version=AZURE_OPENAI_API_VERSION,
                    azure_endpoint=AZURE_OPENAI_ENDPOINT,
                    api_key=AZURE_OPENAI_API_KEY,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                logger.info("Using Azure OpenAI LLM")
            except Exception as e:
                logger.error(f"Error initializing Azure OpenAI LLM: {str(e)}")
                logger.info("Falling back to mock LLM")
                self.llm = MockLLM()
    
    def generate_answer(
        self,
        query: str,
        context: List[Dict[str, Any]],
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate an answer to a query using the LLM
        
        Args:
            query (str): Query from the user
            context (List[Dict[str, Any]]): Relevant documents from the vector store
            chat_history (Optional[List[Dict[str, str]]]): Chat history
            
        Returns:
            str: Generated answer
        """
        if self.use_mock or isinstance(self.llm, MockLLM):
            return self.llm.generate_answer(query, context, chat_history)
        
        # If using the real LLM, use the original implementation
        try:
            # Format context
            formatted_context = ""
            for i, doc in enumerate(context):
                source = doc.get("source", "Unknown")
                github_url = doc.get("github_url", "Unknown")
                content = doc.get("content", "")
                
                formatted_context += f"Document {i+1}:\n"
                formatted_context += f"Source: {source}\n"
                formatted_context += f"GitHub URL: {github_url}\n"
                formatted_context += f"Content:\n{content}\n\n"
            
            # Create prompt
            system_prompt = """You are an AI assistant specialized in answering questions about the Vanna.AI GitHub repository (https://github.com/vanna-ai/vanna).
Your task is to provide accurate, helpful responses based on the repository content provided to you.

Follow these guidelines:
1. Base your answers ONLY on the provided repository content context.
2. If the provided context is insufficient to answer the question, say so. Don't make up information.
3. If the question is clearly unrelated to the Vanna.AI repository, politely indicate that it's out of scope.
4. Include relevant GitHub file links when referencing specific code or documentation.
5. Explain technical concepts clearly, assuming the user has some technical knowledge but may not be familiar with all aspects of the repository.

For code references, include the GitHub URL of the file and specific line numbers when possible.
"""
            
            # Use the LangChain interface with the AzureChatOpenAI model
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Context information is below:\n\n{formatted_context}"},
                {"role": "user", "content": f"Given the context information and not prior knowledge, answer the question: {query}"},
            ]
            
            # Add chat history if available
            if chat_history:
                # Insert chat history before the final user message
                for message in chat_history:
                    # Ensure each message has 'role' and 'content' keys
                    if isinstance(message, dict) and 'role' in message and 'content' in message:
                        messages.insert(-1, message)
                    elif isinstance(message, dict) and len(message) > 0:
                        # Try to convert to role/content format
                        logger.warning(f"Chat history message has incorrect format: {message}")
                        # Create a default message if possible
                        if 'user' in message or 'query' in message or 'question' in message:
                            content = next((message[k] for k in ['user', 'query', 'question'] if k in message), "")
                            if content:
                                messages.insert(-1, {"role": "user", "content": content})
                        elif 'assistant' in message or 'response' in message or 'answer' in message:
                            content = next((message[k] for k in ['assistant', 'response', 'answer'] if k in message), "")
                            if content:
                                messages.insert(-1, {"role": "assistant", "content": content})
            
            # Generate response
            response = self.llm.invoke(messages)
            
            return response.content
        
        except Exception as e:
            logger.error(f"Error generating answer: {str(e)}")
            # Return a simple response if there's an error
            return f"I encountered an error while processing your query about '{query}'. This might be due to an issue with the language model connection. Please try again later or rephrase your question."
    
    def detect_out_of_scope(self, query: str) -> bool:
        """
        Detect if a query is out of scope for the Vanna repository
        
        Args:
            query (str): Query from the user
            
        Returns:
            bool: True if the query is out of scope, False otherwise
        """
        if self.use_mock or isinstance(self.llm, MockLLM):
            return self.llm.detect_out_of_scope(query)
        
        system_prompt = """You are an AI evaluator. Your task is to determine if a given query is related to the Vanna.AI GitHub repository (https://github.com/vanna-ai/vanna).

Vanna.AI is a project focused on:
- Natural language to SQL generation
- Database querying using natural language
- SQL-related machine learning models
- Data visualization
- Python-based data analysis tools

Classification Instructions:
- If the query is related to Vanna.AI, its functionality, code, usage, or implementation, respond with "IN_SCOPE".
- If the query is completely unrelated to Vanna.AI or software development in general, respond with "OUT_OF_SCOPE".
- If the query is about general programming, databases, SQL, or related topics that might be addressed using knowledge from the repository, respond with "IN_SCOPE".
- Be inclusive in your classification - if there's any reasonable connection to Vanna.AI or its domain, classify as "IN_SCOPE".

Your response must be ONLY "IN_SCOPE" or "OUT_OF_SCOPE" with no additional text.
"""
        
        # Use the LangChain interface
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}"}
        ]
        
        try:
            # Generate response
            response = self.llm.invoke(messages)
            # Check if the response contains "OUT_OF_SCOPE"
            return "OUT_OF_SCOPE" in response.content.strip().upper()
        except Exception as e:
            logger.error(f"Error detecting out of scope: {str(e)}")
            # Default to in-scope if there's an error
            return False
    
    def generate_out_of_scope_response(self, query: str) -> str:
        """
        Generate a response for an out-of-scope query
        
        Args:
            query (str): Out-of-scope query from the user
            
        Returns:
            str: Generated response
        """
        if self.use_mock or isinstance(self.llm, MockLLM):
            return self.llm.generate_out_of_scope_response(query)
        
        system_prompt = """You are an AI assistant specialized in answering questions about the Vanna.AI GitHub repository.
You've determined that the user's query is unrelated to the Vanna.AI repository.

Respond politely, explaining that:
1. Their question appears to be outside the scope of the Vanna.AI repository
2. You're specifically designed to answer questions about Vanna.AI's code, functionality, and implementation
3. Suggest that they rephrase their question to relate to Vanna.AI, or ask a different question about Vanna.AI

Be concise, friendly, and helpful in your response.
"""
        
        # Use the LangChain interface
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Out-of-scope query: {query}"}
        ]
        
        try:
            # Generate response
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Error generating out of scope response: {str(e)}")
            # Return a simple response if there's an error
            return "I apologize, but your question appears to be outside the scope of the Vanna.AI repository. I'm specifically designed to answer questions about Vanna.AI's code, functionality, and implementation."
