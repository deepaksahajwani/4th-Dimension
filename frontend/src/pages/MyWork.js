import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  FolderOpen, Clock, AlertCircle, CheckCircle2, 
  Calendar, Target, TrendingUp, Users
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function MyWork({ user, onLogout }) {
  const navigate = useNavigate();
  const [myProjects, setMyProjects] = useState([]);
  const [allDrawings, setAllDrawings] = useState([]);
  const [weeklyTargets, setWeeklyTargets] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [projectsRes, targetsRes] = await Promise.all([
        axios.get(`${API}/projects`),
        axios.get(`${API}/weekly-targets`)
      ]);
      
      // Filter projects where user is team leader
      const leaderProjects = projectsRes.data.filter(p => p.lead_architect_id === user.id);
      setMyProjects(leaderProjects);
      setWeeklyTargets(targetsRes.data);

      // Fetch drawings for my projects only
      if (leaderProjects.length > 0) {
        const drawingsPromises = leaderProjects.map(p => 
          axios.get(`${API}/projects/${p.id}/drawings`)
        );
        const drawingsResponses = await Promise.all(drawingsPromises);
        
        const allDrawingsData = [];
        drawingsResponses.forEach((res, index) => {
          const projectDrawings = res.data.map(d => ({
            ...d,
            project_id: leaderProjects[index].id,
            project_title: leaderProjects[index].title,
            project_code: leaderProjects[index].code
          }));
          allDrawingsData.push(...projectDrawings);
        });

        setAllDrawings(allDrawingsData);
      }
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load your work');
    } finally {
      setLoading(false);
    }
  };

  const getPendingDrawings = () => {
    return allDrawings.filter(d => !d.is_issued || d.has_pending_revision);
  };

  const getCompletedDrawings = () => {
    return allDrawings.filter(d => d.is_issued && !d.has_pending_revision);
  };

  const getPendingDrawingsForProject = (projectId) => {
    return getPendingDrawings().filter(d => d.project_id === projectId);
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

  const sortByUrgency = (drawings) => {
    return [...drawings].sort((a, b) => {
      if (!a.due_date) return 1;
      if (!b.due_date) return -1;
      return new Date(a.due_date) - new Date(b.due_date);
    });
  };

  const pendingDrawings = sortByUrgency(getPendingDrawings());
  const overdueCount = pendingDrawings.filter(d => {
    const days = getDaysUntilDue(d.due_date);
    return days !== null && days < 0;
  }).length;

  const urgentCount = pendingDrawings.filter(d => {
    const days = getDaysUntilDue(d.due_date);
    return days !== null && days >= 0 && days <= 3;
  }).length;

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div>
        {/* Header */}
        <div className="mb-4 sm:mb-6">
          <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900">
            My Work
          </h1>
          <p className="text-sm sm:text-base text-slate-600 mt-1">
            Complete overview of all projects I'm leading and all pending work
          </p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-4 sm:mb-6">
          <Card>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">My Projects</span>
                <FolderOpen className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
              </div>
              <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900">
                {myProjects.length}
              </div>
              <p className="text-[10px] sm:text-xs text-slate-500 mt-1">Leading</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">Pending</span>
                <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
              </div>
              <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900">
                {pendingDrawings.length}
              </div>
              <p className="text-[10px] sm:text-xs text-slate-500 mt-1">Drawings</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">Overdue</span>
                <AlertCircle className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />
              </div>
              <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-red-600">
                {overdueCount}
              </div>
              <p className="text-[10px] sm:text-xs text-slate-500 mt-1">Past deadline</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">Completed</span>
                <CheckCircle2 className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
              </div>
              <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-green-600">
                {getCompletedDrawings().length}
              </div>
              <p className="text-[10px] sm:text-xs text-slate-500 mt-1">Drawings</p>
            </CardContent>
          </Card>
        </div>

        {/* Weekly Targets */}
        {weeklyTargets.length > 0 && (
          <div className="mb-4 sm:mb-6">
            {/* This Week's Target */}
              <Card>
                <CardHeader className="pb-3 sm:pb-4">
                  <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                    <Target className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
                    This Week's Target
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 sm:p-6">
                  {weeklyTargets.slice(0, 1).map((target) => {
                    const completionPercentage = Math.round((target.completed_quantity / target.target_quantity) * 100);
                    const weekStart = new Date(target.week_start_date);
                    const weekEnd = new Date(target.week_end_date);
                    
                    return (
                      <div key={target.id}>
                        <div className="flex items-center justify-between mb-3">
                          <div>
                            <p className="text-xs sm:text-sm text-slate-500">
                              {weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - {weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                            </p>
                            <p className="text-sm sm:text-base font-medium text-slate-900 capitalize mt-1">
                              {target.target_type.replace('_', ' ')}
                            </p>
                          </div>
                          <span className={`px-2 sm:px-3 py-1 rounded-full text-xs sm:text-sm font-medium ${
                            target.status === 'completed' ? 'bg-green-100 text-green-700' :
                            target.status === 'overdue' ? 'bg-red-100 text-red-700' :
                            'bg-blue-100 text-blue-700'
                          }`}>
                            {target.status}
                          </span>
                        </div>
                        
                        <p className="text-xs sm:text-sm text-slate-600 mb-3">
                          {target.target_description}
                        </p>
                        
                        <div className="mb-3">
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs sm:text-sm text-slate-600">Progress</span>
                            <span className="text-sm sm:text-base font-bold text-slate-900">
                              {target.completed_quantity} / {target.target_quantity}
                            </span>
                          </div>
                          <div className="w-full bg-slate-200 rounded-full h-3">
                            <div 
                              className={`h-3 rounded-full transition-all ${
                                completionPercentage === 100 ? 'bg-green-500' :
                                completionPercentage >= 75 ? 'bg-blue-500' :
                                completionPercentage >= 50 ? 'bg-orange-500' :
                                'bg-red-500'
                              }`}
                              style={{ width: `${completionPercentage}%` }}
                            />
                          </div>
                          <p className="text-xs text-slate-500 mt-1">{completionPercentage}% complete</p>
                        </div>
                      </div>
                    );
                  })}
                </CardContent>
              </Card>
          </div>
        )}

        {/* Pending Drawings - Sorted by Urgency */}
        <Card className="mb-4 sm:mb-6">
          <CardHeader className="pb-3 sm:pb-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                <Target className="w-4 h-4 sm:w-5 sm:h-5 text-red-600" />
                Pending Drawings by Urgency
              </CardTitle>
              <div className="flex flex-wrap gap-2">
                {urgentCount > 0 && (
                  <span className="px-2 sm:px-3 py-1 text-xs sm:text-sm bg-amber-100 text-amber-700 rounded font-medium">
                    {urgentCount} urgent (≤3 days)
                  </span>
                )}
                {overdueCount > 0 && (
                  <span className="px-2 sm:px-3 py-1 text-xs sm:text-sm bg-red-100 text-red-700 rounded font-medium">
                    {overdueCount} overdue
                  </span>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-3 sm:p-6">
            {pendingDrawings.length > 0 ? (
              <div className="space-y-2 sm:space-y-3">
                {pendingDrawings.map((drawing) => {
                  const daysUntil = getDaysUntilDue(drawing.due_date);
                  return (
                    <div 
                      key={drawing.id}
                      className="p-3 sm:p-4 border-2 border-slate-200 rounded-lg hover:border-orange-300 transition-colors cursor-pointer"
                      onClick={() => navigate(`/projects/${drawing.project_id}`)}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-2">
                            <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-blue-50 text-blue-700 rounded font-mono font-medium">
                              {drawing.project_code}
                            </span>
                            <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-slate-100 text-slate-700 rounded">
                              {drawing.category}
                            </span>
                            {daysUntil !== null && (
                              <span className={`px-2 py-0.5 text-[10px] sm:text-xs rounded font-bold ${getUrgencyColor(daysUntil)}`}>
                                {daysUntil < 0 ? `OVERDUE ${Math.abs(daysUntil)}d` : 
                                 daysUntil === 0 ? 'DUE TODAY!' : 
                                 daysUntil === 1 ? 'DUE TOMORROW' :
                                 daysUntil <= 3 ? `URGENT - ${daysUntil}d left` :
                                 `${daysUntil}d left`}
                              </span>
                            )}
                            {drawing.has_pending_revision && (
                              <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-amber-100 text-amber-700 rounded font-medium">
                                Revision Needed
                              </span>
                            )}
                          </div>
                          <h4 className="text-sm sm:text-base font-semibold text-slate-900 break-words">
                            {drawing.name}
                          </h4>
                          <p className="text-xs sm:text-sm text-slate-600 mt-1">
                            {drawing.project_title}
                          </p>
                          {drawing.due_date && (
                            <p className="text-xs sm:text-sm text-slate-500 mt-1 flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              Due: {new Date(drawing.due_date).toLocaleDateString('en-US', { 
                                weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' 
                              })}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 sm:py-12">
                <CheckCircle2 className="w-12 h-12 sm:w-16 sm:h-16 text-green-300 mx-auto mb-4" />
                <p className="text-slate-500 text-sm sm:text-base">
                  All caught up! No pending drawings 🎉
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* My Projects Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base sm:text-lg flex items-center gap-2">
              <FolderOpen className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
              My Projects
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3 sm:p-6">
            {myProjects.length > 0 ? (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                {myProjects.map((project) => {
                  const projectPending = getPendingDrawingsForProject(project.id);
                  const projectOverdue = projectPending.filter(d => {
                    const days = getDaysUntilDue(d.due_date);
                    return days !== null && days < 0;
                  }).length;

                  return (
                    <Card 
                      key={project.id}
                      className="cursor-pointer hover:shadow-lg transition-shadow border-2 hover:border-orange-300"
                      onClick={() => navigate(`/projects/${project.id}`)}
                    >
                      <CardContent className="p-3 sm:p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="w-10 h-10 sm:w-12 sm:h-12 bg-gradient-to-br from-orange-400 to-orange-600 rounded-lg flex items-center justify-center text-white font-bold text-sm sm:text-base">
                            {project.code || project.title?.charAt(0) || 'P'}
                          </div>
                          {projectOverdue > 0 && (
                            <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-red-100 text-red-700 rounded font-bold">
                              {projectOverdue} overdue
                            </span>
                          )}
                        </div>
                        <h3 className="font-semibold text-sm sm:text-base text-slate-900 mb-1 truncate">
                          {project.title}
                        </h3>
                        <div className="flex items-center justify-between text-xs sm:text-sm text-slate-600 mt-2">
                          <span>{projectPending.length} pending</span>
                          <span className="text-green-600 font-medium">
                            {allDrawings.filter(d => d.project_id === project.id && d.is_issued && !d.has_pending_revision).length} done
                          </span>
                        </div>
                        {project.project_types && project.project_types.length > 0 && (
                          <div className="flex flex-wrap gap-1 mt-2">
                            {project.project_types.map((type) => (
                              <span 
                                key={type} 
                                className="px-1.5 py-0.5 text-[10px] bg-orange-50 text-orange-700 rounded"
                              >
                                {type}
                              </span>
                            ))}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            ) : (
              <div className="text-center py-8 sm:py-12">
                <FolderOpen className="w-12 h-12 sm:w-16 sm:h-16 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-500 text-sm sm:text-base">
                  You're not leading any projects yet
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </Layout>
  );
}
