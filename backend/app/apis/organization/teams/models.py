# app/apis/organization/teams/models.py
import logging
from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

logger = logging.getLogger(__name__)


class Team(Base):
    """Team model."""
    
    __tablename__ = "team"
    
    team_id = Column(BigInteger, primary_key=True, index=True)
    team_name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    updated_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    updater = relationship("ExistingUser", foreign_keys=[updated_by])
    
    def __repr__(self):
        return f"<Team(team_id={self.team_id}, name={self.team_name})>"