/**
 * usePermissions Hook
 * Fetches and manages user permissions for UI control
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Default permissions (restrictive)
const DEFAULT_PERMISSIONS = {
  can_create_project: false,
  can_edit_project: false,
  can_delete_project: false,
  can_archive_project: false,
  can_create_drawing: false,
  can_edit_drawing: false,
  can_delete_drawing: false,
  can_upload_drawing: false,
  can_approve_drawing: false,
  can_issue_drawing: false,
  can_mark_na: false,
  can_download_drawing: false,
  can_delete_any_comment: false,
  can_manage_users: false,
  can_approve_users: false,
  can_invite_team: false,
  can_view_accounting: false,
  can_edit_accounting: false,
};

export function usePermissions() {
  const [permissions, setPermissions] = useState(DEFAULT_PERMISSIONS);
  const [role, setRole] = useState(null);
  const [isOwner, setIsOwner] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPermissions = useCallback(async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await axios.get(`${API}/v2/me/permissions`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const data = response.data;
      setPermissions(data.permissions || DEFAULT_PERMISSIONS);
      setRole(data.role);
      setIsOwner(data.is_owner);
      setError(null);
    } catch (err) {
      console.error('Error fetching permissions:', err);
      setError(err.message);
      // Keep default restrictive permissions on error
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchPermissions();
  }, [fetchPermissions]);

  // Helper functions for common permission checks
  const canModifyProject = permissions.can_edit_project || permissions.can_delete_project;
  const canModifyDrawing = permissions.can_edit_drawing || permissions.can_upload_drawing;
  const isExternalUser = ['client', 'contractor', 'consultant', 'vendor'].includes(role);

  return {
    permissions,
    role,
    isOwner,
    loading,
    error,
    refetch: fetchPermissions,
    
    // Computed permissions
    canModifyProject,
    canModifyDrawing,
    isExternalUser,
    
    // Quick checks
    can: (permission) => permissions[permission] === true,
  };
}

/**
 * PermissionGate Component
 * Conditionally renders children based on permission
 */
export function PermissionGate({ permission, children, fallback = null }) {
  const { permissions, loading } = usePermissions();

  if (loading) return null;
  
  if (permissions[permission]) {
    return children;
  }
  
  return fallback;
}

/**
 * Get static permissions from user object (for SSR/initial render)
 */
export function getStaticPermissions(user) {
  if (!user) return DEFAULT_PERMISSIONS;
  
  const isOwner = user.is_owner || user.role === 'owner';
  const isTeamLeader = user.role === 'team_leader';
  const isExternalUser = ['client', 'contractor', 'consultant', 'vendor'].includes(user.role);
  
  return {
    can_create_project: isOwner,
    can_edit_project: isOwner,
    can_delete_project: isOwner,
    can_archive_project: isOwner,
    can_create_drawing: isOwner || isTeamLeader,
    can_edit_drawing: isOwner || isTeamLeader,
    can_delete_drawing: isOwner,
    can_upload_drawing: isOwner || isTeamLeader,
    can_approve_drawing: isOwner || isTeamLeader,
    can_issue_drawing: isOwner || isTeamLeader,
    can_mark_na: isOwner || isTeamLeader,
    can_download_drawing: true, // Everyone can download
    can_delete_any_comment: isOwner,
    can_manage_users: isOwner,
    can_approve_users: isOwner || user.is_admin,
    can_invite_team: isOwner,
    can_view_accounting: isOwner,
    can_edit_accounting: isOwner,
  };
}

export default usePermissions;
