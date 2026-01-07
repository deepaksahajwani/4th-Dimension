import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import Layout from '../components/Layout';
import { LoadingState, ErrorState, safeApiCall } from '../utils/stability';
import { 
  LayoutGrid,
  Users,
  AlertCircle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Search,
  Filter,
  Plus,
  MessageSquare,
  Paperclip,
  Mic,
  Send,
  X,
  ChevronDown,
  ChevronUp,
  Calendar,
  Target,
  Flag,
  FileText,
  Square,
  Play,
  Pause,
  Activity,
  HardDrive,
  Bell,
  BarChart3,
  Eye,
  Download,
  RefreshCw,
  Check
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function OwnerDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // New error state for stability
  const [projects, setProjects] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [filteredProjects, setFilteredProjects] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [quickFilter, setQuickFilter] = useState(null); // 'critical', 'all', etc.
  const [teamOverview, setTeamOverview] = useState(null);
  
  // System Metrics (Phase 5)
  const [systemMetrics, setSystemMetrics] = useState(null);
  const [showMetrics, setShowMetrics] = useState(false);
  
  // Pending Approvals
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [pendingApprovalsDialogOpen, setPendingApprovalsDialogOpen] = useState(false);
  const [selectedDrawingForAction, setSelectedDrawingForAction] = useState(null);
  const [revisionComment, setRevisionComment] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  
  // Quick assign dialog
  const [assignDialogOpen, setAssignDialogOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState(null);
  const [selectedMember, setSelectedMember] = useState(null);
  const [assignmentText, setAssignmentText] = useState('');
  const [attachedFiles, setAttachedFiles] = useState([]);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [dueDate, setDueDate] = useState('');
  const [dueTime, setDueTime] = useState('');
  const [priority, setPriority] = useState('MEDIUM');
  const [mediaRecorder, setMediaRecorder] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [playingAudio, setPlayingAudio] = useState(false);
  
  // Progress breakdown dialog
  const [progressDialogOpen, setProgressDialogOpen] = useState(false);

  const fetchAllData = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Fetch all projects
      const projectsRes = await axios.get(`${API}/api/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // For each project, get drawings to calculate progress
      const projectsWithProgress = await Promise.all(
        projectsRes.data.map(async (project) => {
          try {
            const drawingsRes = await axios.get(
              `${API}/api/projects/${project.id}/drawings`,
              { headers: { Authorization: `Bearer ${token}` } }
            );
            
            const drawings = drawingsRes.data;
            const totalDrawings = drawings.length;
            const completedDrawings = drawings.filter(d => d.is_issued || d.is_approved).length;
            const progress = totalDrawings > 0 ? (completedDrawings / totalDrawings) * 100 : 0;
            
            // Get overdue count
            const now = new Date();
            const overdueDrawings = drawings.filter(d => {
              if (!d.due_date || d.is_issued) return false;
              return new Date(d.due_date) < now;
            }).length;
            
            // Determine status
            let status = 'on-track';
            if (overdueDrawings > 0) status = 'critical';
            else if (progress < 30 && totalDrawings > 0) status = 'behind';
            else if (progress >= 80) status = 'excellent';
            
            return {
              ...project,
              totalDrawings,
              completedDrawings,
              progress: Math.round(progress),
              overdueDrawings,
              status
            };
          } catch (err) {
            return {
              ...project,
              totalDrawings: 0,
              completedDrawings: 0,
              progress: 0,
              overdueDrawings: 0,
              status: 'unknown'
            };
          }
        })
      );
      
      setProjects(projectsWithProgress);
      
      // Fetch team overview
      const teamRes = await axios.get(`${API}/api/dashboard/team-overview`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTeamOverview(teamRes.data);
      
      // Fetch team members
      const membersRes = await axios.get(`${API}/api/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const approvedMembers = membersRes.data.filter(m => 
        m.approval_status === 'approved' && m.role !== 'owner'
      );
      setTeamMembers(approvedMembers);
      
      // Fetch pending approval drawings
      try {
        const pendingRes = await axios.get(`${API}/api/drawings/pending-approval`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setPendingApprovals(pendingRes.data);
      } catch (pendingError) {
        console.warn('Could not fetch pending approvals:', pendingError);
      }
      
      // Fetch system metrics (Phase 5)
      try {
        const metricsRes = await axios.get(`${API}/api/metrics/overview`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSystemMetrics(metricsRes.data);
      } catch (metricsError) {
        console.warn('Could not fetch system metrics:', metricsError);
      }
      
      setError(null); // Clear any previous errors
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      console.error('Error details:', error.response?.data);
      const errorMessage = error.response?.data?.detail || error.message || 'Failed to load dashboard';
      setError(errorMessage);
      toast.error(`Failed to load dashboard: ${errorMessage}`);
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!user) return; // Wait for user to load
    
    if (user.role !== 'owner' && !user.is_owner) {
      toast.error('Access denied. Owner only.');
      navigate('/dashboard');
      return;
    }
    fetchAllData();
  }, [user, navigate]);

  useEffect(() => {
    filterProjects();
  }, [projects, searchTerm, filterStatus, quickFilter]);

  const filterProjects = () => {
    let filtered = [...projects];
    
    // Quick filter from stat cards
    if (quickFilter === 'critical') {
      filtered = filtered.filter(p => p.status === 'critical');
    }
    
    // Search filter
    if (searchTerm) {
      filtered = filtered.filter(p => 
        p.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        p.client_name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    
    // Status filter
    if (filterStatus !== 'all') {
      filtered = filtered.filter(p => p.status === filterStatus);
    }
    
    // Sort by priority (critical first, then by progress)
    filtered.sort((a, b) => {
      if (a.status === 'critical' && b.status !== 'critical') return -1;
      if (b.status === 'critical' && a.status !== 'critical') return 1;
      return a.progress - b.progress;
    });
    
    setFilteredProjects(filtered);
  };

  const handleQuickFilter = (filterType) => {
    // Toggle filter
    if (quickFilter === filterType) {
      setQuickFilter(null);
      setFilterStatus('all');
      setSearchTerm('');
    } else {
      setQuickFilter(filterType);
      if (filterType === 'critical') {
        setFilterStatus('all');
      }
      setSearchTerm('');
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'critical': return 'bg-red-100 border-red-500 text-red-900';
      case 'behind': return 'bg-orange-100 border-orange-500 text-orange-900';
      case 'on-track': return 'bg-blue-100 border-blue-500 text-blue-900';
      case 'excellent': return 'bg-green-100 border-green-500 text-green-900';
      default: return 'bg-gray-100 border-gray-500 text-gray-900';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'critical': return <AlertCircle className="w-5 h-5 text-red-600" />;
      case 'behind': return <Clock className="w-5 h-5 text-orange-600" />;
      case 'on-track': return <TrendingUp className="w-5 h-5 text-blue-600" />;
      case 'excellent': return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      default: return <Target className="w-5 h-5 text-gray-600" />;
    }
  };

  const openQuickAssign = (project) => {
    setSelectedProject(project);
    setAssignDialogOpen(true);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setAttachedFiles([...attachedFiles, ...files]);
  };

  const removeFile = (index) => {
    setAttachedFiles(attachedFiles.filter((_, i) => i !== index));
  };

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

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const handleQuickAssign = async () => {
    if (!selectedMember) {
      toast.error('Please select a team member');
      return;
    }
    
    if (!assignmentText && attachedFiles.length === 0 && !audioBlob) {
      toast.error('Please add a message, file, or voice note');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      
      // Calculate due date/time
      let dueDateTimeISO;
      if (dueDate && dueTime) {
        dueDateTimeISO = new Date(`${dueDate}T${dueTime}`).toISOString();
      } else if (dueDate) {
        dueDateTimeISO = new Date(`${dueDate}T23:59:00`).toISOString();
      } else {
        // Default to tomorrow at 5 PM
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(17, 0, 0, 0);
        dueDateTimeISO = tomorrow.toISOString();
      }
      
      // Create task as comment-style (no explicit title needed)
      const taskData = {
        title: assignmentText.substring(0, 80) || 'Quick Task',
        description: assignmentText,
        assigned_to_id: selectedMember,
        due_date_time: dueDateTimeISO,
        priority: priority,
        category: 'OTHER',
        project_id: selectedProject?.id || null,
        status: 'open'
      };
      
      // Create the task first
      const taskResponse = await axios.post(`${API}/api/tasks/ad-hoc`, taskData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const taskId = taskResponse.data.id;
      
      // Upload files if any
      if (attachedFiles.length > 0 || audioBlob) {
        const formData = new FormData();
        
        // Add regular files
        attachedFiles.forEach((file) => {
          formData.append('files', file);
        });
        
        // Add voice note if present
        if (audioBlob) {
          const voiceFile = new File([audioBlob], `voice-note-${Date.now()}.webm`, { 
            type: 'audio/webm' 
          });
          formData.append('files', voiceFile);
        }
        
        // Upload files (if you have a file upload endpoint, use it here)
        // For now, we'll just log that files would be uploaded
        console.log('Files to upload:', attachedFiles.length + (audioBlob ? 1 : 0));
      }
      
      toast.success('Task assigned successfully!');
      setAssignDialogOpen(false);
      resetAssignDialog();
      fetchAllData();
    } catch (error) {
      console.error('Error assigning task:', error);
      toast.error(error.response?.data?.detail || 'Failed to assign task');
    }
  };

  const resetAssignDialog = () => {
    setSelectedProject(null);
    setSelectedMember(null);
    setAssignmentText('');
    setAttachedFiles([]);
    setAudioBlob(null);
    setDueDate('');
    setDueTime('');
    setPriority('MEDIUM');
    setRecordingTime(0);
    setPlayingAudio(false);
    if (mediaRecorder && mediaRecorder.state === 'recording') {
      stopRecording();
    }
  };

  // Pending Approvals Actions
  const handleApproveDrawing = async (drawing) => {
    setActionLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/api/drawings/${drawing.id}`, {
        is_approved: true,
        under_review: false
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`"${drawing.name}" approved!`);
      // Remove from pending list
      setPendingApprovals(prev => prev.filter(d => d.id !== drawing.id));
      setSelectedDrawingForAction(null);
    } catch (error) {
      toast.error('Failed to approve drawing');
    } finally {
      setActionLoading(false);
    }
  };

  const handleRequestRevision = async (drawing) => {
    if (!revisionComment.trim()) {
      toast.error('Please add a comment explaining the revision needed');
      return;
    }
    
    setActionLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      // Add comment with revision flag
      await axios.post(`${API}/api/drawings/${drawing.id}/comments`, {
        text: revisionComment,
        requires_revision: true
      }, { headers });
      
      // Update drawing status
      await axios.put(`${API}/api/drawings/${drawing.id}`, {
        has_pending_revision: true,
        under_review: false,
        is_approved: false
      }, { headers });
      
      toast.success(`Revision requested for "${drawing.name}"`);
      // Remove from pending list
      setPendingApprovals(prev => prev.filter(d => d.id !== drawing.id));
      setSelectedDrawingForAction(null);
      setRevisionComment('');
    } catch (error) {
      toast.error('Failed to request revision');
    } finally {
      setActionLoading(false);
    }
  };

  const handleViewDrawing = (drawing) => {
    if (drawing.file_url) {
      window.open(`${BACKEND_URL}${drawing.file_url}`, '_blank');
    } else {
      toast.error('No file available');
    }
  };

  const handleDownloadDrawing = async (drawing) => {
    if (drawing.file_url) {
      try {
        const link = document.createElement('a');
        link.href = `${BACKEND_URL}${drawing.file_url}`;
        link.download = `${drawing.name}.pdf`;
        link.target = '_blank';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      } catch (error) {
        toast.error('Failed to download');
      }
    }
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-slate-600">Loading your dashboard...</p>
          </div>
        </div>
      </Layout>
    );
  }

  const criticalProjects = projects.filter(p => p.status === 'critical').length;
  const totalProgress = projects.length > 0 
    ? Math.round(projects.reduce((sum, p) => sum + (p.progress || 0), 0) / projects.length)
    : 0;

  // Show loading state
  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="max-w-full mx-auto">
          <LoadingState message="Loading dashboard..." />
        </div>
      </Layout>
    );
  }

  // Show error state with retry option
  if (error) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="max-w-full mx-auto">
          <ErrorState 
            message={error} 
            onRetry={() => {
              setError(null);
              setLoading(true);
              fetchAllData();
            }} 
          />
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-full mx-auto">
        {/* Header */}
        <div className="mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">Owner Command Center</h1>
              <p className="text-sm sm:text-base text-slate-600 mt-1">
                Manage all projects and team members
              </p>
            </div>
            <div className="flex gap-2">
              <Button 
                onClick={() => openQuickAssign(null)}
                className="bg-orange-600 hover:bg-orange-700 text-white"
              >
                <Plus className="w-4 h-4 mr-2" />
                Quick Assign
              </Button>
              <Button 
                onClick={() => navigate('/weekly-dashboard')}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                📊 Weekly View
              </Button>
            </div>
          </div>
        </div>

        {/* PENDING APPROVALS - Primary Action Card */}
        {pendingApprovals.length > 0 && (
          <div 
            onClick={() => setPendingApprovalsDialogOpen(true)}
            className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl shadow-lg p-6 mb-6 cursor-pointer transition-all hover:shadow-xl hover:scale-[1.01]"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="bg-white/20 rounded-full p-3">
                  <FileText className="w-8 h-8 text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white">Drawings Pending Your Approval</h2>
                  <p className="text-orange-100 text-sm mt-1">
                    {pendingApprovals.length} drawing{pendingApprovals.length > 1 ? 's' : ''} awaiting review
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="text-4xl font-bold text-white">{pendingApprovals.length}</p>
                  <p className="text-orange-100 text-xs">Click to Review</p>
                </div>
                <CheckCircle2 className="w-10 h-10 text-white/80" />
              </div>
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div 
            onClick={() => navigate('/projects')}
            className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500 cursor-pointer transition-all hover:shadow-lg"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">Total Projects</p>
                <p className="text-3xl font-bold text-slate-900">{projects.length}</p>
              </div>
              <LayoutGrid className="w-10 h-10 text-blue-500" />
            </div>
            <p className="text-xs text-blue-600 mt-2">Click to view all projects</p>
          </div>
          
          <div 
            onClick={() => handleQuickFilter('critical')}
            className={`bg-white rounded-xl shadow-md p-6 border-l-4 border-red-500 cursor-pointer transition-all hover:shadow-lg ${
              quickFilter === 'critical' ? 'ring-2 ring-red-500' : ''
            }`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">Critical Projects</p>
                <p className="text-3xl font-bold text-red-600">{criticalProjects}</p>
              </div>
              <AlertCircle className="w-10 h-10 text-red-500" />
            </div>
            {quickFilter === 'critical' && (
              <p className="text-xs text-red-600 mt-2">Showing critical only</p>
            )}
          </div>
          
          <div 
            onClick={() => setProgressDialogOpen(true)}
            className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500 cursor-pointer transition-all hover:shadow-lg"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">Avg Progress</p>
                <p className="text-3xl font-bold text-green-600">{totalProgress}%</p>
              </div>
              <TrendingUp className="w-10 h-10 text-green-500" />
            </div>
            <p className="text-xs text-green-600 mt-2">Click to view breakdown</p>
          </div>
          
          <div 
            onClick={() => navigate('/team')}
            className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500 cursor-pointer transition-all hover:shadow-lg"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">Team Size</p>
                <p className="text-3xl font-bold text-purple-600">{teamOverview?.total_team_size || 0}</p>
              </div>
              <Users className="w-10 h-10 text-purple-500" />
            </div>
            <p className="text-xs text-purple-600 mt-2">Click to manage team</p>
          </div>
        </div>

        {/* System Metrics Panel (Phase 5) */}
        <div className="bg-white rounded-xl shadow-md mb-6 overflow-hidden">
          <div 
            onClick={() => setShowMetrics(!showMetrics)}
            className="flex items-center justify-between p-4 cursor-pointer hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <Activity className="w-5 h-5 text-indigo-600" />
              <h2 className="text-lg font-semibold text-slate-900">System Metrics</h2>
              {systemMetrics && (
                <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                  {systemMetrics.system_health?.status || 'healthy'}
                </span>
              )}
            </div>
            {showMetrics ? (
              <ChevronUp className="w-5 h-5 text-slate-400" />
            ) : (
              <ChevronDown className="w-5 h-5 text-slate-400" />
            )}
          </div>
          
          {showMetrics && systemMetrics && (
            <div className="border-t border-slate-200 p-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Notification Stats */}
                <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <Bell className="w-4 h-4 text-blue-600" />
                    <span className="text-sm font-medium text-blue-900">Notifications (7d)</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-xs text-blue-700">Total Sent</span>
                      <span className="text-sm font-semibold text-blue-900">
                        {systemMetrics.notifications?.summary?.total || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-xs text-blue-700">Success Rate</span>
                      <span className="text-sm font-semibold text-green-600">
                        {systemMetrics.notifications?.summary?.success_rate || 100}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-xs text-blue-700">Failed</span>
                      <span className={`text-sm font-semibold ${
                        (systemMetrics.notifications?.summary?.failed || 0) > 0 ? 'text-red-600' : 'text-slate-600'
                      }`}>
                        {systemMetrics.notifications?.summary?.failed || 0}
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Storage Stats */}
                <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <HardDrive className="w-4 h-4 text-purple-600" />
                    <span className="text-sm font-medium text-purple-900">Storage Usage</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-xs text-purple-700">Total Used</span>
                      <span className="text-sm font-semibold text-purple-900">
                        {systemMetrics.storage?.total?.formatted || '0 B'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-xs text-purple-700">3D Images</span>
                      <span className="text-sm font-semibold text-purple-900">
                        {systemMetrics.storage?.breakdown?.['3d_images']?.formatted || '0 B'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-xs text-purple-700">Total Files</span>
                      <span className="text-sm font-semibold text-purple-900">
                        {systemMetrics.storage?.total?.file_count || 0}
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* Drawing Stats */}
                <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <FileText className="w-4 h-4 text-green-600" />
                    <span className="text-sm font-medium text-green-900">Drawing Progress</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-xs text-green-700">Total Drawings</span>
                      <span className="text-sm font-semibold text-green-900">
                        {systemMetrics.system_health?.drawings?.total || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-xs text-green-700">Issued</span>
                      <span className="text-sm font-semibold text-green-900">
                        {systemMetrics.system_health?.drawings?.issued || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-xs text-green-700">Completion Rate</span>
                      <span className="text-sm font-semibold text-green-600">
                        {systemMetrics.system_health?.drawings?.completion_rate || 0}%
                      </span>
                    </div>
                  </div>
                </div>
                
                {/* API Activity */}
                <div className="bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <BarChart3 className="w-4 h-4 text-orange-600" />
                    <span className="text-sm font-medium text-orange-900">Activity (7d)</span>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-xs text-orange-700">Active Users</span>
                      <span className="text-sm font-semibold text-orange-900">
                        {systemMetrics.api_usage?.users?.active || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-xs text-orange-700">Drawings Uploaded</span>
                      <span className="text-sm font-semibold text-orange-900">
                        {systemMetrics.api_usage?.activity?.drawings_uploaded || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-xs text-orange-700">Comments Added</span>
                      <span className="text-sm font-semibold text-orange-900">
                        {systemMetrics.api_usage?.activity?.comments_created || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Last Updated */}
              <div className="mt-4 text-right">
                <span className="text-xs text-slate-500">
                  Last updated: {new Date(systemMetrics.timestamp).toLocaleString()}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Search and Filters */}
        <div className="bg-white rounded-xl shadow-md p-4 mb-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search projects by name, code, or client..."
                className="w-full pl-10 pr-4 py-2 border border-slate-300 rounded-lg"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            <select
              className="px-4 py-2 border border-slate-300 rounded-lg"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
            >
              <option value="all">All Status</option>
              <option value="critical">🔴 Critical</option>
              <option value="behind">🟠 Behind Schedule</option>
              <option value="on-track">🔵 On Track</option>
              <option value="excellent">🟢 Excellent</option>
            </select>
            
            <Button 
              onClick={() => openQuickAssign(null)}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Quick Assign
            </Button>
          </div>
        </div>

        {/* Projects Grid */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-slate-900">
                All Projects ({filteredProjects.length})
              </h2>
              {quickFilter && (
                <div className="flex items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    quickFilter === 'critical' ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'
                  }`}>
                    {quickFilter === 'critical' ? '🔴 Critical Projects' : '📊 All Projects'}
                  </span>
                  <button
                    onClick={() => handleQuickFilter(null)}
                    className="text-slate-500 hover:text-slate-700"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
            <div className="text-sm text-slate-600">
              Showing {filteredProjects.length} of {projects.length}
            </div>
          </div>

          {filteredProjects.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredProjects.map((project) => (
                <div
                  key={project.id}
                  className={`rounded-xl shadow-lg border-2 overflow-hidden hover:shadow-xl transition-all cursor-pointer ${getStatusColor(project.status)}`}
                  onClick={() => navigate(`/projects/${project.id}`)}
                >
                  {/* Project Header */}
                  <div className="bg-white p-4 border-b-2">
                    <div className="flex justify-between items-start mb-2">
                      <div className="flex-1">
                        <h3 className="font-bold text-lg text-slate-900 mb-1">
                          {project.title}
                        </h3>
                        {project.client_name && (
                          <p className="text-sm text-slate-600">{project.client_name}</p>
                        )}
                      </div>
                      {getStatusIcon(project.status)}
                    </div>
                  </div>

                  {/* Project Stats */}
                  <div className="bg-gradient-to-br from-white to-slate-50 p-4">
                    <div className="flex justify-between items-center mb-3">
                      <span className="text-sm text-slate-600">Progress</span>
                      <span className="text-2xl font-bold text-slate-900">
                        {project.progress}%
                      </span>
                    </div>
                    
                    <div className="w-full bg-slate-200 rounded-full h-3 mb-3">
                      <div
                        className={`h-3 rounded-full transition-all ${
                          project.status === 'critical' ? 'bg-red-500' :
                          project.status === 'behind' ? 'bg-orange-500' :
                          project.status === 'excellent' ? 'bg-green-500' :
                          'bg-blue-500'
                        }`}
                        style={{ width: `${project.progress}%` }}
                      ></div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="bg-white p-2 rounded">
                        <span className="text-slate-600">Issued:</span>
                        <span className="font-bold ml-1">
                          {project.completedDrawings}
                        </span>
                      </div>
                      
                      {project.overdueDrawings > 0 && (
                        <div className="bg-red-50 p-2 rounded text-red-700">
                          <AlertCircle className="w-3 h-3 inline mr-1" />
                          <span className="font-bold">{project.overdueDrawings} Overdue</span>
                        </div>
                      )}
                    </div>

                    {/* Quick Actions */}
                    <div className="mt-3 flex gap-2">
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          openQuickAssign(project);
                        }}
                      >
                        <MessageSquare className="w-3 h-3 mr-1" />
                        Assign Task
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/projects/${project.id}`);
                        }}
                      >
                        View Details
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-md p-12 text-center">
              <LayoutGrid className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-2">
                No Projects Found
              </h3>
              <p className="text-slate-600">
                {searchTerm || filterStatus !== 'all' 
                  ? 'Try adjusting your search or filters' 
                  : 'Create your first project to get started'}
              </p>
            </div>
          )}
        </div>

        {/* Team Overview Section */}
        {teamOverview && (
          <div className="mt-8">
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Users className="w-6 h-6 text-purple-600" />
              Team Workload
            </h2>
            
            <div className="bg-white rounded-xl shadow-md p-6">
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-slate-600">Team Average Progress</span>
                  <span className="text-2xl font-bold text-purple-600">
                    {Math.round(teamOverview.avg_progress)}%
                  </span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-4">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-purple-600 h-4 rounded-full"
                    style={{ width: `${teamOverview.avg_progress}%` }}
                  ></div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {teamOverview.team_members.map((member) => (
                  <div
                    key={member.user_id}
                    className="p-4 bg-slate-50 rounded-lg border border-slate-200 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h4 className="font-semibold text-slate-900">{member.name}</h4>
                        <p className="text-xs text-slate-600">{member.role}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold">
                          {member.overall_progress}%
                        </div>
                        <div className="text-xs">{member.status}</div>
                      </div>
                    </div>

                    <div className="w-full bg-slate-200 rounded-full h-2 mb-3">
                      <div
                        className={`h-2 rounded-full ${
                          member.overall_progress >= 75 ? 'bg-green-500' :
                          member.overall_progress >= 50 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${member.overall_progress}%` }}
                      ></div>
                    </div>

                    <div className="flex items-center gap-3 text-xs text-slate-600">
                      <span>{member.projects_count} projects</span>
                      <span>•</span>
                      <span>{member.total_points} points</span>
                    </div>

                    <Button
                      size="sm"
                      variant="outline"
                      className="w-full mt-3 text-xs"
                      onClick={() => {
                        setSelectedMember(member.user_id);
                        setAssignDialogOpen(true);
                      }}
                    >
                      <Plus className="w-3 h-3 mr-1" />
                      Assign Task
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Quick Assign Dialog */}
      <Dialog open={assignDialogOpen} onOpenChange={setAssignDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Quick Task Assignment</DialogTitle>
            {selectedProject && (
              <p className="text-sm text-slate-600 mt-1">
                For project: {selectedProject.title}
              </p>
            )}
          </DialogHeader>

          <div className="space-y-4">
            {/* Team Member Selection */}
            <div>
              <Label>Assign To *</Label>
              <select
                className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                value={selectedMember || ''}
                onChange={(e) => setSelectedMember(e.target.value)}
              >
                <option value="">Select team member</option>
                {teamMembers.map(member => (
                  <option key={member.id} value={member.id}>
                    {member.name} ({member.role})
                  </option>
                ))}
              </select>
            </div>

            {/* Message Input (Comment-style) */}
            <div>
              <Label>Message</Label>
              <Textarea
                className="mt-1"
                placeholder="Type your message, instructions, or task details..."
                value={assignmentText}
                onChange={(e) => setAssignmentText(e.target.value)}
                rows={4}
              />
            </div>

            {/* File Attachments */}
            <div>
              <Label>Attach Files</Label>
              <div className="mt-1">
                <label className="flex items-center gap-2 px-4 py-2 border border-slate-300 rounded-lg cursor-pointer hover:bg-slate-50">
                  <Paperclip className="w-4 h-4 text-slate-600" />
                  <span className="text-sm text-slate-600">Choose files</span>
                  <input
                    type="file"
                    multiple
                    className="hidden"
                    onChange={handleFileSelect}
                  />
                </label>
                
                {attachedFiles.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {attachedFiles.map((file, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-slate-50 rounded">
                        <span className="text-sm text-slate-700">{file.name}</span>
                        <button onClick={() => removeFile(index)}>
                          <X className="w-4 h-4 text-red-600" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Voice Note */}
            <div>
              <Label>Voice Note</Label>
              <div className="mt-1">
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
                      className="text-red-700 hover:bg-red-100 h-6 w-6 p-0 ml-auto"
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
                      className="text-blue-700 hover:bg-blue-100 h-6 w-6 p-0 ml-auto"
                    >
                      <X className="w-3 h-3" />
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* Due Date & Time (Optional) */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label className="text-xs text-slate-600">Due Date (Optional)</Label>
                <input
                  type="date"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                />
              </div>
              <div>
                <Label className="text-xs text-slate-600">Due Time (Optional)</Label>
                <input
                  type="time"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg text-sm"
                  value={dueTime}
                  onChange={(e) => setDueTime(e.target.value)}
                />
              </div>
            </div>

            {/* Priority (Optional) */}
            <div>
              <Label className="text-xs text-slate-600">Priority</Label>
              <select
                className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg text-sm"
                value={priority}
                onChange={(e) => setPriority(e.target.value)}
              >
                <option value="LOW">🟢 Low</option>
                <option value="MEDIUM">🟡 Medium</option>
                <option value="HIGH">🟠 High</option>
                <option value="URGENT">🔴 Urgent</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-3 pt-4">
              <Button
                className="flex-1 bg-blue-600 hover:bg-blue-700"
                onClick={handleQuickAssign}
                disabled={!selectedMember}
              >
                <Send className="w-4 h-4 mr-2" />
                Assign Task
              </Button>
              <Button
                variant="outline"
                className="flex-1"
                onClick={() => {
                  setAssignDialogOpen(false);
                  resetAssignDialog();
                }}
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Progress Breakdown Dialog */}
      <Dialog open={progressDialogOpen} onOpenChange={setProgressDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Project Progress Breakdown</DialogTitle>
            <p className="text-sm text-slate-600 mt-1">
              Average Progress: <span className="font-bold text-green-600">{totalProgress}%</span>
            </p>
          </DialogHeader>

          <div className="space-y-4">
            {projects.length > 0 ? (
              <>
                {/* Progress Summary Stats */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pb-4 border-b">
                  <div className="text-center">
                    <p className="text-2xl font-bold text-green-600">
                      {projects.filter(p => p.progress >= 75).length}
                    </p>
                    <p className="text-xs text-slate-600">75%+ Complete</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-blue-600">
                      {projects.filter(p => p.progress >= 50 && p.progress < 75).length}
                    </p>
                    <p className="text-xs text-slate-600">50-74% Complete</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-orange-600">
                      {projects.filter(p => p.progress >= 25 && p.progress < 50).length}
                    </p>
                    <p className="text-xs text-slate-600">25-49% Complete</p>
                  </div>
                  <div className="text-center">
                    <p className="text-2xl font-bold text-red-600">
                      {projects.filter(p => p.progress < 25).length}
                    </p>
                    <p className="text-xs text-slate-600">Below 25%</p>
                  </div>
                </div>

                {/* Individual Project Progress */}
                <div className="space-y-3">
                  {projects
                    .sort((a, b) => b.progress - a.progress)
                    .map((project) => (
                      <div
                        key={project.id}
                        className="p-4 border border-slate-200 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                        onClick={() => {
                          setProgressDialogOpen(false);
                          navigate(`/projects/${project.id}`);
                        }}
                      >
                        <div className="flex justify-between items-start mb-2">
                          <div className="flex-1">
                            <h4 className="font-semibold text-slate-900">{project.title}</h4>
                            {project.client_name && (
                              <p className="text-xs text-slate-600">{project.client_name}</p>
                            )}
                          </div>
                          <div className="flex items-center gap-2">
                            {getStatusIcon(project.status)}
                            <span className="text-2xl font-bold text-slate-900">
                              {project.progress}%
                            </span>
                          </div>
                        </div>

                        <div className="w-full bg-slate-200 rounded-full h-3 mb-2">
                          <div
                            className={`h-3 rounded-full transition-all ${
                              project.progress >= 75 ? 'bg-green-500' :
                              project.progress >= 50 ? 'bg-blue-500' :
                              project.progress >= 25 ? 'bg-orange-500' :
                              'bg-red-500'
                            }`}
                            style={{ width: `${project.progress}%` }}
                          ></div>
                        </div>

                        <div className="flex items-center gap-4 text-xs text-slate-600">
                          <span className="flex items-center gap-1">
                            <FileText className="w-3 h-3" />
                            {project.completedDrawings} issued
                          </span>
                          {project.overdueDrawings > 0 && (
                            <span className="flex items-center gap-1 text-red-600 font-medium">
                              <AlertCircle className="w-3 h-3" />
                              {project.overdueDrawings} overdue
                            </span>
                          )}
                          <span className={`ml-auto px-2 py-0.5 rounded text-xs font-medium ${
                            project.status === 'critical' ? 'bg-red-100 text-red-700' :
                            project.status === 'behind' ? 'bg-orange-100 text-orange-700' :
                            project.status === 'excellent' ? 'bg-green-100 text-green-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {project.status}
                          </span>
                        </div>
                      </div>
                    ))}
                </div>
              </>
            ) : (
              <div className="text-center py-8 text-slate-600">
                <p>No projects to display</p>
              </div>
            )}
          </div>

          <div className="flex justify-end pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => setProgressDialogOpen(false)}
            >
              Close
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Pending Approvals Dialog */}
      <Dialog open={pendingApprovalsDialogOpen} onOpenChange={setPendingApprovalsDialogOpen}>
        <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5 text-orange-600" />
              Drawings Pending Approval
            </DialogTitle>
            <p className="text-sm text-slate-600 mt-1">
              {pendingApprovals.length} drawing{pendingApprovals.length !== 1 ? 's' : ''} awaiting your review
            </p>
          </DialogHeader>

          <div className="space-y-4 mt-4">
            {pendingApprovals.length > 0 ? (
              pendingApprovals.map((drawing) => (
                <Card key={drawing.id} className="border-l-4 border-l-orange-500">
                  <CardContent className="p-4">
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                      {/* Drawing Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start gap-3">
                          <div className="bg-orange-100 rounded-lg p-2 shrink-0">
                            <FileText className="w-6 h-6 text-orange-600" />
                          </div>
                          <div className="min-w-0">
                            <h4 className="font-semibold text-slate-900 truncate">{drawing.name}</h4>
                            <p className="text-sm text-slate-600">{drawing.category}</p>
                            <div className="flex flex-wrap items-center gap-2 mt-1">
                              <Badge variant="outline" className="text-xs">
                                {drawing.project_title}
                              </Badge>
                              {drawing.project_code && (
                                <Badge variant="secondary" className="text-xs">
                                  {drawing.project_code}
                                </Badge>
                              )}
                            </div>
                            {drawing.reviewed_date && (
                              <p className="text-xs text-slate-500 mt-1">
                                Uploaded: {new Date(drawing.reviewed_date).toLocaleDateString('en-IN', { 
                                  day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' 
                                })}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex flex-wrap gap-2 shrink-0">
                        {drawing.file_url && (
                          <>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleViewDrawing(drawing)}
                              className="gap-1"
                            >
                              <Eye className="w-4 h-4" />
                              View
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => handleDownloadDrawing(drawing)}
                              className="gap-1"
                            >
                              <Download className="w-4 h-4" />
                              Download
                            </Button>
                          </>
                        )}
                        <Button
                          size="sm"
                          className="bg-green-600 hover:bg-green-700 gap-1"
                          onClick={() => handleApproveDrawing(drawing)}
                          disabled={actionLoading}
                        >
                          <Check className="w-4 h-4" />
                          Approve
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          className="text-orange-600 border-orange-300 hover:bg-orange-50 gap-1"
                          onClick={() => setSelectedDrawingForAction(drawing)}
                        >
                          <RefreshCw className="w-4 h-4" />
                          Request Revision
                        </Button>
                      </div>
                    </div>

                    {/* Revision Comment Input (shown when requesting revision) */}
                    {selectedDrawingForAction?.id === drawing.id && (
                      <div className="mt-4 p-4 bg-orange-50 rounded-lg border border-orange-200">
                        <Label className="text-sm font-medium text-orange-900">
                          What revisions are needed?
                        </Label>
                        <Textarea
                          value={revisionComment}
                          onChange={(e) => setRevisionComment(e.target.value)}
                          placeholder="Describe the changes required..."
                          className="mt-2 bg-white"
                          rows={3}
                        />
                        <div className="flex gap-2 mt-3">
                          <Button
                            size="sm"
                            className="bg-orange-600 hover:bg-orange-700"
                            onClick={() => handleRequestRevision(drawing)}
                            disabled={actionLoading || !revisionComment.trim()}
                          >
                            Submit Revision Request
                          </Button>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setSelectedDrawingForAction(null);
                              setRevisionComment('');
                            }}
                          >
                            Cancel
                          </Button>
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            ) : (
              <div className="text-center py-12 bg-slate-50 rounded-lg">
                <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
                <p className="text-lg font-medium text-slate-900">All caught up!</p>
                <p className="text-sm text-slate-600">No drawings pending approval</p>
              </div>
            )}
          </div>

          <DialogFooter className="mt-6 pt-4 border-t">
            <Button
              variant="outline"
              onClick={() => setPendingApprovalsDialogOpen(false)}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
