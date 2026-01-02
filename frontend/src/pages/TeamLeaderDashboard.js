import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { FolderKanban, Calendar, Users, Clock, TrendingUp, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function TeamLeaderDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Fetch drawing stats for each project
      const projectsWithStats = await Promise.all(
        response.data.map(async (project) => {
          try {
            const drawingsRes = await axios.get(`${API}/projects/${project.id}/drawings`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            const drawings = drawingsRes.data || [];
            const totalDrawings = drawings.length;
            const issuedDrawings = drawings.filter(d => d.is_issued).length;
            const pendingRevisions = drawings.filter(d => d.has_pending_revision).length;
            const underReview = drawings.filter(d => d.under_review && !d.is_approved).length;
            const percentComplete = totalDrawings > 0 
              ? Math.round((issuedDrawings / totalDrawings) * 100) 
              : 0;
            
            return {
              ...project,
              totalDrawings,
              issuedDrawings,
              pendingRevisions,
              underReview,
              percentComplete
            };
          } catch (err) {
            return { ...project, totalDrawings: 0, issuedDrawings: 0, pendingRevisions: 0, underReview: 0, percentComplete: 0 };
          }
        })
      );
      
      // Sort by pending work (most urgent first)
      const sorted = projectsWithStats.sort((a, b) => {
        const urgencyA = a.pendingRevisions + a.underReview;
        const urgencyB = b.pendingRevisions + b.underReview;
        return urgencyB - urgencyA;
      });
      
      setProjects(sorted);
    } catch (error) {
      console.error('Error fetching projects:', error);
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'TBD';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  // Calculate summary stats
  const totalPendingRevisions = projects.reduce((sum, p) => sum + (p.pendingRevisions || 0), 0);
  const totalUnderReview = projects.reduce((sum, p) => sum + (p.underReview || 0), 0);
  const activeProjects = projects.filter(p => !p.archived).length;

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="w-8 h-8 border-4 border-orange-500 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
            <p className="text-slate-500">Loading your projects...</p>
          </div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
            Hi, {user?.name?.split(' ')[0]} 👋
          </h1>
          <p className="text-slate-600 mt-1 text-sm sm:text-base">
            Team Leader Dashboard • {activeProjects} Active {activeProjects === 1 ? 'Project' : 'Projects'}
          </p>
        </div>

        {/* Quick Stats */}
        {(totalPendingRevisions > 0 || totalUnderReview > 0) && (
          <div className="grid grid-cols-2 gap-3 mb-6">
            {totalPendingRevisions > 0 && (
              <Card className="border-l-4 border-l-red-500 bg-red-50">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <AlertCircle className="w-8 h-8 text-red-500" />
                    <div>
                      <p className="text-2xl font-bold text-red-700">{totalPendingRevisions}</p>
                      <p className="text-xs text-red-600">Revisions Pending</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
            {totalUnderReview > 0 && (
              <Card className="border-l-4 border-l-amber-500 bg-amber-50">
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Clock className="w-8 h-8 text-amber-500" />
                    <div>
                      <p className="text-2xl font-bold text-amber-700">{totalUnderReview}</p>
                      <p className="text-xs text-amber-600">Awaiting Approval</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Projects List */}
        {projects.length === 0 ? (
          <div className="text-center py-12 px-4">
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-2xl p-8 border border-orange-100 max-w-md mx-auto">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <FolderKanban className="w-8 h-8 text-orange-600" />
              </div>
              
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                No Projects Assigned
              </h3>
              
              <p className="text-slate-600 text-sm leading-relaxed">
                You don&apos;t have any projects assigned yet. Contact the owner to get started.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {projects.filter(p => !p.archived).map((project) => (
              <Card 
                key={project.id} 
                className={`hover:shadow-md transition-all cursor-pointer active:scale-[0.99] ${
                  project.pendingRevisions > 0 ? 'border-l-4 border-l-red-500' :
                  project.underReview > 0 ? 'border-l-4 border-l-amber-500' :
                  'border-l-4 border-l-green-500'
                }`}
                onClick={() => navigate(`/team-leader/project/${project.id}`)}
              >
                <CardContent className="p-4 sm:p-5">
                  {/* Project Header */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-slate-900 truncate">
                        {project.title || project.name}
                      </h3>
                      <p className="text-sm text-slate-500 font-mono">
                        {project.code || 'No Code'}
                      </p>
                    </div>
                    <Badge className={`ml-2 shrink-0 ${
                      project.pendingRevisions > 0 ? 'bg-red-100 text-red-700' :
                      project.underReview > 0 ? 'bg-amber-100 text-amber-700' :
                      'bg-green-100 text-green-700'
                    }`}>
                      {project.percentComplete}%
                    </Badge>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-3">
                    <Progress 
                      value={project.percentComplete} 
                      className="h-2 bg-slate-100"
                    />
                  </div>

                  {/* Status Pills */}
                  <div className="flex flex-wrap gap-2 mb-3">
                    {project.pendingRevisions > 0 && (
                      <span className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded-full flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        {project.pendingRevisions} revision{project.pendingRevisions > 1 ? 's' : ''}
                      </span>
                    )}
                    {project.underReview > 0 && (
                      <span className="px-2 py-1 text-xs bg-amber-100 text-amber-700 rounded-full flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {project.underReview} pending approval
                      </span>
                    )}
                    <span className="px-2 py-1 text-xs bg-slate-100 text-slate-600 rounded-full">
                      {project.issuedDrawings} drawings issued
                    </span>
                  </div>

                  {/* Footer - Only show date if available */}
                  {project.start_date && (
                    <div className="flex items-center justify-between text-sm text-slate-500">
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>{formatDate(project.start_date)}</span>
                      </div>
                      <TrendingUp className="w-4 h-4 text-orange-500" />
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}

            {/* Archived Projects Section */}
            {projects.filter(p => p.archived).length > 0 && (
              <div className="mt-8">
                <h3 className="text-sm font-medium text-slate-500 mb-3">Completed Projects</h3>
                <div className="space-y-3 opacity-75">
                  {projects.filter(p => p.archived).map((project) => (
                    <Card 
                      key={project.id} 
                      className="cursor-pointer hover:shadow-sm"
                      onClick={() => navigate(`/team-leader/project/${project.id}`)}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-center justify-between">
                          <div className="flex-1 min-w-0">
                            <h4 className="font-medium text-slate-700 truncate">{project.title}</h4>
                            <p className="text-xs text-slate-500">{project.code}</p>
                          </div>
                          <Badge className="bg-slate-100 text-slate-600">Completed</Badge>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </Layout>
  );
}
