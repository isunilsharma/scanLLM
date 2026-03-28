"""
Re-export existing models for convenience.

Usage:
    from app.models import ScanJob, ScanStatus, Finding
"""
import sys
from pathlib import Path

# Ensure the backend root is on sys.path so existing model imports work
_backend_dir = str(Path(__file__).parent.parent.parent)
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

from models.scan import ScanJob, ScanStatus  # noqa: F401, E402
from models.finding import Finding  # noqa: F401, E402

# Optional re-exports — these may not exist in every deployment
try:
    from models.github_user import GitHubUser  # noqa: F401
except ImportError:
    pass

try:
    from models.github_token import GitHubToken  # noqa: F401
except ImportError:
    pass

try:
    from models.demo_scan_cache import DemoScanCache  # noqa: F401
except ImportError:
    pass

try:
    from models.oauth_state import OAuthState  # noqa: F401
except ImportError:
    pass

try:
    from app.models.audit_log import AuditLog, AuditAction, AuditResourceType  # noqa: F401
except ImportError:
    pass

__all__ = [
    "ScanJob",
    "ScanStatus",
    "Finding",
    "GitHubUser",
    "GitHubToken",
    "DemoScanCache",
    "OAuthState",
    "AuditLog",
    "AuditAction",
    "AuditResourceType",
]
