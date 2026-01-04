"""
Role-Based Permissions
Defines what each role can and cannot do
"""

from typing import Dict, Set
from enum import Enum
from functools import wraps
from fastapi import HTTPException


class Permission(Enum):
    """All available permissions"""
    # Project permissions
    PROJECT_CREATE = "project:create"
    PROJECT_EDIT = "project:edit"
    PROJECT_DELETE = "project:delete"
    PROJECT_ARCHIVE = "project:archive"
    PROJECT_VIEW = "project:view"
    
    # Drawing permissions
    DRAWING_CREATE = "drawing:create"
    DRAWING_EDIT = "drawing:edit"
    DRAWING_DELETE = "drawing:delete"
    DRAWING_UPLOAD = "drawing:upload"
    DRAWING_APPROVE = "drawing:approve"
    DRAWING_ISSUE = "drawing:issue"
    DRAWING_MARK_NA = "drawing:mark_na"
    DRAWING_VIEW = "drawing:view"
    DRAWING_DOWNLOAD = "drawing:download"
    
    # Comment permissions
    COMMENT_CREATE = "comment:create"
    COMMENT_DELETE_OWN = "comment:delete_own"
    COMMENT_DELETE_ANY = "comment:delete_any"
    COMMENT_VIEW = "comment:view"
    
    # User management
    USER_CREATE = "user:create"
    USER_EDIT = "user:edit"
    USER_DELETE = "user:delete"
    USER_APPROVE = "user:approve"
    USER_VIEW = "user:view"
    
    # Team management
    TEAM_INVITE = "team:invite"
    TEAM_MANAGE = "team:manage"
    
    # Accounting
    ACCOUNTING_VIEW = "accounting:view"
    ACCOUNTING_EDIT = "accounting:edit"
    
    # Notifications
    NOTIFICATION_SEND = "notification:send"


# Role permission mappings
ROLE_PERMISSIONS: Dict[str, Set[Permission]] = {
    "owner": {
        # Full access to everything
        Permission.PROJECT_CREATE, Permission.PROJECT_EDIT, Permission.PROJECT_DELETE,
        Permission.PROJECT_ARCHIVE, Permission.PROJECT_VIEW,
        Permission.DRAWING_CREATE, Permission.DRAWING_EDIT, Permission.DRAWING_DELETE,
        Permission.DRAWING_UPLOAD, Permission.DRAWING_APPROVE, Permission.DRAWING_ISSUE,
        Permission.DRAWING_MARK_NA, Permission.DRAWING_VIEW, Permission.DRAWING_DOWNLOAD,
        Permission.COMMENT_CREATE, Permission.COMMENT_DELETE_OWN, Permission.COMMENT_DELETE_ANY,
        Permission.COMMENT_VIEW,
        Permission.USER_CREATE, Permission.USER_EDIT, Permission.USER_DELETE,
        Permission.USER_APPROVE, Permission.USER_VIEW,
        Permission.TEAM_INVITE, Permission.TEAM_MANAGE,
        Permission.ACCOUNTING_VIEW, Permission.ACCOUNTING_EDIT,
        Permission.NOTIFICATION_SEND,
    },
    
    "team_leader": {
        Permission.PROJECT_VIEW,
        Permission.DRAWING_CREATE, Permission.DRAWING_EDIT, Permission.DRAWING_UPLOAD,
        Permission.DRAWING_APPROVE, Permission.DRAWING_ISSUE, Permission.DRAWING_MARK_NA,
        Permission.DRAWING_VIEW, Permission.DRAWING_DOWNLOAD,
        Permission.COMMENT_CREATE, Permission.COMMENT_DELETE_OWN, Permission.COMMENT_VIEW,
        Permission.USER_VIEW,
    },
    
    "senior_designer": {
        Permission.PROJECT_VIEW,
        Permission.DRAWING_CREATE, Permission.DRAWING_EDIT, Permission.DRAWING_UPLOAD,
        Permission.DRAWING_VIEW, Permission.DRAWING_DOWNLOAD,
        Permission.COMMENT_CREATE, Permission.COMMENT_DELETE_OWN, Permission.COMMENT_VIEW,
    },
    
    "senior_interior_designer": {
        # Same as team_leader - can edit projects and upload drawings
        Permission.PROJECT_VIEW, Permission.PROJECT_EDIT,
        Permission.DRAWING_CREATE, Permission.DRAWING_EDIT, Permission.DRAWING_UPLOAD,
        Permission.DRAWING_APPROVE, Permission.DRAWING_ISSUE, Permission.DRAWING_MARK_NA,
        Permission.DRAWING_VIEW, Permission.DRAWING_DOWNLOAD,
        Permission.COMMENT_CREATE, Permission.COMMENT_DELETE_OWN, Permission.COMMENT_VIEW,
        Permission.USER_VIEW,
    },
    
    "junior_designer": {
        Permission.PROJECT_VIEW,
        Permission.DRAWING_VIEW, Permission.DRAWING_DOWNLOAD,
        Permission.COMMENT_CREATE, Permission.COMMENT_DELETE_OWN, Permission.COMMENT_VIEW,
    },
    
    "client": {
        # View only - NO modify/delete/approve actions
        Permission.PROJECT_VIEW,
        Permission.DRAWING_VIEW, Permission.DRAWING_DOWNLOAD,
        Permission.COMMENT_CREATE, Permission.COMMENT_DELETE_OWN, Permission.COMMENT_VIEW,
    },
    
    "contractor": {
        # Very limited - view assigned projects only
        Permission.PROJECT_VIEW,
        Permission.DRAWING_VIEW, Permission.DRAWING_DOWNLOAD,
        Permission.COMMENT_CREATE, Permission.COMMENT_DELETE_OWN, Permission.COMMENT_VIEW,
    },
    
    "consultant": {
        # Similar to contractor
        Permission.PROJECT_VIEW,
        Permission.DRAWING_VIEW, Permission.DRAWING_DOWNLOAD,
        Permission.COMMENT_CREATE, Permission.COMMENT_DELETE_OWN, Permission.COMMENT_VIEW,
    },
    
    "vendor": {
        # Minimal access
        Permission.PROJECT_VIEW,
        Permission.DRAWING_VIEW,
        Permission.COMMENT_VIEW,
    },
}


