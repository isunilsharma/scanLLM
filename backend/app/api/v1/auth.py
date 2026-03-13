"""
Auth wrapper for v1 API — re-exports existing GitHub OAuth routes.

The existing auth router is mounted at /api/auth. This module provides
a thin re-export so that v1-aware code can import from app.api.v1.auth.
"""
import sys
from pathlib import Path

_backend_dir = str(Path(__file__).parent.parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

# Re-export the existing auth router
from api.auth_github import router as auth_router  # noqa: F401

# Re-export the existing user helper
from api.github_endpoints import get_current_user  # noqa: F401

__all__ = ["auth_router", "get_current_user"]
