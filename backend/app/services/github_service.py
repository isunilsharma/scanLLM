"""
Consolidated GitHub service.

Wraps existing GitHub-related services into a single facade for the
restructured app layout.

Usage:
    from app.services.github_service import GitHubService
"""
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from services.github_api import GitHubAPI
from services.git_utils import GitUtils

try:
    from services.token_encryption import encrypt_token, decrypt_token
except BaseException:
    # cryptography may not be available in all environments
    def encrypt_token(token: str) -> str:  # type: ignore[misc]
        raise RuntimeError("cryptography package not available")

    def decrypt_token(encrypted: str) -> str:  # type: ignore[misc]
        raise RuntimeError("cryptography package not available")


class GitHubService:
    """High-level GitHub operations combining API access and git cloning."""

    def __init__(self, access_token: Optional[str] = None) -> None:
        self._api: Optional[GitHubAPI] = None
        if access_token:
            self._api = GitHubAPI(access_token)

    # ------------------------------------------------------------------
    # API wrappers
    # ------------------------------------------------------------------

    def get_user(self) -> Dict[str, Any]:
        """Fetch the authenticated GitHub user profile."""
        self._require_api()
        return self._api.get_user()  # type: ignore[union-attr]

    def list_repos(self, visibility: str = "all") -> List[Dict[str, Any]]:
        """List repositories for the authenticated user."""
        self._require_api()
        return self._api.get_repos(visibility=visibility)  # type: ignore[union-attr]

    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get details for a single repository."""
        self._require_api()
        return self._api.get_repo(owner, repo)  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # Git operations
    # ------------------------------------------------------------------

    @staticmethod
    def clone_repo(
        repo_url: str,
        shallow: bool = True,
        depth: int = 1,
    ) -> Optional[Path]:
        """Clone a repository to a temporary directory.

        Returns the local path or None on failure.
        """
        return GitUtils.clone_repo(repo_url, shallow=shallow, depth=depth)

    @staticmethod
    def clone_private_repo(
        repo_url: str,
        token: str,
        shallow: bool = True,
        depth: int = 1,
    ) -> Optional[Path]:
        """Clone a private repository using an access token."""
        # Inject token into the URL for authenticated clone
        authed_url = repo_url.replace(
            "https://github.com/",
            f"https://x-access-token:{token}@github.com/",
        )
        return GitUtils.clone_repo(authed_url, shallow=shallow, depth=depth)

    # ------------------------------------------------------------------
    # Token helpers
    # ------------------------------------------------------------------

    @staticmethod
    def encrypt_token(token: str) -> str:
        return encrypt_token(token)

    @staticmethod
    def decrypt_token(encrypted: str) -> str:
        return decrypt_token(encrypted)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _require_api(self) -> None:
        if self._api is None:
            raise ValueError(
                "GitHubService was created without an access_token. "
                "Provide one to use API methods."
            )
