import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { 
  FolderOpen, Users, CheckCircle2, Target, Star, 
  Calendar, TrendingUp, Clock, Award, Bell, FileText, AlertCircle
} from 'lucide-react';
import { toast } from 'sonner';
import { formatErrorMessage } from '@/utils/errorHandler';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard({ user, onLogout }) {
  const navigate = useNavigate();
  const [dailyTasks, setDailyTasks] = useState([]);
  const [weeklyTargets, setWeeklyTargets] = useState([]);
  const [weeklyRating, setWeeklyRating] = useState(null);
  const [teamRatings, setTeamRatings] = useState([]);
  const [pendingDrawings, setPendingDrawings] = useState([]);
  const [upcomingDrawings, setUpcomingDrawings] = useState([]);
  const [overdueCount, setOverdueCount] = useState(0);
  const [dueTodayCount, setDueTodayCount] = useState(0);
  const [totalDue, setTotalDue] = useState(0);
  const [totalProjects, setTotalProjects] = useState(0);
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Redirect owners to Owner Dashboard
    if (user?.role === 'owner') {
      navigate('/owner-dashboard');
      return;
    }
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const today = new Date().toISOString().split('T')[0];
      
      // Use new dashboard stats endpoint for team members
      if (user && !user.is_owner) {
        const [statsRes, tasksRes, targetsRes, ratingsRes] = await Promise.all([
          axios.get(`${API}/dashboard/team-member-stats`),
          axios.get(`${API}/daily-tasks?date=${today}`),
          axios.get(`${API}/weekly-targets`),
          axios.get(`${API}/weekly-ratings`)
        ]);
        
        const stats = statsRes.data;
        setPendingDrawings(stats.due_drawings || []);
        setUpcomingDrawings(stats.upcoming_drawings || []);
        setOverdueCount(stats.overdue_count || 0);
        setDueTodayCount(stats.due_today_count || 0);
        setTotalDue(stats.total_due || 0);
        setTotalProjects(stats.total_projects || 0);
        
        setDailyTasks(tasksRes.data);
        setWeeklyTargets(targetsRes.data);
        
        const ratings = ratingsRes.data;
        if (ratings.length > 0) {
          setWeeklyRating(ratings[0]);
        }
      } else {
        // Owner dashboard - keep existing logic
        const requests = [
          axios.get(`${API}/daily-tasks?date=${today}`),
          axios.get(`${API}/weekly-targets`),
          axios.get(`${API}/weekly-ratings`),
          axios.get(`${API}/projects`)
        ];

        if (user?.is_owner) {
          requests.push(axios.get(`${API}/weekly-ratings`));
        }

        const responses = await Promise.all(requests);
        
        setDailyTasks(responses[0].data);
        setWeeklyTargets(responses[1].data);
        setProjects(responses[3].data);
        
        const ratings = responses[2].data;
        if (ratings.length > 0) {
          setWeeklyRating(ratings[0]);
        }

        if (user?.is_owner && responses[4]) {
          setTeamRatings(responses[4].data);
        }
      }
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteTask = async (taskId) => {
    try {
      await axios.put(`${API}/daily-tasks/${taskId}`, {
        completed: true
      });
      toast.success('Task completed! 🎉');
      fetchData(); // Refresh data
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to complete task'));
    }
  };

  const getCurrentWeekProgress = () => {
    if (weeklyTargets.length === 0) return { total: 0, completed: 0, percentage: 0 };
    
    const currentWeek = weeklyTargets.find(t => {
      const start = new Date(t.week_start_date);
      const end = new Date(t.week_end_date);
      const today = new Date();
      return today >= start && today <= end;
    });

    if (!currentWeek) return { total: 0, completed: 0, percentage: 0 };

    const percentage = currentWeek.target_quantity > 0 
      ? (currentWeek.completed_quantity / currentWeek.target_quantity) * 100 
      : 0;

    return {
      total: currentWeek.target_quantity,
      completed: currentWeek.completed_quantity,
      percentage: Math.round(percentage)
    };
  };

  const renderStars = (rating) => {
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 >= 0.5;
    
    return (
      <div className="flex items-center gap-1">
        {[...Array(5)].map((_, i) => (
          <Star 
            key={i}
            className={`w-4 h-4 ${
              i < fullStars 
                ? 'fill-amber-400 text-amber-400' 
                : i === fullStars && hasHalfStar 
                  ? 'fill-amber-200 text-amber-400'
                  : 'text-slate-300'
            }`}
          />
        ))}
        <span className="text-sm font-medium text-slate-700 ml-1">{rating.toFixed(1)}</span>
      </div>
    );
  };

  const weekProgress = getCurrentWeekProgress();
  const todayCompleted = dailyTasks.filter(t => t.completed).length;
  const todayTotal = dailyTasks.length;

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
        <div className="mb-4 sm:mb-6 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900">
              {user?.is_owner ? 'Team Dashboard' : "Today's Focus"}
            </h1>
            <p className="text-sm sm:text-base text-slate-600 mt-1">
              {user?.is_owner ? 'Overview of team performance and activities' : `What needs your attention today - ${new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}`}
            </p>
          </div>
          <Button 
            onClick={() => navigate('/weekly-dashboard')}
            className="bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-lg whitespace-nowrap"
          >
            📊 Weekly Tasks
          </Button>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 lg:gap-6 mb-4 sm:mb-6">
          {/* Today's Critical */}
          <Card className={overdueCount + dueTodayCount > 0 ? "border-2 border-red-500" : ""}>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">Today's Critical</span>
                <AlertCircle className={`w-4 h-4 sm:w-5 sm:h-5 ${overdueCount + dueTodayCount > 0 ? 'text-red-600' : 'text-slate-400'}`} />
              </div>
              <div className={`text-xl sm:text-2xl lg:text-3xl font-bold ${overdueCount + dueTodayCount > 0 ? 'text-red-600' : 'text-slate-900'}`}>
                {overdueCount + dueTodayCount}
              </div>
              <p className="text-[10px] sm:text-xs text-slate-500 mt-1">
                {overdueCount} overdue • {dueTodayCount} due today
              </p>
            </CardContent>
          </Card>

          {/* All Due Drawings */}
          <Card>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">Due Drawings</span>
                <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
              </div>
              <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900">
                {totalDue}
              </div>
              <p className="text-[10px] sm:text-xs text-slate-500 mt-1">Across {totalProjects} projects</p>
            </CardContent>
          </Card>

          {/* Upcoming Drawings */}
          <Card>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">Upcoming</span>
                <Calendar className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
              </div>
              <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-900">
                {upcomingDrawings.length}
              </div>
              <p className="text-[10px] sm:text-xs text-slate-500 mt-1">Prepare in advance</p>
            </CardContent>
          </Card>

          {/* Last Rating */}
          <Card>
            <CardContent className="p-3 sm:p-4 lg:p-6">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs sm:text-sm text-slate-600">Last Week</span>
                <Award className="w-4 h-4 sm:w-5 sm:h-5 text-amber-600" />
              </div>
              {weeklyRating ? (
                <div className="mt-1">
                  {renderStars(weeklyRating.rating)}
                  <p className="text-xs text-slate-500 mt-1">
                    {weeklyRating.completion_percentage.toFixed(0)}% complete
                  </p>
                </div>
              ) : (
                <div className="text-xl sm:text-2xl lg:text-3xl font-bold text-slate-400">
                  N/A
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:gap-6">
          {/* All Due Drawings */}
          <Card>
            <CardHeader className="pb-3 sm:pb-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                    <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
                    All Due Drawings ({totalDue})
                  </CardTitle>
                  <p className="text-xs sm:text-sm text-slate-500 mt-1">
                    Sorted by priority • {overdueCount} overdue, {dueTodayCount} due today
                  </p>
                </div>
                <Button 
                  onClick={() => navigate('/projects')}
                  variant="outline"
                  size="sm"
                >
                  View Projects →
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-3 sm:p-6">
              {pendingDrawings.length === 0 ? (
                <div className="text-center py-8 sm:py-12">
                  <CheckCircle2 className="w-12 h-12 sm:w-16 sm:h-16 text-green-300 mx-auto mb-3 sm:mb-4" />
                  <p className="text-sm sm:text-base text-slate-500">
                    All caught up! No due drawings 🎉
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {pendingDrawings.map((drawing) => {
                    const daysUntilDue = drawing.due_date 
                      ? Math.ceil((new Date(drawing.due_date) - new Date()) / (1000 * 60 * 60 * 24))
                      : null;
                    const isOverdue = daysUntilDue !== null && daysUntilDue < 0;
                    const isDueToday = daysUntilDue !== null && daysUntilDue === 0;
                    const isUrgent = daysUntilDue !== null && daysUntilDue >= 0 && daysUntilDue <= 2;
                    
                    return (
                      <div 
                        key={drawing.id} 
                        className={`p-3 sm:p-4 rounded-lg border-2 cursor-pointer hover:shadow-md transition-all ${
                          isOverdue ? 'border-red-500 bg-red-50' : 
                          isDueToday ? 'border-orange-500 bg-orange-50' :
                          isUrgent ? 'border-yellow-400 bg-yellow-50' : 
                          'border-slate-200 bg-white'
                        }`}
                        onClick={() => navigate(`/projects/${drawing.project.id}`)}
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2 flex-wrap">
                              <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-slate-100 text-slate-700 rounded font-medium">
                                {drawing.category}
                              </span>
                              <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-blue-100 text-blue-700 rounded">
                                Seq #{drawing.sequence_number}
                              </span>
                              {drawing.has_pending_revision && (
                                <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-amber-100 text-amber-700 rounded font-medium">
                                  Revision Pending
                                </span>
                              )}
                              {daysUntilDue !== null && (
                                <span className={`px-2 py-0.5 text-[10px] sm:text-xs rounded font-medium ${
                                  isOverdue ? 'bg-red-600 text-white' :
                                  isDueToday ? 'bg-orange-600 text-white' :
                                  isUrgent ? 'bg-yellow-600 text-white' :
                                  'bg-green-600 text-white'
                                }`}>
                                  {isOverdue ? `${Math.abs(daysUntilDue)}d overdue` : 
                                   isDueToday ? 'Due today!' :
                                   `${daysUntilDue}d left`}
                                </span>
                              )}
                            </div>
                            <h4 className="font-medium text-sm sm:text-base text-slate-900 mb-1">{drawing.name}</h4>
                            <p className="text-xs sm:text-sm text-slate-600">
                              {drawing.project.code} - {drawing.project.title}
                            </p>
                            {drawing.due_date && (
                              <p className="text-xs text-slate-500 mt-1">
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
              )}
            </CardContent>
          </Card>

          {/* Upcoming Drawings */}
          {upcomingDrawings.length > 0 && (
            <Card>
              <CardHeader className="pb-3 sm:pb-4">
                <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                  <Calendar className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
                  Upcoming Drawings ({upcomingDrawings.length})
                </CardTitle>
                <p className="text-xs sm:text-sm text-slate-500 mt-1">
                  Prepare these in advance
                </p>
              </CardHeader>
              <CardContent className="p-3 sm:p-6">
                <div className="space-y-3">
                  {upcomingDrawings.map((drawing) => (
                    <div 
                      key={drawing.id} 
                      className="p-3 sm:p-4 rounded-lg border border-slate-200 bg-blue-50/30 cursor-pointer hover:shadow-md transition-all"
                      onClick={() => navigate(`/projects/${drawing.project.id}`)}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-2 flex-wrap">
                            <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-slate-100 text-slate-700 rounded font-medium">
                              {drawing.category}
                            </span>
                            <span className="px-2 py-0.5 text-[10px] sm:text-xs bg-blue-100 text-blue-700 rounded">
                              Seq #{drawing.sequence_number}
                            </span>
                          </div>
                          <h4 className="font-medium text-sm sm:text-base text-slate-900 mb-1">{drawing.name}</h4>
                          <p className="text-xs sm:text-sm text-slate-600">
                            {drawing.project.code} - {drawing.project.title}
                          </p>
                          {drawing.due_date && (
                            <p className="text-xs text-slate-500 mt-1">
                              Due: {new Date(drawing.due_date).toLocaleDateString('en-US', { 
                                weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' 
                              })}
                            </p>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

          {/* Weekly Targets & Ratings */}
          <div className="space-y-4 sm:space-y-6">
            {/* This Week's Target */}
            <Card>
              <CardHeader className="pb-3 sm:pb-4">
                <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                  <Target className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
                  This Week's Target
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 sm:p-6">
                {weeklyTargets.length > 0 ? (
                  <div className="space-y-3 sm:space-y-4">
                    {weeklyTargets.filter(t => {
                      const start = new Date(t.week_start_date);
                      const end = new Date(t.week_end_date);
                      const today = new Date();
                      return today >= start && today <= end;
                    }).map((target) => (
                      <div key={target.id} className="space-y-2">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-xs sm:text-sm font-medium text-slate-900 flex-1">
                            {target.target_description}
                          </p>
                          <span className="text-xs sm:text-sm font-bold text-orange-600 flex-shrink-0">
                            {target.completed_quantity}/{target.target_quantity}
                          </span>
                        </div>
                        <div className="w-full bg-slate-200 rounded-full h-2">
                          <div 
                            className="bg-orange-500 h-2 rounded-full transition-all"
                            style={{ 
                              width: `${(target.completed_quantity / target.target_quantity) * 100}%` 
                            }}
                          />
                        </div>
                        <p className="text-[10px] sm:text-xs text-slate-500">
                          Type: {target.target_type}
                        </p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 sm:py-8">
                    <Target className="w-10 h-10 sm:w-12 sm:h-12 text-slate-300 mx-auto mb-2 sm:mb-3" />
                    <p className="text-xs sm:text-sm text-slate-500">
                      No targets assigned yet
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Urgent Drawings (Team Leaders Only) */}
            {!user?.is_owner && pendingDrawings.length > 0 && (
              <Card>
                <CardHeader className="pb-3 sm:pb-4">
                  <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                    <FileText className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
                    My Pending Drawings ({pendingDrawings.length})
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 sm:p-6">
                  <div className="space-y-2 max-h-96 overflow-y-auto">
                    {pendingDrawings.slice(0, 10).map((drawing) => {
                      const daysUntilDue = drawing.due_date 
                        ? Math.ceil((new Date(drawing.due_date) - new Date()) / (1000 * 60 * 60 * 24))
                        : null;
                      const isOverdue = daysUntilDue !== null && daysUntilDue < 0;
                      const isUrgent = daysUntilDue !== null && daysUntilDue >= 0 && daysUntilDue <= 2;
                      
                      return (
                        <div 
                          key={drawing.id} 
                          className={`p-2 sm:p-3 rounded-lg border-2 cursor-pointer hover:shadow-md transition-shadow ${
                            isOverdue ? 'border-red-200 bg-red-50' : 
                            isUrgent ? 'border-orange-200 bg-orange-50' : 
                            'border-slate-200 bg-white'
                          }`}
                          onClick={() => window.location.href = `/projects/${drawing.project.id}`}
                        >
                          <div className="flex items-start justify-between gap-2 mb-1">
                            <div className="flex-1 min-w-0">
                              <p className="text-xs sm:text-sm font-medium text-slate-900 truncate">
                                {drawing.name}
                              </p>
                              <p className="text-[10px] sm:text-xs text-slate-500 truncate">
                                {drawing.project.code} - {drawing.project.title}
                              </p>
                            </div>
                            {daysUntilDue !== null && (
                              <span className={`text-[10px] sm:text-xs font-medium px-2 py-0.5 rounded-full whitespace-nowrap ${
                                isOverdue ? 'bg-red-600 text-white' :
                                isUrgent ? 'bg-orange-600 text-white' :
                                'bg-blue-600 text-white'
                              }`}>
                                {isOverdue ? `${Math.abs(daysUntilDue)}d overdue` : 
                                 daysUntilDue === 0 ? 'Due today' :
                                 `${daysUntilDue}d left`}
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="text-[10px] text-slate-500">{drawing.category}</span>
                            {drawing.has_pending_revision && (
                              <span className="text-[10px] text-orange-600 font-medium">• Revision Pending</span>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                  {pendingDrawings.length > 10 && (
                    <p className="text-xs text-slate-500 text-center mt-3">
                      Showing 10 of {pendingDrawings.length} pending drawings assigned to you
                    </p>
                  )}
                  {pendingDrawings.length > 0 && (
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full mt-3"
                      onClick={() => navigate('/projects')}
                    >
                      View All Projects →
                    </Button>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Recent Ratings */}
            {weeklyRating && (
              <Card>
                <CardHeader className="pb-3 sm:pb-4">
                  <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                    <Star className="w-4 h-4 sm:w-5 sm:h-5 text-amber-600" />
                    Last Week's Performance
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-3 sm:p-6">
                  <div className="space-y-3 sm:space-y-4">
                    <div className="flex items-center justify-between">
                      <span className="text-xs sm:text-sm text-slate-600">Rating</span>
                      {renderStars(weeklyRating.rating)}
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs sm:text-sm text-slate-600">Completion</span>
                      <span className="text-sm sm:text-base font-bold text-slate-900">
                        {weeklyRating.completion_percentage.toFixed(0)}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-xs sm:text-sm text-slate-600">Completed</span>
                      <span className="text-sm sm:text-base font-medium text-slate-900">
                        {weeklyRating.completed_targets}/{weeklyRating.total_targets}
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

          </div>
        </div>

        {/* Owner View - Team Performance */}
        {user?.is_owner && teamRatings.length > 0 && (
          <Card className="mt-4 sm:mt-6">
            <CardHeader>
              <CardTitle className="text-base sm:text-lg flex items-center gap-2">
                <TrendingUp className="w-4 h-4 sm:w-5 sm:h-5 text-blue-600" />
                Team Performance
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 sm:p-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 sm:gap-4">
                {teamRatings.slice(0, 8).map((rating) => (
                  <div 
                    key={rating.id} 
                    className="p-3 sm:p-4 border border-slate-200 rounded-lg hover:border-orange-300 transition-colors"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="w-8 h-8 sm:w-10 sm:h-10 bg-orange-100 rounded-full flex items-center justify-center">
                        <Users className="w-4 h-4 sm:w-5 sm:h-5 text-orange-600" />
                      </div>
                      {renderStars(rating.rating)}
                    </div>
                    <p className="text-xs sm:text-sm font-medium text-slate-900 truncate">
                      Team Member
                    </p>
                    <p className="text-[10px] sm:text-xs text-slate-500 mt-1">
                      {rating.completion_percentage.toFixed(0)}% completion
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </Layout>
  );
}
