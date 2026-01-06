# import logging
# from typing import Optional, List, Dict, Any
# from sqlalchemy.orm import Session, aliased
# from sqlalchemy import func, and_, or_
# from .models import EmployeeHierarchy

# logger = logging.getLogger(__name__)


# class EmployeeHierarchyRepository:
#     """Repository for Employee Hierarchy database operations."""
    
#     def __init__(self, db: Session):
#         self.db = db
    
#     def get_by_user_id(self, user_id: int) -> Optional[EmployeeHierarchy]:
#         """Get FIRST hierarchy entry by user ID."""
#         try:
#             return self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.user_id == user_id
#             ).first()
#         except Exception as e:
#             logger.error(f"Error fetching hierarchy for user {user_id}: {str(e)}")
#             raise
    
#     def get_all_by_user_id(self, user_id: int) -> List[EmployeeHierarchy]:
#         """Get ALL hierarchy entries for a user (multiple entries possible)."""
#         try:
#             entries = self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.user_id == user_id
#             ).order_by(EmployeeHierarchy.depth).all()
#             return entries
#         except Exception as e:
#             logger.error(f"Error fetching all hierarchy for user {user_id}: {str(e)}")
#             raise
    
#     def get_reporting_chain_entries(self, user_id: int) -> List[EmployeeHierarchy]:
#         """Get all hierarchy entries in the reporting chain for a user."""
#         try:
#             # Get the starting entry
#             start_entry = self.get_by_user_id(user_id)
#             if not start_entry:
#                 return []
            
#             # Collect all entries in the chain using loop
#             chain = [start_entry]
#             current_user_id = start_entry.reporting_to_id
            
#             while current_user_id:
#                 next_entry = self.get_by_user_id(current_user_id)
#                 if not next_entry:
#                     break
#                 chain.append(next_entry)
#                 current_user_id = next_entry.reporting_to_id
            
#             return chain
#         except Exception as e:
#             logger.error(f"Error fetching reporting chain for user {user_id}: {str(e)}")
#             raise
    
#     def create_entry(self, user_id: int, reporting_to_id: Optional[int], depth: int, updated_by: int) -> EmployeeHierarchy:
#         """Create a single hierarchy entry."""
#         try:
#             # Check if same entry already exists
#             existing = self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.user_id == user_id,
#                 EmployeeHierarchy.reporting_to_id == reporting_to_id,
#                 EmployeeHierarchy.depth == depth
#             ).first()
            
#             if existing:
#                 return existing
            
#             entry = EmployeeHierarchy(
#                 user_id=user_id,
#                 reporting_to_id=reporting_to_id,
#                 depth=depth,
#                 updated_by=updated_by
#             )
            
#             self.db.add(entry)
#             self.db.commit()
#             self.db.refresh(entry)
            
#             logger.info(f"Created hierarchy entry: user {user_id} reports to {reporting_to_id} at depth {depth}")
#             return entry
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Error creating hierarchy entry: {str(e)}")
#             raise
    
#     def create_complete_reporting_chain(self, user_id: int, first_reporting_to_id: Optional[int], updated_by: int) -> List[EmployeeHierarchy]:
#         """
#         Create complete reporting chain for a new user.
        
#         Example: If user1 reports to user2, and user2 reports to user3,
#         this will create entries for:
#         - user1 reports to user2 (depth 1)
#         - user1 reports to user3 (depth 2)
#         - user1 reports to user4 (depth 3) ... up to the top
#         """
#         try:
#             entries_created = []
            
#             if first_reporting_to_id:
#                 # Step 1: Get the reporting chain of the first manager
#                 manager_chain = self.get_reporting_chain_entries(first_reporting_to_id)
                
#                 if not manager_chain:
#                     raise ValueError(f"Manager {first_reporting_to_id} not found in hierarchy")
                
#                 # Step 2: Create entry for direct report (depth 1)
#                 direct_entry = self.create_entry(
#                     user_id=user_id,
#                     reporting_to_id=first_reporting_to_id,
#                     depth=1,
#                     updated_by=updated_by
#                 )
#                 entries_created.append(direct_entry)
                
#                 # Step 3: Create entries for all managers in the chain (indirect reports)
#                 for i, manager_entry in enumerate(manager_chain, start=2):
#                     indirect_entry = self.create_entry(
#                         user_id=user_id,
#                         reporting_to_id=manager_entry.user_id,
#                         depth=i,
#                         updated_by=updated_by
#                     )
#                     entries_created.append(indirect_entry)
#             else:
#                 # User has no manager (top-level)
#                 top_entry = self.create_entry(
#                     user_id=user_id,
#                     reporting_to_id=None,
#                     depth=0,
#                     updated_by=updated_by
#                 )
#                 entries_created.append(top_entry)
            
