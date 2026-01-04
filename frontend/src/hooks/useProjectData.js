/**
 * Custom hooks for data fetching and state management
 * Extracted from large components for reusability
 */

import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/**
 * Hook for fetching and managing project data
 */
export function useProjectData(projectId) {
  const [project, setProject] = useState(null);
  const [client, setClient] = useState(null);
  const [drawings, setDrawings] = useState([]);
  const [teamLeader, setTeamLeader] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchProjectData = useCallback(async () => {
    if (!projectId) return;
    
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [projectRes, drawingsRes] = await Promise.all([
        axios.get(`${API}/projects/${projectId}`, { headers }),
        axios.get(`${API}/projects/${projectId}/drawings`, { headers })
      ]);

      setProject(projectRes.data);
      setDrawings(drawingsRes.data);

      // Fetch client if exists
      if (projectRes.data.client_id) {
        try {
          const clientRes = await axios.get(
            `${API}/clients/${projectRes.data.client_id}`,
            { headers }
          );
          setClient(clientRes.data);
        } catch (err) {
          console.log('Client not found or not accessible');
        }
      }

      // Fetch team leader if exists
      if (projectRes.data.team_leader_id) {
        try {
          const usersRes = await axios.get(`${API}/users`, { headers });
          const leader = usersRes.data.find(
            u => u.id === projectRes.data.team_leader_id
          );
          setTeamLeader(leader);
        } catch (err) {
          console.log('Team leader not found');
        }
      }

      setError(null);
    } catch (err) {
      console.error('Error fetching project data:', err);
      setError(err.message);
      toast.error('Failed to load project data');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchProjectData();
  }, [fetchProjectData]);

  return {
    project,
    client,
    drawings,
    teamLeader,
    loading,
    error,
    refetch: fetchProjectData,
    setProject,
    setDrawings
  };
}

/**
 * Hook for managing drawing operations
 */
export function useDrawingOperations(projectId, onSuccess) {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);

  const uploadDrawingFile = useCallback(async (drawingId, file, type = 'issue') => {
    if (!file) return;
    
    try {
      setUploading(true);
      setProgress(0);
      
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', file);

      const endpoint = type === 'issue' 
        ? `${API}/drawings/${drawingId}/issue`
        : `${API}/drawings/${drawingId}/resolve`;

      await axios.post(endpoint, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        },
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          setProgress(percentCompleted);
        }
      });

      toast.success(`Drawing ${type === 'issue' ? 'issued' : 'resolved'} successfully`);
      onSuccess?.();
    } catch (err) {
      console.error('Upload error:', err);
      toast.error(err.response?.data?.detail || 'Failed to upload file');
    } finally {
      setUploading(false);
      setProgress(0);
    }
  }, [onSuccess]);

  const createDrawing = useCallback(async (drawingData) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/projects/${projectId}/drawings`,
        drawingData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Drawing created successfully');
      onSuccess?.();
      return true;
    } catch (err) {
      console.error('Create drawing error:', err);
      toast.error(err.response?.data?.detail || 'Failed to create drawing');
      return false;
    }
  }, [projectId, onSuccess]);

  const updateDrawing = useCallback(async (drawingId, drawingData) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API}/drawings/${drawingId}`,
        drawingData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Drawing updated successfully');
      onSuccess?.();
      return true;
    } catch (err) {
      console.error('Update drawing error:', err);
      toast.error(err.response?.data?.detail || 'Failed to update drawing');
      return false;
    }
  }, [onSuccess]);

  const approveDrawing = useCallback(async (drawingId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/drawings/${drawingId}/approve`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Drawing approved successfully');
      onSuccess?.();
      return true;
    } catch (err) {
      console.error('Approve drawing error:', err);
      toast.error(err.response?.data?.detail || 'Failed to approve drawing');
      return false;
    }
  }, [onSuccess]);

  return {
    uploading,
    progress,
    uploadDrawingFile,
    createDrawing,
    updateDrawing,
    approveDrawing
  };
}

/**
 * Hook for managing comments
 */
export function useComments(drawingId) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const fetchComments = useCallback(async () => {
    if (!drawingId) return;
    
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const res = await axios.get(
        `${API}/drawings/${drawingId}/comments`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setComments(res.data);
    } catch (err) {
      console.error('Error fetching comments:', err);
    } finally {
      setLoading(false);
    }
  }, [drawingId]);

  const addComment = useCallback(async (commentText, requiresRevision = false) => {
    if (!drawingId || !commentText.trim()) return false;
    
    try {
      setSubmitting(true);
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/drawings/${drawingId}/comments`,
        {
          comment_text: commentText,
          requires_revision: requiresRevision
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Comment added');
      await fetchComments();
      return true;
    } catch (err) {
      console.error('Error adding comment:', err);
      toast.error('Failed to add comment');
      return false;
    } finally {
      setSubmitting(false);
    }
  }, [drawingId, fetchComments]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  return {
    comments,
    loading,
    submitting,
    fetchComments,
    addComment
  };
}

/**
 * Hook for authentication state
 */
export function useAuth() {
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [isAuthenticated, setIsAuthenticated] = useState(!!token);

  useEffect(() => {
    const handleStorageChange = () => {
      const newToken = localStorage.getItem('token');
      setToken(newToken);
      setIsAuthenticated(!!newToken);
    };

    window.addEventListener('storage', handleStorageChange);
    return () => window.removeEventListener('storage', handleStorageChange);
  }, []);

  const getAuthHeaders = useCallback(() => ({
    Authorization: `Bearer ${token}`
  }), [token]);

  return {
    token,
    isAuthenticated,
    getAuthHeaders
  };
}

export default {
  useProjectData,
  useDrawingOperations,
  useComments,
  useAuth
};
