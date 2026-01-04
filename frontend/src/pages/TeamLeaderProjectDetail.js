import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import LazyImage from '@/components/LazyImage';
import { ChatView } from '@/components/project';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  ArrowLeft,
  FileText,
  Image,
  User,
  MessageSquare,
  Download,
  Eye,
  Upload,
  Check,
  RefreshCw,
  Clock,
  AlertCircle,
  Send,
  Paperclip,
  Mic,
  Square,
  X,
  Plus,
  ChevronDown,
  ChevronUp,
  Phone,
  Mail
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function TeamLeaderProjectDetail({ user, onLogout }) {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  // State
  const [project, setProject] = useState(null);
  const [drawings, setDrawings] = useState([]);
  const [images3D, setImages3D] = useState([]);
  const [imageCategories, setImageCategories] = useState([]);
  const [comments, setComments] = useState([]);
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('drawings');
  const [expandedCategories, setExpandedCategories] = useState({});
  
  // Dialog states
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [selectedDrawing, setSelectedDrawing] = useState(null);
  const [uploadType, setUploadType] = useState('new'); // 'new' or 'revision'
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState([]);
  
  // 3D Images upload
  const [upload3DDialogOpen, setUpload3DDialogOpen] = useState(false);
  const [selected3DCategory, setSelected3DCategory] = useState('');
  const [custom3DCategory, setCustom3DCategory] = useState('');
  const [selected3DFiles, setSelected3DFiles] = useState([]);
  const [uploading3D, setUploading3D] = useState(false);
  const [preset3DCategories, setPreset3DCategories] = useState([]);
  
  // Comments state
  const [showComments, setShowComments] = useState(false);
  const [showNewComment, setShowNewComment] = useState(false);
  const [commentText, setCommentText] = useState('');
  const [commentFile, setCommentFile] = useState(null);
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [unreadComments, setUnreadComments] = useState(0);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const fileInputRef = useRef(null);
  const drawingFileInputRef = useRef(null);
  const image3DFileInputRef = useRef(null);

  useEffect(() => {
    fetchProjectData();
    fetch3DCategories();
  }, [projectId]);

  const fetchProjectData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      const [projectRes, drawingsRes, images3DRes, commentsRes] = await Promise.all([
        axios.get(`${API}/projects/${projectId}`, { headers }),
        axios.get(`${API}/projects/${projectId}/drawings`, { headers }),
        axios.get(`${API}/projects/${projectId}/3d-images`, { headers }).catch(() => ({ data: { categories: [] } })),
        axios.get(`${API}/projects/${projectId}/comments`, { headers }).catch(() => ({ data: [] }))
      ]);

      setProject(projectRes.data);
      setDrawings(drawingsRes.data || []);
      setImages3D(images3DRes.data?.categories || []);
      setComments(commentsRes.data || []);
      
      // Get client info
      if (projectRes.data.client_id) {
        try {
          const clientRes = await axios.get(`${API}/clients/${projectRes.data.client_id}`, { headers });
          setClient(clientRes.data);
        } catch (err) {
          console.log('Client info not available');
        }
      }
      
      // Check unread comments
      const lastViewed = localStorage.getItem(`comments_viewed_${projectId}`);
      if (lastViewed && commentsRes.data) {
        const unread = commentsRes.data.filter(c => 
          new Date(c.created_at) > new Date(lastViewed)
        ).length;
        setUnreadComments(unread);
      } else {
        setUnreadComments(commentsRes.data?.length || 0);
      }
    } catch (error) {
      console.error('Error fetching project:', error);
      toast.error('Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  const fetch3DCategories = async () => {
    try {
      const response = await axios.get(`${API}/3d-image-categories`);
      setPreset3DCategories(response.data.categories || []);
    } catch (error) {
      console.log('Failed to load 3D categories');
    }
  };

  // Drawing actions
  const handleUploadDrawing = async () => {
    if (selectedFiles.length === 0) {
      toast.error('Please select a file');
      return;
    }

    setUploading(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      selectedFiles.forEach(file => formData.append('files', file));
      formData.append('drawing_id', selectedDrawing.id);
      formData.append('upload_type', uploadType === 'revision' ? 'resolve' : 'issue');

      await axios.post(`${API}/drawings/upload`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      // Update drawing status
      const updatePayload = uploadType === 'revision' 
        ? { has_pending_revision: false, under_review: true }
        : { under_review: true };

      await axios.put(`${API}/drawings/${selectedDrawing.id}`, updatePayload, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success(uploadType === 'revision' ? 'Revision uploaded!' : 'Drawing uploaded!');
      setUploadDialogOpen(false);
      setSelectedFiles([]);
      setSelectedDrawing(null);
      fetchProjectData();
    } catch (error) {
      toast.error('Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleApproveDrawing = async (drawing) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/drawings/${drawing.id}`, {
        is_approved: true,
        under_review: false
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Drawing approved!');
      fetchProjectData();
    } catch (error) {
      toast.error('Failed to approve drawing');
    }
  };

  const handleIssueDrawing = async (drawing) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/drawings/${drawing.id}`, {
        is_issued: true,
        issued_date: new Date().toISOString()
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Drawing issued!');
      fetchProjectData();
    } catch (error) {
      toast.error('Failed to issue drawing');
    }
  };

  const handleMarkAsNotApplicable = async (drawingId) => {
    if (!window.confirm('Mark this drawing as Not Applicable? It will be excluded from progress calculation.')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.patch(`${API}/drawings/${drawingId}/mark-not-applicable`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Drawing marked as Not Applicable');
      fetchProjectData();
    } catch (error) {
      toast.error('Failed to mark drawing as N/A');
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
      const link = document.createElement('a');
      link.href = `${BACKEND_URL}${drawing.file_url}`;
      link.download = drawing.name || 'drawing';
      link.click();
      toast.success('Download started');
    }
  };

  // 3D Images upload
  const handleUpload3DImages = async () => {
    const category = custom3DCategory || selected3DCategory;
    if (!category) {
      toast.error('Please select or enter a category');
      return;
    }
    if (selected3DFiles.length === 0) {
      toast.error('Please select images');
      return;
    }

    setUploading3D(true);
    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('category', category);
      selected3DFiles.forEach(file => formData.append('files', file));

      await axios.post(`${API}/projects/${projectId}/3d-images`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      toast.success(`${selected3DFiles.length} image(s) uploaded!`);
      setUpload3DDialogOpen(false);
      setSelected3DFiles([]);
      setSelected3DCategory('');
      setCustom3DCategory('');
      fetchProjectData();
    } catch (error) {
      toast.error('Failed to upload images');
    } finally {
      setUploading3D(false);
    }
  };

  // Voice recording
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
      
      if (commentFile) formData.append('file', commentFile);
      if (audioBlob) formData.append('voice_note', audioBlob, 'voice_note.webm');

      await axios.post(`${API}/projects/${projectId}/comments`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });

      toast.success('Comment posted!');
      setCommentText('');
      setCommentFile(null);
      setAudioBlob(null);
      setShowNewComment(false);
      fetchProjectData();
    } catch (error) {
      toast.error('Failed to post comment');
    } finally {
      setSubmitting(false);
    }
  };

  const openCommentsPanel = () => {
    setShowComments(true);
    localStorage.setItem(`comments_viewed_${projectId}`, new Date().toISOString());
    setUnreadComments(0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const toggleCategory = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

  // Group drawings by status
  const pendingRevisions = drawings.filter(d => d.has_pending_revision && !d.is_not_applicable);
  const underReview = drawings.filter(d => d.under_review && !d.is_approved && !d.has_pending_revision && !d.is_not_applicable);
  const readyToIssue = drawings.filter(d => d.is_approved && !d.is_issued && !d.is_not_applicable);
  const issued = drawings.filter(d => d.is_issued && !d.has_pending_revision && !d.is_not_applicable);
  const notStarted = drawings.filter(d => !d.file_url && !d.is_issued && !d.has_pending_revision && !d.is_not_applicable);
  const notApplicable = drawings.filter(d => d.is_not_applicable);

  // Progress calculation - excludes N/A drawings
  const applicableDrawings = drawings.filter(d => !d.is_not_applicable);
  const totalDrawings = applicableDrawings.length;
  const issuedCount = issued.length;
  const percentComplete = totalDrawings > 0 ? Math.round((issuedCount / totalDrawings) * 100) : 0;

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="w-8 h-8 border-4 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
        </div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="text-center py-12">
          <p className="text-slate-500">Project not found</p>
          <Button onClick={() => navigate('/team-leader')} className="mt-4">Go Back</Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center gap-3 mb-4">
          <Button variant="ghost" size="sm" onClick={() => navigate('/team-leader')} className="p-2">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div className="flex-1 min-w-0">
            <h1 className="text-xl font-bold text-slate-900 truncate">{project.title}</h1>
            <p className="text-sm text-slate-500 font-mono">{project.code}</p>
          </div>
        </div>

        {/* Progress Card */}
        <Card className="mb-4 border-l-4 border-l-orange-500">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">Progress</span>
              <Badge className="bg-orange-100 text-orange-700">{percentComplete}%</Badge>
            </div>
            <Progress value={percentComplete} className="h-2" />
            <p className="text-xs text-slate-500 mt-2">{issuedCount}/{totalDrawings} drawings issued</p>
          </CardContent>
        </Card>

        {/* Section Tabs */}
        <div className="flex gap-2 mb-4 overflow-x-auto pb-2">
          {['drawings', '3d', 'client', 'comments'].map((section) => (
            <Button
              key={section}
              variant={activeSection === section ? 'default' : 'outline'}
              size="sm"
              onClick={() => setActiveSection(section)}
              className={`shrink-0 ${activeSection === section ? 'bg-orange-500 hover:bg-orange-600' : ''}`}
            >
              {section === 'drawings' && <FileText className="w-4 h-4 mr-1" />}
              {section === '3d' && <Image className="w-4 h-4 mr-1" />}
              {section === 'client' && <User className="w-4 h-4 mr-1" />}
              {section === 'comments' && (
                <div className="relative">
                  <MessageSquare className="w-4 h-4 mr-1" />
                  {unreadComments > 0 && (
                    <span className="absolute -top-2 -right-1 w-4 h-4 bg-red-500 text-white text-[10px] rounded-full flex items-center justify-center">
                      {unreadComments}
                    </span>
                  )}
                </div>
              )}
              {section.charAt(0).toUpperCase() + section.slice(1).replace('3d', '3D')}
            </Button>
          ))}
        </div>

        {/* DRAWINGS SECTION */}
        {activeSection === 'drawings' && (
          <div className="space-y-4">
            {/* Pending Revisions - Red Alert */}
            {pendingRevisions.length > 0 && (
              <Card className="border-red-200 bg-red-50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 text-red-700">
                    <AlertCircle className="w-4 h-4" />
                    Revisions Required ({pendingRevisions.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {pendingRevisions.map(drawing => (
                    <div key={drawing.id} className="bg-white p-3 rounded-lg flex items-center justify-between">
                      <div className="flex-1 min-w-0 mr-2">
                        <p className="font-medium text-sm truncate">{drawing.name}</p>
                        <p className="text-xs text-slate-500">{drawing.category}</p>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => {
                          setSelectedDrawing(drawing);
                          setUploadType('revision');
                          setUploadDialogOpen(true);
                        }}
                        className="bg-red-600 hover:bg-red-700 shrink-0"
                      >
                        <Upload className="w-4 h-4 mr-1" />
                        Upload
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Under Review - Amber */}
            {underReview.length > 0 && (
              <Card className="border-amber-200 bg-amber-50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 text-amber-700">
                    <Clock className="w-4 h-4" />
                    Pending Approval ({underReview.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {underReview.map(drawing => (
                    <div key={drawing.id} className="bg-white p-3 rounded-lg flex items-center justify-between">
                      <div className="flex-1 min-w-0 mr-2">
                        <p className="font-medium text-sm truncate">{drawing.name}</p>
                        <p className="text-xs text-slate-500">{drawing.category}</p>
                      </div>
                      <div className="flex gap-2 shrink-0">
                        <Button size="sm" variant="outline" onClick={() => handleViewDrawing(drawing)}>
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button size="sm" onClick={() => handleApproveDrawing(drawing)} className="bg-green-600 hover:bg-green-700">
                          <Check className="w-4 h-4 mr-1" />
                          Approve
                        </Button>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Ready to Issue - Green */}
            {readyToIssue.length > 0 && (
              <Card className="border-green-200 bg-green-50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 text-green-700">
                    <Check className="w-4 h-4" />
                    Ready to Issue ({readyToIssue.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {readyToIssue.map(drawing => (
                    <div key={drawing.id} className="bg-white p-3 rounded-lg flex items-center justify-between">
                      <div className="flex-1 min-w-0 mr-2">
                        <p className="font-medium text-sm truncate">{drawing.name}</p>
                        <p className="text-xs text-slate-500">{drawing.category}</p>
                      </div>
                      <Button size="sm" onClick={() => handleIssueDrawing(drawing)} className="bg-blue-600 hover:bg-blue-700 shrink-0">
                        Issue
                      </Button>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Not Started */}
            {notStarted.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 text-slate-600">
                    <FileText className="w-4 h-4" />
                    Not Started ({notStarted.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {notStarted.map(drawing => (
                    <div key={drawing.id} className="bg-slate-50 p-3 rounded-lg flex items-center justify-between">
                      <div className="flex-1 min-w-0 mr-2">
                        <p className="font-medium text-sm truncate">{drawing.name}</p>
                        <p className="text-xs text-slate-500">{drawing.category}</p>
                      </div>
                      <div className="flex gap-1 shrink-0">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => {
                            setSelectedDrawing(drawing);
                            setUploadType('new');
                            setUploadDialogOpen(true);
                          }}
                        >
                          <Upload className="w-4 h-4 mr-1" />
                          Upload
                        </Button>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleMarkAsNotApplicable(drawing.id)}
                          className="text-slate-500 hover:text-slate-700"
                          title="Mark as Not Applicable"
                        >
                          N/A
                        </Button>
                      </div>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Not Applicable Section */}
            {notApplicable.length > 0 && (
              <Card className="border-slate-200 bg-slate-50 opacity-60">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 text-slate-500">
                    <X className="w-4 h-4" />
                    Not Applicable ({notApplicable.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {notApplicable.map(drawing => (
                    <div key={drawing.id} className="bg-white/50 p-3 rounded-lg">
                      <p className="font-medium text-sm text-slate-500 truncate">{drawing.name}</p>
                      <p className="text-xs text-slate-400">{drawing.category}</p>
                    </div>
                  ))}
                </CardContent>
              </Card>
            )}

            {/* Issued */}
            {issued.length > 0 && (
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm flex items-center gap-2 text-slate-600">
                    <Check className="w-4 h-4 text-green-600" />
                    Issued ({issued.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  {issued.slice(0, 5).map(drawing => (
                    <div key={drawing.id} className="bg-slate-50 p-3 rounded-lg flex items-center justify-between">
                      <div className="flex-1 min-w-0 mr-2">
                        <p className="font-medium text-sm truncate">{drawing.name}</p>
                        <p className="text-xs text-slate-500">{drawing.category} • Rev {drawing.current_revision || 0}</p>
                      </div>
                      <div className="flex gap-1 shrink-0">
                        <Button size="sm" variant="ghost" onClick={() => handleViewDrawing(drawing)}>
                          <Eye className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => handleDownloadDrawing(drawing)}>
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                  {issued.length > 5 && (
                    <p className="text-xs text-center text-slate-500">+{issued.length - 5} more issued drawings</p>
                  )}
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* 3D IMAGES SECTION */}
        {activeSection === '3d' && (
          <div className="space-y-4">
            <Button
              onClick={() => setUpload3DDialogOpen(true)}
              className="w-full bg-purple-600 hover:bg-purple-700"
            >
              <Plus className="w-4 h-4 mr-2" />
              Upload 3D Images
            </Button>

            {images3D.length === 0 ? (
              <div className="text-center py-12 bg-slate-50 rounded-lg">
                <Image className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                <p className="text-slate-500">No 3D images yet</p>
                <p className="text-xs text-slate-400">Upload room-wise visualizations</p>
              </div>
            ) : (
              images3D.map(({ category, images }) => (
                <Card key={category}>
                  <CardHeader 
                    className="pb-2 cursor-pointer"
                    onClick={() => toggleCategory(category)}
                  >
                    <CardTitle className="text-sm flex items-center justify-between">
                      <span className="flex items-center gap-2">
                        <Image className="w-4 h-4 text-purple-600" />
                        {category} ({images.length})
                      </span>
                      {expandedCategories[category] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </CardTitle>
                  </CardHeader>
                  {expandedCategories[category] && (
                    <CardContent>
                      <div className="grid grid-cols-2 gap-2">
                        {images.map(img => (
                          <div key={img.id} className="relative aspect-video bg-slate-100 rounded-lg overflow-hidden">
                            <LazyImage
                              src={`${BACKEND_URL}${img.file_url}`}
                              alt={img.title || category}
                              className="w-full h-full object-cover"
                              placeholderClassName="aspect-video"
                            />
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  )}
                </Card>
              ))
            )}
          </div>
        )}

        {/* CLIENT SECTION */}
        {activeSection === 'client' && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <User className="w-5 h-5 text-green-600" />
                Client Information
              </CardTitle>
            </CardHeader>
            <CardContent>
              {client ? (
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center shrink-0">
                    <User className="w-8 h-8 text-green-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-slate-900">{client.name}</h3>
                    {client.email && (
                      <a href={`mailto:${client.email}`} className="flex items-center gap-1 text-sm text-blue-600 hover:underline">
                        <Mail className="w-3 h-3" />
                        {client.email}
                      </a>
                    )}
                    {client.phone && (
                      <a href={`tel:${client.phone}`} className="flex items-center gap-1 text-sm text-blue-600 hover:underline">
                        <Phone className="w-3 h-3" />
                        {client.phone}
                      </a>
                    )}
                  </div>
                </div>
              ) : (
                <p className="text-center text-slate-500 py-4">No client assigned</p>
              )}
            </CardContent>
          </Card>
        )}

        {/* COMMENTS SECTION - WhatsApp Style */}
        {activeSection === 'comments' && (
          <Card className="overflow-hidden">
            <div className="bg-gradient-to-r from-purple-600 to-purple-700 px-4 py-3">
              <h3 className="text-white font-medium text-sm">Project Discussion</h3>
              <p className="text-purple-200 text-xs">{comments.length} {comments.length === 1 ? 'message' : 'messages'}</p>
            </div>
            <div className="h-[400px]">
              <ChatView
                messages={comments}
                currentUserId={user?.id}
                loading={loading}
                onSendMessage={handleSendComment}
                placeholder="Type a message..."
                emptyStateText="No messages yet"
                emptyStateSubtext="Start the project discussion"
              />
            </div>
          </Card>
        )}

        {/* Upload Drawing Dialog */}
        <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>
                {uploadType === 'revision' ? 'Upload Revision' : 'Upload Drawing'}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              {selectedDrawing && (
                <div className="bg-slate-50 p-3 rounded-lg">
                  <p className="font-medium">{selectedDrawing.name}</p>
                  <p className="text-sm text-slate-500">{selectedDrawing.category}</p>
                </div>
              )}
              <div>
                <input
                  type="file"
                  ref={drawingFileInputRef}
                  onChange={(e) => setSelectedFiles(Array.from(e.target.files || []))}
                  accept=".pdf"
                  className="hidden"
                />
                <Button
                  variant="outline"
                  onClick={() => drawingFileInputRef.current?.click()}
                  className="w-full"
                >
                  <Paperclip className="w-4 h-4 mr-2" />
                  {selectedFiles.length > 0 ? selectedFiles[0].name : 'Select PDF'}
                </Button>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setUploadDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleUploadDrawing} disabled={uploading || selectedFiles.length === 0} className="bg-orange-500 hover:bg-orange-600">
                {uploading ? 'Uploading...' : 'Upload'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Upload 3D Images Dialog */}
        <Dialog open={upload3DDialogOpen} onOpenChange={setUpload3DDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Upload 3D Images</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Category</Label>
                <select
                  value={selected3DCategory}
                  onChange={(e) => {
                    setSelected3DCategory(e.target.value);
                    if (e.target.value !== 'custom') setCustom3DCategory('');
                  }}
                  className="w-full p-2 border rounded-lg mt-1"
                >
                  <option value="">Select category...</option>
                  {preset3DCategories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                  <option value="custom">+ Custom Category</option>
                </select>
              </div>
              {selected3DCategory === 'custom' && (
                <div>
                  <Label>Custom Category Name</Label>
                  <Input
                    value={custom3DCategory}
                    onChange={(e) => setCustom3DCategory(e.target.value)}
                    placeholder="e.g., Entertainment Room"
                    className="mt-1"
                  />
                </div>
              )}
              <div>
                <input
                  type="file"
                  ref={image3DFileInputRef}
                  onChange={(e) => setSelected3DFiles(Array.from(e.target.files || []))}
                  accept="image/*"
                  multiple
                  className="hidden"
                />
                <Button
                  variant="outline"
                  onClick={() => image3DFileInputRef.current?.click()}
                  className="w-full"
                >
                  <Image className="w-4 h-4 mr-2" />
                  {selected3DFiles.length > 0 ? `${selected3DFiles.length} image(s) selected` : 'Select Images'}
                </Button>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setUpload3DDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleUpload3DImages} disabled={uploading3D} className="bg-purple-600 hover:bg-purple-700">
                {uploading3D ? 'Uploading...' : 'Upload'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* New Comment Dialog */}
        <Dialog open={showNewComment} onOpenChange={setShowNewComment}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>New Comment</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Write your comment..."
                className="w-full min-h-[100px] p-3 border rounded-lg resize-none"
              />
              <div>
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={(e) => setCommentFile(e.target.files?.[0])}
                  className="hidden"
                />
                <Button variant="outline" onClick={() => fileInputRef.current?.click()} className="w-full justify-start">
                  <Paperclip className="w-4 h-4 mr-2" />
                  {commentFile ? commentFile.name : 'Attach File'}
                </Button>
              </div>
              <div>
                {!audioBlob ? (
                  <Button
                    variant="outline"
                    onClick={isRecording ? stopRecording : startRecording}
                    className={`w-full justify-start ${isRecording ? 'bg-red-50 border-red-300 text-red-700' : ''}`}
                  >
                    {isRecording ? <><Square className="w-4 h-4 mr-2" />Stop Recording</> : <><Mic className="w-4 h-4 mr-2" />Record Voice</>}
                  </Button>
                ) : (
                  <div className="flex items-center gap-2">
                    <audio controls src={URL.createObjectURL(audioBlob)} className="flex-1 h-10" />
                    <Button variant="ghost" size="sm" onClick={() => setAudioBlob(null)}><X className="w-4 h-4" /></Button>
                  </div>
                )}
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowNewComment(false)}>Cancel</Button>
              <Button onClick={handleSubmitComment} disabled={submitting} className="bg-orange-500 hover:bg-orange-600">
                {submitting ? 'Posting...' : 'Post'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