#             self.db.commit()
#             logger.info(f"Created {len(entries_created)} hierarchy entries for user {user_id}")
#             return entries_created
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Error creating complete reporting chain: {str(e)}")
#             raise
    
#     def delete_by_user_id(self, user_id: int) -> bool:
#         """Delete ALL hierarchy entries for a user."""
#         try:
#             entries = self.get_all_by_user_id(user_id)
#             if not entries:
#                 return False
            
#             for entry in entries:
#                 self.db.delete(entry)
            
#             self.db.commit()
#             logger.info(f"Deleted {len(entries)} hierarchy entries for user {user_id}")
#             return True
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Error deleting hierarchy entries for user {user_id}: {str(e)}")
#             raise
    
#     def get_all(self, skip: int = 0, limit: int = 100) -> List[EmployeeHierarchy]:
#         """Get all hierarchy entries with pagination."""
#         try:
#             entries = self.db.query(EmployeeHierarchy).order_by(
#                 EmployeeHierarchy.user_id,
#                 EmployeeHierarchy.depth
#             ).offset(skip).limit(limit).all()
#             return entries
#         except Exception as e:
#             logger.error(f"Error fetching all hierarchy entries: {str(e)}")
#             raise
    
#     def get_count(self) -> int:
#         """Get total hierarchy entry count."""
#         try:
#             count = self.db.query(func.count(EmployeeHierarchy.id)).scalar()
#             return count
#         except Exception as e:
#             logger.error(f"Error getting hierarchy count: {str(e)}")
#             raise
    
#     def get_users_by_manager(self, manager_id: int) -> List[EmployeeHierarchy]:
#         """Get all users who report to a specific manager."""
#         try:
#             entries = self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.reporting_to_id == manager_id
#             ).all()
#             return entries
#         except Exception as e:
#             logger.error(f"Error fetching users by manager {manager_id}: {str(e)}")
#             raiseimport logging
# from typing import Optional, List, Dict, Any
# from sqlalchemy.orm import Session, aliased
# from sqlalchemy import func, and_, or_
# from .models import EmployeeHierarchy

# logger = logging.getLogger(__name__)


# class EmployeeHierarchyRepository:
#     """Repository for Employee Hierarchy database operations."""
    
#     def __init__(self, db: Session):
#         self.db = db
    
#     def get_by_user_id(self, user_id: int) -> Optional[EmployeeHierarchy]:
#         """Get FIRST hierarchy entry by user ID."""
#         try:
#             return self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.user_id == user_id
#             ).first()
#         except Exception as e:
#             logger.error(f"Error fetching hierarchy for user {user_id}: {str(e)}")
#             raise
    
#     def get_all_by_user_id(self, user_id: int) -> List[EmployeeHierarchy]:
#         """Get ALL hierarchy entries for a user (multiple entries possible)."""
#         try:
#             entries = self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.user_id == user_id
#             ).order_by(EmployeeHierarchy.depth).all()
#             return entries
#         except Exception as e:
#             logger.error(f"Error fetching all hierarchy for user {user_id}: {str(e)}")
#             raise
    
#     def get_reporting_chain_entries(self, user_id: int) -> List[EmployeeHierarchy]:
#         """Get all hierarchy entries in the reporting chain for a user."""
#         try:
#             # Get the starting entry
#             start_entry = self.get_by_user_id(user_id)
#             if not start_entry:
#                 return []
            
#             # Collect all entries in the chain using loop
#             chain = [start_entry]
#             current_user_id = start_entry.reporting_to_id
            
#             while current_user_id:
#                 next_entry = self.get_by_user_id(current_user_id)
#                 if not next_entry:
#                     break
#                 chain.append(next_entry)
#                 current_user_id = next_entry.reporting_to_id
            
#             return chain
#         except Exception as e:
#             logger.error(f"Error fetching reporting chain for user {user_id}: {str(e)}")
#             raise
    
#     def create_entry(self, user_id: int, reporting_to_id: Optional[int], depth: int, updated_by: int) -> EmployeeHierarchy:
#         """Create a single hierarchy entry."""
#         try:
#             # Check if same entry already exists
#             existing = self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.user_id == user_id,
#                 EmployeeHierarchy.reporting_to_id == reporting_to_id,
#                 EmployeeHierarchy.depth == depth
#             ).first()
            
