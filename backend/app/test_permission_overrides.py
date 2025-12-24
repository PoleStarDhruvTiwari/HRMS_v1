# test_permission_overrides.py
"""
Test permission override system.
"""

from app.database.session import SessionLocal
from app.apis.access_control.user_permissions.repositories import UserPermissionRepository
from app.apis.access_control.permissions.models import Permission

def test_permission_override():
    """Test the permission override logic."""
    db = SessionLocal()
    
    try:
        repo = UserPermissionRepository(db)
        
        # Test user with role M2 (role_id=4)
        user_id = 5
        role_id = 4
        
        print("🔍 Testing Permission Override System")
        print("=" * 50)
        
        # 1. Check initial permissions
        print("\n1. User's initial permissions (from role M2):")
        effective = repo.get_user_effective_permissions(user_id)
        print(f"   Role permissions: {effective['role_permissions']}")
        print(f"   Granted extra: {effective['granted_permissions']}")
        print(f"   Revoked from role: {effective['revoked_permissions']}")
        print(f"   Effective permissions: {effective['effective_permissions']}")
        
        # 2. Grant extra permission
        print("\n2. Granting extra permission 'leave.approve':")
        leave_approve = db.query(Permission).filter(
            Permission.permission_key == "leave.approve"
        ).first()
        
        if leave_approve:
            repo.grant_extra_permission(
                user_id=user_id,
                permission_id=leave_approve.permission_id,
                granted_by=1  # admin user
            )
            print(f"   ✅ Granted: leave.approve")
        
        # 3. Revoke role permission
        print("\n3. Revoking role permission 'attendance.edit':")
        attendance_edit = db.query(Permission).filter(
            Permission.permission_key == "attendance.edit"
        ).first()
        
        if attendance_edit:
            repo.revoke_role_permission(
                user_id=user_id,
                permission_id=attendance_edit.permission_id,
                revoked_by=1  # admin user
            )
            print(f"   ✅ Revoked: attendance.edit")
        
        # 4. Check final permissions
        print("\n4. Final permission check:")
        effective = repo.get_user_effective_permissions(user_id)
        print(f"   Role permissions: {effective['role_permissions']}")
        print(f"   Granted extra: {effective['granted_permissions']}")
        print(f"   Revoked from role: {effective['revoked_permissions']}")
        print(f"   Effective permissions: {effective['effective_permissions']}")
        
        # 5. Test permission check
        print("\n5. Testing individual permission checks:")
        checks = [
            ("attendance.view", "Should have (from role)"),
            ("attendance.edit", "Should NOT have (revoked)"),
            ("leave.view", "Should have (from role)"),
            ("leave.approve", "Should have (granted extra)")
        ]
        
        for perm_key, expected in checks:
            has_perm = repo.check_user_has_permission(user_id, perm_key)
            status = "✅ YES" if has_perm else "❌ NO"
            print(f"   {perm_key}: {status} - {expected}")
        
        print("\n" + "=" * 50)
        print("🎉 Permission override test completed!")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_permission_override()