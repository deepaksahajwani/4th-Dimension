import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import Layout from '../components/Layout';
import { 
  Calendar, 
  CheckCircle2, 
  Circle, 
  Clock, 
  AlertCircle,
  TrendingUp,
  Users,
  Plus,
  ChevronRight,
  Flag,
  Target,
  Award
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function WeeklyDashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState(null);
  const [teamOverview, setTeamOverview] = useState(null);
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [newTask, setNewTask] = useState({
    title: '',
    description: '',
    assigned_to_id: '',
    due_date: '',
    due_time: '',
    priority: 'MEDIUM',
    project_id: ''
  });
  const [teamMembers, setTeamMembers] = useState([]);
  const [projects, setProjects] = useState([]);

  useEffect(() => {
    fetchDashboardData();
    if (user?.role === 'owner') {
      fetchTeamOverview();
      fetchTeamMembers();
      fetchProjects();
    }
  }, [user]);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!user || !user.id) {
        console.error('User not loaded yet');
        setLoading(false);
        return;
      }
      console.log('Fetching dashboard for user:', user.id);
      const response = await axios.get(
        `${API}/api/dashboard/weekly-progress/${user.id}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      console.log('Dashboard data received:', response.data);
      setDashboardData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard:', error);
      console.error('Error details:', error.response?.data);
      toast.error(`Failed to load dashboard: ${error.response?.data?.detail || error.message}`);
      setLoading(false);
    }
  };

  const fetchTeamOverview = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API}/api/dashboard/team-overview`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setTeamOverview(response.data);
    } catch (error) {
      console.error('Error fetching team overview:', error);
    }
  };

  const fetchTeamMembers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const approvedMembers = response.data.filter(u => 
        u.approval_status === 'approved' && u.role !== 'owner'
      );
      setTeamMembers(approvedMembers);
    } catch (error) {
      console.error('Error fetching team members:', error);
    }
  };

  const fetchProjects = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/api/projects`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setProjects(response.data);
    } catch (error) {
      console.error('Error fetching projects:', error);
    }
  };

  const handleCreateTask = async () => {
    try {
      const token = localStorage.getItem('token');
      
      // Combine date and time
      const dueDateTime = `${newTask.due_date}T${newTask.due_time}:00`;
      
      await axios.post(
        `${API}/api/tasks/ad-hoc`,
        {
          title: newTask.title,
          description: newTask.description,
          assigned_to_id: newTask.assigned_to_id,
          due_date_time: dueDateTime,
          priority: newTask.priority,
          project_id: newTask.project_id || null,
          category: 'OTHER'
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Task assigned successfully!');
      setTaskDialogOpen(false);
      setNewTask({
        title: '',
        description: '',
        assigned_to_id: '',
        due_date: '',
        due_time: '',
        priority: 'MEDIUM',
        project_id: ''
      });
      fetchDashboardData();
      fetchTeamOverview();
    } catch (error) {
      console.error('Error creating task:', error);
      toast.error('Failed to create task');
    }
  };

  const handleMarkComplete = async (taskId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(
        `${API}/api/tasks/${taskId}/complete`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Task marked as complete!');
      fetchDashboardData();
    } catch (error) {
      console.error('Error marking task complete:', error);
      toast.error('Failed to mark task complete');
    }
  };

  const getStatusColor = (status) => {
    if (status.includes('✅')) return 'text-green-600 bg-green-50';
    if (status.includes('🟡')) return 'text-yellow-600 bg-yellow-50';
    if (status.includes('🟢')) return 'text-blue-600 bg-blue-50';
    if (status.includes('🔴')) return 'text-red-600 bg-red-50';
    return 'text-gray-600 bg-gray-50';
  };

  const getUrgencyColor = (urgency) => {
    if (urgency.includes('🔴')) return 'bg-red-100 border-red-300 text-red-800';
    if (urgency.includes('🟠')) return 'bg-orange-100 border-orange-300 text-orange-800';
    if (urgency.includes('🟡')) return 'bg-yellow-100 border-yellow-300 text-yellow-800';
    return 'bg-blue-100 border-blue-300 text-blue-800';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">Weekly Dashboard</h1>
              <p className="text-sm text-slate-600">
                Week of {new Date(dashboardData?.week_start).toLocaleDateString()} - {new Date(dashboardData?.week_end).toLocaleDateString()}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {user?.role === 'owner' && (
                <Button onClick={() => setTaskDialogOpen(true)} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="w-4 h-4 mr-2" />
                  Assign Task
                </Button>
              )}
              <Button 
                variant="outline" 
                onClick={() => navigate('/owner-dashboard')}
              >
                Owner Dashboard
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overall Progress Card */}
        <div className="bg-white rounded-xl shadow-lg p-6 mb-8 border border-slate-200">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <Target className="w-8 h-8 text-blue-600" />
              <div>
                <h2 className="text-xl font-bold text-slate-900">This Week's Progress</h2>
                <p className="text-sm text-slate-600">
                  {dashboardData?.overall.completed_points} of {dashboardData?.overall.total_points} points completed
                </p>
              </div>
            </div>
            <div className="text-right">
              <div className="text-3xl font-bold text-blue-600">
                {dashboardData?.overall.progress_percentage || 0}%
              </div>
              <div className="text-xs text-slate-500">Overall Progress</div>
            </div>
          </div>
          
          {/* Progress Bar */}
          <div className="w-full bg-slate-200 rounded-full h-6 overflow-hidden">
            <div 
              className="bg-gradient-to-r from-blue-500 to-blue-600 h-6 rounded-full transition-all duration-500 flex items-center justify-center"
              style={{ width: `${dashboardData?.overall.progress_percentage || 0}%` }}
            >
              {(dashboardData?.overall.progress_percentage || 0) > 10 && (
                <span className="text-xs font-bold text-white">
                  {dashboardData?.overall.progress_percentage || 0}%
                </span>
              )}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
            <div className="text-center p-3 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">
                {dashboardData?.overall.projects_count || 0}
              </div>
              <div className="text-xs text-slate-600">Active Projects</div>
            </div>
            <div className="text-center p-3 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">
                {dashboardData?.overall.completed_points || 0}
              </div>
              <div className="text-xs text-slate-600">Points Done</div>
            </div>
            <div className="text-center p-3 bg-orange-50 rounded-lg">
              <div className="text-2xl font-bold text-orange-600">
                {(dashboardData?.overall.total_points || 0) - (dashboardData?.overall.completed_points || 0)}
              </div>
              <div className="text-xs text-slate-600">Points Pending</div>
            </div>
            <div className="text-center p-3 bg-purple-50 rounded-lg">
              <div className="text-2xl font-bold text-purple-600">
                {dashboardData?.ad_hoc_tasks?.total || 0}
              </div>
              <div className="text-xs text-slate-600">Ad-hoc Tasks</div>
            </div>
          </div>
        </div>

        {/* Projects Section */}
        <div className="mb-8">
          <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
            <Calendar className="w-6 h-6 text-blue-600" />
            Your Projects
          </h2>
          
          {dashboardData?.projects && dashboardData.projects.length > 0 ? (
            <div className="grid gap-6">
              {dashboardData.projects.map((project) => (
                <div 
                  key={project.project_id} 
                  className="bg-white rounded-xl shadow-md border border-slate-200 overflow-hidden hover:shadow-lg transition-shadow"
                >
                  {/* Project Header */}
                  <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-4 text-white">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-lg font-bold">{project.project_title}</h3>
                        <p className="text-sm text-blue-100">{project.project_code}</p>
                        {project.client_name && (
                          <p className="text-xs text-blue-200 mt-1">Client: {project.client_name}</p>
                        )}
                      </div>
                      <div className="text-right">
                        <div className="text-2xl font-bold">{project.progress_percentage}%</div>
                        <div className="text-xs text-blue-200">Complete</div>
                      </div>
                    </div>
                    
                    {/* Project Progress Bar */}
                    <div className="w-full bg-blue-800 rounded-full h-2 mt-3">
                      <div 
                        className="bg-white h-2 rounded-full transition-all duration-500"
                        style={{ width: `${project.progress_percentage}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Drawings List */}
                  <div className="p-4">
                    <div className="text-sm text-slate-600 mb-3">
                      {project.completed_points} of {project.total_points} points • {project.drawings.length} drawings
                    </div>
                    
                    <div className="space-y-2">
                      {project.drawings.map((drawing) => (
                        <div 
                          key={drawing.id}
                          className={`p-3 rounded-lg border-2 ${getStatusColor(drawing.status)} transition-all hover:scale-[1.02]`}
                        >
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                {drawing.is_completed ? (
                                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                                ) : (
                                  <Circle className="w-5 h-5 text-slate-400" />
                                )}
                                <h4 className="font-semibold text-slate-900">{drawing.name}</h4>
                                <span className="text-xs px-2 py-1 bg-slate-200 text-slate-700 rounded-full">
                                  {drawing.complexity} • {drawing.points} pts
                                </span>
                              </div>
                              <div className="flex items-center gap-3 mt-2 text-xs text-slate-600">
                                <span className="flex items-center gap-1">
                                  <Flag className="w-3 h-3" />
                                  {drawing.category}
                                </span>
                                {drawing.due_date && (
                                  <span className="flex items-center gap-1">
                                    <Clock className="w-3 h-3" />
                                    Due: {new Date(drawing.due_date).toLocaleDateString()}
                                  </span>
                                )}
                              </div>
                            </div>
                            <div className="text-sm font-medium px-3 py-1 rounded-full">
                              {drawing.status}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-md p-12 text-center border border-slate-200">
              <Calendar className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-slate-900 mb-2">No Active Projects</h3>
              <p className="text-slate-600">You don't have any active projects this week.</p>
            </div>
          )}
        </div>

        {/* Ad-hoc Tasks Section */}
        {dashboardData?.ad_hoc_tasks && dashboardData.ad_hoc_tasks.total > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Plus className="w-6 h-6 text-orange-600" />
              Additional Tasks This Week
            </h2>
            
            <div className="bg-white rounded-xl shadow-md p-6 border border-slate-200">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <div className="text-sm text-slate-600">
                    {dashboardData.ad_hoc_tasks.completed} of {dashboardData.ad_hoc_tasks.total} tasks completed
                  </div>
                </div>
                <div className="text-2xl font-bold text-orange-600">
                  {dashboardData.ad_hoc_tasks.progress_percentage}%
                </div>
              </div>

              <div className="w-full bg-slate-200 rounded-full h-4 mb-6">
                <div 
                  className="bg-gradient-to-r from-orange-500 to-orange-600 h-4 rounded-full transition-all duration-500"
                  style={{ width: `${dashboardData.ad_hoc_tasks.progress_percentage}%` }}
                ></div>
              </div>

              <div className="space-y-3">
                {dashboardData.ad_hoc_tasks.tasks.map((task) => (
                  <div 
                    key={task.id}
                    className={`p-4 rounded-lg border-2 ${getUrgencyColor(task.urgency)}`}
                  >
                    <div className="flex justify-between items-start">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-lg">{task.urgency.split(' ')[0]}</span>
                          <h4 className="font-semibold text-slate-900">{task.title}</h4>
                        </div>
                        {task.description && (
                          <p className="text-sm text-slate-600 mb-2">{task.description}</p>
                        )}
                        <div className="flex items-center gap-3 text-xs text-slate-600">
                          <span className="flex items-center gap-1">
                            <Clock className="w-3 h-3" />
                            {new Date(task.due_date_time).toLocaleString()}
                          </span>
                          <span className="px-2 py-1 bg-slate-200 rounded-full">
                            {task.priority}
                          </span>
                        </div>
                      </div>
                      {!task.is_completed && (
                        <Button 
                          size="sm"
                          onClick={() => handleMarkComplete(task.id)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <CheckCircle2 className="w-4 h-4 mr-1" />
                          Complete
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {dashboardData.ad_hoc_tasks.completed < dashboardData.ad_hoc_tasks.total && (
                <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg text-sm text-yellow-800">
                  <AlertCircle className="w-4 h-4 inline mr-2" />
                  Incomplete tasks will roll over to next week
                </div>
              )}
            </div>
          </div>
        )}

        {/* Owner Team Overview */}
        {user?.role === 'owner' && teamOverview && (
          <div className="mb-8">
            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center gap-2">
              <Users className="w-6 h-6 text-purple-600" />
              Team Overview
            </h2>
            
            <div className="bg-white rounded-xl shadow-md p-6 border border-slate-200">
              <div className="mb-6">
                <div className="text-sm text-slate-600 mb-2">Team Average Progress</div>
                <div className="flex items-center gap-4">
                  <div className="flex-1 bg-slate-200 rounded-full h-4">
                    <div 
                      className="bg-gradient-to-r from-purple-500 to-purple-600 h-4 rounded-full"
                      style={{ width: `${teamOverview.avg_progress}%` }}
                    ></div>
                  </div>
                  <div className="text-2xl font-bold text-purple-600">
                    {Math.round(teamOverview.avg_progress)}%
                  </div>
                </div>
              </div>

              <div className="space-y-3">
                {teamOverview.team_members.map((member) => (
                  <div 
                    key={member.user_id}
                    className="p-4 bg-slate-50 rounded-lg border border-slate-200 hover:shadow-md transition-shadow"
                  >
                    <div className="flex justify-between items-center mb-2">
                      <div>
                        <h4 className="font-semibold text-slate-900">{member.name}</h4>
                        <p className="text-xs text-slate-600">{member.role} • {member.email}</p>
                      </div>
                      <div className="text-right">
                        <div className="text-xl font-bold text-slate-900">
                          {member.overall_progress}%
                        </div>
                        <div className="text-xs">{member.status}</div>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-4 text-xs text-slate-600">
                      <span>{member.projects_count} projects</span>
                      <span>•</span>
                      <span>{member.total_points} points</span>
                      <span>•</span>
                      <span>{member.ad_hoc_tasks} tasks</span>
                    </div>
                    
                    <div className="w-full bg-slate-200 rounded-full h-2 mt-3">
                      <div 
                        className={`h-2 rounded-full ${
                          member.overall_progress >= 75 ? 'bg-green-500' :
                          member.overall_progress >= 50 ? 'bg-yellow-500' :
                          'bg-red-500'
                        }`}
                        style={{ width: `${member.overall_progress}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Create Task Dialog */}
      <Dialog open={taskDialogOpen} onOpenChange={setTaskDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Assign New Task</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            <div>
              <Label>Task Title *</Label>
              <input
                type="text"
                className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                value={newTask.title}
                onChange={(e) => setNewTask({...newTask, title: e.target.value})}
                placeholder="e.g., Update client presentation"
              />
            </div>

            <div>
              <Label>Description</Label>
              <Textarea
                className="mt-1"
                value={newTask.description}
                onChange={(e) => setNewTask({...newTask, description: e.target.value})}
                placeholder="Task details..."
                rows={3}
              />
            </div>

            <div>
              <Label>Assign To *</Label>
              <select
                className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                value={newTask.assigned_to_id}
                onChange={(e) => setNewTask({...newTask, assigned_to_id: e.target.value})}
              >
                <option value="">Select team member</option>
                {teamMembers.map(member => (
                  <option key={member.id} value={member.id}>
                    {member.name} ({member.role})
                  </option>
                ))}
              </select>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Due Date *</Label>
                <input
                  type="date"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={newTask.due_date}
                  onChange={(e) => setNewTask({...newTask, due_date: e.target.value})}
                />
              </div>
              <div>
                <Label>Due Time *</Label>
                <input
                  type="time"
                  className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                  value={newTask.due_time}
                  onChange={(e) => setNewTask({...newTask, due_time: e.target.value})}
                />
              </div>
            </div>

            <div>
              <Label>Priority</Label>
              <select
                className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                value={newTask.priority}
                onChange={(e) => setNewTask({...newTask, priority: e.target.value})}
              >
                <option value="LOW">Low</option>
                <option value="MEDIUM">Medium</option>
                <option value="HIGH">High</option>
                <option value="CRITICAL">Critical</option>
              </select>
            </div>

            <div>
              <Label>Related Project (Optional)</Label>
              <select
                className="w-full mt-1 px-3 py-2 border border-slate-300 rounded-lg"
                value={newTask.project_id}
                onChange={(e) => setNewTask({...newTask, project_id: e.target.value})}
              >
                <option value="">None (General Task)</option>
                {projects.map(project => (
                  <option key={project.id} value={project.id}>
                    {project.title} ({project.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex gap-3 pt-4">
              <Button 
                className="flex-1 bg-blue-600 hover:bg-blue-700"
                onClick={handleCreateTask}
                disabled={!newTask.title || !newTask.assigned_to_id || !newTask.due_date || !newTask.due_time}
              >
                Assign Task
              </Button>
              <Button 
                variant="outline" 
                className="flex-1"
                onClick={() => setTaskDialogOpen(false)}
              >
                Cancel
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