#             if existing:
#                 return existing
            
#             entry = EmployeeHierarchy(
#                 user_id=user_id,
#                 reporting_to_id=reporting_to_id,
#                 depth=depth,
#                 updated_by=updated_by
#             )
            
#             self.db.add(entry)
#             self.db.commit()
#             self.db.refresh(entry)
            
#             logger.info(f"Created hierarchy entry: user {user_id} reports to {reporting_to_id} at depth {depth}")
#             return entry
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Error creating hierarchy entry: {str(e)}")
#             raise
    
#     def create_complete_reporting_chain(self, user_id: int, first_reporting_to_id: Optional[int], updated_by: int) -> List[EmployeeHierarchy]:
#         """
#         Create complete reporting chain for a new user.
        
#         Example: If user1 reports to user2, and user2 reports to user3,
#         this will create entries for:
#         - user1 reports to user2 (depth 1)
#         - user1 reports to user3 (depth 2)
#         - user1 reports to user4 (depth 3) ... up to the top
#         """
#         try:
#             entries_created = []
            
#             if first_reporting_to_id:
#                 # Step 1: Get the reporting chain of the first manager
#                 manager_chain = self.get_reporting_chain_entries(first_reporting_to_id)
                
#                 if not manager_chain:
#                     raise ValueError(f"Manager {first_reporting_to_id} not found in hierarchy")
                
#                 # Step 2: Create entry for direct report (depth 1)
#                 direct_entry = self.create_entry(
#                     user_id=user_id,
#                     reporting_to_id=first_reporting_to_id,
#                     depth=1,
#                     updated_by=updated_by
#                 )
#                 entries_created.append(direct_entry)
                
#                 # Step 3: Create entries for all managers in the chain (indirect reports)
#                 for i, manager_entry in enumerate(manager_chain, start=2):
#                     indirect_entry = self.create_entry(
#                         user_id=user_id,
#                         reporting_to_id=manager_entry.user_id,
#                         depth=i,
#                         updated_by=updated_by
#                     )
#                     entries_created.append(indirect_entry)
#             else:
#                 # User has no manager (top-level)
#                 top_entry = self.create_entry(
#                     user_id=user_id,
#                     reporting_to_id=None,
#                     depth=0,
#                     updated_by=updated_by
#                 )
#                 entries_created.append(top_entry)
            
#             self.db.commit()
#             logger.info(f"Created {len(entries_created)} hierarchy entries for user {user_id}")
#             return entries_created
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Error creating complete reporting chain: {str(e)}")
#             raise
    
#     def delete_by_user_id(self, user_id: int) -> bool:
#         """Delete ALL hierarchy entries for a user."""
#         try:
#             entries = self.get_all_by_user_id(user_id)
#             if not entries:
#                 return False
            
#             for entry in entries:
#                 self.db.delete(entry)
            
#             self.db.commit()
#             logger.info(f"Deleted {len(entries)} hierarchy entries for user {user_id}")
#             return True
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Error deleting hierarchy entries for user {user_id}: {str(e)}")
#             raise
    
#     def get_all(self, skip: int = 0, limit: int = 100) -> List[EmployeeHierarchy]:
#         """Get all hierarchy entries with pagination."""
#         try:
#             entries = self.db.query(EmployeeHierarchy).order_by(
#                 EmployeeHierarchy.user_id,
#                 EmployeeHierarchy.depth
#             ).offset(skip).limit(limit).all()
#             return entries
#         except Exception as e:
#             logger.error(f"Error fetching all hierarchy entries: {str(e)}")
#             raise
    
#     def get_count(self) -> int:
#         """Get total hierarchy entry count."""
#         try:
#             count = self.db.query(func.count(EmployeeHierarchy.id)).scalar()
#             return count
#         except Exception as e:
#             logger.error(f"Error getting hierarchy count: {str(e)}")
#             raise
    
#     def get_users_by_manager(self, manager_id: int) -> List[EmployeeHierarchy]:
#         """Get all users who report to a specific manager."""
#         try:
#             entries = self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.reporting_to_id == manager_id
#             ).all()
#             return entries
#         except Exception as e:
#             logger.error(f"Error fetching users by manager {manager_id}: {str(e)}")
#             raiseimport logging
# from typing import Optional, List, Dict, Any
# from sqlalchemy.orm import Session, aliased
# from sqlalchemy import func, and_, or_
# from .models import EmployeeHierarchy

