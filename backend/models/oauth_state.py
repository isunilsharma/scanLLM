from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from datetime import datetime, timedelta, timezone
from core.database import Base

class OAuthState(Base):
    __tablename__ = "oauth_states"
    
    state = Column(String, primary_key=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    @staticmethod
    def is_valid(state: str, db):
        """Check if state is valid and not expired"""
        obj = db.query(OAuthState).filter(OAuthState.state == state).first()
        if not obj:
            return False
        if obj.expires_at < datetime.now(timezone.utc):
            db.delete(obj)
            db.commit()
            return False
        # Delete after use
        db.delete(obj)
        db.commit()
        return True
