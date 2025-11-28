"""Ownership mapping via GitHub API"""
import requests
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class OwnershipMapper:
    def __init__(self):
        self.cache = {}  # Simple cache to avoid duplicate API calls
        self.rate_limited = False
    
    def get_file_ownership(self, repo_url: str, file_path: str) -> Dict[str, Any]:
        """
        Get ownership info for a file from GitHub API (unauthenticated).
        Rate limit: 60 requests/hour
        """
        if self.rate_limited:
            return {}
        
        # Check cache
        cache_key = f"{repo_url}:{file_path}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            # Parse repo URL to extract owner/repo
            parts = repo_url.replace('https://github.com/', '').split('/')
            if len(parts) < 2:
                return {}
            
            owner, repo = parts[0], parts[1]
            
            # GitHub API endpoint for file commits
            url = f"https://api.github.com/repos/{owner}/{repo}/commits"
            params = {
                'path': file_path,
                'per_page': 1
            }
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 403:  # Rate limited
                logger.warning("GitHub API rate limited")
                self.rate_limited = True
                return {}
            
            if response.status_code != 200:
                return {}
            
            data = response.json()
            if not data or len(data) == 0:
                return {}
            
            commit = data[0]
            commit_date_str = commit.get('commit', {}).get('committer', {}).get('date')
            
            # Parse ISO date string to datetime object
            commit_date = None
            if commit_date_str:
                try:
                    commit_date = datetime.fromisoformat(commit_date_str.replace('Z', '+00:00'))
                except Exception:
                    logger.debug(f"Failed to parse date: {commit_date_str}")
            
            ownership = {
                'owner_name': commit.get('commit', {}).get('author', {}).get('name'),
                'owner_email': commit.get('commit', {}).get('author', {}).get('email'),
                'owner_committed_at': commit_date  # Now a datetime object
            }
            
            # Cache the result
            self.cache[cache_key] = ownership
            return ownership
            
        except Exception as e:
            logger.debug(f"Failed to get ownership for {file_path}: {str(e)}")
            return {}
