import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import LazyImage from '@/components/LazyImage';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import {
  ArrowLeft,
  FileText,
  Image,
  User,
  MessageSquare,
  Download,
  Eye,
  Calendar,
  Send,
  Paperclip,
  Mic,
  Square,
  X,
  ChevronRight,
  ChevronDown,
  ChevronUp,
  Clock,
  Phone,
  Mail
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function ExternalProjectDetail({ user, onLogout }) {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  // State
  const [project, setProject] = useState(null);
  const [drawings, setDrawings] = useState([]);
  const [images3D, setImages3D] = useState([]);
  const [teamLeader, setTeamLeader] = useState(null);
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState(null);
  const [expandedCategories, setExpandedCategories] = useState({});
  
  // Comments state
  const [showComments, setShowComments] = useState(false);
  const [showNewComment, setShowNewComment] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [commentFile, setCommentFile] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [unreadComments, setUnreadComments] = useState(0);
  
  // Audio recording refs
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const fileInputRef = useRef(null);

  useEffect(() => {
    fetchProjectData();
    fetchComments();
  }, [projectId]);

  const fetchProjectData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [projectRes, drawingsRes, images3DRes] = await Promise.all([
        axios.get(`${API}/projects/${projectId}`, { headers }),
        axios.get(`${API}/projects/${projectId}/drawings`, { headers }),
        axios.get(`${API}/projects/${projectId}/3d-images`, { headers }).catch(() => ({ data: { categories: [] } }))
      ]);

      setProject(projectRes.data);
      setDrawings(drawingsRes.data || []);
      setImages3D(images3DRes.data?.categories || []);
      
      // Get team leader info - try from project response first, then fetch if needed
      if (projectRes.data.team_leader_name) {
        // Team leader info already in project response
        setTeamLeader({
          id: projectRes.data.team_leader_id,
          name: projectRes.data.team_leader_name,
          email: projectRes.data.team_leader_email,
          mobile: projectRes.data.team_leader_phone,
          role: projectRes.data.team_leader_role
        });
      } else if (projectRes.data.team_leader_id) {
        // Fetch team leader details
        try {
          const leaderRes = await axios.get(`${API}/users/${projectRes.data.team_leader_id}`, { headers });
          setTeamLeader(leaderRes.data);
        } catch (err) {
          console.log('Team leader info not available via API, using project data');
        }
      }
    } catch (error) {
      console.error('Error fetching project:', error);
      toast.error('Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  const fetchComments = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/projects/${projectId}/comments`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setComments(response.data || []);
      
      // Check for unread comments (simplified - in production would track last viewed)
      const lastViewed = localStorage.getItem(`comments_viewed_${projectId}`);
      if (lastViewed) {
        const unread = (response.data || []).filter(c => 
          new Date(c.created_at) > new Date(lastViewed)
        ).length;
        setUnreadComments(unread);
      } else {
        setUnreadComments(response.data?.length || 0);
      }
    } catch (error) {
      console.log('Comments not available');
    }
  };

  const handleViewDrawing = (drawing) => {
    if (drawing.file_url) {
      // Ensure full URL with backend
      const fullUrl = drawing.file_url.startsWith('http') 
        ? drawing.file_url 
        : `${BACKEND_URL}${drawing.file_url}`;
      window.open(fullUrl, '_blank');
    } else {
      toast.error('Drawing file not available');
    }
  };

  const handleDownloadDrawing = async (drawing) => {
    if (drawing.file_url) {
      // Ensure full URL with backend
      const fullUrl = drawing.file_url.startsWith('http') 
        ? drawing.file_url 
        : `${BACKEND_URL}${drawing.file_url}`;
      const link = document.createElement('a');
      link.href = fullUrl;
      link.download = drawing.name || 'drawing';
      link.target = '_blank';
      link.click();
      toast.success('Download started');
    } else {
      toast.error('Drawing file not available');
    }
  };

  // Voice recording functions
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
      toast.error('Could not access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleSubmitComment = async () => {
    if (!commentText.trim() && !commentFile && !audioBlob) {
      toast.error('Please add text, file, or voice note');
      return;
    }

    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('text', commentText);
      formData.append('project_id', projectId);
      
      if (commentFile) {
        formData.append('file', commentFile);
      }
      
      if (audioBlob) {
        formData.append('voice_note', audioBlob, 'voice_note.webm');
      }

      await axios.post(`${API}/projects/${projectId}/comments`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      toast.success('Comment posted successfully');
      setCommentText('');
      setCommentFile(null);
      setAudioBlob(null);
      setShowNewComment(false);
      fetchComments();
    } catch (error) {
      toast.error('Failed to post comment');
    } finally {
      setSubmitting(false);
    }
  };

  const openCommentsPanel = () => {
    setShowComments(true);
    // Mark as viewed
    localStorage.setItem(`comments_viewed_${projectId}`, new Date().toISOString());
    setUnreadComments(0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Calculate stats
  const totalDrawings = drawings.length;
  const issuedDrawings = drawings.filter(d => d.is_issued).length;
  const percentComplete = totalDrawings > 0 ? Math.round((issuedDrawings / totalDrawings) * 100) : 0;

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-slate-500">Loading project...</p>
          </div>
        </div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="text-center py-12">
          <p className="text-slate-500">Project not found</p>
          <Button onClick={() => navigate('/external-dashboard')} className="mt-4">
            Go Back
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => navigate('/external-dashboard')}
            className="p-2"
          >
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl sm:text-2xl font-bold text-slate-900 truncate">
              {project.title || project.name}
            </h1>
            {project.code && (
              <p className="text-sm text-slate-500 font-mono">
                {project.code}
              </p>
            )}
          </div>
        </div>

        {/* Progress Card */}
        <Card className="mb-6 border-l-4 border-l-orange-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-slate-700">Project Progress</span>
              <Badge className="bg-orange-100 text-orange-700">{percentComplete}%</Badge>
            </div>
            <Progress value={percentComplete} className="h-2 bg-slate-100" />
            <p className="text-xs text-slate-500 mt-2">
              {issuedDrawings} drawings issued
            </p>
          </CardContent>
        </Card>

        {/* Action Cards Grid */}
        <div className="grid grid-cols-2 gap-4 mb-6">
          {/* Drawings Card */}
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md active:scale-[0.98] ${
              activeSection === 'drawings' ? 'ring-2 ring-orange-500' : ''
            }`}
            onClick={() => setActiveSection(activeSection === 'drawings' ? null : 'drawings')}
          >
            <CardContent className="p-4 text-center">
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-2">
                <FileText className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-semibold text-slate-900">Drawings</h3>
              <p className="text-xs text-slate-500">{totalDrawings} files</p>
            </CardContent>
          </Card>

          {/* 3D Images Card */}
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md active:scale-[0.98] ${
              activeSection === '3d' ? 'ring-2 ring-orange-500' : ''
            }`}
            onClick={() => setActiveSection(activeSection === '3d' ? null : '3d')}
          >
            <CardContent className="p-4 text-center">
              <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-2">
                <Image className="w-6 h-6 text-purple-600" />
              </div>
              <h3 className="font-semibold text-slate-900">3D Images</h3>
              <p className="text-xs text-slate-500">
                {images3D.reduce((sum, cat) => sum + (cat.images?.length || 0), 0)} images
              </p>
            </CardContent>
          </Card>

          {/* Team Leader Card */}
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md active:scale-[0.98] ${
              activeSection === 'leader' ? 'ring-2 ring-orange-500' : ''
            }`}
            onClick={() => setActiveSection(activeSection === 'leader' ? null : 'leader')}
          >
            <CardContent className="p-4 text-center">
              <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-2">
                <User className="w-6 h-6 text-green-600" />
              </div>
              <h3 className="font-semibold text-slate-900">Team Leader</h3>
              <p className="text-xs text-slate-500 truncate">
                {teamLeader?.name || project.team_leader_name || 'Not assigned'}
              </p>
            </CardContent>
          </Card>

          {/* Comments Card */}
          <Card 
            className={`cursor-pointer transition-all hover:shadow-md active:scale-[0.98] relative ${
              activeSection === 'comments' ? 'ring-2 ring-orange-500' : ''
            }`}
            onClick={() => {
              setActiveSection(activeSection === 'comments' ? null : 'comments');
              if (activeSection !== 'comments') {
                localStorage.setItem(`comments_viewed_${projectId}`, new Date().toISOString());
                setUnreadComments(0);
              }
            }}
          >
            <CardContent className="p-4 text-center">
              <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-2 relative">
                <MessageSquare className="w-6 h-6 text-orange-600" />
                {unreadComments > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {unreadComments > 9 ? '9+' : unreadComments}
                  </span>
                )}
              </div>
              <h3 className="font-semibold text-slate-900">Comments</h3>
              <p className="text-xs text-slate-500">{comments.length} messages</p>
            </CardContent>
          </Card>
        </div>

        {/* Expanded Sections */}
        {activeSection === 'drawings' && (
          <Card className="mb-6 animate-in slide-in-from-top-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <FileText className="w-5 h-5 text-blue-600" />
                Drawings
              </CardTitle>
            </CardHeader>
            <CardContent>
              {drawings.length === 0 ? (
                <p className="text-center text-slate-500 py-8">No drawings uploaded yet</p>
              ) : (
                <div className="space-y-3">
                  {drawings.filter(d => d.is_issued).map((drawing) => (
                    <div 
                      key={drawing.id}
                      className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                    >
                      <div className="flex-1 min-w-0 mr-3">
                        <p className="font-medium text-slate-900 truncate">{drawing.name}</p>
                        <div className="flex items-center gap-2 text-xs text-slate-500">
                          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                            Issued
                          </Badge>
                          {drawing.current_revision && (
                            <span>Rev {drawing.current_revision}</span>
                          )}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleViewDrawing(drawing)}
                          className="p-2"
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => handleDownloadDrawing(drawing)}
                          className="p-2"
                        >
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {drawings.filter(d => !d.is_issued).length > 0 && (
                    <p className="text-xs text-slate-400 text-center pt-2">
                      {drawings.filter(d => !d.is_issued).length} drawings pending issue
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {activeSection === '3d' && (
          <Card className="mb-6 animate-in slide-in-from-top-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <Image className="w-5 h-5 text-purple-600" />
                3D Images
              </CardTitle>
            </CardHeader>
            <CardContent>
              {images3D.length === 0 ? (
                <div className="text-center py-8">
                  <Image className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No 3D images uploaded yet</p>
                  <p className="text-xs text-slate-400 mt-1">Room-wise visualizations will appear here</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {images3D.map(({ category, images }) => (
                    <div key={category} className="border rounded-lg overflow-hidden">
                      <button
                        onClick={() => setExpandedCategories(prev => ({
                          ...prev,
                          [category]: !prev[category]
                        }))}
                        className="w-full flex items-center justify-between p-3 bg-slate-50 hover:bg-slate-100 transition-colors"
                      >
                        <div className="flex items-center gap-2">
                          <Image className="w-4 h-4 text-purple-600" />
                          <span className="font-medium text-slate-900">{category}</span>
                          <Badge variant="outline" className="text-xs">{images.length}</Badge>
                        </div>
                        {expandedCategories[category] ? (
                          <ChevronUp className="w-4 h-4 text-slate-500" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-slate-500" />
                        )}
                      </button>
                      {expandedCategories[category] && (
                        <div className="p-3 grid grid-cols-2 gap-2">
                          {images.map((img) => (
                            <div 
                              key={img.id} 
                              className="relative aspect-video bg-slate-100 rounded-lg overflow-hidden cursor-pointer hover:opacity-90 transition-opacity"
                              onClick={() => window.open(`${BACKEND_URL}${img.file_url}`, '_blank')}
                            >
                              <LazyImage
                                src={`${BACKEND_URL}${img.file_url}`}
                                alt={img.title || category}
                                className="w-full h-full object-cover"
                                placeholderClassName="aspect-video"
                              />
                              <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-2">
                                <p className="text-white text-xs truncate">{img.title || 'View Image'}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {activeSection === 'leader' && (
          <Card className="mb-6 animate-in slide-in-from-top-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                <User className="w-5 h-5 text-green-600" />
                Team Leader
              </CardTitle>
            </CardHeader>
            <CardContent>
              {teamLeader || project.team_leader_name ? (
                <div 
                  className="flex items-center gap-4 cursor-pointer hover:bg-slate-50 p-2 rounded-lg -m-2 transition-colors"
                  onClick={() => {
                    const leaderId = teamLeader?.id || project.team_leader_id;
                    if (leaderId) navigate(`/team/${leaderId}`);
                  }}
                >
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                    <User className="w-8 h-8 text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-slate-900 hover:text-orange-600">
                      {teamLeader?.name || project.team_leader_name}
                    </h3>
                    {teamLeader?.email && (
                      <a 
                        href={`mailto:${teamLeader.email}`}
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-1 text-sm text-blue-600 hover:underline"
                      >
                        <Mail className="w-3 h-3" />
                        {teamLeader.email}
                      </a>
                    )}
                    {teamLeader?.mobile && (
                      <a 
                        href={`tel:${teamLeader.mobile}`}
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-1 text-sm text-blue-600 hover:underline"
                      >
                        <Phone className="w-3 h-3" />
                        {teamLeader.mobile}
                      </a>
                    )}
                    <p className="text-xs text-orange-500 mt-1">Tap to view profile</p>
                  </div>
                </div>
              ) : (
                <p className="text-center text-slate-500 py-4">Team leader not assigned yet</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Comments Section - Inline */}
        {activeSection === 'comments' && (
          <Card className="mb-6 animate-in slide-in-from-top-2">
            <CardHeader className="pb-3 flex flex-row items-center justify-between">
              <CardTitle className="text-lg flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-orange-600" />
                Comments
              </CardTitle>
              <Button
                onClick={() => setShowNewComment(true)}
                className="bg-orange-500 hover:bg-orange-600"
                size="sm"
              >
                <Send className="w-4 h-4 mr-1" />
                Post Comment
              </Button>
            </CardHeader>
            <CardContent>
              {comments.length === 0 ? (
                <div className="text-center py-8">
                  <MessageSquare className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <p className="text-slate-500">No comments yet</p>
                  <p className="text-xs text-slate-400">Start the conversation!</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {comments.map((comment) => (
                    <div key={comment.id} className="bg-slate-50 rounded-lg p-3">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center shrink-0">
                          <User className="w-4 h-4 text-orange-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-slate-900 text-sm">
                              {comment.user_name || 'User'}
                            </span>
                            <span className="text-xs text-slate-400">
                              {formatDate(comment.created_at)}
                            </span>
                          </div>
                          {comment.text && (
                            <p className="text-sm text-slate-700">{comment.text}</p>
                          )}
                          {comment.file_url && (
                            <a 
                              href={comment.file_url.startsWith('http') ? comment.file_url : `${BACKEND_URL}${comment.file_url}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-1"
                            >
                              <Paperclip className="w-3 h-3" />
                              Attached file
                            </a>
                          )}
                          {comment.voice_note_url && (
                            <audio 
                              controls 
                              src={comment.voice_note_url.startsWith('http') ? comment.voice_note_url : `${BACKEND_URL}${comment.voice_note_url}`}
                              className="mt-2 w-full h-8"
                            />
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Floating Comments Button - Only show when comments section is not active */}
        {activeSection !== 'comments' && (
          <button
            onClick={() => {
              setActiveSection('comments');
              localStorage.setItem(`comments_viewed_${projectId}`, new Date().toISOString());
              setUnreadComments(0);
            }}
            className="fixed bottom-6 right-6 w-14 h-14 bg-orange-500 hover:bg-orange-600 text-white rounded-full shadow-lg flex items-center justify-center transition-all active:scale-95 z-40"
          >
            <MessageSquare className="w-6 h-6" />
            {unreadComments > 0 && (
              <span className="absolute -top-1 -right-1 w-6 h-6 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
                {unreadComments > 9 ? '9+' : unreadComments}
              </span>
            )}
          </button>
        )}

        {/* Comments Panel (Slide-up modal) */}
        <Dialog open={showComments} onOpenChange={setShowComments}>
          <DialogContent className="max-w-lg max-h-[80vh] flex flex-col p-0">
            <DialogHeader className="p-4 border-b">
              <DialogTitle className="flex items-center gap-2">
                <MessageSquare className="w-5 h-5 text-orange-600" />
                Comments
              </DialogTitle>
            </DialogHeader>
            
            <div className="flex-1 overflow-y-auto p-4">
              {comments.length === 0 ? (
                <div className="text-center py-8">
                  <MessageSquare className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                  <p className="text-slate-500">No comments yet</p>
                  <p className="text-xs text-slate-400">Start the conversation!</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {comments.map((comment) => (
                    <div key={comment.id} className="bg-slate-50 rounded-lg p-3">
                      <div className="flex items-start gap-3">
                        <div className="w-8 h-8 bg-orange-100 rounded-full flex items-center justify-center shrink-0">
                          <User className="w-4 h-4 text-orange-600" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium text-slate-900 text-sm">
                              {comment.user_name || 'User'}
                            </span>
                            <span className="text-xs text-slate-400">
                              {formatDate(comment.created_at)}
                            </span>
                          </div>
                          {comment.text && (
                            <p className="text-sm text-slate-700">{comment.text}</p>
                          )}
                          {comment.file_url && (
                            <a 
                              href={comment.file_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="inline-flex items-center gap-1 text-xs text-blue-600 hover:underline mt-1"
                            >
                              <Paperclip className="w-3 h-3" />
                              Attached file
                            </a>
                          )}
                          {comment.voice_note_url && (
                            <audio 
                              controls 
                              src={comment.voice_note_url}
                              className="mt-2 w-full h-8"
                            />
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Post Comment Button */}
            <div className="p-4 border-t">
              <Button 
                onClick={() => setShowNewComment(true)}
                className="w-full bg-orange-500 hover:bg-orange-600"
              >
                <Send className="w-4 h-4 mr-2" />
                Post Comment
              </Button>
            </div>
          </DialogContent>
        </Dialog>

        {/* New Comment Dialog */}
        <Dialog open={showNewComment} onOpenChange={setShowNewComment}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>New Comment</DialogTitle>
            </DialogHeader>
            
            <div className="space-y-4">
              {/* Text Input */}
              <div>
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  placeholder="Write your comment..."
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              {/* File Upload */}
              <div>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => setCommentFile(e.target.files?.[0])}
                  className="hidden"
                />
                <Button
                  variant="outline"
                  onClick={() => fileInputRef.current?.click()}
                  className="w-full justify-start"
                >
                  <Paperclip className="w-4 h-4 mr-2" />
                  {commentFile ? commentFile.name : 'Attach File'}
                </Button>
                {commentFile && (
                  <button
                    onClick={() => setCommentFile(null)}
                    className="text-xs text-red-500 hover:underline mt-1"
                  >
                    Remove file
                  </button>
                )}
              </div>

              {/* Voice Recording */}
              <div>
                {!audioBlob ? (
                  <Button
                    variant="outline"
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`w-full justify-start ${isRecording ? 'bg-red-50 border-red-300 text-red-700' : ''}`}
                  >
                    {isRecording ? (
                      <>
                        <Square className="w-4 h-4 mr-2" />
                        Stop Recording...
                      </>
                    ) : (
                      <>
                        <Mic className="w-4 h-4 mr-2" />
                        Record Voice Note
                      </>
                    )}
                  </Button>
                ) : (
                  <div className="flex items-center gap-2">
                    <audio controls src={URL.createObjectURL(audioBlob)} className="flex-1 h-10" />
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setAudioBlob(null)}
                    >
                      <X className="w-4 h-4" />
                    </Button>
                  </div>
                )}
              </div>
            </div>

            <DialogFooter className="mt-4">
              <Button variant="outline" onClick={() => setShowNewComment(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleSubmitComment}
                disabled={submitting || (!commentText.trim() && !commentFile && !audioBlob)}
                className="bg-orange-500 hover:bg-orange-600"
              >
                {submitting ? 'Posting...' : 'Post Comment'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