# logger = logging.getLogger(__name__)


# class EmployeeHierarchyRepository:
#     """Repository for Employee Hierarchy database operations."""
    
#     def __init__(self, db: Session):
#         self.db = db
    
#     def get_by_user_id(self, user_id: int) -> Optional[EmployeeHierarchy]:
#         """Get FIRST hierarchy entry by user ID."""
#         try:
#             return self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.user_id == user_id
#             ).first()
#         except Exception as e:
#             logger.error(f"Error fetching hierarchy for user {user_id}: {str(e)}")
#             raise
    
#     def get_all_by_user_id(self, user_id: int) -> List[EmployeeHierarchy]:
#         """Get ALL hierarchy entries for a user (multiple entries possible)."""
#         try:
#             entries = self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.user_id == user_id
#             ).order_by(EmployeeHierarchy.depth).all()
#             return entries
#         except Exception as e:
#             logger.error(f"Error fetching all hierarchy for user {user_id}: {str(e)}")
#             raise
    
#     def get_reporting_chain_entries(self, user_id: int) -> List[EmployeeHierarchy]:
#         """Get all hierarchy entries in the reporting chain for a user."""
#         try:
#             # Get the starting entry
#             start_entry = self.get_by_user_id(user_id)
#             if not start_entry:
#                 return []
            
#             # Collect all entries in the chain using loop
#             chain = [start_entry]
#             current_user_id = start_entry.reporting_to_id
            
#             while current_user_id:
#                 next_entry = self.get_by_user_id(current_user_id)
#                 if not next_entry:
#                     break
#                 chain.append(next_entry)
#                 current_user_id = next_entry.reporting_to_id
            
#             return chain
#         except Exception as e:
#             logger.error(f"Error fetching reporting chain for user {user_id}: {str(e)}")
#             raise
    
#     def create_entry(self, user_id: int, reporting_to_id: Optional[int], depth: int, updated_by: int) -> EmployeeHierarchy:
#         """Create a single hierarchy entry."""
#         try:
#             # Check if same entry already exists
#             existing = self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.user_id == user_id,
#                 EmployeeHierarchy.reporting_to_id == reporting_to_id,
#                 EmployeeHierarchy.depth == depth
#             ).first()
            
#             if existing:
#                 return existing
            
#             entry = EmployeeHierarchy(
#                 user_id=user_id,
#                 reporting_to_id=reporting_to_id,
#                 depth=depth,
#                 updated_by=updated_by
#             )
            
#             self.db.add(entry)
#             self.db.commit()
#             self.db.refresh(entry)
            
#             logger.info(f"Created hierarchy entry: user {user_id} reports to {reporting_to_id} at depth {depth}")
#             return entry
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Error creating hierarchy entry: {str(e)}")
#             raise
    
#     def create_complete_reporting_chain(self, user_id: int, first_reporting_to_id: Optional[int], updated_by: int) -> List[EmployeeHierarchy]:
#         """
#         Create complete reporting chain for a new user.
        
#         Example: If user1 reports to user2, and user2 reports to user3,
#         this will create entries for:
#         - user1 reports to user2 (depth 1)
#         - user1 reports to user3 (depth 2)
#         - user1 reports to user4 (depth 3) ... up to the top
#         """
#         try:
#             entries_created = []
            
#             if first_reporting_to_id:
#                 # Step 1: Get the reporting chain of the first manager
#                 manager_chain = self.get_reporting_chain_entries(first_reporting_to_id)
                
#                 if not manager_chain:
#                     raise ValueError(f"Manager {first_reporting_to_id} not found in hierarchy")
                
#                 # Step 2: Create entry for direct report (depth 1)
#                 direct_entry = self.create_entry(
#                     user_id=user_id,
#                     reporting_to_id=first_reporting_to_id,
#                     depth=1,
#                     updated_by=updated_by
#                 )
#                 entries_created.append(direct_entry)
                
#                 # Step 3: Create entries for all managers in the chain (indirect reports)
#                 for i, manager_entry in enumerate(manager_chain, start=2):
#                     indirect_entry = self.create_entry(
#                         user_id=user_id,
#                         reporting_to_id=manager_entry.user_id,
#                         depth=i,
#                         updated_by=updated_by
#                     )
#                     entries_created.append(indirect_entry)
#             else:
#                 # User has no manager (top-level)
#                 top_entry = self.create_entry(
#                     user_id=user_id,
#                     reporting_to_id=None,
#                     depth=0,
#                     updated_by=updated_by
#                 )
#                 entries_created.append(top_entry)
            
