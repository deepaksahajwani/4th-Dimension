import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
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
  ArrowLeft, Plus, CheckCircle2, Circle, AlertCircle, Check,
  Calendar, Edit, Trash2, FileText, Users, Clock, MessageSquare, Send, Upload, X, 
  Download, Eye, ChevronDown, Mic, Square, Play, Pause, Phone, Mail, Building, HardHat, Briefcase, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';
import { formatErrorMessage } from '@/utils/errorHandler';
import { DrawingCard, DeleteProjectDialog, ArchiveProjectDialog, ChatView } from '@/components/project';
import TeamLeaderAccess from '@/components/TeamLeaderAccess';
import { usePermissions } from '@/hooks/usePermissions';
import { LoadingState, ErrorState } from '@/utils/stability';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DRAWING_CATEGORIES = ['Architecture', 'Interior', 'Landscape', 'Planning'];

export default function ProjectDetail({ user, onLogout }) {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const location = window.location;
  
  // Role-based permissions hook
  const { permissions, isOwner, role, loading: permissionsLoading } = usePermissions();
  
  const [project, setProject] = useState(null);
  const [client, setClient] = useState(null);
  const [drawings, setDrawings] = useState([]);
  const [brandCategories, setBrandCategories] = useState([]);
  const [teamLeader, setTeamLeader] = useState(null);
  const [allTeamMembers, setAllTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // New error state for stability
  const [activeTab, setActiveTab] = useState('drawings');
  const [highlightedDrawingId, setHighlightedDrawingId] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showRevisionHistory, setShowRevisionHistory] = useState({});
  
  // Drawing dialog states
  const [drawingDialogOpen, setDrawingDialogOpen] = useState(false);
  const [revisionDialogOpen, setRevisionDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [selectedDrawing, setSelectedDrawing] = useState(null);
  const [editingDrawing, setEditingDrawing] = useState(null);
  
  // Project action dialog states
  const [editProjectDialogOpen, setEditProjectDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [deleteOtpSent, setDeleteOtpSent] = useState(false);
  const [deleteOtp, setDeleteOtp] = useState('');
  const [sendingOtp, setSendingOtp] = useState(false);
  const [archiveDialogOpen, setArchiveDialogOpen] = useState(false);
  const [archiveDate, setArchiveDate] = useState('');
  
  // File upload states
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [uploadType, setUploadType] = useState(''); // 'issue' or 'resolve'
  const [selectedFileDrawing, setSelectedFileDrawing] = useState(null);
  const [uploadingFile, setUploadingFile] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [selectedFiles, setSelectedFiles] = useState([]);
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
  const [referenceFiles, setReferenceFiles] = useState([]);
  const [submittingComment, setSubmittingComment] = useState(false);
  
  // Project-level comments state
  const [projectComments, setProjectComments] = useState([]);
  const [loadingProjectComments, setLoadingProjectComments] = useState(false);
  
  // Voice recording states
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [playingAudio, setPlayingAudio] = useState(false);
  
  // Comment revision state
  const [markForRevision, setMarkForRevision] = useState(false);
  
  // Issue drawing states
  const [issueDialogOpen, setIssueDialogOpen] = useState(false);
  const [selectedIssueDrawing, setSelectedIssueDrawing] = useState(null);
  const [selectedRecipients, setSelectedRecipients] = useState([]);
  const [availableRecipients, setAvailableRecipients] = useState([]);
  const [revisionFormData, setRevisionFormData] = useState({
    revision_notes: '',
    revision_due_date: ''
  });
  
  // Revision voice note and file states
  const [revisionIsRecording, setRevisionIsRecording] = useState(false);
  const [revisionAudioBlob, setRevisionAudioBlob] = useState(null);
  const [revisionMediaRecorder, setRevisionMediaRecorder] = useState(null);
  const [revisionRecordingTime, setRevisionRecordingTime] = useState(0);
  const [revisionFiles, setRevisionFiles] = useState([]);
  
  // Co-Client states
  const [coClients, setCoClients] = useState([]);
  const [coClientDialogOpen, setCoClientDialogOpen] = useState(false);
  const [coClientFormData, setCoClientFormData] = useState({
    name: '',
    email: '',
    phone: '',
    relationship: 'Family Member',
    notes: ''
  });

  // Project Team states (contractors, consultants)
  const [projectTeam, setProjectTeam] = useState({ contractors: [], consultants: [], co_clients: [] });
  const [allContractors, setAllContractors] = useState([]);
  const [allConsultants, setAllConsultants] = useState([]);
  const [contractorTypes, setContractorTypes] = useState([]);
  const [consultantTypes, setConsultantTypes] = useState([]);
  const [assignContractorDialogOpen, setAssignContractorDialogOpen] = useState(false);
  const [assignConsultantDialogOpen, setAssignConsultantDialogOpen] = useState(false);
  const [selectedContractorType, setSelectedContractorType] = useState('');
  const [selectedContractorId, setSelectedContractorId] = useState('');
  const [selectedConsultantType, setSelectedConsultantType] = useState('');
  const [selectedConsultantId, setSelectedConsultantId] = useState('');
  const [inviteNewContractor, setInviteNewContractor] = useState(false);
  const [inviteNewConsultant, setInviteNewConsultant] = useState(false);
  const [newContractorData, setNewContractorData] = useState({ name: '', phone: '', email: '' });
  const [newConsultantData, setNewConsultantData] = useState({ name: '', phone: '', email: '' });

  useEffect(() => {
    fetchProjectData();
  }, [projectId]);

  const fetchProjectData = async () => {
    try {
      // Add timestamp to prevent caching
      const timestamp = Date.now();
      const [projectRes, drawingsRes, brandCategoriesRes, usersRes, teamRes, contractorsRes, consultantsRes, contractorTypesRes, consultantTypesRes] = await Promise.all([
        axios.get(`${API}/projects/${projectId}?t=${timestamp}`),
        axios.get(`${API}/projects/${projectId}/drawings?t=${timestamp}`),
        axios.get(`${API}/brand-categories`),
        axios.get(`${API}/users`),
        axios.get(`${API}/projects/${projectId}/team?t=${timestamp}`).catch(() => ({ data: { contractors: [], consultants: [], co_clients: [] } })),
        axios.get(`${API}/contractors`).catch(() => ({ data: [] })),
        axios.get(`${API}/consultants`).catch(() => ({ data: [] })),
        axios.get(`${API}/contractor-types`).catch(() => ({ data: [] })),
        axios.get(`${API}/consultant-types`).catch(() => ({ data: [] }))
      ]);
      
      setProject(projectRes.data);
      setDrawings(drawingsRes.data);
      setBrandCategories(brandCategoriesRes.data);
      setAllTeamMembers(usersRes.data);
      setProjectTeam(teamRes.data);
      setAllContractors(contractorsRes.data);
      setAllConsultants(consultantsRes.data);
      setContractorTypes(contractorTypesRes.data);
      setConsultantTypes(consultantTypesRes.data);
      
      // Find team leader
      if (projectRes.data.team_leader_id) {
        const leader = usersRes.data.find(u => u.id === projectRes.data.team_leader_id);
        setTeamLeader(leader);
      } else if (projectRes.data.lead_architect_id) {
        // Legacy fallback
        const leader = usersRes.data.find(u => u.id === projectRes.data.lead_architect_id);
        setTeamLeader(leader);
      }
      
      // Fetch client if client_id exists
      if (projectRes.data.client_id) {
        const clientRes = await axios.get(`${API}/clients/${projectRes.data.client_id}`);
        setClient(clientRes.data);
      }
      
      // Fetch co-clients
      const coClientsRes = await axios.get(`${API}/projects/${projectId}/co-clients?t=${timestamp}`);
      setCoClients(coClientsRes.data);
      
      // Fetch project-level comments
      try {
        const commentsRes = await axios.get(`${API}/projects/${projectId}/comments?t=${timestamp}`);
        setProjectComments(commentsRes.data || []);
      } catch (err) {
        console.log('Project comments not available');
        setProjectComments([]);
      }
      
      // Handle deep link - check if there's a drawing query parameter
      const urlParams = new URLSearchParams(window.location.search);
      const drawingId = urlParams.get('drawing');
      if (drawingId) {
        setActiveTab('drawings');
        setHighlightedDrawingId(drawingId);
        
        // Scroll to the drawing after a short delay
        setTimeout(() => {
          const drawingElement = document.getElementById(`drawing-${drawingId}`);
          if (drawingElement) {
            drawingElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
            // Flash highlight effect
            drawingElement.classList.add('ring-4', 'ring-amber-400', 'ring-opacity-75');
            setTimeout(() => {
              drawingElement.classList.remove('ring-4', 'ring-amber-400', 'ring-opacity-75');
            }, 3000);
          }
        }, 500);
        
        // Clear the query parameter from URL
        window.history.replaceState({}, '', `/projects/${projectId}`);
      }
      setError(null); // Clear any previous errors
    } catch (error) {
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load project data';
      setError(errorMessage);
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

  // Project-level comment handler for ChatView
  const handleSendProjectComment = async ({ text, file, voiceNote }) => {
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('text', text || '');
    
    if (file) formData.append('file', file);
    if (voiceNote) formData.append('voice_note', voiceNote, 'voice_note.webm');

    await axios.post(`${API}/projects/${projectId}/comments`, formData, {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'multipart/form-data'
      }
    });

    // Refresh comments
    const commentsRes = await axios.get(`${API}/projects/${projectId}/comments`);
    setProjectComments(commentsRes.data || []);
  };

  const loadRecipientsForCategory = async (category) => {
    console.log('Loading recipients for category:', category);
    
    const recipients = [];
    
    // Always include the current user (owner) if they are the owner
    if (user && user.is_owner) {
      recipients.push({
        id: user.id || 'owner',
        name: user.name || 'Owner',
        type: 'owner',
        role: 'Owner'
      });
    }
    
    // Add client if available (project's client)
    if (client) {
      recipients.push({
        id: client.user_id || client.id,
        name: client.name || 'Project Client',
        type: 'client',
        role: 'Client'
      });
    }
    
    // Add team leader/project manager if assigned to this project
    if (teamLeader) {
      recipients.push({
        id: teamLeader.id,
        name: `${teamLeader.name} (Team Leader)`,
        type: 'team_leader',
        role: 'Team Leader'
      });
    }
    
    // Add PROJECT-SPECIFIC contractors from projectTeam (not all contractors)
    if (projectTeam && projectTeam.contractors && Array.isArray(projectTeam.contractors)) {
      projectTeam.contractors.forEach(contractor => {
        if (contractor && contractor.id && !recipients.find(r => r.id === contractor.id)) {
          recipients.push({
            id: contractor.user_id || contractor.id,
            name: `${contractor.name || 'Contractor'} (${contractor.contractor_type || 'Contractor'})`,
            type: 'contractor',
            role: contractor.contractor_type || 'Contractor'
          });
        }
      });
    }
    
    // Add PROJECT-SPECIFIC consultants from projectTeam
    if (projectTeam && projectTeam.consultants && Array.isArray(projectTeam.consultants)) {
      projectTeam.consultants.forEach(consultant => {
        if (consultant && consultant.id && !recipients.find(r => r.id === consultant.id)) {
          recipients.push({
            id: consultant.user_id || consultant.id,
            name: `${consultant.name || 'Consultant'} (${consultant.type || 'Consultant'})`,
            type: 'consultant',
            role: consultant.type || 'Consultant'
          });
        }
      });
    }
    
    // Add co-clients if any
    if (projectTeam && projectTeam.co_clients && Array.isArray(projectTeam.co_clients)) {
      projectTeam.co_clients.forEach(coClient => {
        if (coClient && coClient.id && !recipients.find(r => r.id === coClient.id)) {
          recipients.push({
            id: coClient.user_id || coClient.id,
            name: `${coClient.name || 'Co-Client'}`,
            type: 'co_client',
            role: 'Co-Client'
          });
        }
      });
    }
    
    console.log('Loaded project-specific recipients:', recipients);
    console.log('Total recipients:', recipients.length);
    
    setAvailableRecipients(recipients);
    setSelectedRecipients([]); // Reset selection
  };

  const handleToggleIssued = async (drawing) => {
    // Only allow issuing, not un-issuing (un-issue feature removed)
    if (drawing.is_issued) {
      toast.info('This drawing has already been issued');
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
    setRevisionAudioBlob(null);
    setRevisionFiles([]);
    setRevisionRecordingTime(0);
    setRevisionDialogOpen(true);
  };

  // Revision voice note functions
  const startRevisionRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      const chunks = [];
      
      recorder.ondataavailable = (e) => chunks.push(e.data);
      recorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setRevisionAudioBlob(blob);
        setRevisionIsRecording(false);
        stream.getTracks().forEach(track => track.stop());
      };
      
      setRevisionMediaRecorder(recorder);
      recorder.start();
      setRevisionIsRecording(true);
      setRevisionRecordingTime(0);
      
      // Update recording time
      const interval = setInterval(() => {
        setRevisionRecordingTime(prev => prev + 1);
      }, 1000);
      recorder.onstart = () => recorder._interval = interval;
      recorder.onstop = () => {
        clearInterval(recorder._interval);
        const blob = new Blob(chunks, { type: 'audio/webm' });
        setRevisionAudioBlob(blob);
        setRevisionIsRecording(false);
        stream.getTracks().forEach(track => track.stop());
      };
    } catch (error) {
      console.error('Revision recording error:', error);
      toast.error('Could not access microphone');
    }
  };

  const stopRevisionRecording = () => {
    if (revisionMediaRecorder && revisionMediaRecorder.state === 'recording') {
      revisionMediaRecorder.stop();
    }
  };

  const clearRevisionVoiceNote = () => {
    setRevisionAudioBlob(null);
    setRevisionRecordingTime(0);
  };

  const playRevisionVoiceNote = () => {
    if (revisionAudioBlob) {
      const audio = new Audio(URL.createObjectURL(revisionAudioBlob));
      audio.play();
    }
  };

  const handleRevisionFileChange = (e) => {
    const files = Array.from(e.target.files);
    setRevisionFiles(prev => [...prev, ...files]);
  };

  const removeRevisionFile = (index) => {
    setRevisionFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleRequestRevision = async (e) => {
    e.preventDefault();
    
    // Validate - need at least notes or voice note
    if (!revisionFormData.revision_notes.trim() && !revisionAudioBlob) {
      toast.error('Please provide revision notes or a voice note');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      
      // First, update the drawing with revision request
      await axios.put(`${API}/drawings/${selectedDrawing.id}`, {
        has_pending_revision: true,
        revision_notes: revisionFormData.revision_notes || '[Voice Note]',
        revision_due_date: revisionFormData.revision_due_date
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Upload voice note if present
      if (revisionAudioBlob) {
        const formData = new FormData();
        formData.append('voice_note', revisionAudioBlob, 'revision_voice_note.webm');
        formData.append('drawing_id', selectedDrawing.id);
        formData.append('type', 'revision_request');
        
        await axios.post(`${API}/drawings/${selectedDrawing.id}/voice-note`, formData, {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
      }
      
      // Upload reference files if present
      if (revisionFiles.length > 0) {
        const formData = new FormData();
        revisionFiles.forEach(file => {
          formData.append('files', file);
        });
        formData.append('type', 'revision_reference');
        
        await axios.post(`${API}/drawings/${selectedDrawing.id}/revision-files`, formData, {
          headers: { 
            Authorization: `Bearer ${token}`,
            'Content-Type': 'multipart/form-data'
          }
        });
      }
      
      toast.success('Revision requested successfully!');
      setRevisionDialogOpen(false);
      setRevisionAudioBlob(null);
      setRevisionFiles([]);
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
      
      // Try to open inline first, fallback to new tab
      try {
        // Create temporary iframe for PDF viewing (works on mobile)
        const iframe = document.createElement('iframe');
        iframe.style.position = 'fixed';
        iframe.style.top = '0';
        iframe.style.left = '0';
        iframe.style.width = '100%';
        iframe.style.height = '100%';
        iframe.style.zIndex = '9999';
        iframe.style.border = 'none';
        iframe.style.backgroundColor = '#000';
        iframe.src = blobUrl;
        
        // Add close button overlay
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '✕ Close PDF';
        closeBtn.style.position = 'fixed';
        closeBtn.style.top = '10px';
        closeBtn.style.right = '10px';
        closeBtn.style.zIndex = '10000';
        closeBtn.style.padding = '8px 16px';
        closeBtn.style.backgroundColor = '#fff';
        closeBtn.style.border = '1px solid #ccc';
        closeBtn.style.borderRadius = '4px';
        closeBtn.style.cursor = 'pointer';
        closeBtn.style.fontSize = '14px';
        closeBtn.style.fontWeight = 'bold';
        
        closeBtn.onclick = () => {
          document.body.removeChild(iframe);
          document.body.removeChild(closeBtn);
          window.URL.revokeObjectURL(blobUrl);
        };
        
        document.body.appendChild(iframe);
        document.body.appendChild(closeBtn);
        toast.success('PDF opened successfully');
        
      } catch (error) {
        // Fallback to download if iframe fails
        console.log('Iframe failed, downloading instead');
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `${drawing.name}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);
        toast.success('PDF downloaded');
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
    // Allow submission if there's text, voice note, or file attachments
    if (!newCommentText.trim() && !audioBlob && referenceFiles.length === 0) {
      toast.error('Please enter a comment, record a voice note, or attach file(s)');
      return;
    }

    setSubmittingComment(true);

    try {
      let commentId = editingComment?.id;
      
      if (editingComment) {
        // Update existing comment
        await axios.put(`${API}/drawings/comments/${editingComment.id}`, {
          comment_text: newCommentText
        });
        toast.success('Comment updated');
      } else {
        // Create new comment (allow empty text if there's a voice note or files)
        const commentText = newCommentText.trim() || 
                           (audioBlob ? '[Voice Note]' : '') || 
                           (referenceFiles.length > 0 ? `[${referenceFiles.length} File(s) Attached]` : '');
        const response = await axios.post(`${API}/drawings/${selectedCommentDrawing.id}/comments`, {
          drawing_id: selectedCommentDrawing.id,
          comment_text: commentText,
          requires_revision: markForRevision // Add revision flag
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
      
      // If there are reference files, upload them
      if (referenceFiles.length > 0 && commentId) {
        const formData = new FormData();
        referenceFiles.forEach((file, index) => {
          formData.append('files', file);
        });
        
        await axios.post(`${API}/drawings/comments/${commentId}/upload-reference`, formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        toast.success(`📎 ${referenceFiles.length} file(s) attached!`);
      }
      
      setNewCommentText('');
      setEditingComment(null);
      setReferenceFiles([]); // Clear reference files after successful submission
      setMarkForRevision(false); // Clear revision flag
      clearVoiceNote(); // Clear voice note after successful submission
      await fetchComments(selectedCommentDrawing.id);
      
      // Handle voice note upload if present
      if (audioBlob && commentId) {
        await uploadVoiceNote(commentId);
      }
      
      // Refresh project data to update comment counts
      await fetchProjectData();
      
      // Close dialog after posting comment (Issue #2)
      setCommentDialogOpen(false);
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to save comment'));
    } finally {
      setSubmittingComment(false);
    }
  };

  // Voice Recording Functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      
      recorder.onstart = () => {
        setIsRecording(true);
        setRecordingTime(0);
      };
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          setAudioBlob(event.data);
        }
      };
      
      recorder.onstop = () => {
        setIsRecording(false);
        stream.getTracks().forEach(track => track.stop());
      };
      
      setMediaRecorder(recorder);
      recorder.start();
      
      // Start timer
      const timer = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);
      
      // Store timer to clear later
      recorder.timer = timer;
      
    } catch (error) {
      toast.error('Could not access microphone');
      console.error('Recording error:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      mediaRecorder.stop();
      clearInterval(mediaRecorder.timer);
    }
  };

  const clearVoiceNote = () => {
    setAudioBlob(null);
    setRecordingTime(0);
    setPlayingAudio(false);
  };

  const playVoiceNote = () => {
    if (audioBlob) {
      const audio = new Audio(URL.createObjectURL(audioBlob));
      setPlayingAudio(true);
      audio.play();
      audio.onended = () => setPlayingAudio(false);
    }
  };

  const uploadVoiceNote = async (commentId) => {
    if (!audioBlob) return;
    
    try {
      const formData = new FormData();
      formData.append('voice_note', audioBlob, 'voice_note.webm');
      
      await axios.post(`${API}/drawings/comments/${commentId}/upload-voice`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      toast.success('🎙️ Voice note attached!');
      clearVoiceNote();
      
    } catch (error) {
      toast.error('Failed to upload voice note');
      console.error('Voice upload error:', error);
    }
  };

  const handleIssueDrawingWithRecipients = async () => {
    try {
      if (selectedRecipients.length === 0) {
        toast.error('Please select at least one recipient');
        return;
      }
      
      const token = localStorage.getItem('token');
      
      // Issue the drawing
      await axios.put(`${API}/drawings/${selectedIssueDrawing.id}`, {
        is_issued: true,
        issued_date: new Date().toISOString(),
        status: 'issued',
        recipients: selectedRecipients.map(r => ({ id: r.id, type: r.type }))
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Send notifications to selected recipients
      try {
        await axios.post(`${API}/drawings/${selectedIssueDrawing.id}/notify-issue`, {
          recipient_ids: selectedRecipients.map(r => r.id),
          drawing_name: selectedIssueDrawing.name,
          drawing_category: selectedIssueDrawing.category
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
      } catch (notificationError) {
        console.warn('Failed to send notifications:', notificationError);
      }
      
      // Unlock next drawing in sequence
      await unlockNextDrawing(selectedIssueDrawing.sequence_number);
      
      toast.success(`Drawing issued to ${selectedRecipients.length} recipient(s)`);
      setIssueDialogOpen(false);
      setSelectedIssueDrawing(null);
      setSelectedRecipients([]);
      fetchProjectData();
      
    } catch (error) {
      console.error('Error issuing drawing:', error);
      toast.error(formatErrorMessage(error, 'Failed to issue drawing'));
    }
  };
  
  const unlockNextDrawing = async (currentSequence) => {
    try {
      const token = localStorage.getItem('token');
      
      // Find and activate the next drawing in sequence
      await axios.post(`${API}/projects/${projectId}/unlock-next-drawing`, {
        current_sequence: currentSequence
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      console.log(`Unlocked next drawing after sequence ${currentSequence}`);
      
    } catch (error) {
      console.warn('Error unlocking next drawing:', error);
      // Don't show error to user as this is not critical
    }
  };
  
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
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

  // Co-Client handlers
  const handleAddCoClient = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/projects/${projectId}/co-clients`, {
        ...coClientFormData,
        project_id: projectId,
        main_client_id: project.client_id
      });
      toast.success('Co-client added successfully!');
      setCoClientDialogOpen(false);
      resetCoClientForm();
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to add co-client'));
    }
  };

  const handleRemoveCoClient = async (coClientId) => {
    if (!confirm('Are you sure you want to remove this co-client?')) return;
    
    try {
      await axios.delete(`${API}/co-clients/${coClientId}`);
      toast.success('Co-client removed successfully');
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to remove co-client'));
    }
  };

  const resetCoClientForm = () => {
    setCoClientFormData({
      name: '',
      email: '',
      phone: '',
      relationship: 'Family Member',
      notes: ''
    });
  };

  // Contractor handlers
  const handleAssignContractor = async () => {
    if (!selectedContractorType) {
      toast.error('Please select a contractor type');
      return;
    }

    try {
      if (inviteNewContractor) {
        // First create the contractor, then assign
        if (!newContractorData.name || !newContractorData.phone) {
          toast.error('Name and phone are required for new contractor');
          return;
        }
        
        const createRes = await axios.post(`${API}/contractors`, {
          name: newContractorData.name,
          phone: newContractorData.phone,
          email: newContractorData.email || null,
          contractor_type: selectedContractorType
        });
        
        const newContractor = createRes.data;
        
        await axios.post(`${API}/projects/${projectId}/assign-contractor`, {
          contractor_id: newContractor.id,
          contractor_type: selectedContractorType,
          send_notification: true
        });
        
        toast.success(`${newContractorData.name} invited and assigned as ${selectedContractorType} contractor!`);
      } else {
        if (!selectedContractorId) {
          toast.error('Please select a contractor');
          return;
        }
        
        await axios.post(`${API}/projects/${projectId}/assign-contractor`, {
          contractor_id: selectedContractorId,
          contractor_type: selectedContractorType,
          send_notification: true
        });
        
        toast.success(`Contractor assigned as ${selectedContractorType}!`);
      }
      
      setAssignContractorDialogOpen(false);
      resetContractorForm();
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to assign contractor'));
    }
  };

  const handleUnassignContractor = async (contractorType) => {
    if (!confirm(`Remove ${contractorType} contractor from this project?`)) return;
    
    try {
      await axios.delete(`${API}/projects/${projectId}/unassign-contractor/${contractorType}`);
      toast.success(`${contractorType} contractor removed from project`);
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to remove contractor'));
    }
  };

  const resetContractorForm = () => {
    setSelectedContractorType('');
    setSelectedContractorId('');
    setInviteNewContractor(false);
    setNewContractorData({ name: '', phone: '', email: '' });
  };

  // Consultant handlers
  const handleAssignConsultant = async () => {
    if (!selectedConsultantType) {
      toast.error('Please select a consultant type');
      return;
    }

    try {
      if (inviteNewConsultant) {
        // Create contact-only consultant assignment
        if (!newConsultantData.name || !newConsultantData.phone) {
          toast.error('Name and phone are required');
          return;
        }
        
        await axios.post(`${API}/projects/${projectId}/assign-consultant`, {
          consultant_type: selectedConsultantType,
          consultant_name: newConsultantData.name,
          consultant_phone: newConsultantData.phone,
          consultant_email: newConsultantData.email || null,
          send_notification: false  // No notification for contact-only
        });
        
        toast.success(`${newConsultantData.name} added as ${selectedConsultantType} consultant!`);
      } else {
        if (!selectedConsultantId) {
          toast.error('Please select a consultant');
          return;
        }
        
        await axios.post(`${API}/projects/${projectId}/assign-consultant`, {
          consultant_id: selectedConsultantId,
          consultant_type: selectedConsultantType,
          send_notification: true
        });
        
        toast.success(`Consultant assigned as ${selectedConsultantType}!`);
      }
      
      setAssignConsultantDialogOpen(false);
      resetConsultantForm();
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to assign consultant'));
    }
  };

  const handleUnassignConsultant = async (consultantType) => {
    if (!confirm(`Remove ${consultantType} consultant from this project?`)) return;
    
    try {
      await axios.delete(`${API}/projects/${projectId}/unassign-consultant/${consultantType}`);
      toast.success(`${consultantType} consultant removed from project`);
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to remove consultant'));
    }
  };

  const resetConsultantForm = () => {
    setSelectedConsultantType('');
    setSelectedConsultantId('');
    setInviteNewConsultant(false);
    setNewConsultantData({ name: '', phone: '', email: '' });
  };

  // Drawing N/A handler
  const handleMarkAsNotApplicable = async (drawingId) => {
    if (!confirm('Mark this drawing as Not Applicable? It will be removed from the drawing list for this project.')) {
      return;
    }
    
    try {
      await axios.patch(`${API}/drawings/${drawingId}/mark-not-applicable`);
      toast.success('Drawing marked as not applicable');
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to mark drawing as N/A'));
    }
  };

  // Project action handlers
  const handleEditProject = () => {
    navigate('/projects', { state: { editProjectId: projectId } });
  };

  const handleRequestDeleteOtp = async () => {
    setSendingOtp(true);
    try {
      await axios.post(`${API}/projects/${projectId}/request-deletion-otp`);
      toast.success('OTP sent to your email');
      setDeleteOtpSent(true);
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to send OTP'));
    } finally {
      setSendingOtp(false);
    }
  };

  const handleDeleteProject = async () => {
    // OTP verification temporarily suspended
    try {
      await axios.delete(`${API}/projects/${projectId}`);
      toast.success('Project deleted successfully');
      setDeleteDialogOpen(false);
      setDeleteOtpSent(false);
      setDeleteOtp('');
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
    if (selectedFiles.length === 0) {
      toast.error('Please select PDF file(s)');
      return;
    }
    
    // Validate file sizes (50MB limit for better UX)
    const maxSize = 50 * 1024 * 1024; // 50MB
    const oversizedFiles = selectedFiles.filter(file => file.size > maxSize);
    if (oversizedFiles.length > 0) {
      toast.error(`File(s) too large: ${oversizedFiles.map(f => f.name).join(', ')}. Maximum size is 50MB per file.`);
      return;
    }
    
    setUploadingFile(true);
    setUploadProgress(0);
    
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      
      selectedFiles.forEach((file, index) => {
        formData.append('files', file);
      });
      formData.append('drawing_id', selectedFileDrawing.id);
      formData.append('upload_type', uploadType);
      
      console.log(`Starting upload of ${selectedFiles.length} file(s)...`, {
        fileNames: selectedFiles.map(f => f.name),
        totalSize: selectedFiles.reduce((sum, f) => sum + f.size, 0),
        uploadType
      });
      
      // Upload files to backend with progress tracking
      const uploadResponse = await axios.post(`${API}/drawings/upload`, formData, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        },
        timeout: 300000, // 5 minute timeout for multiple large files
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
          console.log(`Upload progress: ${percentCompleted}%`);
        }
      });
      
      console.log('Upload response received:', uploadResponse.data);
      const uploadedFiles = uploadResponse.data.uploaded_files;
      
      // Set progress to 100% briefly before updating status
      setUploadProgress(100);
      
      // Use the first uploaded file as the main file URL for backward compatibility
      const primaryFileUrl = uploadedFiles[0]?.url;
      
      // Update drawing with file URL
      const updatePayload = uploadType === 'issue' 
        ? { 
            under_review: true, 
            file_url: primaryFileUrl,
            has_pending_revision: false  // Explicitly set to false
          }
        : { 
            has_pending_revision: false, 
            under_review: true,  // Resolved goes back to review state
            file_url: primaryFileUrl  // Update with new resolved file
          };
      
      if (uploadType === 'resolve') {
        // Add to revision_file_urls array
        const current_urls = selectedFileDrawing.revision_file_urls || [];
        const new_urls = uploadedFiles.map(file => file.url);
        updatePayload.revision_file_urls = [...current_urls, ...new_urls];
      }
      
      console.log('Updating drawing status...');
      await axios.put(`${API}/drawings/${selectedFileDrawing.id}`, updatePayload, {
        headers: { Authorization: `Bearer ${token}` },
        timeout: 15000 // 15 second timeout
      });
      
      console.log('Upload complete, showing success message');
      const message = uploadType === 'issue' 
        ? `${selectedFiles.length} drawing(s) uploaded for review!`
        : `${selectedFiles.length} revision(s) resolved with PDF(s)!`;
      toast.success(message);
      
      // Reset states
      setUploadDialogOpen(false);
      setSelectedFiles([]);
      setSelectedFileDrawing(null);
      setUploadProgress(0);
      
      // Refresh data
      await fetchProjectData();
    } catch (error) {
      console.error('File upload error:', error);
      setUploadProgress(0);
      
      if (error.code === 'ECONNABORTED') {
        toast.error('Upload timeout - files may be too large. Try compressing them or uploading fewer files.');
      } else if (error.response?.status === 413) {
        toast.error('Files too large. Maximum size is 50MB per file.');
      } else {
        toast.error(formatErrorMessage(error, 'Failed to upload file(s)'));
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
    // Filter out N/A drawings
    return drawings.filter(d => d.category === category && !d.is_not_applicable);
  };

  const getPendingDrawingsSortedByUrgency = () => {
    // Filter out N/A drawings
    const pending = drawings.filter(d => (!d.is_issued || d.has_pending_revision) && !d.is_not_applicable);
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

  // DrawingCard component extracted to /components/project/DrawingCard.jsx

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <LoadingState message="Loading project..." />
      </Layout>
    );
  }

  // Show error state with retry option
  if (error) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <ErrorState 
          message={error} 
          onRetry={() => {
            setError(null);
            setLoading(true);
            fetchProjectData();
          }} 
        />
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
                
                <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900 mb-1 sm:mb-2 break-words">{project.title}</h1>
                {client && (
                  <p className="text-sm sm:text-base lg:text-lg text-slate-600 truncate">{client.name}</p>
                )}
                
                {/* Team Leader */}
                {teamLeader && (
                  <div 
                    className="mt-2 sm:mt-3 flex items-center gap-2 px-3 py-2 bg-orange-50 rounded-lg border border-orange-200 w-fit cursor-pointer hover:bg-orange-100 hover:border-orange-300 transition-colors"
                    onClick={() => navigate(`/team/${teamLeader.id}`)}
                  >
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

              {/* Settings Menu - Only for Owner/Team Leader (Mobile-friendly dropdown) */}
              {(permissions.can_edit_project || permissions.can_archive_project || permissions.can_delete_project) && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" className="h-9 w-9 p-0">
                      <Edit className="w-4 h-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end" className="w-48">
                    {permissions.can_edit_project && (
                      <DropdownMenuItem onClick={handleEditProject}>
                        <Edit className="w-4 h-4 mr-2" />
                        Edit Project
                      </DropdownMenuItem>
                    )}
                    {!project.archived && permissions.can_archive_project && (
                      <DropdownMenuItem onClick={() => setArchiveDialogOpen(true)} className="text-orange-600">
                        <Calendar className="w-4 h-4 mr-2" />
                        Archive Project
                      </DropdownMenuItem>
                    )}
                    {permissions.can_delete_project && (
                      <DropdownMenuItem onClick={() => setDeleteDialogOpen(true)} className="text-red-600">
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete Project
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-8 w-full">
            <TabsTrigger value="urgent" className="text-xs sm:text-sm">Urgent</TabsTrigger>
            <TabsTrigger value="issued" className="text-xs sm:text-sm">Issued</TabsTrigger>
            <TabsTrigger value="drawings" className="text-xs sm:text-sm">All</TabsTrigger>
            <TabsTrigger value="chat" className="text-xs sm:text-sm relative">
              Chat
              {projectComments.length > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center">
                  {projectComments.length}
                </span>
              )}
            </TabsTrigger>
            <TabsTrigger value="info" className="text-xs sm:text-sm">Info</TabsTrigger>
            <TabsTrigger value="brands" className="text-xs sm:text-sm">Brands</TabsTrigger>
            <TabsTrigger value="team" className="text-xs sm:text-sm">Team</TabsTrigger>
            <TabsTrigger value="coclients" className="text-xs sm:text-sm">Co-Clients</TabsTrigger>
          </TabsList>

          {/* Issued Drawings Tab */}
          <TabsContent value="issued" className="mt-4 sm:mt-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-sm flex items-center gap-2">
                  <Check className="w-4 h-4 text-green-600" />
                  Issued Drawings
                </CardTitle>
              </CardHeader>
              <CardContent>
                {drawings.filter(d => d.is_issued && !d.is_not_applicable).length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <Check className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                    <p className="text-sm">No drawings issued yet</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {[...drawings.filter(d => d.is_issued && !d.is_not_applicable)]
                      .sort((a, b) => {
                        const dateA = a.issued_date ? new Date(a.issued_date) : new Date(0);
                        const dateB = b.issued_date ? new Date(b.issued_date) : new Date(0);
                        return dateB - dateA;
                      })
                      .map(drawing => (
                        <div key={drawing.id} className="bg-green-50 p-3 rounded-lg border border-green-100">
                          <div className="flex items-center justify-between">
                            <div className="flex-1 min-w-0 mr-2">
                              <p className="font-medium text-sm truncate">{drawing.name}</p>
                              <p className="text-xs text-slate-500">{drawing.category} • Rev {drawing.current_revision || 0}</p>
                              {drawing.issued_date && (
                                <p className="text-xs text-green-600">
                                  Issued: {new Date(drawing.issued_date).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' })}
                                </p>
                              )}
                            </div>
                            <div className="flex gap-1 shrink-0">
                              {drawing.file_url && (
                                <>
                                  <Button size="sm" variant="ghost" onClick={() => handleViewDrawing(drawing)} title="View">
                                    <Eye className="w-4 h-4" />
                                  </Button>
                                  <Button size="sm" variant="ghost" onClick={() => handleDownloadDrawing(drawing)} title="Download">
                                    <Download className="w-4 h-4" />
                                  </Button>
                                </>
                              )}
                              <Button 
                                size="sm" 
                                variant="ghost" 
                                onClick={() => navigate(`/projects/${projectId}/drawing/${drawing.id}`)} 
                                title="View Details & Comments"
                              >
                                <MessageSquare className="w-4 h-4" />
                              </Button>
                              <Button 
                                size="sm" 
                                variant="ghost"
                                onClick={() => setShowRevisionHistory(prev => ({...prev, [drawing.id]: !prev[drawing.id]}))}
                                title="Revision History"
                              >
                                <Clock className="w-4 h-4" />
                              </Button>
                              {/* Request Revision on issued drawing */}
                              <Button 
                                size="sm" 
                                variant="outline"
                                className="text-orange-600 border-orange-300 hover:bg-orange-50"
                                onClick={() => handleOpenRevisionDialog(drawing)}
                                title="Request Revision"
                              >
                                <RefreshCw className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                          {/* Revision History Expandable */}
                          {showRevisionHistory[drawing.id] && drawing.revision_history && drawing.revision_history.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-green-200">
                              <p className="text-xs font-medium text-slate-600 mb-2">Revision History:</p>
                              <div className="space-y-1">
                                {drawing.revision_history.map((rev, idx) => (
                                  <div key={idx} className="flex items-center justify-between text-xs bg-white p-2 rounded">
                                    <span className="text-slate-600">Rev {rev.revision || idx}</span>
                                    <span className="text-slate-500">{rev.date ? new Date(rev.date).toLocaleDateString('en-IN') : 'N/A'}</span>
                                    {rev.file_url && (
                                      <Button 
                                        size="sm" 
                                        variant="ghost" 
                                        className="h-6 px-2"
                                        onClick={() => window.open(`${BACKEND_URL}${rev.file_url}`, '_blank')}
                                      >
                                        <Eye className="w-3 h-3" />
                                      </Button>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Project Chat Tab - WhatsApp Style */}
          <TabsContent value="chat" className="mt-4 sm:mt-6">
            <Card className="overflow-hidden">
              <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-4 py-3">
                <h3 className="text-white font-medium text-sm">Project Discussion</h3>
                <p className="text-purple-200 text-xs">{projectComments.length} {projectComments.length === 1 ? 'message' : 'messages'}</p>
              </div>
              <div className="h-[400px]">
                <ChatView
                  messages={projectComments}
                  currentUserId={user?.id}
                  loading={loadingProjectComments}
                  onSendMessage={handleSendProjectComment}
                  placeholder="Type a message..."
                  emptyStateText="No messages yet"
                  emptyStateSubtext="Start the project discussion"
                />
              </div>
            </Card>
          </TabsContent>

          {/* Urgent Drawings Tab - Sorted by Due Date */}
          <TabsContent value="urgent" className="mt-4 sm:mt-6">
            {/* Pending Approval Section - Owner can approve drawings */}
            {(() => {
              const pendingApproval = drawings.filter(d => 
                d.under_review && !d.is_approved && !d.has_pending_revision && !d.is_not_applicable && d.file_url
              );
              
              if (pendingApproval.length === 0) return null;
              
              return (
                <Card className="border-amber-200 bg-amber-50 mb-6">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm flex items-center gap-2 text-amber-700">
                      <Clock className="w-4 h-4" />
                      Pending Approval
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {pendingApproval.map(drawing => (
                      <div key={drawing.id} className="bg-white p-3 rounded-lg flex items-center justify-between">
                        <div className="flex-1 min-w-0 mr-2">
                          <p className="font-medium text-sm truncate">{drawing.name}</p>
                          <p className="text-xs text-slate-500">{drawing.category}</p>
                        </div>
                        <div className="flex gap-2 shrink-0">
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => handleViewPDF(drawing)}
                            title="View"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            variant="outline" 
                            onClick={() => handleDownloadPDF(drawing)}
                            title="Download"
                          >
                            <Download className="w-4 h-4" />
                          </Button>
                          <Button 
                            size="sm" 
                            onClick={() => handleApproveDrawing(drawing)} 
                            className="bg-green-600 hover:bg-green-700"
                          >
                            <Check className="w-4 h-4 mr-1" />
                            Approve
                          </Button>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              );
            })()}

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
                            {/* Issue button - only shown when not issued and no pending revision */}
                            {!drawing.is_issued && !drawing.has_pending_revision && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleToggleIssued(drawing)}
                                className="flex-1 sm:flex-none text-xs h-8"
                              >
                                Issue
                              </Button>
                            )}
                            
                            {/* Comment/Revision button */}
                            {(drawing.is_issued || drawing.has_pending_revision || drawing.revision_count > 0) && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  if (drawing.has_pending_revision) {
                                    // Resolve function - upload revised files
                                    setUploadType('resolve');
                                    setSelectedFileDrawing(drawing);
                                    setUploadDialogOpen(true);
                                  } else {
                                    // Open comment dialog for revision feedback
                                    handleOpenComments(drawing);
                                  }
                                }}
                                className={`flex-1 sm:flex-none text-xs h-8 ${
                                  drawing.has_pending_revision ? "border-green-500 text-green-600" : 
                                  "border-amber-500 text-amber-600"
                                }`}
                              >
                                {drawing.has_pending_revision ? "Resolve" : "Comment"}
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
                            
                            {/* Mark as N/A Button - Show for non-issued drawings */}
                            {!drawing.is_issued && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleMarkAsNotApplicable(drawing.id)}
                                className="flex-1 sm:flex-none text-xs h-8 border-slate-400 text-slate-600 hover:bg-slate-50"
                                title="Mark this drawing as not applicable for this project"
                              >
                                N/A
                              </Button>
                            )}
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
                        Drawings completed
                      </p>
                      <p className="text-xs text-green-700">View all in &quot;All Drawings&quot; tab</p>
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
                {/* Progress: issued / (total - N/A) */}
                {(() => {
                  const issued = drawings.filter(d => d.is_issued && !d.is_not_applicable).length;
                  const total = drawings.filter(d => !d.is_not_applicable).length;
                  const progress = total > 0 ? ((issued / total) * 100).toFixed(1) : 0;
                  const revisions = drawings.filter(d => d.has_pending_revision && !d.is_not_applicable).length;
                  return (
                    <div className="mt-2">
                      <div className="flex items-center gap-3 text-sm">
                        <span className="font-medium text-green-600">{issued} issued</span>
                        {revisions > 0 && <span className="text-amber-600">{revisions} revisions</span>}
                      </div>
                      <div className="mt-2 h-2 bg-slate-100 rounded-full overflow-hidden w-full max-w-xs">
                        <div 
                          className="h-full bg-green-500 rounded-full transition-all duration-500"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <p className="text-xs text-slate-500 mt-1">{progress}% complete</p>
                    </div>
                  );
                })()}
              </div>
              {/* Add Drawing button - Only for owner/team leader */}
              {permissions.can_create_drawing && (
              <Button 
                onClick={() => setDrawingDialogOpen(true)}
                className="bg-orange-500 hover:bg-orange-600 w-full sm:w-auto"
                size="sm"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Drawing
              </Button>
              )}
            </div>

            {/* Search Bar */}
            <div className="relative mb-4">
              <input
                type="text"
                placeholder="Search drawings by name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-2 pl-10 border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
              <FileText className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  <X className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Drawings by Category */}
            {DRAWING_CATEGORIES.filter(cat => project.project_types?.includes(cat)).map((category) => {
              const allCategoryDrawings = getDrawingsByCategory(category);
              const categoryDrawings = searchQuery.trim() 
                ? allCategoryDrawings.filter(d => d.name.toLowerCase().includes(searchQuery.toLowerCase()))
                : allCategoryDrawings;
              
              if (searchQuery.trim() && categoryDrawings.length === 0) return null;
              
              return (
                <div key={category} className="mb-8">
                  <div className="flex items-center gap-3 mb-4">
                    <FileText className="w-5 h-5 text-orange-500" />
                    <h3 className="text-xl font-semibold text-slate-900">{category}</h3>
                  </div>
                  
                  {categoryDrawings.length > 0 ? (
                    <div className="space-y-3">
                      {categoryDrawings.map((drawing) => (
                        <DrawingCard 
                          key={drawing.id} 
                          drawing={drawing}
                          user={user}
                          permissions={permissions}
                          projectContractors={projectTeam.contractors || []}
                          onToggleIssued={handleToggleIssued}
                          onResolveRevision={handleResolveRevision}
                          onOpenRevisionDialog={handleOpenRevisionDialog}
                          onApproveDrawing={handleApproveDrawing}
                          onOpenIssueDialog={(drawing) => {
                            setSelectedIssueDrawing(drawing);
                            loadRecipientsForCategory(drawing.category);
                            setIssueDialogOpen(true);
                          }}
                          onViewPDF={handleViewPDF}
                          onDownloadPDF={handleDownloadPDF}
                          onOpenComments={handleOpenComments}
                          onMarkAsNotApplicable={handleMarkAsNotApplicable}
                          onProgressUpdate={fetchProjectData}
                        />
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="p-8 text-center">
                        <p className="text-slate-500">No {category.toLowerCase()} drawings yet</p>
                        {permissions.can_create_drawing && (
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
                        )}
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

          {/* Team Tab - Contractors & Consultants */}
          <TabsContent value="team" className="mt-6">
            <div className="space-y-6">
              {/* Team Leader Access Management */}
              {(user?.is_owner || user?.role === 'team_leader') && (
                <TeamLeaderAccess 
                  projectId={projectId} 
                  projectName={project.title}
                  user={user}
                  onAccessChange={fetchProjectData}
                />
              )}
              
              {/* Contractors Section */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <HardHat className="w-5 h-5 text-orange-600" />
                        Contractors
                      </CardTitle>
                      <p className="text-sm text-slate-600 mt-1">
                        Contractors assigned to this project
                      </p>
                    </div>
                    {(user?.is_owner || user?.role === 'team_member') && (
                      <Button 
                        onClick={() => setAssignContractorDialogOpen(true)}
                        className="bg-orange-500 hover:bg-orange-600"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Contractor
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {projectTeam.contractors && projectTeam.contractors.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {projectTeam.contractors.map((contractor) => (
                        <Card key={contractor.id || contractor.assigned_type} className="border border-orange-200 bg-orange-50/30">
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="px-2 py-0.5 text-xs bg-orange-100 text-orange-700 rounded font-medium">
                                    {contractor.assigned_type || contractor.contractor_type}
                                  </span>
                                </div>
                                <h4 className="font-medium text-slate-900">{contractor.name}</h4>
                                <div className="space-y-1 text-sm text-slate-600 mt-2">
                                  {contractor.phone && (
                                    <p className="flex items-center gap-2">
                                      <Phone className="w-3 h-3" /> {contractor.phone}
                                    </p>
                                  )}
                                  {contractor.email && (
                                    <p className="flex items-center gap-2">
                                      <Mail className="w-3 h-3" /> {contractor.email}
                                    </p>
                                  )}
                                  {contractor.company_name && (
                                    <p className="flex items-center gap-2">
                                      <Building className="w-3 h-3" /> {contractor.company_name}
                                    </p>
                                  )}
                                </div>
                              </div>
                              {(user?.is_owner || user?.role === 'team_member') && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleUnassignContractor(contractor.assigned_type)}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <HardHat className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                      <p className="text-slate-500">No contractors assigned yet</p>
                      {(user?.is_owner || user?.role === 'team_member') && (
                        <p className="text-sm text-slate-400 mt-1">
                          Add contractors to manage project execution
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Consultants Section */}
              <Card>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Briefcase className="w-5 h-5 text-blue-600" />
                        Consultants
                      </CardTitle>
                      <p className="text-sm text-slate-600 mt-1">
                        Professional consultants engaged for this project
                      </p>
                    </div>
                    {(user?.is_owner || user?.role === 'team_member') && (
                      <Button 
                        onClick={() => setAssignConsultantDialogOpen(true)}
                        className="bg-blue-500 hover:bg-blue-600"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Consultant
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {projectTeam.consultants && projectTeam.consultants.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {projectTeam.consultants.map((consultant, idx) => (
                        <Card key={consultant.id || idx} className="border border-blue-200 bg-blue-50/30">
                          <CardContent className="p-4">
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded font-medium">
                                    {consultant.assigned_type || consultant.type}
                                  </span>
                                  {consultant.is_contact_only && (
                                    <span className="px-2 py-0.5 text-xs bg-slate-100 text-slate-600 rounded">
                                      Contact Only
                                    </span>
                                  )}
                                </div>
                                <h4 className="font-medium text-slate-900">{consultant.name}</h4>
                                <div className="space-y-1 text-sm text-slate-600 mt-2">
                                  {consultant.phone && (
                                    <p className="flex items-center gap-2">
                                      <Phone className="w-3 h-3" /> {consultant.phone}
                                    </p>
                                  )}
                                  {consultant.email && (
                                    <p className="flex items-center gap-2">
                                      <Mail className="w-3 h-3" /> {consultant.email}
                                    </p>
                                  )}
                                </div>
                              </div>
                              {(user?.is_owner || user?.role === 'team_member') && (
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleUnassignConsultant(consultant.assigned_type)}
                                  className="text-red-600 hover:text-red-700 hover:bg-red-50"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              )}
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Briefcase className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                      <p className="text-slate-500">No consultants assigned yet</p>
                      {(user?.is_owner || user?.role === 'team_member') && (
                        <p className="text-sm text-slate-400 mt-1">
                          Engage consultants for specialized expertise
                        </p>
                      )}
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* Co-Clients Tab */}
          <TabsContent value="coclients" className="mt-6">
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>Co-Clients / Associate Clients</CardTitle>
                    <p className="text-sm text-slate-600 mt-1">
                      Additional people who can view and comment on this project (without access to financial details)
                    </p>
                  </div>
                  {(user?.is_owner || (client && user?.email === client.email)) && (
                    <Button 
                      onClick={() => setCoClientDialogOpen(true)}
                      className="bg-orange-500 hover:bg-orange-600"
                    >
                      <Plus className="w-4 h-4 mr-2" />
                      Add Co-Client
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                {coClients.length > 0 ? (
                  <div className="space-y-3">
                    {coClients.map((coClient) => (
                      <Card key={coClient.id} className="border border-slate-200">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-2">
                                <h4 className="font-medium text-slate-900">{coClient.name}</h4>
                                <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded">
                                  {coClient.relationship}
                                </span>
                              </div>
                              <div className="space-y-1 text-sm text-slate-600">
                                <p className="flex items-center gap-2">
                                  <span className="font-medium">Email:</span> {coClient.email}
                                </p>
                                {coClient.phone && (
                                  <p className="flex items-center gap-2">
                                    <span className="font-medium">Phone:</span> {coClient.phone}
                                  </p>
                                )}
                                {coClient.notes && (
                                  <p className="flex items-center gap-2">
                                    <span className="font-medium">Notes:</span> {coClient.notes}
                                  </p>
                                )}
                                <p className="text-xs text-slate-500 mt-2">
                                  Added on {new Date(coClient.created_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            {(user?.is_owner || (client && user?.email === client.email)) && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleRemoveCoClient(coClient.id)}
                                className="text-red-600 hover:text-red-700 hover:bg-red-50"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            )}
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <Users className="w-16 h-16 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-500">No co-clients added yet</p>
                    {(user?.is_owner || (client && user?.email === client.email)) && (
                      <p className="text-sm text-slate-400 mt-2">
                        Add co-clients to give others view/comment access to this project
                      </p>
                    )}
                  </div>
                )}
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
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Request Revision</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleRequestRevision} className="space-y-4">
              <div>
                <Label className="text-slate-600 mb-2 block">Drawing</Label>
                <p className="text-slate-900 font-medium">{selectedDrawing?.name}</p>
              </div>

              <div>
                <Label>What revisions are required?</Label>
                <textarea
                  className="flex min-h-[100px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={revisionFormData.revision_notes}
                  onChange={(e) => setRevisionFormData({ ...revisionFormData, revision_notes: e.target.value })}
                  placeholder="Describe the revisions needed in detail... (optional if using voice note)"
                />
              </div>

              {/* Voice Note Section */}
              <div className="border rounded-lg p-3 bg-slate-50">
                <Label className="mb-2 block">Voice Note (Optional)</Label>
                <div className="flex items-center gap-2">
                  {!revisionIsRecording && !revisionAudioBlob && (
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={startRevisionRecording}
                      className="flex items-center gap-2"
                    >
                      <Mic className="w-4 h-4" />
                      Record Voice Note
                    </Button>
                  )}
                  
                  {revisionIsRecording && (
                    <div className="flex items-center gap-2">
                      <div className="flex items-center gap-1 text-red-500">
                        <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
                        Recording: {Math.floor(revisionRecordingTime / 60)}:{(revisionRecordingTime % 60).toString().padStart(2, '0')}
                      </div>
                      <Button
                        type="button"
                        variant="destructive"
                        size="sm"
                        onClick={stopRevisionRecording}
                      >
                        <Square className="w-4 h-4 mr-1" />
                        Stop
                      </Button>
                    </div>
                  )}
                  
                  {revisionAudioBlob && !revisionIsRecording && (
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="bg-green-50 text-green-700">
                        Voice note recorded ({Math.floor(revisionRecordingTime / 60)}:{(revisionRecordingTime % 60).toString().padStart(2, '0')})
                      </Badge>
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={playRevisionVoiceNote}
                      >
                        <Play className="w-4 h-4" />
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={clearRevisionVoiceNote}
                        className="text-red-500"
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </div>

              {/* File Attachments Section */}
              <div className="border rounded-lg p-3 bg-slate-50">
                <Label className="mb-2 block">Reference Files (Optional)</Label>
                <div className="space-y-2">
                  <input
                    type="file"
                    multiple
                    onChange={handleRevisionFileChange}
                    className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-amber-50 file:text-amber-700 hover:file:bg-amber-100"
                    accept=".pdf,.jpg,.jpeg,.png,.dwg,.dxf"
                  />
                  <p className="text-xs text-slate-500">Attach reference images, marked-up PDFs, or CAD files</p>
                  
                  {revisionFiles.length > 0 && (
                    <div className="mt-2 space-y-1">
                      {revisionFiles.map((file, index) => (
                        <div key={index} className="flex items-center justify-between bg-white p-2 rounded border">
                          <span className="text-sm truncate">{file.name}</span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={() => removeRevisionFile(index)}
                            className="text-red-500 h-6 w-6 p-0"
                          >
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
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
                  onClick={() => {
                    setRevisionDialogOpen(false);
                    setRevisionAudioBlob(null);
                    setRevisionFiles([]);
                  }}
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
                        
                        {/* Voice Note */}
                        {comment.voice_note_url && (
                          <div className="mt-3 bg-gradient-to-r from-blue-50 to-indigo-50 px-4 py-3 rounded-lg border border-blue-200">
                            <div className="flex items-center gap-3">
                              <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center">
                                <Mic className="w-4 h-4 text-white" />
                              </div>
                              <div className="flex-1">
                                <p className="text-xs text-blue-600 font-medium mb-1">Voice Note</p>
                                <audio 
                                  controls 
                                  className="w-full h-8"
                                  src={`${API}/voice-notes/${comment.voice_note_url.split('/').pop()}`}
                                  preload="metadata"
                                >
                                  Your browser does not support audio playback.
                                </audio>
                              </div>
                            </div>
                          </div>
                        )}
                        
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
                  <div className="flex items-center gap-2 flex-wrap">
                    {/* File Attachment */}
                    <input
                      type="file"
                      accept="image/*,.pdf,.doc,.docx,.txt,.dwg,.dxf,.dwf,.dgn,.xls,.xlsx,.csv,.ppt,.pptx,.zip,.rar"
                      onChange={(e) => setReferenceFiles(Array.from(e.target.files))}
                      className="hidden"
                      id="reference-upload"
                      multiple
                    />
                    <label 
                      htmlFor="reference-upload"
                      className="inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border border-input bg-background hover:bg-accent hover:text-accent-foreground h-9 px-3 cursor-pointer"
                    >
                      <Upload className="w-4 h-4 mr-2" />
                      Attach Files
                    </label>
                    
                    {/* Voice Recording */}
                    <div className="flex items-center gap-2">
                      {!isRecording && !audioBlob && (
                        <Button
                          type="button"
                          variant="outline"
                          size="sm"
                          onClick={startRecording}
                          className="text-red-600 border-red-200 hover:bg-red-50"
                        >
                          <Mic className="w-4 h-4 mr-2" />
                          Voice Note
                        </Button>
                      )}
                      
                      {isRecording && (
                        <div className="flex items-center gap-2 bg-red-50 px-3 py-2 rounded-lg border border-red-200">
                          <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse"></div>
                          <span className="text-sm text-red-700 font-mono">
                            {formatTime(recordingTime)}
                          </span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={stopRecording}
                            className="text-red-700 hover:bg-red-100 h-6 w-6 p-0"
                          >
                            <Square className="w-3 h-3" />
                          </Button>
                        </div>
                      )}
                      
                      {audioBlob && !isRecording && (
                        <div className="flex items-center gap-2 bg-blue-50 px-3 py-2 rounded-lg border border-blue-200">
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={playVoiceNote}
                            className="text-blue-700 hover:bg-blue-100 h-6 w-6 p-0"
                            disabled={playingAudio}
                          >
                            {playingAudio ? <Pause className="w-3 h-3" /> : <Play className="w-3 h-3" />}
                          </Button>
                          <span className="text-sm text-blue-700">
                            🎙️ {formatTime(recordingTime)} voice note
                          </span>
                          <Button
                            type="button"
                            variant="ghost"
                            size="sm"
                            onClick={clearVoiceNote}
                            className="text-blue-700 hover:bg-blue-100 h-6 w-6 p-0"
                          >
                            <X className="w-3 h-3" />
                          </Button>
                        </div>
                      )}
                    </div>
                    
                    {referenceFiles.length > 0 && (
                      <div className="flex flex-col gap-1">
                        <span className="text-xs text-slate-600 font-medium">
                          📎 {referenceFiles.length} file(s) selected:
                        </span>
                        {referenceFiles.map((file, index) => (
                          <div key={index} className="flex items-center gap-2 text-xs text-slate-600 bg-slate-50 px-2 py-1 rounded">
                            <span className="truncate max-w-[200px]">{file.name}</span>
                            <span className="text-slate-400">({(file.size / 1024).toFixed(1)}KB)</span>
                            <button
                              onClick={() => {
                                const newFiles = referenceFiles.filter((_, i) => i !== index);
                                setReferenceFiles(newFiles);
                              }}
                              className="text-red-600 hover:text-red-800 ml-auto"
                              type="button"
                            >
                              <X className="w-3 h-3" />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                  
                  {/* Revision Required Checkbox */}
                  {!editingComment && selectedCommentDrawing?.is_issued && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mt-3">
                      <label className="flex items-center gap-3 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={markForRevision}
                          onChange={(e) => setMarkForRevision(e.target.checked)}
                          className="w-4 h-4 text-amber-600 border-amber-300 rounded focus:ring-amber-500"
                        />
                        <div>
                          <span className="text-sm font-medium text-amber-800">
                            🔄 Mark drawing for revision
                          </span>
                          <p className="text-xs text-amber-700 mt-1">
                            Check this if the drawing needs changes and should return to &quot;Revision Needed&quot; status
                          </p>
                        </div>
                      </label>
                    </div>
                  )}
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
                      disabled={submittingComment}
                      className="bg-purple-600 hover:bg-purple-700"
                    >
                      <Send className="w-4 h-4 mr-2" />
                      {submittingComment ? 'Posting...' : (editingComment ? 'Update' : 'Post')}
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Issue Drawing Dialog */}
        <Dialog open={issueDialogOpen} onOpenChange={setIssueDialogOpen}>
          <DialogContent className="max-w-md mx-auto">
            <DialogHeader>
              <DialogTitle className="text-base sm:text-lg">Issue Drawing to Recipients</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              {selectedIssueDrawing && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                  <p className="text-sm font-medium text-blue-800 truncate">
                    {selectedIssueDrawing.name}
                  </p>
                  <p className="text-xs text-blue-600 mt-1">
                    {selectedIssueDrawing.category}
                  </p>
                </div>
              )}
              
              <div>
                <Label className="text-sm font-medium">Select Recipients *</Label>
                <p className="text-xs text-slate-500 mt-1 mb-3">
                  Choose who should be notified about this drawing issue
                </p>
                
                {availableRecipients.length === 0 ? (
                  <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded p-2">
                    No recipients available for this drawing category
                  </p>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto">
                    {availableRecipients.map((recipient) => (
                      <label key={recipient.id} className="flex items-center gap-3 p-2 border border-slate-200 rounded hover:bg-slate-50 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedRecipients.some(r => r.id === recipient.id)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedRecipients([...selectedRecipients, recipient]);
                            } else {
                              setSelectedRecipients(selectedRecipients.filter(r => r.id !== recipient.id));
                            }
                          }}
                          className="w-4 h-4 text-blue-600 border-slate-300 rounded focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <p className="text-sm font-medium text-slate-900">{recipient.name}</p>
                          <p className="text-xs text-slate-500">{recipient.role}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                )}
                
                {selectedRecipients.length > 0 && (
                  <div className="mt-3 p-2 bg-green-50 border border-green-200 rounded">
                    <p className="text-xs text-green-700 font-medium">
                      ✓ {selectedRecipients.length} recipient(s) selected
                    </p>
                  </div>
                )}
              </div>
            </div>
            
            <DialogFooter className="flex flex-col sm:flex-row gap-2">
              <Button 
                variant="outline" 
                onClick={() => {
                  setIssueDialogOpen(false);
                  setSelectedIssueDrawing(null);
                  setSelectedRecipients([]);
                }}
                className="w-full sm:w-auto text-xs sm:text-sm"
              >
                Cancel
              </Button>
              <Button 
                onClick={handleIssueDrawingWithRecipients}
                disabled={selectedRecipients.length === 0}
                className="bg-green-600 hover:bg-green-700 text-white w-full sm:w-auto text-xs sm:text-sm"
              >
                Issue Drawing ({selectedRecipients.length})
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Project Dialog */}
        <DeleteProjectDialog
          open={deleteDialogOpen}
          onOpenChange={setDeleteDialogOpen}
          project={project}
          onConfirm={handleDeleteProject}
        />

        {/* Archive Project Dialog */}
        <ArchiveProjectDialog
          open={archiveDialogOpen}
          onOpenChange={setArchiveDialogOpen}
          project={project}
          archiveDate={archiveDate}
          setArchiveDate={setArchiveDate}
          onConfirm={handleArchiveProject}
        />

        {/* File Upload Dialog */}
        <Dialog open={uploadDialogOpen} onOpenChange={(open) => {
          // Prevent closing during upload
          if (!uploadingFile || !open) {
            setUploadDialogOpen(open);
            if (!open) {
              setSelectedFiles([]);
              setUploadProgress(0);
            }
          } else {
            toast.warning('Please wait for upload to complete');
          }
        }}>
          <DialogContent className="max-w-lg mx-auto">
            <DialogHeader>
              <DialogTitle className="text-base sm:text-lg">
                {uploadType === 'issue' ? 'Upload Drawing Files' : 'Upload Revised Files'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <p className="text-xs sm:text-sm text-slate-600">
                {uploadType === 'issue' 
                  ? 'Upload drawing files (.pdf, .dwg, .dxf) before issuing.'
                  : 'Upload revised files to complete the resolution.'}
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <p className="text-xs sm:text-sm text-blue-800 font-medium truncate">
                  {selectedFileDrawing?.name}
                </p>
                <p className="text-xs text-blue-600 mt-1">
                  {selectedFileDrawing?.category}
                </p>
              </div>
              <div>
                <Label className="text-xs sm:text-sm font-medium">Select Drawing Files * (Max 50MB each)</Label>
                <Input
                  type="file"
                  accept=".pdf,.dwg,.dxf,.dwf,.dgn"
                  onChange={(e) => setSelectedFiles(Array.from(e.target.files))}
                  className="mt-2 text-xs sm:text-sm"
                  disabled={uploadingFile}
                  multiple
                />
                {selectedFiles.length > 0 && (
                  <div className="mt-3 space-y-2">
                    <p className="text-xs text-green-600 font-medium">
                      ✓ Selected {selectedFiles.length} file(s):
                    </p>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {selectedFiles.map((file, index) => (
                        <div key={index} className="flex items-center justify-between bg-slate-50 px-2 py-1.5 rounded text-xs">
                          <div className="flex-1 min-w-0">
                            <span className="truncate block">{file.name}</span>
                            <span className="text-slate-500">({(file.size / (1024 * 1024)).toFixed(1)}MB)</span>
                          </div>
                          <button
                            onClick={() => {
                              const newFiles = selectedFiles.filter((_, i) => i !== index);
                              setSelectedFiles(newFiles);
                            }}
                            className="text-red-600 hover:text-red-800 ml-2 p-1"
                            type="button"
                            disabled={uploadingFile}
                          >
                            <X className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
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
            <DialogFooter className="flex flex-col sm:flex-row gap-2">
              <Button 
                variant="outline" 
                onClick={() => {
                  setUploadDialogOpen(false);
                  setSelectedFiles([]);
                  setSelectedFileDrawing(null);
                }}
                disabled={uploadingFile}
                className="w-full sm:w-auto text-xs sm:text-sm"
              >
                Cancel
              </Button>
              <Button 
                onClick={handleFileUpload}
                disabled={selectedFiles.length === 0 || uploadingFile}
                className="bg-blue-600 hover:bg-blue-700 text-white w-full sm:w-auto text-xs sm:text-sm"
              >
                {uploadingFile 
                  ? `Uploading ${uploadProgress}%...` 
                  : uploadType === 'issue' 
                    ? `Upload ${selectedFiles.length > 0 ? selectedFiles.length : ''} for Review`
                    : `Upload ${selectedFiles.length > 0 ? selectedFiles.length : ''} Resolved`}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Add Co-Client Dialog */}
        <Dialog open={coClientDialogOpen} onOpenChange={setCoClientDialogOpen}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Add Co-Client / Associate Client</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAddCoClient} className="space-y-4">
              <div>
                <Label>Name *</Label>
                <Input
                  value={coClientFormData.name}
                  onChange={(e) => setCoClientFormData({ ...coClientFormData, name: e.target.value })}
                  placeholder="Full name"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Email *</Label>
                  <Input
                    type="email"
                    value={coClientFormData.email}
                    onChange={(e) => setCoClientFormData({ ...coClientFormData, email: e.target.value })}
                    placeholder="email@example.com"
                    required
                  />
                </div>
                <div>
                  <Label>Phone</Label>
                  <Input
                    type="tel"
                    value={coClientFormData.phone}
                    onChange={(e) => setCoClientFormData({ ...coClientFormData, phone: e.target.value })}
                    placeholder="+1234567890"
                  />
                </div>
              </div>

              <div>
                <Label>Relationship *</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={coClientFormData.relationship}
                  onChange={(e) => setCoClientFormData({ ...coClientFormData, relationship: e.target.value })}
                  required
                >
                  <option value="Spouse">Spouse</option>
                  <option value="Family Member">Family Member</option>
                  <option value="Representative">Representative</option>
                  <option value="Staff">Staff</option>
                  <option value="Business Partner">Business Partner</option>
                  <option value="Other">Other</option>
                </select>
              </div>

              <div>
                <Label>Notes</Label>
                <textarea
                  className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={coClientFormData.notes}
                  onChange={(e) => setCoClientFormData({ ...coClientFormData, notes: e.target.value })}
                  placeholder="Any additional information..."
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setCoClientDialogOpen(false);
                    resetCoClientForm();
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-orange-500 hover:bg-orange-600">
                  Add Co-Client
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Assign Contractor Dialog */}
        <Dialog open={assignContractorDialogOpen} onOpenChange={setAssignContractorDialogOpen}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <HardHat className="w-5 h-5 text-orange-600" />
                Assign Contractor to Project
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Contractor Type *</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={selectedContractorType}
                  onChange={(e) => setSelectedContractorType(e.target.value)}
                  required
                >
                  <option value="">Select type...</option>
                  {contractorTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="inviteNewContractor"
                  checked={inviteNewContractor}
                  onChange={(e) => setInviteNewContractor(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <Label htmlFor="inviteNewContractor" className="cursor-pointer">Invite new contractor (not in system)</Label>
              </div>

              {!inviteNewContractor ? (
                <div>
                  <Label>Select Existing Contractor *</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                    value={selectedContractorId}
                    onChange={(e) => setSelectedContractorId(e.target.value)}
                  >
                    <option value="">Select contractor...</option>
                    {allContractors
                      .filter(c => !selectedContractorType || c.contractor_type === selectedContractorType)
                      .map((contractor) => (
                        <option key={contractor.id} value={contractor.id}>
                          {contractor.name} ({contractor.contractor_type}) - {contractor.phone}
                        </option>
                      ))}
                  </select>
                </div>
              ) : (
                <div className="space-y-3 p-4 bg-orange-50 rounded-lg border border-orange-200">
                  <p className="text-sm font-medium text-orange-800">New Contractor Details</p>
                  <div>
                    <Label>Name *</Label>
                    <Input
                      value={newContractorData.name}
                      onChange={(e) => setNewContractorData({ ...newContractorData, name: e.target.value })}
                      placeholder="Contractor name"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>Phone *</Label>
                      <Input
                        type="tel"
                        value={newContractorData.phone}
                        onChange={(e) => setNewContractorData({ ...newContractorData, phone: e.target.value })}
                        placeholder="+919876543210"
                      />
                    </div>
                    <div>
                      <Label>Email</Label>
                      <Input
                        type="email"
                        value={newContractorData.email}
                        onChange={(e) => setNewContractorData({ ...newContractorData, email: e.target.value })}
                        placeholder="email@example.com"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-orange-600">
                    An invitation will be sent to the contractor&apos;s phone
                  </p>
                </div>
              )}

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setAssignContractorDialogOpen(false);
                    resetContractorForm();
                  }}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleAssignContractor}
                  className="bg-orange-500 hover:bg-orange-600"
                >
                  {inviteNewContractor ? 'Invite & Assign' : 'Assign Contractor'}
                </Button>
              </DialogFooter>
            </div>
          </DialogContent>
        </Dialog>

        {/* Assign Consultant Dialog */}
        <Dialog open={assignConsultantDialogOpen} onOpenChange={setAssignConsultantDialogOpen}>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-blue-600" />
                Assign Consultant to Project
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Consultant Type *</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={selectedConsultantType}
                  onChange={(e) => setSelectedConsultantType(e.target.value)}
                  required
                >
                  <option value="">Select type...</option>
                  {consultantTypes.map((type) => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="inviteNewConsultant"
                  checked={inviteNewConsultant}
                  onChange={(e) => setInviteNewConsultant(e.target.checked)}
                  className="rounded border-slate-300"
                />
                <Label htmlFor="inviteNewConsultant" className="cursor-pointer">Add new consultant (contact info only)</Label>
              </div>

              {!inviteNewConsultant ? (
                <div>
                  <Label>Select Existing Consultant</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                    value={selectedConsultantId}
                    onChange={(e) => setSelectedConsultantId(e.target.value)}
                  >
                    <option value="">Select consultant...</option>
                    {allConsultants
                      .filter(c => !selectedConsultantType || c.type === selectedConsultantType)
                      .map((consultant) => (
                        <option key={consultant.id} value={consultant.id}>
                          {consultant.name} ({consultant.type}) - {consultant.phone}
                        </option>
                      ))}
                  </select>
                </div>
              ) : (
                <div className="space-y-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <p className="text-sm font-medium text-blue-800">New Consultant Contact Details</p>
                  <div>
                    <Label>Name *</Label>
                    <Input
                      value={newConsultantData.name}
                      onChange={(e) => setNewConsultantData({ ...newConsultantData, name: e.target.value })}
                      placeholder="Consultant name"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label>Phone *</Label>
                      <Input
                        type="tel"
                        value={newConsultantData.phone}
                        onChange={(e) => setNewConsultantData({ ...newConsultantData, phone: e.target.value })}
                        placeholder="+919876543210"
                      />
                    </div>
                    <div>
                      <Label>Email</Label>
                      <Input
                        type="email"
                        value={newConsultantData.email}
                        onChange={(e) => setNewConsultantData({ ...newConsultantData, email: e.target.value })}
                        placeholder="email@example.com"
                      />
                    </div>
                  </div>
                  <p className="text-xs text-blue-600">
                    This will add contact information only (no portal access)
                  </p>
                </div>
              )}

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setAssignConsultantDialogOpen(false);
                    resetConsultantForm();
                  }}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={handleAssignConsultant}
                  className="bg-blue-500 hover:bg-blue-600"
                >
                  {inviteNewConsultant ? 'Add Contact' : 'Assign Consultant'}
                </Button>
              </DialogFooter>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
