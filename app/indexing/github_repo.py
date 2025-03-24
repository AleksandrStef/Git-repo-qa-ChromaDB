import os
import time
import tempfile
from typing import Dict, List, Optional, Tuple
import git
from github import Github, Repository
from app.config import GITHUB_ACCESS_TOKEN, REPO_URL, REPO_BRANCH
from app.config import INDEXABLE_EXTENSIONS, EXCLUDE_PATTERNS
from app.utils.logger import logger

class GitHubRepoHandler:
    """
    Handler for cloning and indexing GitHub repositories
    """
    
    def __init__(self, repo_url: str = REPO_URL, branch: str = REPO_BRANCH):
        """
        Initialize the GitHub repository handler
        
        Args:
            repo_url (str): URL of the GitHub repository
            branch (str): Branch of the repository to clone
        """
        self.repo_url = repo_url
        self.branch = branch
        self.temp_dir = None
        self.repo_path = None
        self.github_client = Github(GITHUB_ACCESS_TOKEN) if GITHUB_ACCESS_TOKEN else Github()
        
        # Extract owner and repo name from URL
        parts = repo_url.rstrip('/').split('/')
        self.owner = parts[-2]
        self.repo_name = parts[-1]
        
        # Get GitHub repository object
        self.github_repo = self.github_client.get_repo(f"{self.owner}/{self.repo_name}")
        
    def clone_repo(self) -> str:
        """
        Clone the repository to a temporary directory
        
        Returns:
            str: Path to the cloned repository
        """
        start_time = time.time()
        logger.info(f"Cloning repository {self.repo_url} branch {self.branch}...")
        
        # Create a temporary directory for the repository
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        
        # Clone the repository
        git.Repo.clone_from(
            self.repo_url,
            self.repo_path,
            branch=self.branch,
            depth=1  # Shallow clone for faster download
        )
        
        logger.info(f"Repository cloned in {time.time() - start_time:.2f} seconds")
        return self.repo_path
    
    def get_file_content(self, file_path: str) -> Tuple[str, Optional[str]]:
        """
        Get the content of a file from the repository
        
        Args:
            file_path (str): Path to the file relative to the repository root
            
        Returns:
            Tuple[str, Optional[str]]: The content of the file and its GitHub URL
        """
        try:
            # Get file content from cloned repo
            with open(os.path.join(self.repo_path, file_path), 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Generate GitHub URL for the file
            github_url = f"{self.repo_url}/blob/{self.branch}/{file_path}"
            
            return content, github_url
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {str(e)}")
            return "", None
    
    def get_file_paths(self) -> List[str]:
        """
        Get a list of all file paths in the repository that should be indexed
        
        Returns:
            List[str]: List of file paths relative to the repository root
        """
        file_paths = []
        
        # Walk through the repository directory
        for root, dirs, files in os.walk(self.repo_path):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if not any(pattern in d for pattern in EXCLUDE_PATTERNS)]
            
            # Process files
            for file in files:
                # Check if file has an indexable extension
                if any(file.endswith(ext) for ext in INDEXABLE_EXTENSIONS):
                    file_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                    file_paths.append(file_path)
        
        logger.info(f"Found {len(file_paths)} indexable files")
        return file_paths
    
    def get_repo_files(self) -> Dict[str, Dict[str, str]]:
        """
        Get all indexable files from the repository
        
        Returns:
            Dict[str, Dict[str, str]]: Dictionary mapping file paths to dictionaries 
                                      containing content and GitHub URL
        """
        if not self.repo_path:
            self.clone_repo()
        
        files_dict = {}
        file_paths = self.get_file_paths()
        
        for file_path in file_paths:
            content, github_url = self.get_file_content(file_path)
            if content:
                files_dict[file_path] = {
                    "content": content,
                    "github_url": github_url
                }
        
        return files_dict
    
    def get_file_metadata(self, file_path: str) -> Dict[str, str]:
        """
        Get metadata for a file in the repository
        
        Args:
            file_path (str): Path to the file relative to the repository root
            
        Returns:
            Dict[str, str]: Dictionary containing metadata about the file
        """
        try:
            # Convert file path to GitHub path format
            github_path = file_path.replace('\\', '/')
            
            # Get file content from GitHub API
            file_content = self.github_repo.get_contents(github_path, ref=self.branch)
            
            # Get last commit for the file
            commits = list(self.github_repo.get_commits(path=github_path, sha=self.branch))
            last_commit = commits[0] if commits else None
            
            metadata = {
                "name": os.path.basename(file_path),
                "path": file_path,
                "github_url": f"{self.repo_url}/blob/{self.branch}/{github_path}",
                "raw_url": f"https://raw.githubusercontent.com/{self.owner}/{self.repo_name}/{self.branch}/{github_path}",
                "size": str(file_content.size) if hasattr(file_content, 'size') else "Unknown",
                "type": os.path.splitext(file_path)[1],
                "last_commit_date": last_commit.commit.author.date.isoformat() if last_commit else "Unknown",
                "last_commit_author": last_commit.commit.author.name if last_commit else "Unknown",
                "last_commit_message": last_commit.commit.message if last_commit else "Unknown",
            }
            
            return metadata
        except Exception as e:
            logger.error(f"Error getting metadata for {file_path}: {str(e)}")
            return {
                "name": os.path.basename(file_path),
                "path": file_path,
                "github_url": f"{self.repo_url}/blob/{self.branch}/{file_path.replace('\\', '/')}",
                "error": str(e)
            }
    
    def cleanup(self):
        """
        Clean up temporary directory
        """
        if self.temp_dir:
            self.temp_dir.cleanup()
            logger.info("Temporary repository directory cleaned up")