#             self.db.commit()
#             logger.info(f"Created {len(entries_created)} hierarchy entries for user {user_id}")
#             return entries_created
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Error creating complete reporting chain: {str(e)}")
#             raise
    
#     def delete_by_user_id(self, user_id: int) -> bool:
#         """Delete ALL hierarchy entries for a user."""
#         try:
#             entries = self.get_all_by_user_id(user_id)
#             if not entries:
#                 return False
            
#             for entry in entries:
#                 self.db.delete(entry)
            
#             self.db.commit()
#             logger.info(f"Deleted {len(entries)} hierarchy entries for user {user_id}")
#             return True
            
#         except Exception as e:
#             self.db.rollback()
#             logger.error(f"Error deleting hierarchy entries for user {user_id}: {str(e)}")
#             raise
    
#     def get_all(self, skip: int = 0, limit: int = 100) -> List[EmployeeHierarchy]:
#         """Get all hierarchy entries with pagination."""
#         try:
#             entries = self.db.query(EmployeeHierarchy).order_by(
#                 EmployeeHierarchy.user_id,
#                 EmployeeHierarchy.depth
#             ).offset(skip).limit(limit).all()
#             return entries
#         except Exception as e:
#             logger.error(f"Error fetching all hierarchy entries: {str(e)}")
#             raise
    
#     def get_count(self) -> int:
#         """Get total hierarchy entry count."""
#         try:
#             count = self.db.query(func.count(EmployeeHierarchy.id)).scalar()
#             return count
#         except Exception as e:
#             logger.error(f"Error getting hierarchy count: {str(e)}")
#             raise
    
#     def get_users_by_manager(self, manager_id: int) -> List[EmployeeHierarchy]:
#         """Get all users who report to a specific manager."""
#         try:
#             entries = self.db.query(EmployeeHierarchy).filter(
#                 EmployeeHierarchy.reporting_to_id == manager_id
#             ).all()
#             return entries
#         except Exception as e:
#             logger.error(f"Error fetching users by manager {manager_id}: {str(e)}")
#             raise

import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, aliased
from sqlalchemy import func, and_, or_
from .models import EmployeeHierarchy

logger = logging.getLogger(__name__)


