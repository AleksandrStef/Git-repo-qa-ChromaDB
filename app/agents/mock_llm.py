from typing import Dict, Any, List, Optional
import re
import time
import random

class MockLLM:
    """
    Mock implementation of an LLM for testing without Azure OpenAI API
    """
    
    def __init__(self):
        """
        Initialize the mock LLM
        """
        # Some canned responses for out-of-scope questions
        self.out_of_scope_responses = [
            "I apologize, but your question about '{query}' appears to be outside the scope of the Vanna.AI repository. I'm specifically designed to answer questions about Vanna.AI's code, functionality, and implementation. Would you like to ask something about Vanna.AI instead?",
            "Your question about '{query}' doesn't seem to be related to the Vanna.AI repository. I'm trained to provide information specifically about Vanna.AI, which is a tool focused on natural language to SQL generation. Feel free to ask me about that instead!",
            "I'm specialized in answering questions about the Vanna.AI repository, which focuses on natural language to SQL generation and database querying. Your question about '{query}' appears to be outside that scope. Is there something about Vanna.AI you'd like to know?"
        ]
    
    def generate_answer(self, query: str, context: List[Dict[str, Any]], chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generate a mock answer based on the context
        
        Args:
            query (str): Query from the user
            context (List[Dict[str, Any]]): Relevant documents from the vector store
            chat_history (Optional[List[Dict[str, str]]]): Chat history
            
        Returns:
            str: Generated answer
        """
        # Simulate thinking time
        time.sleep(0.5)
        
        # If no context is provided, return a generic response
        if not context:
            return f"Based on my knowledge of the Vanna.AI repository, I can tell you that Vanna is a tool for natural language to SQL generation. However, I don't have specific information related to your query about '{query}'. Could you try asking something more specific about Vanna's functionality, code structure, or implementation details?"
        
        # Extract content from all context documents
        all_content = "\n".join([doc.get("content", "") for doc in context])
        
        # Generate a response based on the content
        if "SQL" in query or "sql" in query:
            return f"Vanna.AI is designed to translate natural language queries into SQL. Based on the repository, Vanna provides a way to connect to databases and generate SQL queries from natural language inputs. The relevant code can be found in {context[0].get('source', 'the repository')}."
        
        if "install" in query.lower():
            return "You can install Vanna using pip: `pip install vanna`. After installation, you can import it in your Python code with `import vanna`. The repository also contains examples of how to initialize and use Vanna with different database backends."
        
        if "database" in query.lower() or "connect" in query.lower():
            return "Vanna.AI supports connecting to various database systems. You can connect to a database by creating a Vanna instance and providing the connection details. The repository shows examples for connecting to different database types including PostgreSQL, MySQL, and others."
        
        # Default response using content from the first context document
        source = context[0].get("source", "the Vanna.AI repository")
        github_url = context[0].get("github_url", "")
        content_sample = context[0].get("content", "")[:150] + "..."
        
        return f"Based on information from {source} ({github_url}), Vanna.AI provides functionality related to your query about '{query}'. The repository contains code such as:\n\n```\n{content_sample}\n```\n\nThis suggests that Vanna is a tool for natural language to SQL generation, helping users query databases using plain English."
    
    def detect_out_of_scope(self, query: str) -> bool:
        """
        Determine if a query is out of scope for the Vanna repository
        
        Args:
            query (str): Query from the user
            
        Returns:
            bool: True if the query is out of scope, False otherwise
        """
        # Simulate thinking time
        time.sleep(0.2)
        
        # List of keywords relevant to Vanna
        vanna_keywords = [
            "vanna", "sql", "database", "query", "natural language", "nl2sql", 
            "data", "analytics", "database", "postgres", "mysql", "sqlite",
            "embedding", "ai", "model", "train", "connection", "jupyter",
            "notebook", "python", "repository", "github", "code", "install"
        ]
        
        # List of obviously out-of-scope topics
        out_of_scope_keywords = [
            "capital of", "recipe", "weather", "stock", "price", "history",
            "war", "president", "king", "queen", "actor", "movie", "film",
            "song", "music", "artist", "game", "sports", "team", "player",
            "birthday", "age", "height", "weight", "married", "spouse",
            "children", "died", "born", "capital", "population", "area"
        ]
        
        # Check if the query contains any out-of-scope keywords
        for keyword in out_of_scope_keywords:
            if keyword.lower() in query.lower():
                return True
                
        # Check if the query contains any Vanna keywords
        for keyword in vanna_keywords:
            if keyword.lower() in query.lower():
                return False
        
        # If no clear indicators, return a probabilistic result (30% chance of being out of scope)
        return random.random() < 0.3
    
    def generate_out_of_scope_response(self, query: str) -> str:
        """
        Generate a response for an out-of-scope query
        
        Args:
            query (str): Out-of-scope query from the user
            
        Returns:
            str: Generated response
        """
        # Simulate thinking time
        time.sleep(0.3)
        
        # Choose a random response and format it with the query
        response = random.choice(self.out_of_scope_responses)
        return response.format(query=query)
