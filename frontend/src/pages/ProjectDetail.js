import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { 
  ArrowLeft, Plus, CheckCircle2, Circle, AlertCircle, 
  Calendar, Edit, Trash2, FileText, Users, Clock, MessageSquare, Send, Upload, X, 
  Download, Eye, ChevronDown
} from 'lucide-react';
import { toast } from 'sonner';
import { formatErrorMessage } from '@/utils/errorHandler';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DRAWING_CATEGORIES = ['Architecture', 'Interior', 'Landscape', 'Planning'];

export default function ProjectDetail({ user, onLogout }) {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [client, setClient] = useState(null);
  const [drawings, setDrawings] = useState([]);
  const [brandCategories, setBrandCategories] = useState([]);
  const [teamLeader, setTeamLeader] = useState(null);
  const [projectTeam, setProjectTeam] = useState([]);
  const [allTeamMembers, setAllTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('drawings');
  
  // Drawing dialog states
  const [drawingDialogOpen, setDrawingDialogOpen] = useState(false);
  const [revisionDialogOpen, setRevisionDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [selectedDrawing, setSelectedDrawing] = useState(null);
  const [editingDrawing, setEditingDrawing] = useState(null);
  
  // Project action dialog states
  const [editProjectDialogOpen, setEditProjectDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);
  const [archiveDate, setArchiveDate] = useState('');
  
  // File upload states
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadType, setUploadType] = useState(''); // 'issue' or 'resolve'
  const [selectedFileDrawing, setSelectedFileDrawing] = useState(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [drawingFormData, setDrawingFormData] = useState({
    category: 'Architecture',
    name: '',
    due_date: '',
    notes: ''
  });
  
  // Comment states
  const [commentDialogOpen, setCommentDialogOpen] = useState(false);
  const [selectedCommentDrawing, setSelectedCommentDrawing] = useState(null);
  const [comments, setComments] = useState([]);
  const [newCommentText, setNewCommentText] = useState('');
  const [editingComment, setEditingComment] = useState(null);
  const [loadingComments, setLoadingComments] = useState(false);
  const [referenceFile, setReferenceFile] = useState(null);
  const [revisionFormData, setRevisionFormData] = useState({
    revision_notes: '',
    revision_due_date: ''
  });

  useEffect(() => {
    fetchProjectData();
  }, [projectId]);

  const fetchProjectData = async () => {
    try {
      // Add timestamp to prevent caching
      const timestamp = Date.now();
      const [projectRes, drawingsRes, brandCategoriesRes, usersRes] = await Promise.all([
        axios.get(`${API}/projects/${projectId}?t=${timestamp}`),
        axios.get(`${API}/projects/${projectId}/drawings?t=${timestamp}`),
        axios.get(`${API}/brand-categories`),
        axios.get(`${API}/users`)
      ]);
      
      setProject(projectRes.data);
      setDrawings(drawingsRes.data);
      setBrandCategories(brandCategoriesRes.data);
      setAllTeamMembers(usersRes.data);
      
      // Find team leader
      if (projectRes.data.lead_architect_id) {
        const leader = usersRes.data.find(u => u.id === projectRes.data.lead_architect_id);
        setTeamLeader(leader);
      }
      
      // Fetch client if client_id exists
      if (projectRes.data.client_id) {
        const clientRes = await axios.get(`${API}/clients/${projectRes.data.client_id}`);
        setClient(clientRes.data);
      }
    } catch (error) {
      toast.error('Failed to load project data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddDrawing = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/projects/${projectId}/drawings`, {
        ...drawingFormData,
        project_id: projectId
      });
      toast.success('Drawing added successfully!');
      setDrawingDialogOpen(false);
      resetDrawingForm();
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to add drawing'));
    }
  };

  const handleToggleIssued = async (drawing) => {
    // If drawing is currently issued, un-issue it
    if (drawing.is_issued) {
      try {
        const token = localStorage.getItem('token');
        await axios.put(`${API}/drawings/${drawing.id}`, {
          is_issued: false
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Drawing un-issued');
        fetchProjectData();
      } catch (error) {
        console.error('Un-issue error:', error);
        toast.error(formatErrorMessage(error, 'Failed to un-issue drawing'));
      }
      return;
    }
    
    // If drawing is approved, issue it
    if (drawing.is_approved && drawing.file_url) {
      try {
        const token = localStorage.getItem('token');
        await axios.put(`${API}/drawings/${drawing.id}`, {
          is_issued: true
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Drawing issued successfully!');
        fetchProjectData();
      } catch (error) {
        console.error('Issue error:', error);
        toast.error(formatErrorMessage(error, 'Failed to issue drawing'));
      }
      return;
    }
    
    // If no file exists, open upload dialog for review
    setSelectedFileDrawing(drawing);
    setUploadType('issue');
    setUploadDialogOpen(true);
  };

  const handleApproveDrawing = async (drawing) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/drawings/${drawing.id}`, {
        is_approved: true
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Drawing approved for issuance');
      fetchProjectData();
    } catch (error) {
      console.error('Approve error:', error);
      toast.error(formatErrorMessage(error, 'Failed to approve drawing'));
    }
  };

  const handleOpenRevisionDialog = (drawing) => {
    setSelectedDrawing(drawing);
    setRevisionFormData({
      revision_notes: '',
      revision_due_date: ''
    });
    setRevisionDialogOpen(true);
  };

  const handleRequestRevision = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/drawings/${selectedDrawing.id}`, {
        has_pending_revision: true,
        revision_notes: revisionFormData.revision_notes,
        revision_due_date: revisionFormData.revision_due_date
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Revision requested successfully!');
      setRevisionDialogOpen(false);
      fetchProjectData();
    } catch (error) {
      console.error('Request revision error:', error);
      toast.error(formatErrorMessage(error, 'Failed to request revision'));
    }
  };

  const handleResolveRevision = async (drawing) => {
    // Show upload dialog for revision resolution
    setSelectedFileDrawing(drawing);
    setUploadType('resolve');
    setUploadDialogOpen(true);
  };

  const handleShowHistory = (drawing) => {
    setSelectedDrawing(drawing);
    setHistoryDialogOpen(true);
  };

  const handleViewPDF = async (drawing) => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch file with authentication
      const response = await fetch(`${API}/drawings/${drawing.id}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load file');
      }

      // Create blob from response
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      // Open in new window (works best on iOS)
      const newWindow = window.open(blobUrl, '_blank');
      
      if (newWindow) {
        toast.success('PDF opened successfully');
        // Cleanup blob URL after window opens
        setTimeout(() => window.URL.revokeObjectURL(blobUrl), 1000);
      } else {
        toast.error('Please allow popups to view PDF');
      }
      
    } catch (error) {
      console.error('PDF view error:', error);
      toast.error('Failed to open PDF');
    }
  };

  const handleDownloadPDF = async (drawing) => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch file with authentication
      const response = await fetch(`${API}/drawings/${drawing.id}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to download file');
      }

      // Create blob from response
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      // Trigger download
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = `${drawing.name}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      toast.success('Download started');
      setTimeout(() => window.URL.revokeObjectURL(blobUrl), 100);
      
    } catch (error) {
      console.error('PDF download error:', error);
      toast.error('Failed to download PDF');
    }
  };

  const handleViewCommentFile = async (fileUrl, fileName) => {
    try {
      const token = localStorage.getItem('token');
      
      // Extract filename from URL (e.g., "/uploads/comment_references/file.pdf" -> "file.pdf")
      const filename = fileUrl.split('/').pop();
      
      // Use authenticated endpoint
      const response = await fetch(`${API}/comments/reference/${filename}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to load file');
      }

      // Create blob from response
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      // Open in new window
      const newWindow = window.open(blobUrl, '_blank');
      
      if (newWindow) {
        toast.success('File opened successfully');
        setTimeout(() => window.URL.revokeObjectURL(blobUrl), 1000);
      } else {
        toast.error('Please allow popups to view file');
      }
      
    } catch (error) {
      console.error('File view error:', error);
      toast.error('Failed to open file');
    }
  };

  const handleDownloadCommentFile = async (fileUrl, fileName) => {
    try {
      const token = localStorage.getItem('token');
      
      // Extract filename from URL
      const filename = fileUrl.split('/').pop();
      
      // Use authenticated endpoint
      const response = await fetch(`${API}/comments/reference/${filename}/download`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (!response.ok) {
        throw new Error('Failed to download file');
      }

      // Create blob from response
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      
      // Get file extension from URL
      const fileExtension = fileUrl.split('.').pop();
      const downloadFileName = `${fileName}.${fileExtension}`;
      
      // Trigger download
      const a = document.createElement('a');
      a.href = blobUrl;
      a.download = downloadFileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      
      toast.success('Download started');
      setTimeout(() => window.URL.revokeObjectURL(blobUrl), 100);
      
    } catch (error) {
      console.error('File download error:', error);
      toast.error('Failed to download file');
    }
  };

  const handleDeleteDrawing = async (drawingId) => {
    if (!window.confirm('Are you sure you want to delete this drawing?')) return;
    
    try {
      await axios.delete(`${API}/drawings/${drawingId}`);
      toast.success('Drawing deleted successfully');
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to delete drawing'));
    }
  };

  // Comment handlers
  const handleOpenComments = async (drawing) => {
    setSelectedCommentDrawing(drawing);
    setCommentDialogOpen(true);
    await fetchComments(drawing.id);
    
    // Mark comments as read
    if (drawing.unread_comments > 0) {
      try {
        await axios.post(`${API}/drawings/${drawing.id}/mark-comments-read`);
        // Refresh drawing data to update unread count
        fetchProjectData();
      } catch (error) {
        console.error('Error marking comments as read:', error);
      }
    }
  };

  const fetchComments = async (drawingId) => {
    setLoadingComments(true);
    try {
      const response = await axios.get(`${API}/drawings/${drawingId}/comments`);
      setComments(response.data);
    } catch (error) {
      console.error('Error fetching comments:', error);
      toast.error('Failed to load comments');
    } finally {
      setLoadingComments(false);
    }
  };

  const handleSubmitComment = async () => {
    if (!newCommentText.trim()) {
      toast.error('Please enter a comment');
      return;
    }

    try {
      let commentId = editingComment?.id;
      
      if (editingComment) {
        // Update existing comment
        await axios.put(`${API}/drawings/comments/${editingComment.id}`, {
          comment_text: newCommentText
        });
        toast.success('Comment updated');
      } else {
        // Create new comment
        const response = await axios.post(`${API}/drawings/${selectedCommentDrawing.id}/comments`, {
          drawing_id: selectedCommentDrawing.id,
          comment_text: newCommentText
        });
        commentId = response.data.id;
        
        // Show notification for new comment
        toast.success('💬 New comment added!', {
          duration: 3000,
          style: {
            background: '#10b981',
            color: '#fff',
          },
        });
      }
      
      // If there's a reference file, upload it
      if (referenceFile && commentId) {
        const formData = new FormData();
        formData.append('file', referenceFile);
        
        await axios.post(`${API}/drawings/comments/${commentId}/upload-reference`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        toast.success('📎 Reference file attached!');
        setReferenceFile(null);
      }
      
      setNewCommentText('');
      setEditingComment(null);
      await fetchComments(selectedCommentDrawing.id);
      
      // Refresh project data to update comment counts
      await fetchProjectData();
      
      // Close dialog after posting comment (Issue #2)
      setCommentDialogOpen(false);
    } catch (error) {
      console.error('Comment error:', error);
      toast.error(formatErrorMessage(error, 'Failed to save comment'));
    }
  };

  const handleEditComment = (comment) => {
    setEditingComment(comment);
    setNewCommentText(comment.comment_text);
  };

  const handleDeleteComment = async (commentId) => {
    if (!window.confirm('Delete this comment?')) return;

    try {
      await axios.delete(`${API}/drawings/comments/${commentId}`);
      toast.success('Comment deleted');
      await fetchComments(selectedCommentDrawing.id);
    } catch (error) {
      console.error('Delete comment error:', error);
      toast.error('Failed to delete comment');
    }
  };

  const handleUploadReference = async (commentId) => {
    if (!referenceFile) {
      toast.error('Please select a file');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('file', referenceFile);

      await axios.post(`${API}/drawings/comments/${commentId}/upload-reference`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      toast.success('Reference file uploaded');
      setReferenceFile(null);
      await fetchComments(selectedCommentDrawing.id);
    } catch (error) {
      console.error('Upload reference error:', error);
      toast.error('Failed to upload reference file');
    }
  };

  const resetDrawingForm = () => {
    setDrawingFormData({
      category: 'Architecture',
      name: '',
      due_date: '',
      notes: ''
    });
    setEditingDrawing(null);
  };

  // Project action handlers
  const handleEditProject = () => {
    navigate('/projects', { state: { editProjectId: projectId } });
  };

  const handleDeleteProject = async () => {
    try {
      await axios.delete(`${API}/projects/${projectId}`);
      toast.success('Project deleted successfully');
      setDeleteDialogOpen(false);
      navigate('/projects');
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to delete project'));
    }
  };

  const handleArchiveProject = async () => {
    if (!archiveDate) {
      toast.error('Please select a completion date');
      return;
    }
    
    try {
      await axios.put(`${API}/projects/${projectId}`, {
        archived: true,
        end_date: archiveDate
      });
      toast.success('Project archived successfully');
      setArchiveDialogOpen(false);
      setArchiveDate('');
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to archive project'));
    }
  };

  const handleFileUpload = async () => {
    if (!selectedFile) {
      toast.error('Please select a PDF file');
      return;
    }
    
    // Validate file size (50MB limit for better UX)
    const maxSize = 50 * 1024 * 1024; // 50MB
    if (selectedFile.size > maxSize) {
      toast.error('File size exceeds 50MB limit. Please compress the PDF.');
      return;
    }
    
    setUploadingFile(true);
    setUploadProgress(0);
    
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('drawing_id', selectedFileDrawing.id);
      formData.append('upload_type', uploadType);
      
      console.log('Starting file upload...', {
        fileName: selectedFile.name,
        fileSize: selectedFile.size,
        uploadType
      });
      
      // Upload file to backend with progress tracking
      const uploadResponse = await axios.post(`${API}/drawings/upload`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        },
        timeout: 120000, // 2 minute timeout for larger files
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
          console.log(`Upload progress: ${percentCompleted}%`);
        }
      });
      
      console.log('Upload response received:', uploadResponse.data);
      const file_url = uploadResponse.data.file_url;
      
      // Set progress to 100% briefly before updating status
      setUploadProgress(100);
      
      // Update drawing with file URL
      const updatePayload = uploadType === 'issue' 
        ? { 
            under_review: true, 
            file_url,
            has_pending_revision: false  // Explicitly set to false
          }
        : { 
            has_pending_revision: false, 
            under_review: true,  // Resolved goes back to review state
            file_url  // Update with new resolved file
          };
      
      if (uploadType === 'resolve') {
        // Add to revision_file_urls array
        const current_urls = selectedFileDrawing.revision_file_urls || [];
        updatePayload.revision_file_urls = [...current_urls, file_url];
      }
      
      console.log('Updating drawing status...');
      await axios.put(`${API}/drawings/${selectedFileDrawing.id}`, updatePayload, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 15000 // 15 second timeout
      });
      
      console.log('Upload complete, showing success message');
      toast.success(uploadType === 'issue' ? 'Drawing uploaded for review!' : 'Revision resolved with PDF!');
      
      // Reset states
      setUploadDialogOpen(false);
      setSelectedFile(null);
      setSelectedFileDrawing(null);
      setUploadProgress(0);
      
      // Refresh data
      await fetchProjectData();
    } catch (error) {
      console.error('File upload error:', error);
      setUploadProgress(0);
      
      if (error.code === 'ECONNABORTED') {
        toast.error('Upload timeout - file may be too large. Try compressing it.');
      } else if (error.response?.status === 413) {
        toast.error('File too large. Maximum size is 50MB.');
      } else {
        toast.error(formatErrorMessage(error, 'Failed to upload file'));
      }
    } finally {
      console.log('Resetting upload state');
      // Use setTimeout to ensure state reset happens
      setTimeout(() => {
        setUploadingFile(false);
      }, 100);
    }
  };

  const getDrawingsByCategory = (category) => {
    return drawings.filter(d => d.category === category);
  };

  const getPendingDrawingsSortedByUrgency = () => {
    const pending = drawings.filter(d => !d.is_issued || d.has_pending_revision);
    return pending.sort((a, b) => {
      if (!a.due_date) return 1;
      if (!b.due_date) return -1;
      return new Date(a.due_date) - new Date(b.due_date);
    });
  };

  const getCompletedDrawings = () => {
    return drawings.filter(d => d.is_issued && !d.has_pending_revision);
  };

  const getDaysUntilDue = (dueDate) => {
    if (!dueDate) return null;
    const today = new Date();
    const due = new Date(dueDate);
    const diffTime = due - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getUrgencyColor = (daysUntil) => {
    if (daysUntil === null) return 'bg-slate-100 text-slate-600';
    if (daysUntil < 0) return 'bg-red-100 text-red-700';
    if (daysUntil <= 3) return 'bg-red-100 text-red-700';
    if (daysUntil <= 7) return 'bg-amber-100 text-amber-700';
    return 'bg-green-100 text-green-700';
  };

  const getDrawingStatusIcon = (drawing) => {
    if (drawing.has_pending_revision) {
      return <AlertCircle className="w-5 h-5 text-amber-500" />;
    }
    if (drawing.is_issued) {
      return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    }
    return <Circle className="w-5 h-5 text-slate-300" />;
  };

  const getDrawingStatusText = (drawing) => {
    if (drawing.has_pending_revision) return 'Revision Needed';
    if (drawing.is_issued) return 'Issued';
    return 'Pending';
  };

  const getDrawingStatusColor = (drawing) => {
    if (drawing.has_pending_revision) return 'bg-amber-50 text-amber-700 border-amber-200';
    if (drawing.is_issued) return 'bg-green-50 text-green-700 border-green-200';
    return 'bg-slate-50 text-slate-600 border-slate-200';
  };

  const DrawingCard = ({ drawing }) => (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-3 sm:p-4">
        <div className="flex flex-col sm:flex-row sm:items-start gap-3">
          <div className="flex items-start gap-2 sm:gap-3 flex-1 min-w-0">
            <div className="flex-shrink-0 mt-0.5">
              {getDrawingStatusIcon(drawing)}
            </div>
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-sm sm:text-base text-slate-900 break-words">{drawing.name}</h4>
              <div className="flex flex-wrap gap-1.5 sm:gap-2 mt-2">
                <span className={`px-2 py-0.5 text-[10px] sm:text-xs rounded border ${getDrawingStatusColor(drawing)}`}>
                  {getDrawingStatusText(drawing)}
                </span>
                {drawing.revision_count > 0 && (
                  <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-blue-50 text-blue-700 rounded border border-blue-200">
                    R{drawing.revision_count}
                  </span>
                )}
                {drawing.due_date && (
                  <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-slate-100 text-slate-600 rounded border border-slate-200 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    <span className="hidden sm:inline">{new Date(drawing.due_date).toLocaleDateString()}</span>
                    <span className="sm:hidden">{new Date(drawing.due_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
                  </span>
                )}
              </div>
              {drawing.notes && (
                <p className="text-xs sm:text-sm text-slate-600 mt-2 line-clamp-2">{drawing.notes}</p>
              )}
            </div>
          </div>
          
          <div className="flex flex-wrap sm:flex-nowrap gap-1.5 sm:gap-2 sm:ml-4">
            {/* STATE 1: PENDING - Show UPLOAD button */}
            {!drawing.file_url && drawing.has_pending_revision !== true && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleToggleIssued(drawing)}
                className="flex-1 sm:flex-none text-xs h-8"
              >
                Upload
              </Button>
            )}
            
            {/* STATE 3: REVISION PENDING - Show RESOLVE button */}
            {drawing.has_pending_revision === true && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleResolveRevision(drawing)}
                className="flex-1 sm:flex-none text-xs h-8 border-green-500 text-green-600"
                title="Upload Revised Drawing"
              >
                Resolve
              </Button>
            )}
            
            {/* STATE 2 & 5: UNDER REVIEW or ISSUED - Show REVISE button */}
            {(drawing.under_review || drawing.is_issued) && drawing.has_pending_revision !== true && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleOpenRevisionDialog(drawing)}
                className="flex-1 sm:flex-none text-xs h-8 border-amber-500 text-amber-600"
                title="Request Revision"
              >
                Revise
              </Button>
            )}
            
            {/* STATE 2: UNDER REVIEW - Show APPROVE button */}
            {drawing.under_review && !drawing.is_approved && drawing.has_pending_revision !== true && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleApproveDrawing(drawing)}
                className="flex-1 sm:flex-none text-xs h-8 border-green-500 text-green-600"
                title="Approve for Issuance"
              >
                Approve
              </Button>
            )}
            
            {/* STATE 4: APPROVED - Show ISSUE button */}
            {drawing.is_approved && !drawing.is_issued && drawing.has_pending_revision !== true && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleToggleIssued(drawing)}
                className="flex-1 sm:flex-none text-xs h-8 border-blue-500 text-blue-600"
                title="Issue Drawing"
              >
                Issue
              </Button>
            )}
            
            {/* STATE 5: ISSUED - Show UN-ISSUE button */}
            {drawing.is_issued && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleToggleIssued(drawing)}
                className="flex-1 sm:flex-none text-xs h-8"
                title="Un-Issue Drawing"
              >
                Un-Issue
              </Button>
            )}
            
            {/* PDF Button - Show in States 2, 3, 4, 5 (when file exists) */}
            {drawing.file_url && (drawing.under_review || drawing.is_approved || drawing.is_issued || drawing.has_pending_revision === true) && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1 sm:flex-none text-xs h-8 border-blue-500 text-blue-600"
                  >
                    📄 PDF <ChevronDown className="w-3 h-3 ml-1" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent>
                  <DropdownMenuItem onClick={() => handleViewPDF(drawing)}>
                    <Eye className="w-4 h-4 mr-2" />
                    View
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={() => handleDownloadPDF(drawing)}>
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            )}
            
            {/* Comment Button - Always show */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleOpenComments(drawing)}
              className="flex-1 sm:flex-none text-xs h-8 border-purple-500 text-purple-600 relative"
              title="Comments"
            >
              <MessageSquare className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
              Comments
              {drawing.comment_count > 0 && !drawing.unread_comments && (
                <span className="absolute -top-1 -right-1 bg-purple-600 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
                  {drawing.comment_count}
                </span>
              )}
              {drawing.unread_comments > 0 && (
                <span className="absolute -top-1 -right-1 bg-red-600 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center animate-pulse">
                  {drawing.unread_comments}
                </span>
              )}
            </Button>
            
            {user?.role === 'owner' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleDeleteDrawing(drawing.id)}
                className="text-red-600 hover:text-red-700 text-xs h-8 px-2 sm:px-3"
              >
                <Trash2 className="w-3 h-3 sm:w-4 sm:h-4" />
              </Button>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
        </div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="text-center py-12">
          <p className="text-slate-500">Project not found</p>
          <Button onClick={() => navigate('/projects')} className="mt-4">
            Back to Projects
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <Button
          variant="ghost"
          onClick={() => navigate('/projects')}
          className="mb-4 sm:mb-6"
          size="sm"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          <span className="hidden sm:inline">Back to Projects</span>
          <span className="sm:hidden">Back</span>
        </Button>

        {/* Project Info Card */}
        <Card className="mb-4 sm:mb-6">
          <CardContent className="p-4 sm:p-6">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-2 mb-2">
                  <span className="px-2 sm:px-3 py-1 bg-orange-100 text-orange-700 font-mono text-xs sm:text-sm font-medium rounded">
                    {project.code}
                  </span>
                  {project.archived && (
                    <span className="px-2 sm:px-3 py-1 bg-amber-100 text-amber-700 text-xs sm:text-sm rounded">
                      Archived
                    </span>
                  )}
                </div>
                
                {/* Project Access Code (Owner Only) */}
                {user?.is_owner && project.project_access_code && (
                  <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                    <p className="text-xs text-blue-600 font-medium mb-1">Project Access Code (Share with Contractors/Clients)</p>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-blue-900">{project.project_access_code}</span>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => {
                          navigator.clipboard.writeText(project.project_access_code);
                          toast.success('Access code copied!');
                        }}
                        className="h-6 px-2 text-xs border-blue-300"
                      >
                        Copy
                      </Button>
                    </div>
                  </div>
                )}
                <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900 mb-1 sm:mb-2 break-words">{project.title}</h1>
                {client && (
                  <p className="text-sm sm:text-base lg:text-lg text-slate-600 truncate">{client.name}</p>
                )}
                
                {/* Team Leader */}
                {teamLeader && (
                  <div className="mt-2 sm:mt-3 flex items-center gap-2 px-3 py-2 bg-orange-50 rounded-lg border border-orange-200 w-fit">
                    <div className="w-6 h-6 sm:w-8 sm:h-8 bg-orange-500 rounded-full flex items-center justify-center text-white font-bold text-xs sm:text-sm">
                      {teamLeader.name?.charAt(0)}
                    </div>
                    <div>
                      <p className="text-[10px] sm:text-xs text-orange-600 font-medium">Team Leader</p>
                      <p className="text-xs sm:text-sm font-semibold text-orange-900">{teamLeader.name}</p>
                    </div>
                  </div>
                )}
                
                {/* Project Types */}
                {project.project_types && project.project_types.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 sm:gap-2 mt-2 sm:mt-3">
                    {project.project_types.map((type) => (
                      <span 
                        key={type} 
                        className="px-2 py-0.5 sm:py-1 text-[10px] sm:text-xs lg:text-sm bg-orange-50 text-orange-700 rounded border border-orange-200"
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                )}

                {/* Dates */}
                <div className="flex flex-col sm:flex-row sm:gap-6 gap-2 mt-3 sm:mt-4 text-xs sm:text-sm text-slate-600">
                  {project.start_date && (
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3 h-3 sm:w-4 sm:h-4" />
                      <span>Started: {new Date(project.start_date).toLocaleDateString()}</span>
                    </div>
                  )}
                  {project.end_date && (
                    <div className="flex items-center gap-2">
                      <Calendar className="w-3 h-3 sm:w-4 sm:h-4" />
                      <span>Ended: {new Date(project.end_date).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex flex-col sm:flex-row gap-2">
                <Button
                  variant="outline"
                  onClick={handleEditProject}
                  size="sm"
                  className="w-full sm:w-auto"
                >
                  <Edit className="w-4 h-4 mr-2" />
                  Edit
                </Button>
                
                {!project.archived && user?.is_owner && (
                  <Button
                    variant="outline"
                    onClick={() => setArchiveDialogOpen(true)}
                    size="sm"
                    className="w-full sm:w-auto border-orange-300 text-orange-700 hover:bg-orange-50"
                  >
                    <Calendar className="w-4 h-4 mr-2" />
                    Archive
                  </Button>
                )}
                
                {user?.is_owner && (
                  <Button
                    variant="outline"
                    onClick={() => setDeleteDialogOpen(true)}
                    size="sm"
                    className="w-full sm:w-auto border-red-300 text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4 mr-2" />
                    Delete
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-4 w-full">
            <TabsTrigger value="urgent" className="text-xs sm:text-sm">Urgent</TabsTrigger>
            <TabsTrigger value="drawings" className="text-xs sm:text-sm">All</TabsTrigger>
            <TabsTrigger value="info" className="text-xs sm:text-sm">Info</TabsTrigger>
            <TabsTrigger value="brands" className="text-xs sm:text-sm">Brands</TabsTrigger>
          </TabsList>

          {/* Urgent Drawings Tab - Sorted by Due Date */}
          <TabsContent value="urgent" className="mt-4 sm:mt-6">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4 sm:mb-6">
              <div className="flex-1 min-w-0">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-slate-900 flex items-center gap-2">
                  <Clock className="w-5 h-5 text-red-600" />
                  Pending Drawings by Urgency
                </h2>
                <p className="text-xs sm:text-sm text-slate-600 mt-1">
                  {getPendingDrawingsSortedByUrgency().length} pending • Sorted by due date (most urgent first)
                </p>
              </div>
            </div>

            {getPendingDrawingsSortedByUrgency().length > 0 ? (
              <div className="space-y-3">
                {getPendingDrawingsSortedByUrgency().map((drawing) => {
                  const daysUntil = getDaysUntilDue(drawing.due_date);
                  return (
                    <Card key={drawing.id} className="border-l-4 border-l-red-500">
                      <CardContent className="p-3 sm:p-4">
                        <div className="flex flex-col gap-3">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-2">
                                <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-slate-100 text-slate-700 rounded">
                                  {drawing.category}
                                </span>
                                {daysUntil !== null && (
                                  <span className={`px-2 py-0.5 text-[10px] sm:text-xs rounded font-medium ${getUrgencyColor(daysUntil)}`}>
                                    {daysUntil < 0 ? `${Math.abs(daysUntil)} days overdue` : 
                                     daysUntil === 0 ? 'Due today!' : 
                                     daysUntil === 1 ? 'Due tomorrow' : 
                                     `${daysUntil} days left`}
                                  </span>
                                )}
                              </div>
                              <h4 className="font-medium text-sm sm:text-base text-slate-900 break-words">{drawing.name}</h4>
                              {drawing.due_date && (
                                <p className="text-xs sm:text-sm text-slate-600 mt-1">
                                  Due: {new Date(drawing.due_date).toLocaleDateString('en-US', { 
                                    weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' 
                                  })}
                                </p>
                              )}
                            </div>
                          </div>
                          
                          <div className="flex flex-wrap gap-1.5 sm:gap-2">
                            {/* Issue/Unissue button - hidden when there's a pending revision */}
                            {!drawing.has_pending_revision && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleToggleIssued(drawing)}
                                className="flex-1 sm:flex-none text-xs h-8"
                              >
                                {drawing.is_issued ? "Unissue" : "Issue"}
                              </Button>
                            )}
                            
                            {/* Revise/Resolve button */}
                            {(drawing.is_issued || drawing.has_pending_revision || drawing.revision_count > 0) && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  if (drawing.has_pending_revision) {
                                    handleResolveRevision(drawing);
                                  } else {
                                    handleOpenRevisionDialog(drawing);
                                  }
                                }}
                                className={`flex-1 sm:flex-none text-xs h-8 ${
                                  drawing.has_pending_revision ? "border-green-500 text-green-600" : 
                                  "border-amber-500 text-amber-600"
                                }`}
                              >
                                {drawing.has_pending_revision ? "Resolve" : "Revise"}
                              </Button>
                            )}
                            {drawing.revision_history && drawing.revision_history.length > 0 && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleShowHistory(drawing)}
                                className="flex-1 sm:flex-none text-xs h-8"
                              >
                                History
                              </Button>
                            )}
                            
                            {/* PDF Download/View Button */}
                            {drawing.file_url && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleDownloadPDF(drawing)}
                                className="flex-1 sm:flex-none text-xs h-8 border-blue-500 text-blue-600"
                                title="Download PDF"
                              >
                                📄 PDF
                              </Button>
                            )}
                            
                            {/* Comment Button */}
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => handleOpenComments(drawing)}
                              className="flex-1 sm:flex-none text-xs h-8 border-purple-500 text-purple-600"
                              title="Comments"
                            >
                              <MessageSquare className="w-3 h-3 sm:w-4 sm:h-4 mr-1" />
                              Comments
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            ) : (
              <Card>
                <CardContent className="p-8 text-center">
                  <CheckCircle2 className="w-12 h-12 sm:w-16 sm:h-16 text-green-300 mx-auto mb-4" />
                  <p className="text-slate-500 text-sm sm:text-base">All drawings are up to date! 🎉</p>
                </CardContent>
              </Card>
            )}

            {/* Completed Drawings Summary */}
            {getCompletedDrawings().length > 0 && (
              <Card className="mt-6 bg-green-50 border-green-200">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                    <div>
                      <p className="text-sm font-medium text-green-900">
                        {getCompletedDrawings().length} drawings completed
                      </p>
                      <p className="text-xs text-green-700">View all in "All Drawings" tab</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Drawings Tab */}
          <TabsContent value="drawings" className="mt-4 sm:mt-6">
            <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-4 sm:mb-6">
              <div className="flex-1 min-w-0">
                <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-slate-900">Project Drawings</h2>
                <p className="text-xs sm:text-sm text-slate-600 mt-1">
                  {drawings.length} total • {drawings.filter(d => d.is_issued).length} issued • {drawings.filter(d => d.has_pending_revision).length} revisions
                </p>
              </div>
              <Button 
                onClick={() => setDrawingDialogOpen(true)}
                className="bg-orange-500 hover:bg-orange-600 w-full sm:w-auto"
                size="sm"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Drawing
              </Button>
            </div>

            {/* Drawings by Category */}
            {DRAWING_CATEGORIES.filter(cat => project.project_types?.includes(cat)).map((category) => {
              const categoryDrawings = getDrawingsByCategory(category);
              
              return (
                <div key={category} className="mb-8">
                  <div className="flex items-center gap-3 mb-4">
                    <FileText className="w-5 h-5 text-orange-500" />
                    <h3 className="text-xl font-semibold text-slate-900">{category}</h3>
                    <span className="text-sm text-slate-500">({categoryDrawings.length})</span>
                  </div>
                  
                  {categoryDrawings.length > 0 ? (
                    <div className="space-y-3">
                      {categoryDrawings.map((drawing) => (
                        <DrawingCard key={drawing.id} drawing={drawing} />
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="p-8 text-center">
                        <p className="text-slate-500">No {category.toLowerCase()} drawings yet</p>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setDrawingFormData({ ...drawingFormData, category });
                            setDrawingDialogOpen(true);
                          }}
                          className="mt-3"
                        >
                          <Plus className="w-4 h-4 mr-2" />
                          Add {category} Drawing
                        </Button>
                      </CardContent>
                    </Card>
                  )}
                </div>
              );
            })}
          </TabsContent>

          {/* Project Info Tab */}
          <TabsContent value="info" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Project Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {project.site_address && (
                  <div>
                    <Label className="text-slate-600">Site Address</Label>
                    <p className="text-slate-900">{project.site_address}</p>
                  </div>
                )}
                {project.notes && (
                  <div>
                    <Label className="text-slate-600">Notes</Label>
                    <p className="text-slate-900">{project.notes}</p>
                  </div>
                )}
                <div>
                  <Label className="text-slate-600">Status</Label>
                  <p className="text-slate-900">{project.status?.replace(/_/g, ' ')}</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Brands Tab */}
          <TabsContent value="brands" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Brands Used in Project</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600">Brand management will be available soon</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Add Drawing Dialog */}
        <Dialog open={drawingDialogOpen} onOpenChange={setDrawingDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Add New Drawing</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAddDrawing} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Category *</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                    value={drawingFormData.category}
                    onChange={(e) => setDrawingFormData({ ...drawingFormData, category: e.target.value })}
                    required
                  >
                    {DRAWING_CATEGORIES.filter(cat => project.project_types?.includes(cat)).map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>Due Date *</Label>
                  <Input
                    type="date"
                    value={drawingFormData.due_date}
                    onChange={(e) => setDrawingFormData({ ...drawingFormData, due_date: e.target.value })}
                    required
                  />
                </div>
              </div>
              
              <div>
                <Label>Drawing Name *</Label>
                <Input
                  value={drawingFormData.name}
                  onChange={(e) => setDrawingFormData({ ...drawingFormData, name: e.target.value })}
                  placeholder="e.g., Ground Floor Plan, Elevation - North"
                  required
                />
              </div>

              <div>
                <Label>Notes</Label>
                <textarea
                  className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={drawingFormData.notes}
                  onChange={(e) => setDrawingFormData({ ...drawingFormData, notes: e.target.value })}
                  placeholder="Additional notes or specifications"
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setDrawingDialogOpen(false);
                    resetDrawingForm();
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-orange-500 hover:bg-orange-600">
                  Add Drawing
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Request Revision Dialog */}
        <Dialog open={revisionDialogOpen} onOpenChange={setRevisionDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Request Revision</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleRequestRevision} className="space-y-4">
              <div>
                <Label className="text-slate-600 mb-2 block">Drawing</Label>
                <p className="text-slate-900 font-medium">{selectedDrawing?.name}</p>
              </div>

              <div>
                <Label>What revisions are required? *</Label>
                <textarea
                  className="flex min-h-[120px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={revisionFormData.revision_notes}
                  onChange={(e) => setRevisionFormData({ ...revisionFormData, revision_notes: e.target.value })}
                  placeholder="Describe the revisions needed in detail..."
                  required
                />
              </div>

              <div>
                <Label>Revised Drawing Due Date *</Label>
                <Input
                  type="date"
                  value={revisionFormData.revision_due_date}
                  onChange={(e) => setRevisionFormData({ ...revisionFormData, revision_due_date: e.target.value })}
                  required
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setRevisionDialogOpen(false)}
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-amber-500 hover:bg-amber-600">
                  Request Revision
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Revision History Dialog */}
        <Dialog open={historyDialogOpen} onOpenChange={setHistoryDialogOpen}>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Revision History: {selectedDrawing?.name}</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 max-h-[60vh] overflow-y-auto">
              {selectedDrawing?.revision_history && selectedDrawing.revision_history.length > 0 ? (
                selectedDrawing.revision_history.map((revision, index) => (
                  <Card key={index} className="border-l-4 border-l-blue-500">
                    <CardContent className="p-4">
                      <div className="flex items-center gap-2 mb-3">
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded font-medium">
                          Revision {index + 1}
                        </span>
                        {revision.resolved_date && (
                          <span className="px-2 py-1 text-xs bg-green-100 text-green-700 rounded">
                            Resolved
                          </span>
                        )}
                        {!revision.resolved_date && (
                          <span className="px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded">
                            Pending
                          </span>
                        )}
                      </div>

                      <div className="space-y-2 text-sm">
                        <div className="flex items-start gap-2">
                          <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                          <div>
                            <span className="font-medium text-slate-700">Issued:</span>
                            <span className="text-slate-600 ml-2">
                              {new Date(revision.issued_date).toLocaleDateString()} at {new Date(revision.issued_date).toLocaleTimeString()}
                            </span>
                          </div>
                        </div>

                        {revision.revision_requested_date && (
                          <>
                            <div className="flex items-start gap-2">
                              <AlertCircle className="w-4 h-4 text-amber-500 mt-0.5" />
                              <div className="flex-1">
                                <div>
                                  <span className="font-medium text-slate-700">Revision Requested:</span>
                                  <span className="text-slate-600 ml-2">
                                    {new Date(revision.revision_requested_date).toLocaleDateString()} at {new Date(revision.revision_requested_date).toLocaleTimeString()}
                                  </span>
                                </div>
                                {revision.revision_notes && (
                                  <div className="mt-2 p-2 bg-amber-50 rounded text-slate-700">
                                    <span className="font-medium">Revision Notes:</span>
                                    <p className="mt-1">{revision.revision_notes}</p>
                                  </div>
                                )}
                                {revision.revision_due_date && (
                                  <div className="mt-1 text-slate-600">
                                    <span className="font-medium">Due:</span> {new Date(revision.revision_due_date).toLocaleDateString()}
                                  </div>
                                )}
                              </div>
                            </div>
                          </>
                        )}

                        {revision.resolved_date && (
                          <div className="flex items-start gap-2">
                            <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                            <div>
                              <span className="font-medium text-slate-700">Resolved:</span>
                              <span className="text-slate-600 ml-2">
                                {new Date(revision.resolved_date).toLocaleDateString()} at {new Date(revision.resolved_date).toLocaleTimeString()}
                              </span>
                            </div>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))
              ) : (
                <p className="text-center text-slate-500 py-8">No revision history yet</p>
              )}
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setHistoryDialogOpen(false)}>
                Close
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Comments Dialog */}
        <Dialog open={commentDialogOpen} onOpenChange={setCommentDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[80vh]">
            <DialogHeader>
              <DialogTitle>Comments: {selectedCommentDrawing?.name}</DialogTitle>
            </DialogHeader>
            <div className="flex flex-col h-full">
              {/* Comments List */}
              <div className="flex-1 overflow-y-auto space-y-4 mb-4 max-h-[40vh]">
                {loadingComments ? (
                  <div className="flex justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
                  </div>
                ) : comments.length > 0 ? (
                  comments.map((comment) => (
                    <Card key={comment.id} className="border-l-4 border-l-purple-500">
                      <CardContent className="p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <span className="font-medium text-slate-900">{comment.user_name}</span>
                            <span className="text-xs text-slate-500 ml-2">
                              ({comment.user_role})
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-500">
                              {new Date(comment.created_at).toLocaleString()}
                            </span>
                            {user?.id === comment.user_id && (
                              <div className="flex gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleEditComment(comment)}
                                  className="h-6 px-2"
                                >
                                  <Edit className="w-3 h-3" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDeleteComment(comment.id)}
                                  className="h-6 px-2 text-red-600"
                                >
                                  <Trash2 className="w-3 h-3" />
                                </Button>
                              </div>
                            )}
                          </div>
                        </div>
                        <p className="text-slate-700 whitespace-pre-wrap">{comment.comment_text}</p>
                        
                        {/* Reference Files */}
                        {comment.reference_files && comment.reference_files.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-2">
                            {comment.reference_files.map((file, idx) => (
                              <DropdownMenu key={idx}>
                                <DropdownMenuTrigger asChild>
                                  <button className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 cursor-pointer inline-flex items-center gap-1">
                                    📎 Reference {idx + 1} <ChevronDown className="w-3 h-3" />
                                  </button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent>
                                  <DropdownMenuItem onClick={() => handleViewCommentFile(file, `Reference_${idx + 1}`)}>
                                    <Eye className="w-4 h-4 mr-2" />
                                    View
                                  </DropdownMenuItem>
                                  <DropdownMenuItem onClick={() => handleDownloadCommentFile(file, `Reference_${idx + 1}`)}>
                                    <Download className="w-4 h-4 mr-2" />
                                    Download
                                  </DropdownMenuItem>
                                </DropdownMenuContent>
                              </DropdownMenu>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))
                ) : (
                  <div className="text-center py-8 text-slate-500">
                    No comments yet. Be the first to comment!
                  </div>
                )}
              </div>
              
              {/* Add/Edit Comment Form */}
              <div className="border-t pt-4">
                <Label className="text-sm font-medium mb-2 block">
                  {editingComment ? 'Edit Comment' : 'Add Comment'}
                </Label>
                <textarea
                  value={newCommentText}
                  onChange={(e) => setNewCommentText(e.target.value)}
                  placeholder="Write your comment here..."
                  className="w-full p-3 border rounded-lg min-h-[100px] focus:outline-none focus:ring-2 focus:ring-purple-500"
                />
                <div className="flex justify-between items-center mt-3">
                  <div className="flex items-center gap-2">
                    <input
                      type="file"
                      accept="image/*,.pdf"
                      onChange={(e) => setReferenceFile(e.target.files[0])}
                      className="hidden"
                      id="reference-upload"
                    />
                    <label 
                      htmlFor="reference-upload"
                      className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-3 cursor-pointer"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Attach File
                    </label>
                    {referenceFile && (
                      <span className="text-xs text-slate-600 flex items-center gap-2">
                        📎 {referenceFile.name}
                        <button
                          onClick={() => setReferenceFile(null)}
                          className="text-red-600 hover:text-red-800"
                          type="button"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </span>
                    )}
                  </div>
                  <div className="flex gap-2">
                    {editingComment && (
                      <Button
                        variant="outline"
                        onClick={() => {
                          setEditingComment(null);
                          setNewCommentText('');
                        }}
                      >
                        Cancel
                      </Button>
                    )}
                    <Button
                      onClick={handleSubmitComment}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      <Send className="w-4 h-4 mr-2" />
                      {editingComment ? 'Update' : 'Post'}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Delete Project Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Project</DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <p className="text-slate-700 mb-3">
                Are you sure you want to delete this project? This action cannot be undone.
              </p>
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <p className="text-sm text-red-800 font-medium">
                  <strong>{project?.code}</strong> - {project?.title}
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleDeleteProject}
                className="bg-red-600 hover:bg-red-700 text-white"
              >
                Delete Project
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Archive Project Dialog */}
        <Dialog open={archiveDialogOpen} onOpenChange={setArchiveDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Archive Project</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <p className="text-slate-700">
                Archiving this project will mark it as completed. Please enter the project completion date.
              </p>
              <div>
                <Label>Completion Date *</Label>
                <Input
                  type="date"
                  value={archiveDate}
                  onChange={(e) => setArchiveDate(e.target.value)}
                  required
                />
              </div>
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                <p className="text-sm text-orange-800">
                  <strong>{project?.code}</strong> - {project?.title}
                </p>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => {
                setArchiveDialogOpen(false);
                setArchiveDate('');
              }}>
                Cancel
              </Button>
              <Button 
                onClick={handleArchiveProject}
                className="bg-orange-600 hover:bg-orange-700 text-white"
              >
                Archive Project
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* File Upload Dialog */}
        <Dialog open={uploadDialogOpen} onOpenChange={(open) => {
          // Prevent closing during upload
          if (!uploadingFile || !open) {
            setUploadDialogOpen(open);
            if (!open) {
              setSelectedFile(null);
              setUploadProgress(0);
            }
          } else {
            toast.warning('Please wait for upload to complete');
          }
        }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>
                {uploadType === 'issue' ? 'Upload Drawing PDF to Issue' : 'Upload Revised Drawing PDF'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <p className="text-sm text-slate-600">
                {uploadType === 'issue' 
                  ? 'Please upload the PDF file of this drawing before issuing it.'
                  : 'Please upload the revised PDF file to complete the resolution.'}
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-sm text-blue-800 font-medium">
                  {selectedFileDrawing?.name}
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  {selectedFileDrawing?.category}
                </p>
              </div>
              <div>
                <Label>Select PDF File * (Max 50MB)</Label>
                <Input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => setSelectedFile(e.target.files[0])}
                  className="mt-1"
                  disabled={uploadingFile}
                />
                {selectedFile && (
                  <div className="mt-2 space-y-2">
                    <p className="text-xs text-green-600">
                      ✓ Selected: {selectedFile.name}
                    </p>
                    <p className="text-xs text-slate-500">
                      Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                )}
                {uploadingFile && (
                  <div className="mt-3 space-y-2">
                    <div className="flex justify-between text-xs text-slate-600">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <div className="w-full bg-slate-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadProgress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button 
                variant="outline" 
                onClick={() => {
                  setUploadDialogOpen(false);
                  setSelectedFile(null);
                  setSelectedFileDrawing(null);
                }}
                disabled={uploadingFile}
              >
                Cancel
              </Button>
              <Button 
                onClick={handleFileUpload}
                disabled={!selectedFile || uploadingFile}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                {uploadingFile 
                  ? `Uploading ${uploadProgress}%...` 
                  : uploadType === 'issue' ? 'Upload for Review' : 'Upload Resolved'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
