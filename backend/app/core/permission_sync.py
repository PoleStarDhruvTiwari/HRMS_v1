# # app/core/permission_sync.py
# """
# AUTOMATIC PERMISSION SYNCHRONIZATION SYSTEM

# ⚠️ IMPORTANT: This is the ONLY module that can modify permissions table.
# Code is the source of truth. Database is a read-only mirror.
# """

# app/core/permission_sync.py
import logging
from typing import Dict, List, Set
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database.session import SessionLocal
from app.core.permissions import PermissionKey

logger = logging.getLogger(__name__)
SYSTEM_USER_ID = 2

class PermissionSyncService:
    @staticmethod
    def sync() -> Dict[str, List[str]]:
        """Sync database permissions with code definitions."""
        db = SessionLocal()
        try:
            # Get permissions from code and database
            code_perms = set(PermissionKey.values())
            result = db.execute(text("SELECT permission_key, status FROM permissions"))
            db_perms = {row[0]: row[1] for row in result}
            
            actions = {'inserted': [], 'reactivated': [], 'soft_deleted': [], 'unchanged': []}
            
            # Process each code permission
            for perm_key in sorted(code_perms):
                if perm_key not in db_perms:
                    # Insert new permission
                    parts = perm_key.split('.')
                    module = parts[0] if parts else 'system'
                    description = f"{module.replace('_', ' ').title()} permission"
                    
                    db.execute(
                        text("""
                            INSERT INTO permissions (permission_key, description, updated_by, status)
                            VALUES (:key, :desc, :user_id, 'active')
                        """),
                        {"key": perm_key, "desc": description, "user_id": SYSTEM_USER_ID}
                    )
                    actions['inserted'].append(perm_key)
                    
                elif db_perms[perm_key] == 'deleted':
                    # Reactivate deleted permission
                    db.execute(
                        text("""
                            UPDATE permissions 
                            SET status = 'active', updated_by = :user_id
                            WHERE permission_key = :key
                        """),
                        {"key": perm_key, "user_id": SYSTEM_USER_ID}
                    )
                    actions['reactivated'].append(perm_key)
                    
                else:
                    actions['unchanged'].append(perm_key)
            
            # Soft delete permissions not in code
            for perm_key, status in db_perms.items():
                if perm_key not in code_perms and status == 'active':
                    db.execute(
                        text("""
                            UPDATE permissions 
                            SET status = 'deleted', updated_by = :user_id
                            WHERE permission_key = :key
                        """),
                        {"key": perm_key, "user_id": SYSTEM_USER_ID}
                    )
                    actions['soft_deleted'].append(perm_key)
            
            db.commit()
            return actions
            
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    
    @staticmethod
    def get_sync_status() -> Dict[str, any]:
        """Get sync status between code and database."""
        db = SessionLocal()
        try:
            code_perms = set(PermissionKey.values())
            result = db.execute(text("SELECT permission_key, status FROM permissions"))
            db_perms = {row[0]: row[1] for row in result}
            
            active_in_db = {k for k, v in db_perms.items() if v == 'active'}
            deleted_in_db = {k for k, v in db_perms.items() if v == 'deleted'}
            
            return {
                'code': {'total': len(code_perms), 'permissions': sorted(code_perms)},
                'database': {
                    'active': len(active_in_db),
                    'deleted': len(deleted_in_db),
                    'total': len(db_perms)
                },
                'drift': {
                    'missing_in_db': sorted(code_perms - set(db_perms.keys())),
                    'extra_in_db': sorted(set(db_perms.keys()) - code_perms),
                },
                'summary': {
                    'in_sync': code_perms == active_in_db,
                    'needs_attention': len(code_perms - active_in_db) > 0 or len(active_in_db - code_perms) > 0
                }
            }
        finally:
            db.close()


def sync_permissions() -> Dict[str, List[str]]:
    """Public interface for permission synchronization."""
    return PermissionSyncService.sync()


def get_permission_sync_status() -> Dict[str, any]:
    """Public interface for getting sync status."""
    return PermissionSyncService.get_sync_status()

