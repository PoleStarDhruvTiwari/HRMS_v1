# app/core/permissions.py
from enum import Enum


class PermissionKey(str, Enum):
    # =====================================================
    # AUTH / SESSION
    # =====================================================
    SESSION_VIEW_SELF = "session.view.self"
    SESSION_TERMINATE_SELF = "session.terminate.self"
    SESSION_TERMINATE_ANY = "session.terminate.any"

    # =====================================================
    # USER MANAGEMENT
    # =====================================================
    USER_CREATE = "user.create"
    USER_VIEW = "user.view"
    USER_VIEW_SELF = "user.view.self"
    USER_UPDATE = "user.update"
    USER_DEACTIVATE = "user.deactivate"

    # =====================================================
    # ROLE MANAGEMENT
    # =====================================================
    ROLE_CREATE = "role.create"
    ROLE_VIEW = "role.view"
    ROLE_UPDATE = "role.update"
    ROLE_DELETE = "role.delete"
    ROLE_ASSIGN = "role.assign"
    ROLE_REVOKE = "role.revoke"

    # =====================================================
    # PERMISSION MANAGEMENT
    # =====================================================
    PERMISSION_VIEW = "permission.view"

    # =====================================================
    # MODULE MANAGEMENT
    # =====================================================
    MODULE_VIEW = "module.view"
    MODULE_CREATE = "module.create"
    MODULE_UPDATE = "module.update"
    MODULE_DELETE = "module.delete"

    # =====================================================
    # ORGANIZATION / STRUCTURE
    # =====================================================
    OFFICE_VIEW = "office.view"
    OFFICE_CREATE = "office.create"
    OFFICE_UPDATE = "office.update"
    OFFICE_DELETE = "office.delete"

    TEAM_VIEW = "team.view"
    TEAM_CREATE = "team.create"
    TEAM_UPDATE = "team.update"
    TEAM_DELETE = "team.delete"

    DESIGNATION_VIEW = "designation.view"
    DESIGNATION_CREATE = "designation.create"
    DESIGNATION_UPDATE = "designation.update"
    DESIGNATION_DELETE = "designation.delete"

    SHIFT_VIEW = "shift.view"
    SHIFT_CREATE = "shift.create"
    SHIFT_UPDATE = "shift.update"
    SHIFT_DELETE = "shift.delete"

    # =====================================================
    # ATTENDANCE
    # =====================================================
    ATTENDANCE_MARK = "attendance.mark"
    ATTENDANCE_VIEW_SELF = "attendance.view.self"
    ATTENDANCE_VIEW_TEAM = "attendance.view.team"
    ATTENDANCE_EDIT = "attendance.edit"
    ATTENDANCE_APPROVE = "attendance.approve"
    ATTENDANCE_REJECT = "attendance.reject"

    # =====================================================
    # LEAVE
    # =====================================================
    LEAVE_APPLY = "leave.apply"
    LEAVE_VIEW_SELF = "leave.view.self"
    LEAVE_VIEW_TEAM = "leave.view.team"
    LEAVE_APPROVE = "leave.approve"
    LEAVE_REJECT = "leave.reject"
    LEAVE_CANCEL = "leave.cancel"

    # =====================================================
    # ADMIN / SYSTEM
    # =====================================================
    SYSTEM_AUDIT_VIEW = "system.audit.view"
    SYSTEM_CONFIG_MANAGE = "system.config.manage"

    # =====================================================
    # USER PERMISSIONS (Direct assignment)
    # =====================================================
    USER_PERMISSION_VIEW = "user_permission.view"
    USER_PERMISSION_GRANT = "user_permission.grant"
    USER_PERMISSION_REVOKE = "user_permission.revoke"

    @classmethod
    def values(cls) -> list[str]:
        return [permission.value for permission in cls]