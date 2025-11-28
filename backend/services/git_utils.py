import subprocess
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
        Clone a git repository to a temporary directory using subprocess.
        This works even if git binary is not in standard PATH.
        Returns the path to the cloned repo or None on failure.
        """
        try:
            temp_dir = tempfile.mkdtemp(prefix="repo_scan_")
            temp_path = Path(temp_dir)
            
            logger.info(f"Cloning {repo_url} to {temp_path}")
            
            # Build git clone command
            cmd = ["git", "clone"]
            if shallow:
                cmd.extend(["--depth", str(depth), "--single-branch"])
            cmd.extend([repo_url, str(temp_path)])
            
            # Execute git clone via subprocess
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Git clone failed: {result.stderr}")
                raise Exception(f"Git clone failed: {result.stderr}")
            
            logger.info(f"Successfully cloned {repo_url}")
            return temp_path
            
        except FileNotFoundError:
            # Git executable not found
            logger.error("Git executable not found in PATH. Using fallback method...")
            return GitUtils._clone_repo_fallback(repo_url, temp_dir if 'temp_dir' in locals() else None)
        except Exception as e:
            logger.error(f"Failed to clone {repo_url}: {str(e)}")
            if 'temp_dir' in locals() and Path(temp_dir).exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            return None
    
    @staticmethod
    def _clone_repo_fallback(repo_url: str, temp_dir: Optional[str] = None) -> Optional[Path]:
        """
        Fallback method when git binary is not available.
        Downloads repo as ZIP from GitHub.
        """
        try:
            import requests
            import zipfile
            import io
            
            if not temp_dir:
                temp_dir = tempfile.mkdtemp(prefix="repo_scan_")
            temp_path = Path(temp_dir)
            
            logger.info(f"Using fallback ZIP download for {repo_url}")
            
            # Convert GitHub URL to ZIP download URL
            # https://github.com/owner/repo -> https://github.com/owner/repo/archive/refs/heads/main.zip
            if 'github.com' in repo_url:
                zip_url = repo_url.rstrip('/') + '/archive/refs/heads/main.zip'
                
                # Download ZIP
                response = requests.get(zip_url, timeout=30)
                if response.status_code != 200:
                    # Try master branch
                    zip_url = repo_url.rstrip('/') + '/archive/refs/heads/master.zip'
                    response = requests.get(zip_url, timeout=30)
                
                if response.status_code != 200:
                    raise Exception(f"Failed to download repository ZIP: HTTP {response.status_code}")
                
                # Extract ZIP
                with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
                    # GitHub ZIPs contain a root folder, extract into temp_dir
                    zip_file.extractall(temp_path)
                
                # Find the extracted directory (GitHub adds repo-branch name)
                extracted_dirs = [d for d in temp_path.iterdir() if d.is_dir()]
                if extracted_dirs:
                    # Move contents up one level
                    extracted_dir = extracted_dirs[0]
                    for item in extracted_dir.iterdir():
                        shutil.move(str(item), temp_path / item.name)
                    extracted_dir.rmdir()
                
                logger.info(f"Successfully downloaded and extracted {repo_url}")
                return temp_path
            else:
                raise Exception("Only GitHub repositories supported in fallback mode")
                
        except Exception as e:
            logger.error(f"Fallback clone failed: {str(e)}")
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
