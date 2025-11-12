import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Users, FolderOpen, Clock, AlertCircle, CheckCircle2, 
  Calendar, TrendingUp, Target
} from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function WorkTracker({ user, onLogout }) {
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [allDrawings, setAllDrawings] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('by-leader'); // 'by-leader' or 'by-project'
  const [selectedLeader, setSelectedLeader] = useState('all');
  const [selectedProject, setSelectedProject] = useState('all');

  useEffect(() => {
    if (!user?.is_owner) {
      navigate('/dashboard');
      return;
    }
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const [projectsRes, usersRes] = await Promise.all([
        axios.get(`${API}/projects`),
        axios.get(`${API}/users`)
      ]);

      setProjects(projectsRes.data);
      setTeamMembers(usersRes.data);

      // Fetch all drawings for all projects
      const drawingsPromises = projectsRes.data.map(p => 
        axios.get(`${API}/projects/${p.id}/drawings`)
      );
      const drawingsResponses = await Promise.all(drawingsPromises);
      
      // Combine all drawings with project info
      const allDrawingsData = [];
      drawingsResponses.forEach((res, index) => {
        const projectDrawings = res.data.map(d => ({
          ...d,
          project_id: projectsRes.data[index].id,
          project_title: projectsRes.data[index].title,
          project_code: projectsRes.data[index].code,
          team_leader_id: projectsRes.data[index].lead_architect_id
        }));
        allDrawingsData.push(...projectDrawings);
      });

      setAllDrawings(allDrawingsData);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load tracking data');
    } finally {
      setLoading(false);
    }
  };

  const getPendingDrawings = () => {
    return allDrawings.filter(d => !d.is_issued || d.has_pending_revision);
  };

  const getDrawingsByTeamLeader = (leaderId) => {
    if (leaderId === 'all') return getPendingDrawings();
    return getPendingDrawings().filter(d => d.team_leader_id === leaderId);
  };

  const getDrawingsByProject = (projectId) => {
    if (projectId === 'all') return getPendingDrawings();
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

  const getTeamLeaderStats = (leaderId) => {
    const leaderDrawings = getDrawingsByTeamLeader(leaderId);
    const overdue = leaderDrawings.filter(d => {
      const days = getDaysUntilDue(d.due_date);
      return days !== null && days < 0;
    }).length;
    const urgent = leaderDrawings.filter(d => {
      const days = getDaysUntilDue(d.due_date);
      return days !== null && days >= 0 && days <= 3;
    }).length;

    return { total: leaderDrawings.length, overdue, urgent };
  };

  const getProjectStats = (projectId) => {
    const projectDrawings = getDrawingsByProject(projectId);
    const overdue = projectDrawings.filter(d => {
      const days = getDaysUntilDue(d.due_date);
      return days !== null && days < 0;
    }).length;

    return { total: projectDrawings.length, overdue };
  };

  const teamLeadersWithWork = teamMembers.filter(tm => {
    const stats = getTeamLeaderStats(tm.id);
    return stats.total > 0;
  });

  const projectsWithPendingWork = projects.filter(p => {
    const stats = getProjectStats(p.id);
    return stats.total > 0;
  });

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
            Work Tracker
          </h1>
          <p className="text-sm sm:text-base text-slate-600 mt-1">
            Track all pending work across projects and team leaders
          </p>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-4 sm:mb-6">
          <Card>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">Total Pending</span>
                <Clock className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
              </div>
              <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900">
                {getPendingDrawings().length}
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
                {getPendingDrawings().filter(d => {
                  const days = getDaysUntilDue(d.due_date);
                  return days !== null && days < 0;
                }).length}
              </div>
              <p className="text-[10px] sm:text-xs text-slate-500 mt-1">Past deadline</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">Active Projects</span>
                <FolderOpen className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
              </div>
              <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900">
                {projectsWithPendingWork.length}
              </div>
              <p className="text-[10px] sm:text-xs text-slate-500 mt-1">With pending work</p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">Team Leaders</span>
                <Users className="w-4 h-4 sm:w-5 sm:h-5 text-green-600" />
              </div>
              <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900">
                {teamLeadersWithWork.length}
              </div>
              <p className="text-[10px] sm:text-xs text-slate-500 mt-1">With active work</p>
            </CardContent>
          </Card>
        </div>

        {/* View Tabs */}
        <Tabs value={viewMode} onValueChange={setViewMode}>
          <TabsList className="grid grid-cols-2 w-full sm:w-auto">
            <TabsTrigger value="by-leader" className="text-xs sm:text-sm">
              <Users className="w-4 h-4 mr-2" />
              By Team Leader
            </TabsTrigger>
            <TabsTrigger value="by-project" className="text-xs sm:text-sm">
              <FolderOpen className="w-4 h-4 mr-2" />
              By Project
            </TabsTrigger>
          </TabsList>

          {/* By Team Leader View */}
          <TabsContent value="by-leader" className="mt-4 sm:mt-6 space-y-4 sm:space-y-6">
            {teamLeadersWithWork.map((leader) => {
              const stats = getTeamLeaderStats(leader.id);
              const leaderDrawings = sortByUrgency(getDrawingsByTeamLeader(leader.id));

              return (
                <Card key={leader.id}>
                  <CardHeader className="pb-3 sm:pb-4">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 sm:w-12 sm:h-12 bg-orange-500 rounded-full flex items-center justify-center text-white font-bold text-sm sm:text-base">
                          {leader.name?.charAt(0)}
                        </div>
                        <div>
                          <h3 className="text-base sm:text-lg font-bold text-slate-900">{leader.name}</h3>
                          <p className="text-xs sm:text-sm text-slate-500 capitalize">
                            {leader.role?.replace('_', ' ')}
                          </p>
                        </div>
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <span className="px-2 sm:px-3 py-1 text-xs sm:text-sm bg-slate-100 text-slate-700 rounded">
                          {stats.total} pending
                        </span>
                        {stats.overdue > 0 && (
                          <span className="px-2 sm:px-3 py-1 text-xs sm:text-sm bg-red-100 text-red-700 rounded font-medium">
                            {stats.overdue} overdue
                          </span>
                        )}
                        {stats.urgent > 0 && (
                          <span className="px-2 sm:px-3 py-1 text-xs sm:text-sm bg-amber-100 text-amber-700 rounded font-medium">
                            {stats.urgent} urgent
                          </span>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="p-3 sm:p-6">
                    <div className="space-y-2 sm:space-y-3">
                      {leaderDrawings.map((drawing) => {
                        const daysUntil = getDaysUntilDue(drawing.due_date);
                        return (
                          <div 
                            key={drawing.id}
                            className="p-3 sm:p-4 border border-slate-200 rounded-lg hover:border-orange-300 transition-colors cursor-pointer"
                            onClick={() => navigate(`/projects/${drawing.project_id}`)}
                          >
                            <div className="flex flex-col sm:flex-row sm:items-start gap-2 sm:gap-3">
                              <div className="flex-1 min-w-0">
                                <div className="flex flex-wrap items-center gap-2 mb-1">
                                  <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-blue-50 text-blue-700 rounded font-mono">
                                    {drawing.project_code}
                                  </span>
                                  <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-slate-100 text-slate-700 rounded">
                                    {drawing.category}
                                  </span>
                                  {daysUntil !== null && (
                                    <span className={`px-2 py-0.5 text-[10px] sm:text-xs rounded font-medium ${getUrgencyColor(daysUntil)}`}>
                                      {daysUntil < 0 ? `${Math.abs(daysUntil)}d overdue` : 
                                       daysUntil === 0 ? 'Today!' : 
                                       `${daysUntil}d left`}
                                    </span>
                                  )}
                                </div>
                                <p className="text-sm sm:text-base font-medium text-slate-900 break-words">
                                  {drawing.name}
                                </p>
                                <p className="text-xs sm:text-sm text-slate-500 mt-1">
                                  {drawing.project_title}
                                </p>
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              );
            })}

            {teamLeadersWithWork.length === 0 && (
              <Card>
                <CardContent className="p-8 text-center">
                  <CheckCircle2 className="w-12 h-12 sm:w-16 sm:h-16 text-green-300 mx-auto mb-4" />
                  <p className="text-slate-500">No pending work! All caught up 🎉</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* By Project View */}
          <TabsContent value="by-project" className="mt-4 sm:mt-6 space-y-4 sm:space-y-6">
            {projectsWithPendingWork.map((project) => {
              const stats = getProjectStats(project.id);
              const projectDrawings = sortByUrgency(getDrawingsByProject(project.id));
              const leader = teamMembers.find(tm => tm.id === project.lead_architect_id);

              return (
                <Card key={project.id}>
                  <CardHeader className="pb-3 sm:pb-4">
                    <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-3">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="px-2 sm:px-3 py-1 bg-orange-100 text-orange-700 font-mono text-xs sm:text-sm font-medium rounded">
                            {project.code}
                          </span>
                          {stats.overdue > 0 && (
                            <span className="px-2 sm:px-3 py-1 text-xs sm:text-sm bg-red-100 text-red-700 rounded font-medium">
                              {stats.overdue} overdue
                            </span>
                          )}
                        </div>
                        <h3 className="text-base sm:text-lg font-bold text-slate-900">{project.title}</h3>
                        {leader && (
                          <p className="text-xs sm:text-sm text-slate-600 mt-1">
                            Team Leader: {leader.name}
                          </p>
                        )}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => navigate(`/projects/${project.id}`)}
                        className="w-full sm:w-auto"
                      >
                        View Project
                      </Button>
                    </div>
                  </CardHeader>
                  <CardContent className="p-3 sm:p-6">
                    <div className="space-y-2 sm:space-y-3">
                      {projectDrawings.map((drawing) => {
                        const daysUntil = getDaysUntilDue(drawing.due_date);
                        return (
                          <div 
                            key={drawing.id}
                            className="p-3 sm:p-4 border border-slate-200 rounded-lg hover:border-orange-300 transition-colors"
                          >
                            <div className="flex flex-wrap items-center gap-2 mb-2">
                              <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-slate-100 text-slate-700 rounded">
                                {drawing.category}
                              </span>
                              {daysUntil !== null && (
                                <span className={`px-2 py-0.5 text-[10px] sm:text-xs rounded font-medium ${getUrgencyColor(daysUntil)}`}>
                                  {daysUntil < 0 ? `${Math.abs(daysUntil)} days overdue` : 
                                   daysUntil === 0 ? 'Due today!' : 
                                   `${daysUntil} days left`}
                                </span>
                              )}
                            </div>
                            <p className="text-sm sm:text-base font-medium text-slate-900 break-words">
                              {drawing.name}
                            </p>
                            {drawing.due_date && (
                              <p className="text-xs sm:text-sm text-slate-500 mt-1">
                                Due: {new Date(drawing.due_date).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  </CardContent>
                </Card>
              );
            })}

            {projectsWithPendingWork.length === 0 && (
              <Card>
                <CardContent className="p-8 text-center">
                  <CheckCircle2 className="w-12 h-12 sm:w-16 sm:h-16 text-green-300 mx-auto mb-4" />
                  <p className="text-slate-500">No pending work! All projects up to date 🎉</p>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  );
}
