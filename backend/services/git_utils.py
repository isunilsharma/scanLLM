import git
import tempfile
import shutil
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class GitUtils:
    @staticmethod
    def clone_repo(repo_url: str, shallow: bool = True, depth: int = 1) -> Optional[Path]:
        """
        Clone a git repository to a temporary directory.
        Returns the path to the cloned repo or None on failure.
        """
        try:
            temp_dir = tempfile.mkdtemp(prefix="repo_scan_")
            temp_path = Path(temp_dir)
            
            logger.info(f"Cloning {repo_url} to {temp_path}")
            
            if shallow:
                git.Repo.clone_from(
                    repo_url,
                    temp_path,
                    depth=depth,
                    single_branch=True
                )
            else:
                git.Repo.clone_from(repo_url, temp_path)
            
            logger.info(f"Successfully cloned {repo_url}")
            return temp_path
        except Exception as e:
            logger.error(f"Failed to clone {repo_url}: {str(e)}")
            if temp_dir and Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None
    
    @staticmethod
    def cleanup_repo(repo_path: Path):
        """Remove cloned repository directory."""
        try:
            if repo_path and repo_path.exists():
                shutil.rmtree(repo_path, ignore_errors=True)
                logger.info(f"Cleaned up {repo_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup {repo_path}: {str(e)}")
