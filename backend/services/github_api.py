import requests
import logging
import base64
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class GitHubAPI:
    BASE_URL = "https://api.github.com"
    
    def __init__(self, access_token: str):
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Accept': 'application/vnd.github+json',
            'X-GitHub-Api-Version': '2022-11-28'
        }
    
    def get_user(self) -> Dict[str, Any]:
        response = requests.get(f"{self.BASE_URL}/user", headers=self.headers, timeout=10)
        response.raise_for_status()
        return response.json()
    
    def get_repos(self, visibility: str = 'all') -> List[Dict[str, Any]]:
        repos = []
        page = 1
        while True:
            response = requests.get(
                f"{self.BASE_URL}/user/repos",
                headers=self.headers,
                params={'visibility': visibility, 'per_page': 100, 'page': page, 'sort': 'updated'},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                break
            repos.extend(data)
            if len(data) < 100 or page >= 10:
                break
            page += 1
        return repos
    
    def get_file_tree(self, owner: str, repo: str, branch: str = 'main') -> List[Dict]:
        try:
            response = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/{branch}?recursive=1",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('tree', [])
        except requests.RequestException as e:
            logger.debug(f"Tree fetch failed for {branch}, trying master: {e}")
            response = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/git/trees/master?recursive=1",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json().get('tree', [])

    def get_file_content(self, owner: str, repo: str, path: str, ref: str = 'main') -> Optional[str]:
        try:
            response = requests.get(
                f"{self.BASE_URL}/repos/{owner}/{repo}/contents/{path}",
                headers=self.headers,
                params={'ref': ref},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            if 'content' in data:
                return base64.b64decode(data['content']).decode('utf-8', errors='ignore')
        except requests.RequestException as e:
            logger.debug(f"Failed to fetch {path}: {e}")
        return None