def get_user_permissions(role: str, is_owner: bool = False, is_admin: bool = False) -> Set[Permission]:
    """Get permissions for a user based on role and flags"""
    if is_owner:
        return ROLE_PERMISSIONS["owner"]
    
    permissions = ROLE_PERMISSIONS.get(role, set())
    
    # Admins get additional user management permissions
    if is_admin:
        permissions = permissions | {
            Permission.USER_APPROVE,
            Permission.USER_VIEW,
        }
    
    return permissions


def has_permission(role: str, permission: Permission, is_owner: bool = False, is_admin: bool = False) -> bool:
    """Check if role has specific permission"""
    permissions = get_user_permissions(role, is_owner, is_admin)
    return permission in permissions


def check_permission(permission: Permission):
    """Decorator to check permission on route handlers"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get current_user from kwargs
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")
            
            user_permissions = get_user_permissions(
                current_user.role,
                current_user.is_owner,
                getattr(current_user, 'is_admin', False)
            )
            
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Frontend permission mapping for UI elements
def get_frontend_permissions(role: str, is_owner: bool = False, is_admin: bool = False) -> Dict[str, bool]:
    """Get permissions formatted for frontend UI control"""
    permissions = get_user_permissions(role, is_owner, is_admin)
    
    return {
        # Buttons to show/hide
        "can_create_project": Permission.PROJECT_CREATE in permissions,
        "can_edit_project": Permission.PROJECT_EDIT in permissions,
        "can_delete_project": Permission.PROJECT_DELETE in permissions,
        "can_archive_project": Permission.PROJECT_ARCHIVE in permissions,
        
        "can_create_drawing": Permission.DRAWING_CREATE in permissions,
        "can_edit_drawing": Permission.DRAWING_EDIT in permissions,
        "can_delete_drawing": Permission.DRAWING_DELETE in permissions,
        "can_upload_drawing": Permission.DRAWING_UPLOAD in permissions,
        "can_approve_drawing": Permission.DRAWING_APPROVE in permissions,
        "can_issue_drawing": Permission.DRAWING_ISSUE in permissions,
        "can_mark_na": Permission.DRAWING_MARK_NA in permissions,
        "can_download_drawing": Permission.DRAWING_DOWNLOAD in permissions,
        
        "can_delete_any_comment": Permission.COMMENT_DELETE_ANY in permissions,
        
        "can_manage_users": Permission.USER_CREATE in permissions,
        "can_approve_users": Permission.USER_APPROVE in permissions,
        "can_invite_team": Permission.TEAM_INVITE in permissions,
        
        "can_view_accounting": Permission.ACCOUNTING_VIEW in permissions,
        "can_edit_accounting": Permission.ACCOUNTING_EDIT in permissions,
    }
