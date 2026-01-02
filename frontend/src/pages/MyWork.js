import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { 
  AlertTriangle, Clock, CheckCircle2, 
  Calendar, ArrowRight, FileText, MessageSquare,
  Eye, ChevronDown, ChevronUp, RefreshCw
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function MyWork({ user, onLogout }) {
  const navigate = useNavigate();
  const [actionItems, setActionItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedProjects, setExpandedProjects] = useState({});
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchActionItems();
  }, []);

  const fetchActionItems = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      // Get all projects
      const projectsRes = await axios.get(`${API}/projects`, { headers });
      
      // Filter projects where user is team_leader_id (not lead_architect_id)
      const myProjects = projectsRes.data.filter(p => p.team_leader_id === user.id);
      
      // Fetch drawings and comments for each project
      const projectsWithActions = await Promise.all(
        myProjects.map(async (project) => {
          try {
            const [drawingsRes, commentsRes] = await Promise.all([
              axios.get(`${API}/projects/${project.id}/drawings`, { headers }),
              axios.get(`${API}/projects/${project.id}/comments`, { headers }).catch(() => ({ data: [] }))
            ]);
            
            const drawings = drawingsRes.data || [];
            const comments = commentsRes.data || [];
            
            // Categorize actionable items
            const revisionsNeeded = drawings.filter(d => d.has_pending_revision);
            const pendingApproval = drawings.filter(d => d.under_review && !d.is_approved && !d.has_pending_revision);
            const readyToIssue = drawings.filter(d => d.is_approved && !d.is_issued);
            const notStarted = drawings.filter(d => !d.file_url && !d.is_issued && !d.has_pending_revision && !d.under_review);
            
            // Check for unread comments (within last 24 hours)
            const recentComments = comments.filter(c => {
              const commentTime = new Date(c.created_at);
              const now = new Date();
              const hoursDiff = (now - commentTime) / (1000 * 60 * 60);
              return hoursDiff < 24 && c.user_id !== user.id;
            });
            
            return {
              ...project,
              revisionsNeeded,
              pendingApproval,
              readyToIssue,
              notStarted,
              recentComments,
              totalActions: revisionsNeeded.length + pendingApproval.length + readyToIssue.length + recentComments.length
            };
          } catch (err) {
            return {
              ...project,
              revisionsNeeded: [],
              pendingApproval: [],
              readyToIssue: [],
              notStarted: [],
              recentComments: [],
              totalActions: 0
            };
          }
        })
      );
      
      // Sort by total actions (most urgent first)
      const sorted = projectsWithActions.sort((a, b) => {
        // Priority: Revisions > Pending Approval > Ready to Issue
        const urgencyA = (a.revisionsNeeded.length * 3) + (a.pendingApproval.length * 2) + a.readyToIssue.length;
        const urgencyB = (b.revisionsNeeded.length * 3) + (b.pendingApproval.length * 2) + b.readyToIssue.length;
        return urgencyB - urgencyA;
      });
      
      setActionItems(sorted);
      
      // Auto-expand projects with actions
      const expanded = {};
      sorted.forEach(p => {
        if (p.totalActions > 0) expanded[p.id] = true;
      });
      setExpandedProjects(expanded);
      
    } catch (error) {
      console.error('Error fetching action items:', error);
      toast.error('Failed to load your tasks');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    fetchActionItems();
  };

  const toggleProject = (projectId) => {
    setExpandedProjects(prev => ({
      ...prev,
      [projectId]: !prev[projectId]
    }));
  };

  const goToProjectAction = (projectId) => {
    navigate(`/team-leader/project/${projectId}`);
  };

  // Calculate totals
  const totalRevisions = actionItems.reduce((sum, p) => sum + p.revisionsNeeded.length, 0);
  const totalPendingApproval = actionItems.reduce((sum, p) => sum + p.pendingApproval.length, 0);
  const totalReadyToIssue = actionItems.reduce((sum, p) => sum + p.readyToIssue.length, 0);
  const totalRecentComments = actionItems.reduce((sum, p) => sum + p.recentComments.length, 0);
  const totalAllActions = totalRevisions + totalPendingApproval + totalReadyToIssue + totalRecentComments;

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600 mx-auto mb-4"></div>
            <p className="text-slate-500">Loading your tasks...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
              My Work
            </h1>
            <p className="text-sm sm:text-base text-slate-600 mt-1">
              Actionable tasks across all your projects
            </p>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={handleRefresh}
            disabled={refreshing}
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Action Summary Cards */}
        {totalAllActions > 0 && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
            {totalRevisions > 0 && (
              <Card className="border-l-4 border-l-red-500 bg-red-50">
                <CardContent className="p-3 sm:p-4">
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                    <div>
                      <p className="text-xl sm:text-2xl font-bold text-red-700">{totalRevisions}</p>
                      <p className="text-xs text-red-600">Revisions Needed</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {totalPendingApproval > 0 && (
              <Card className="border-l-4 border-l-amber-500 bg-amber-50">
                <CardContent className="p-3 sm:p-4">
                  <div className="flex items-center gap-2">
                    <Clock className="w-5 h-5 text-amber-600" />
                    <div>
                      <p className="text-xl sm:text-2xl font-bold text-amber-700">{totalPendingApproval}</p>
                      <p className="text-xs text-amber-600">Awaiting Approval</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {totalReadyToIssue > 0 && (
              <Card className="border-l-4 border-l-green-500 bg-green-50">
                <CardContent className="p-3 sm:p-4">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-green-600" />
                    <div>
                      <p className="text-xl sm:text-2xl font-bold text-green-700">{totalReadyToIssue}</p>
                      <p className="text-xs text-green-600">Ready to Issue</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            
            {totalRecentComments > 0 && (
              <Card className="border-l-4 border-l-blue-500 bg-blue-50">
                <CardContent className="p-3 sm:p-4">
                  <div className="flex items-center gap-2">
                    <MessageSquare className="w-5 h-5 text-blue-600" />
                    <div>
                      <p className="text-xl sm:text-2xl font-bold text-blue-700">{totalRecentComments}</p>
                      <p className="text-xs text-blue-600">New Comments</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* All Caught Up Message */}
        {totalAllActions === 0 && actionItems.length > 0 && (
          <Card className="mb-6 border-green-200 bg-green-50">
            <CardContent className="p-6 text-center">
              <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
              <h3 className="text-lg font-semibold text-green-800">All Caught Up!</h3>
              <p className="text-green-600 text-sm">No pending actions across your {actionItems.length} projects</p>
            </CardContent>
          </Card>
        )}

        {/* No Projects Message */}
        {actionItems.length === 0 && (
          <Card className="mb-6">
            <CardContent className="p-8 text-center">
              <FileText className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-700">No Projects Assigned</h3>
              <p className="text-slate-500 text-sm mt-2">You are not assigned as team leader to any projects yet.</p>
            </CardContent>
          </Card>
        )}

        {/* Project-wise Action List */}
        <div className="space-y-4">
          {actionItems.map((project) => (
            <Card 
              key={project.id}
              className={`overflow-hidden ${
                project.revisionsNeeded.length > 0 ? 'border-l-4 border-l-red-500' :
                project.pendingApproval.length > 0 ? 'border-l-4 border-l-amber-500' :
                project.readyToIssue.length > 0 ? 'border-l-4 border-l-green-500' :
                'border-l-4 border-l-slate-300'
              }`}
            >
              {/* Project Header - Clickable */}
              <div 
                className="p-4 cursor-pointer hover:bg-slate-50 transition-colors"
                onClick={() => toggleProject(project.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-slate-900 truncate">{project.title}</h3>
                      {project.totalActions > 0 && (
                        <Badge className="bg-orange-100 text-orange-700 shrink-0">
                          {project.totalActions} action{project.totalActions > 1 ? 's' : ''}
                        </Badge>
                      )}
                    </div>
                    <p className="text-xs text-slate-500 font-mono">{project.code || 'No Code'}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        goToProjectAction(project.id);
                      }}
                      className="text-orange-600 hover:text-orange-700"
                    >
                      <span className="hidden sm:inline">Open</span>
                      <ArrowRight className="w-4 h-4 ml-1" />
                    </Button>
                    {expandedProjects[project.id] ? 
                      <ChevronUp className="w-5 h-5 text-slate-400" /> : 
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    }
                  </div>
                </div>
                
                {/* Quick Status Pills */}
                {project.totalActions > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {project.revisionsNeeded.length > 0 && (
                      <span className="px-2 py-0.5 text-xs bg-red-100 text-red-700 rounded-full">
                        {project.revisionsNeeded.length} revision{project.revisionsNeeded.length > 1 ? 's' : ''}
                      </span>
                    )}
                    {project.pendingApproval.length > 0 && (
                      <span className="px-2 py-0.5 text-xs bg-amber-100 text-amber-700 rounded-full">
                        {project.pendingApproval.length} pending approval
                      </span>
                    )}
                    {project.readyToIssue.length > 0 && (
                      <span className="px-2 py-0.5 text-xs bg-green-100 text-green-700 rounded-full">
                        {project.readyToIssue.length} ready to issue
                      </span>
                    )}
                    {project.recentComments.length > 0 && (
                      <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                        {project.recentComments.length} new comment{project.recentComments.length > 1 ? 's' : ''}
                      </span>
                    )}
                  </div>
                )}
              </div>

              {/* Expanded Action Details */}
              {expandedProjects[project.id] && project.totalActions > 0 && (
                <div className="border-t bg-slate-50 p-4 space-y-3">
                  
                  {/* Revisions Needed */}
                  {project.revisionsNeeded.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-red-700 mb-2 flex items-center gap-1">
                        <AlertTriangle className="w-3 h-3" />
                        REVISIONS NEEDED
                      </p>
                      <div className="space-y-1">
                        {project.revisionsNeeded.map(drawing => (
                          <div 
                            key={drawing.id} 
                            className="flex items-center justify-between bg-white p-2 rounded border border-red-200"
                          >
                            <div className="flex-1 min-w-0 mr-2">
                              <p className="text-sm font-medium truncate">{drawing.name}</p>
                              <p className="text-xs text-slate-500">{drawing.category}</p>
                            </div>
                            <Button 
                              size="sm" 
                              variant="outline"
                              className="text-red-600 border-red-300 hover:bg-red-50 shrink-0"
                              onClick={() => goToProjectAction(project.id)}
                            >
                              Upload
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Pending Approval */}
                  {project.pendingApproval.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-amber-700 mb-2 flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        AWAITING APPROVAL
                      </p>
                      <div className="space-y-1">
                        {project.pendingApproval.map(drawing => (
                          <div 
                            key={drawing.id} 
                            className="flex items-center justify-between bg-white p-2 rounded border border-amber-200"
                          >
                            <div className="flex-1 min-w-0 mr-2">
                              <p className="text-sm font-medium truncate">{drawing.name}</p>
                              <p className="text-xs text-slate-500">{drawing.category}</p>
                            </div>
                            <div className="flex gap-1 shrink-0">
                              <Button 
                                size="sm" 
                                variant="outline"
                                className="text-slate-600"
                                onClick={() => goToProjectAction(project.id)}
                              >
                                <Eye className="w-3 h-3" />
                              </Button>
                              <Button 
                                size="sm"
                                className="bg-green-600 hover:bg-green-700"
                                onClick={() => goToProjectAction(project.id)}
                              >
                                Approve
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Ready to Issue */}
                  {project.readyToIssue.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-green-700 mb-2 flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        READY TO ISSUE
                      </p>
                      <div className="space-y-1">
                        {project.readyToIssue.map(drawing => (
                          <div 
                            key={drawing.id} 
                            className="flex items-center justify-between bg-white p-2 rounded border border-green-200"
                          >
                            <div className="flex-1 min-w-0 mr-2">
                              <p className="text-sm font-medium truncate">{drawing.name}</p>
                              <p className="text-xs text-slate-500">{drawing.category}</p>
                            </div>
                            <Button 
                              size="sm"
                              className="bg-blue-600 hover:bg-blue-700 shrink-0"
                              onClick={() => goToProjectAction(project.id)}
                            >
                              Issue
                            </Button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Recent Comments */}
                  {project.recentComments.length > 0 && (
                    <div>
                      <p className="text-xs font-medium text-blue-700 mb-2 flex items-center gap-1">
                        <MessageSquare className="w-3 h-3" />
                        NEW COMMENTS (Last 24h)
                      </p>
                      <div className="space-y-1">
                        {project.recentComments.slice(0, 3).map(comment => (
                          <div 
                            key={comment.id} 
                            className="bg-white p-2 rounded border border-blue-200"
                          >
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xs font-medium text-slate-700">{comment.user_name || 'User'}</span>
                              <span className="text-xs text-slate-400">
                                {new Date(comment.created_at).toLocaleTimeString('en-US', { 
                                  hour: '2-digit', 
                                  minute: '2-digit' 
                                })}
                              </span>
                            </div>
                            {comment.text && (
                              <p className="text-sm text-slate-600 line-clamp-2">{comment.text}</p>
                            )}
                          </div>
                        ))}
                        {project.recentComments.length > 3 && (
                          <p className="text-xs text-center text-blue-600">
                            +{project.recentComments.length - 3} more comments
                          </p>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Quick Action Button */}
                  <Button 
                    className="w-full mt-2 bg-orange-500 hover:bg-orange-600"
                    onClick={() => goToProjectAction(project.id)}
                  >
                    Go to Project <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              )}

              {/* No Actions - Collapsed State */}
              {expandedProjects[project.id] && project.totalActions === 0 && (
                <div className="border-t bg-slate-50 p-4 text-center">
                  <CheckCircle2 className="w-8 h-8 text-green-400 mx-auto mb-2" />
                  <p className="text-sm text-slate-500">No pending actions for this project</p>
                  <Button 
                    variant="outline"
                    size="sm"
                    className="mt-2"
                    onClick={() => goToProjectAction(project.id)}
                  >
                    View Project
                  </Button>
                </div>
              )}
            </Card>
          ))}
        </div>
      </div>
    </Layout>
  );
}
