#!/usr/bin/env python
"""
Test script for the Vanna AI Repository Q&A system.
This script indexes the repository and then runs a few test questions.
"""

import time
import argparse
import requests
import json
import sys
from typing import Dict, Any, List

# Default API URL
DEFAULT_API_URL = "http://localhost:8000"

# Test questions (in-scope and out-of-scope)
TEST_QUESTIONS = [
    # In-scope questions
    "What is Vanna AI and what does it do?",
    "How does Vanna convert natural language to SQL?",
    "What are the main components of the Vanna architecture?",
    "How can I install and use Vanna?",
    
    # Out-of-scope questions
    "What is the capital of France?",
    "Tell me about quantum computing",
    "How does blockchain work?",
    "What's the recipe for chocolate cake?"
]

def check_server_running(api_url: str) -> bool:
    """
    Check if the server is running
    
    Args:
        api_url (str): API URL
        
    Returns:
        bool: Whether the server is running
    """
    try:
        response = requests.get(f"{api_url}")
        return response.status_code == 200
    except Exception:
        return False

def index_repository(api_url: str, force: bool = False) -> Dict[str, Any]:
    """
    Index the repository
    
    Args:
        api_url (str): API URL
        force (bool): Whether to force reindexing
        
    Returns:
        Dict[str, Any]: Response JSON
    """
    print(f"{'Force re-indexing' if force else 'Indexing'} repository...")
    
    try:
        response = requests.post(
            f"{api_url}/api/index",
            json={"force_reindex": force}
        )
        
        return response.json()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the application is running.")
        sys.exit(1)


def wait_for_indexing_completion(api_url: str, timeout: int = 600) -> bool:
    """
    Wait for indexing to complete
    
    Args:
        api_url (str): API URL
        timeout (int): Timeout in seconds
        
    Returns:
        bool: Whether indexing completed successfully
    """
    print("Waiting for indexing to complete...")
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"{api_url}/api/index/status")
            status = response.json()
            
            if status.get("in_progress", True) == False:
                if status.get("document_count", 0) > 0:
                    print(f"Indexing completed in {time.time() - start_time:.2f} seconds")
                    print(f"Indexed {status.get('document_count', 0)} documents")
                    return True
                else:
                    print("Indexing failed")
                    return False
            
            print("Indexing in progress, waiting...")
            time.sleep(10)
        except requests.exceptions.ConnectionError:
            print("Error: Lost connection to the server.")
            return False
    
    print(f"Indexing timed out after {timeout} seconds")
    return False


def query_repository(api_url: str, query: str) -> Dict[str, Any]:
    """
    Query the repository
    
    Args:
        api_url (str): API URL
        query (str): Query string
        
    Returns:
        Dict[str, Any]: Response JSON
    """
    print(f"Querying: {query}")
    
    try:
        response = requests.post(
            f"{api_url}/api/query",
            json={"query": query}
        )
        
        return response.json()
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the application is running.")
        return {
            "query": query,
            "answer": "Error: Could not connect to the server.",
            "is_out_of_scope": False,
            "processing_time": {},
            "error": "Connection error"
        }


def run_tests(api_url: str, questions: List[str] = None) -> None:
    """
    Run tests
    
    Args:
        api_url (str): API URL
        questions (List[str]): Questions to test
    """
    if questions is None:
        questions = TEST_QUESTIONS
    
    results = []
    
    for i, question in enumerate(questions):
        print(f"\nTest {i+1}/{len(questions)}: {question}")
        
        start_time = time.time()
        response = query_repository(api_url, question)
        total_time = time.time() - start_time
        
        if "error" in response and response["error"]:
            print(f"Error: {response['error']}")
            continue
            
        print(f"Response: {response.get('answer')}")
        print(f"Is out of scope: {response.get('is_out_of_scope')}")
        print(f"Total response time: {total_time:.2f} seconds")
        
        if "processing_time" in response:
            print(f"Processing times: {json.dumps(response.get('processing_time', {}), indent=2)}")
        
        results.append({
            "question": question,
            "answer": response.get("answer"),
            "is_out_of_scope": response.get("is_out_of_scope"),
            "total_time": total_time,
            "processing_time": response.get("processing_time", {})
        })
    
    if not results:
        print("\nNo successful test results to summarize.")
        return
        
    # Print summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)
    
    total_time = sum(result["total_time"] for result in results)
    avg_time = total_time / len(results)
    in_scope = sum(1 for result in results if not result["is_out_of_scope"])
    out_of_scope = sum(1 for result in results if result["is_out_of_scope"])
    
    print(f"Total questions: {len(results)}")
    print(f"In-scope questions: {in_scope}")
    print(f"Out-of-scope questions: {out_of_scope}")
    print(f"Average response time: {avg_time:.2f} seconds")
    print(f"Total test time: {total_time:.2f} seconds")


def main():
    """
    Main function
    """
    parser = argparse.ArgumentParser(description="Test the Vanna AI Repository Q&A system")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="API URL")
    parser.add_argument("--force-index", action="store_true", help="Force reindexing of the repository")
    parser.add_argument("--skip-index", action="store_true", help="Skip indexing and go straight to querying")
    parser.add_argument("--questions", type=str, nargs="+", help="Questions to test")
    
    args = parser.parse_args()
    
    # Check if server is running
    if not check_server_running(args.api_url):
        print("Error: Server is not running. Please start the server with 'python -m app.main' before running tests.")
        print("Command: python -m app.main")
        return
    
    # Check API health
    try:
        health_response = requests.get(f"{args.api_url}/api/health")
        health_data = health_response.json()
        print(f"API health: {health_data.get('status')}")
        
        is_indexed = health_data.get("vector_store", {}).get("document_count", 0) > 0
        print(f"Repository indexed: {is_indexed}")
    except Exception as e:
        print(f"Error checking API health: {str(e)}")
        return
    
    # Index repository if needed
    if not args.skip_index:
        if not is_indexed or args.force_index:
            index_response = index_repository(args.api_url, args.force_index)
            print(f"Indexing response: {json.dumps(index_response, indent=2)}")
            
            if index_response.get("success", False):
                wait_for_indexing_completion(args.api_url)
        else:
            print("Repository already indexed, skipping indexing")
    
    # Run tests
    run_tests(args.api_url, args.questions)


if __name__ == "__main__":
    main()
