import logging
from sqlalchemy import Column, BigInteger, SmallInteger, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database.base import Base

logger = logging.getLogger(__name__)


class TeamHierarchy(Base):
    """Team Hierarchy model representing parent-child team relationships."""
    
    __tablename__ = "team_hierarchy"
    
    id = Column(BigInteger, primary_key=True, index=True)
    parent_team_id = Column(BigInteger, ForeignKey('team.team_id'), index=True)
    child_team_id = Column(BigInteger, ForeignKey('team.team_id'), nullable=False, index=True)
    depth_level = Column(SmallInteger, nullable=False, default=0)
    updated_by = Column(BigInteger, ForeignKey('users.user_id'), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    parent_team = relationship(
        "Team", 
        foreign_keys=[parent_team_id],
        backref="child_hierarchies"
    )
    child_team = relationship(
        "Team", 
        foreign_keys=[child_team_id],
        backref="parent_hierarchies"
    )
    updater = relationship(
        "ExistingUser", 
        foreign_keys=[updated_by]
    )
    
    def __repr__(self):
        return f"<TeamHierarchy(id={self.id}, parent={self.parent_team_id}, child={self.child_team_id}, depth={self.depth_level})>"