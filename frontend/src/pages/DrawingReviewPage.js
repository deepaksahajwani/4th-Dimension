import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import {
  ArrowLeft,
  Download,
  Eye,
  Check,
  X,
  MessageSquare,
  Send,
  AlertTriangle,
  FileText,
  Image,
  RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function DrawingReviewPage({ user, onLogout }) {
  const { projectId, drawingId, imageId } = useParams();
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [item, setItem] = useState(null); // Drawing or 3D image
  const [itemType, setItemType] = useState(drawingId ? 'drawing' : '3d-image');
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [actionTaken, setActionTaken] = useState(false);

  useEffect(() => {
    fetchData();
  }, [projectId, drawingId, imageId]);

  const fetchData = async () => {
    try {
      // Get token if available - for magic link users, auth is via httponly cookie
      const token = localStorage.getItem('token');
      const useCookieAuth = localStorage.getItem('use_cookie_auth');
      
      // Build request config - include withCredentials for cookie-based auth
      const config = {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        withCredentials: useCookieAuth ? true : false
      };

      // Fetch project
      const projectRes = await axios.get(`${API}/projects/${projectId}`, config);
      setProject(projectRes.data);

      if (drawingId) {
        // Fetch specific drawing
        const drawingsRes = await axios.get(`${API}/projects/${projectId}/drawings`, config);
        const drawing = drawingsRes.data.find(d => d.id === drawingId);
        if (drawing) {
          setItem(drawing);
          setItemType('drawing');
          // Fetch comments for this drawing
          try {
            const commentsRes = await axios.get(`${API}/drawings/${drawingId}/comments`, config);
            setComments(commentsRes.data || []);
          } catch (e) {
            setComments([]);
          }
        } else {
          toast.error('Drawing not found');
          navigate(`/projects/${projectId}`);
        }
      } else if (imageId) {
        // Fetch specific 3D image
        const imagesRes = await axios.get(`${API}/projects/${projectId}/3d-images`, { headers });
        let foundImage = null;
        for (const category of imagesRes.data.categories || []) {
          const img = category.images.find(i => i.id === imageId);
          if (img) {
            foundImage = { ...img, category: category.category };
            break;
          }
        }
        if (foundImage) {
          setItem(foundImage);
          setItemType('3d-image');
        } else {
          toast.error('Image not found');
          navigate(`/projects/${projectId}`);
        }
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load item');
    } finally {
      setLoading(false);
    }
  };

  const handleView = () => {
    if (item?.file_url) {
      window.open(`${BACKEND_URL}${item.file_url}`, '_blank');
    }
  };

  const handleDownload = () => {
    if (item?.file_url) {
      const link = document.createElement('a');
      link.href = `${BACKEND_URL}${item.file_url}`;
      link.download = item.name || item.title || 'download';
      link.click();
    }
  };

  const handleApprove = async () => {
    if (itemType !== 'drawing') return;
    
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const useCookieAuth = localStorage.getItem('use_cookie_auth');
      const config = {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        withCredentials: useCookieAuth ? true : false
      };
      await axios.put(`${API}/drawings/${drawingId}`, {
        is_approved: true,
        under_review: false
      }, config);
      toast.success('Drawing approved!');
      setActionTaken(true);
      setItem(prev => ({ ...prev, is_approved: true, under_review: false }));
    } catch (error) {
      toast.error('Failed to approve drawing');
    } finally {
      setSubmitting(false);
    }
  };

  const handleRequestRevision = async () => {
    if (itemType !== 'drawing' || !newComment.trim()) {
      toast.error('Please add a comment explaining the revision needed');
      return;
    }
    
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      // Add comment with revision flag
      await axios.post(`${API}/drawings/${drawingId}/comments`, {
        text: newComment,
        requires_revision: true
      }, { headers });
      
      // Update drawing status
      await axios.put(`${API}/drawings/${drawingId}`, {
        has_pending_revision: true,
        under_review: false,
        is_approved: false
      }, { headers });
      
      toast.success('Revision requested');
      setActionTaken(true);
      setNewComment('');
      setItem(prev => ({ ...prev, has_pending_revision: true, under_review: false }));
    } catch (error) {
      toast.error('Failed to request revision');
    } finally {
      setSubmitting(false);
    }
  };

  const handleAddComment = async () => {
    if (!newComment.trim()) return;
    
    setSubmitting(true);
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      
      if (itemType === 'drawing') {
        await axios.post(`${API}/drawings/${drawingId}/comments`, {
          text: newComment
        }, { headers });
      } else {
        // For 3D images - add to project comments
        await axios.post(`${API}/projects/${projectId}/comments`, {
          text: newComment,
          image_id: imageId
        }, { headers });
      }
      
      toast.success('Comment added');
      setNewComment('');
      fetchData(); // Refresh to show new comment
    } catch (error) {
      toast.error('Failed to add comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDoneSkip = () => {
    navigate(`/projects/${projectId}`);
  };

  const getStatusBadge = () => {
    if (itemType !== 'drawing') return null;
    
    if (item?.is_issued) {
      return <Badge className="bg-green-100 text-green-700">Issued</Badge>;
    }
    if (item?.is_approved) {
      return <Badge className="bg-blue-100 text-blue-700">Approved</Badge>;
    }
    if (item?.has_pending_revision) {
      return <Badge className="bg-red-100 text-red-700">Revision Needed</Badge>;
    }
    if (item?.under_review) {
      return <Badge className="bg-amber-100 text-amber-700">Pending Approval</Badge>;
    }
    return <Badge className="bg-slate-100 text-slate-600">Not Started</Badge>;
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
        </div>
      </Layout>
    );
  }

  if (!item) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="max-w-2xl mx-auto px-4 py-8 text-center">
          <AlertTriangle className="w-16 h-16 text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Item Not Found</h2>
          <p className="text-slate-600 mb-4">The requested item could not be found.</p>
          <Button onClick={handleDoneSkip}>Go to Project</Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-3xl mx-auto px-4 py-6">
        {/* Header with project context */}
        <div className="mb-6">
          <button 
            onClick={handleDoneSkip}
            className="flex items-center text-sm text-slate-500 hover:text-slate-700 mb-2"
          >
            <ArrowLeft className="w-4 h-4 mr-1" />
            Back to {project?.title || 'Project'}
          </button>
          <p className="text-xs text-slate-400 font-mono">{project?.code}</p>
        </div>

        {/* Main Card - The Item */}
        <Card className="mb-6 border-2 border-orange-200 shadow-lg">
          <CardHeader className="pb-3">
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                {itemType === 'drawing' ? (
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <FileText className="w-6 h-6 text-blue-600" />
                  </div>
                ) : (
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Image className="w-6 h-6 text-purple-600" />
                  </div>
                )}
                <div>
                  <CardTitle className="text-lg">
                    {item.name || item.title || 'Untitled'}
                  </CardTitle>
                  <p className="text-sm text-slate-500">
                    {item.category || 'Uncategorized'}
                  </p>
                </div>
              </div>
              {getStatusBadge()}
            </div>
          </CardHeader>
          
          <CardContent className="space-y-4">
            {/* Preview - Image or PDF indicator */}
            {item.file_url && (
              <div className="relative bg-slate-100 rounded-lg overflow-hidden">
                {itemType === '3d-image' || item.file_url?.match(/\.(jpg|jpeg|png|gif|webp)$/i) ? (
                  <img 
                    src={`${BACKEND_URL}${item.file_url}`}
                    alt={item.name || item.title}
                    className="w-full max-h-[400px] object-contain"
                  />
                ) : (
                  <div className="flex flex-col items-center justify-center py-12">
                    <FileText className="w-16 h-16 text-slate-400 mb-3" />
                    <p className="text-slate-500 font-medium">{item.name || 'PDF Document'}</p>
                    <p className="text-xs text-slate-400 mt-1">Click View to open</p>
                  </div>
                )}
              </div>
            )}

            {/* Info */}
            {itemType === 'drawing' && (
              <div className="grid grid-cols-2 gap-4 text-sm">
                {item.current_revision !== undefined && (
                  <div>
                    <span className="text-slate-500">Revision:</span>
                    <span className="ml-2 font-medium">R{item.current_revision || 0}</span>
                  </div>
                )}
                {item.uploaded_by_name && (
                  <div>
                    <span className="text-slate-500">Uploaded by:</span>
                    <span className="ml-2 font-medium">{item.uploaded_by_name}</span>
                  </div>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap gap-2 pt-2">
              {item.file_url && (
                <>
                  <Button onClick={handleView} variant="outline" className="flex-1">
                    <Eye className="w-4 h-4 mr-2" />
                    View
                  </Button>
                  <Button onClick={handleDownload} variant="outline" className="flex-1">
                    <Download className="w-4 h-4 mr-2" />
                    Download
                  </Button>
                </>
              )}
            </div>

            {/* Approval Actions - Only for drawings pending approval */}
            {itemType === 'drawing' && item.under_review && !item.is_approved && (
              <div className="border-t pt-4 mt-4">
                <p className="text-sm font-medium text-slate-700 mb-3">Take Action:</p>
                <div className="flex gap-2">
                  <Button 
                    onClick={handleApprove}
                    disabled={submitting}
                    className="flex-1 bg-green-600 hover:bg-green-700"
                  >
                    <Check className="w-4 h-4 mr-2" />
                    Approve
                  </Button>
                  <Button 
                    onClick={handleRequestRevision}
                    disabled={submitting || !newComment.trim()}
                    variant="outline"
                    className="flex-1 border-red-300 text-red-600 hover:bg-red-50"
                  >
                    <RefreshCw className="w-4 h-4 mr-2" />
                    Request Revision
                  </Button>
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  * To request revision, add a comment below first
                </p>
              </div>
            )}

            {/* Success Message */}
            {actionTaken && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                <Check className="w-8 h-8 text-green-600 mx-auto mb-2" />
                <p className="text-green-700 font-medium">Action completed!</p>
                <p className="text-sm text-green-600">You can now return to the project.</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Comments Section */}
        <Card className="mb-6">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              Comments
            </CardTitle>
          </CardHeader>
          <CardContent>
            {/* Existing Comments */}
            {comments.length > 0 ? (
              <div className="space-y-3 mb-4 max-h-[200px] overflow-y-auto">
                {comments.map((comment, idx) => (
                  <div key={comment.id || idx} className="bg-slate-50 rounded-lg p-3">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-medium text-sm">{comment.user_name || 'User'}</span>
                      <span className="text-xs text-slate-400">
                        {comment.created_at ? new Date(comment.created_at).toLocaleDateString() : ''}
                      </span>
                      {comment.requires_revision && (
                        <Badge className="bg-red-100 text-red-600 text-xs">Revision Request</Badge>
                      )}
                    </div>
                    <p className="text-sm text-slate-600">{comment.text}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-slate-400 mb-4">No comments yet</p>
            )}

            {/* Add Comment */}
            <div className="flex gap-2">
              <Textarea
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                placeholder="Add a comment..."
                className="flex-1 min-h-[60px]"
              />
              <Button 
                onClick={handleAddComment}
                disabled={submitting || !newComment.trim()}
                size="sm"
                className="self-end"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Done / Skip Button */}
        <div className="flex justify-center">
          <Button 
            onClick={handleDoneSkip}
            size="lg"
            className="px-8 bg-slate-600 hover:bg-slate-700"
          >
            Done / Skip
          </Button>
        </div>
      </div>
    </Layout>
  );
}