class EmployeeHierarchyRepository:
    """Repository for Employee Hierarchy database operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_user_id(self, user_id: int) -> Optional[EmployeeHierarchy]:
        """Get FIRST hierarchy entry by user ID."""
        try:
            return self.db.query(EmployeeHierarchy).filter(
                EmployeeHierarchy.user_id == user_id
            ).first()
        except Exception as e:
            logger.error(f"Error fetching hierarchy for user {user_id}: {str(e)}")
            raise
    
    def get_all_by_user_id(self, user_id: int) -> List[EmployeeHierarchy]:
        """Get ALL hierarchy entries for a user (multiple entries possible)."""
        try:
            entries = self.db.query(EmployeeHierarchy).filter(
                EmployeeHierarchy.user_id == user_id
            ).order_by(EmployeeHierarchy.depth).all()
            return entries
        except Exception as e:
            logger.error(f"Error fetching all hierarchy for user {user_id}: {str(e)}")
            raise
    
    def get_reporting_chain_entries(self, user_id: int) -> List[EmployeeHierarchy]:
        """Get all hierarchy entries in the reporting chain for a user."""
        try:
            # Get the starting entry
            start_entry = self.get_by_user_id(user_id)
            if not start_entry:
                return []
            
            # Collect all entries in the chain using loop
            chain = [start_entry]
            current_user_id = start_entry.reporting_to_id
            
            while current_user_id:
                next_entry = self.get_by_user_id(current_user_id)
                if not next_entry:
                    break
                chain.append(next_entry)
                current_user_id = next_entry.reporting_to_id
            
            return chain
        except Exception as e:
            logger.error(f"Error fetching reporting chain for user {user_id}: {str(e)}")
            raise
    
    def create_entry(self, user_id: int, reporting_to_id: Optional[int], depth: int, updated_by: int) -> EmployeeHierarchy:
        """Create a single hierarchy entry."""
        try:
            # Check if same entry already exists
            existing = self.db.query(EmployeeHierarchy).filter(
                EmployeeHierarchy.user_id == user_id,
                EmployeeHierarchy.reporting_to_id == reporting_to_id,
                EmployeeHierarchy.depth == depth
            ).first()
            
            if existing:
                return existing
            
            entry = EmployeeHierarchy(
                user_id=user_id,
                reporting_to_id=reporting_to_id,
                depth=depth,
                updated_by=updated_by
            )
            
            self.db.add(entry)
            self.db.commit()
            self.db.refresh(entry)
            
            logger.info(f"Created hierarchy entry: user {user_id} reports to {reporting_to_id} at depth {depth}")
            return entry
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating hierarchy entry: {str(e)}")
            raise
        
    def create_complete_reporting_chain(self, user_id: int, first_reporting_to_id: Optional[int], updated_by: int) -> List[EmployeeHierarchy]:
        """
        Create complete reporting chain for a new user.
        
        Copies the entire reporting chain of the first_reportee_id,
        but increases all depths by 1 for the new user.
        """
        try:
            entries_created = []
            
            if first_reporting_to_id:
                # Step 1: Get ALL reporting entries of the first reportee
                reportee_entries = self.get_all_by_user_id(first_reporting_to_id)
                
                if not reportee_entries:
                    raise ValueError(f"No hierarchy entries found for user {first_reporting_to_id}")
                
                # Step 2: Create entries for the new user based on reportee's chain
                for reportee_entry in reportee_entries:
                    # For direct report (reportee_entry.reporting_to_id is None means top-level)
                    if reportee_entry.reporting_to_id is None:
                        # This should not happen if first_reportee_id reports to someone
                        continue
                    
                    # Calculate new depth: reportee's depth + 1
                    new_depth = reportee_entry.depth + 1
                    
                    # Create entry
                    new_entry = self.create_entry(
                        user_id=user_id,
                        reporting_to_id=reportee_entry.reporting_to_id,
                        depth=new_depth,
                        updated_by=updated_by
                    )
                    entries_created.append(new_entry)
                
                # Step 3: Also create the direct reporting entry (user → first_reportee_id)
                # This is depth 1 (the reportee itself, not who they report to)
                direct_entry = self.create_entry(
                    user_id=user_id,
                    reporting_to_id=first_reporting_to_id,
                    depth=1,
                    updated_by=updated_by
                )
                entries_created.append(direct_entry)
                
                # Step 4: Sort entries by depth for clarity
                entries_created.sort(key=lambda x: x.depth)
                
            else:
                # User has no manager (top-level)
                top_entry = self.create_entry(
                    user_id=user_id,
                    reporting_to_id=None,
                    depth=0,
                    updated_by=updated_by
                )
                entries_created.append(top_entry)
            
            self.db.commit()
            logger.info(f"Created {len(entries_created)} hierarchy entries for user {user_id}")
            return entries_created
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creating complete reporting chain: {str(e)}")
            raise
    
    def delete_by_user_id(self, user_id: int) -> bool:
        """Delete ALL hierarchy entries for a user."""
        try:
            entries = self.get_all_by_user_id(user_id)
            if not entries:
                return False
            
            for entry in entries:
                self.db.delete(entry)
            
            self.db.commit()
            logger.info(f"Deleted {len(entries)} hierarchy entries for user {user_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting hierarchy entries for user {user_id}: {str(e)}")
            raise
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[EmployeeHierarchy]:
        """Get all hierarchy entries with pagination."""
        try:
            entries = self.db.query(EmployeeHierarchy).order_by(
                EmployeeHierarchy.user_id,
                EmployeeHierarchy.depth
            ).offset(skip).limit(limit).all()
            return entries
        except Exception as e:
            logger.error(f"Error fetching all hierarchy entries: {str(e)}")
            raise
    
    def get_count(self) -> int:
        """Get total hierarchy entry count."""
        try:
            count = self.db.query(func.count(EmployeeHierarchy.id)).scalar()
            return count
        except Exception as e:
            logger.error(f"Error getting hierarchy count: {str(e)}")
            raise
    
    def get_users_by_manager(self, manager_id: int) -> List[EmployeeHierarchy]:
        """Get all users who report to a specific manager."""
        try:
            entries = self.db.query(EmployeeHierarchy).filter(
                EmployeeHierarchy.reporting_to_id == manager_id
            ).all()
            return entries
        except Exception as e:
            logger.error(f"Error fetching users by manager {manager_id}: {str(e)}")
            raise