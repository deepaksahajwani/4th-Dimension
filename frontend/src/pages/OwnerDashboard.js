import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import Layout from '../components/Layout';
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
  Calendar,
  Target,
  Flag,
  FileText
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Textarea } from '../components/ui/textarea';
import { Label } from '../components/ui/label';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function OwnerDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [filteredProjects, setFilteredProjects] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [teamOverview, setTeamOverview] = useState(null);
  
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
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  useEffect(() => {
    if (user?.role !== 'owner') {
      toast.error('Access denied. Owner only.');
      navigate('/dashboard');
      return;
    }
    fetchAllData();
  }, [user]);

  useEffect(() => {
    filterProjects();
  }, [projects, searchTerm, filterStatus]);

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
      
      setLoading(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      console.error('Error details:', error.response?.data);
      toast.error(`Failed to load dashboard: ${error.response?.data?.detail || error.message}`);
      setLoading(false);
    }
  };

  const filterProjects = () => {
    let filtered = [...projects];
    
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
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      toast.error('Could not access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
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
            <Button 
              onClick={() => navigate('/weekly-dashboard')}
              className="bg-blue-600 hover:bg-blue-700 text-white"
            >
              📊 Weekly View
            </Button>
          </div>
        </div>
        {/* Quick Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">Total Projects</p>
                <p className="text-3xl font-bold text-slate-900">{projects.length}</p>
              </div>
              <LayoutGrid className="w-10 h-10 text-blue-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-red-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">Critical Projects</p>
                <p className="text-3xl font-bold text-red-600">{criticalProjects}</p>
              </div>
              <AlertCircle className="w-10 h-10 text-red-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">Avg Progress</p>
                <p className="text-3xl font-bold text-green-600">{totalProgress}%</p>
              </div>
              <TrendingUp className="w-10 h-10 text-green-500" />
            </div>
          </div>
          
          <div className="bg-white rounded-xl shadow-md p-6 border-l-4 border-purple-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-600 mb-1">Team Size</p>
                <p className="text-3xl font-bold text-purple-600">{teamOverview?.total_team_size || 0}</p>
              </div>
              <Users className="w-10 h-10 text-purple-500" />
            </div>
          </div>
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
            <h2 className="text-xl font-bold text-slate-900">
              All Projects ({filteredProjects.length})
            </h2>
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
                        <p className="text-sm text-slate-600">{project.code}</p>
                      </div>
                      {getStatusIcon(project.status)}
                    </div>
                    
                    {project.client_name && (
                      <p className="text-xs text-slate-600 mt-2">
                        Client: {project.client_name}
                      </p>
                    )}
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
                        <span className="text-slate-600">Drawings:</span>
                        <span className="font-bold ml-1">
                          {project.completedDrawings}/{project.totalDrawings}
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
              <div className="mt-1 flex gap-2">
                {!isRecording && !audioBlob && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={startRecording}
                    className="flex-1"
                  >
                    <Mic className="w-4 h-4 mr-2" />
                    Record Voice Note
                  </Button>
                )}
                
                {isRecording && (
                  <Button
                    type="button"
                    variant="outline"
                    onClick={stopRecording}
                    className="flex-1 bg-red-50 border-red-300"
                  >
                    <div className="w-2 h-2 bg-red-600 rounded-full animate-pulse mr-2"></div>
                    Stop Recording
                  </Button>
                )}
                
                {audioBlob && (
                  <div className="flex-1 flex items-center gap-2">
                    <div className="flex-1 bg-blue-50 p-2 rounded text-sm text-blue-700">
                      Voice note recorded
                    </div>
                    <button onClick={() => setAudioBlob(null)}>
                      <X className="w-4 h-4 text-red-600" />
                    </button>
                  </div>
                )}
              </div>
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
    </Layout>
  );
}
