# Vanna AI Repository Q&A System

A LangChain and LangGraph-based AI agent system for answering questions about the Vanna AI GitHub repository.

## Features

- **Repository Indexing**: Automatically clones and indexes the [Vanna AI GitHub repository](https://github.com/vanna-ai/vanna) using ChromaDB as a vector store.
- **Question Answering**: Uses Azure OpenAI to answer questions based on the indexed content.
- **Out-of-Scope Detection**: Detects and responds appropriately to questions that are unrelated to the repository.
- **REST API**: Provides an API for querying the system and managing the indexing process.
- **Performance Metrics**: Reports on the speed of indexing and querying operations.
- **File Links**: Provides GitHub links to relevant files and code used during answer generation.

## Architecture

This system uses a combination of LangChain, LangGraph, and Azure OpenAI to create an intelligent Q&A system:

1. **Data Indexing Layer**: Uses the GitHub API to clone and process repository files, which are then split and indexed in a ChromaDB vector store using Azure OpenAI embeddings.
2. **Agent Workflow**: Implements a LangGraph-based workflow that:
   - Detects if a query is in scope or not
   - Retrieves relevant context for in-scope queries
   - Generates appropriate answers using Azure OpenAI
3. **API Layer**: FastAPI-based REST API for interacting with the system

## Requirements

- Python 3.10+
- Azure OpenAI API access
- GitHub Access Token (optional, but recommended for higher rate limits)
- Docker (for containerized deployment)

## Setup and Installation

### Environment Variables

Create a `.env` file based on the provided `.env.example`:

```
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_DEPLOYMENT_NAME=your_azure_openai_deployment_name
AZURE_OPENAI_API_VERSION=2023-05-15

# GitHub Configuration
GITHUB_ACCESS_TOKEN=your_github_access_token

# Vector Database Configuration
CHROMA_PERSIST_DIRECTORY=data/chroma

# Repository Configuration
REPO_URL=https://github.com/vanna-ai/vanna
REPO_BRANCH=main
```

### Local Development

1. Clone this repository:
   ```bash
   git clone https://github.com/AleksandrStef/Git-repo-qa-ChromaDB.git
   cd Git-repo-qa-ChromaDB
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python -m app.main
   ```

4. Access the API at http://localhost:8000 and the Swagger documentation at http://localhost:8000/docs

### Docker Deployment

1. Build and start the Docker container:
   ```bash
   docker-compose up -d
   ```

2. Access the API at http://localhost:8000

## API Usage

### Index the Repository

Before you can ask questions, you need to index the repository:

```bash
curl -X POST http://localhost:8000/api/index -H "Content-Type: application/json" -d '{}'
```

### Check Indexing Status

```bash
curl http://localhost:8000/api/index/status
```

### Ask a Question

```bash
curl -X POST http://localhost:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does Vanna AI convert natural language to SQL?"}'
```

### Check API Health

```bash
curl http://localhost:8000/api/health
```

## Vector Database Choice

This project uses **ChromaDB** as the vector database for the following reasons:

1. **Ease of Integration**: ChromaDB integrates well with LangChain, simplifying development.
2. **Embedded Database**: It can run in-process without requiring a separate service, making deployment simpler.
3. **Performance**: ChromaDB offers good performance for this scale of application.
4. **Document Metadata**: It has strong support for document metadata, which is important for tracking file sources and GitHub URLs.

For embeddings, we use Azure OpenAI's **text-embedding-3-small** model, which provides fast embeddings with good semantic understanding.

## Performance

The system's performance depends on several factors:

- **Indexing**: First-time indexing typically takes 3-5 minutes for the entire Vanna AI repository.
- **Query Latency**: Typical query response time is 1-3 seconds, including:
  - Scope detection: ~0.5 seconds
  - Context retrieval: ~0.1-0.3 seconds
  - Answer generation: ~0.5-2 seconds depending on query complexity

Detailed performance metrics are included in each query response.

## Accuracy Improvement Techniques

The system implements several techniques to improve the accuracy of responses:

1. **Chunking Strategy**: Document text is split with overlapping chunks to preserve context boundaries.
2. **Metadata Enrichment**: Each document chunk is enriched with metadata including file path, GitHub URL, and file type.
3. **Two-stage Response**: A dedicated LLM step first determines if questions are in scope before answering.
4. **Context Relevance**: The retrieval system provides the most semantically relevant context for each query.
5. **Prompt Engineering**: Carefully crafted prompts guide the LLM to provide accurate, repository-specific answers.

## Evaluation

The system has been tested with both in-scope questions about the Vanna AI repository and out-of-scope questions. Sample questions for evaluation:

### In-Scope Questions
- "What is Vanna AI's main purpose?"
- "How does Vanna convert natural language to SQL?"
- "Explain how Vanna handles database connections"
- "What machine learning models does Vanna use?"

### Out-of-Scope Questions
- "What is the capital of France?"
- "How does cryptocurrency mining work?"
- "Write me a recipe for chocolate cake"
- "What are the latest trends in fashion?"

