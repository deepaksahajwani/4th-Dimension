import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Users, Target, Plus, Calendar, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';
import { formatErrorMessage } from '@/utils/errorHandler';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function AssignTargets({ user, onLogout }) {
  const navigate = useNavigate();
  const [teamMembers, setTeamMembers] = useState([]);
  const [projects, setProjects] = useState([]);
  const [weeklyTargets, setWeeklyTargets] = useState([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  
  const [formData, setFormData] = useState({
    assigned_to_id: '',
    week_start_date: '',
    target_type: 'drawing_completion',
    target_description: '',
    target_quantity: '',
    project_id: '',
    drawing_ids: [],
    daily_breakdown: [0, 0, 0, 0, 0] // Mon-Fri
  });

  useEffect(() => {
    if (!user?.is_owner) {
      navigate('/dashboard');
      return;
    }
    fetchData();
  }, [user]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };
      
      const [usersRes, projectsRes, targetsRes] = await Promise.all([
        axios.get(`${API}/users`, { headers }),
        axios.get(`${API}/projects`, { headers }),
        axios.get(`${API}/weekly-targets`, { headers })
      ]);
      setTeamMembers(usersRes.data);
      setProjects(projectsRes.data);
      setWeeklyTargets(targetsRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const getNextMonday = () => {
    const today = new Date();
    const dayOfWeek = today.getDay();
    const daysUntilMonday = dayOfWeek === 0 ? 1 : (8 - dayOfWeek);
    const nextMonday = new Date(today);
    nextMonday.setDate(today.getDate() + daysUntilMonday);
    return nextMonday.toISOString().split('T')[0];
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    try {
      // Validate daily breakdown matches target quantity
      const totalDaily = formData.daily_breakdown.reduce((a, b) => a + b, 0);
      if (totalDaily !== parseInt(formData.target_quantity)) {
        toast.error(`Daily breakdown (${totalDaily}) must equal target quantity (${formData.target_quantity})`);
        return;
      }

      await axios.post(`${API}/weekly-targets`, formData);
      toast.success('Weekly target assigned successfully!');
      setDialogOpen(false);
      resetForm();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to assign target'));
    }
  };

  const resetForm = () => {
    setFormData({
      assigned_to_id: '',
      week_start_date: getNextMonday(),
      target_type: 'drawing_completion',
      target_description: '',
      target_quantity: '',
      project_id: '',
      drawing_ids: [],
      daily_breakdown: [0, 0, 0, 0, 0]
    });
  };

  const handleQuantityChange = (value) => {
    const quantity = parseInt(value) || 0;
    setFormData({ ...formData, target_quantity: value });
    
    // Auto-distribute evenly across weekdays
    if (quantity > 0) {
      const perDay = Math.floor(quantity / 5);
      const remainder = quantity % 5;
      const breakdown = [perDay, perDay, perDay, perDay, perDay];
      // Add remainder to first days
      for (let i = 0; i < remainder; i++) {
        breakdown[i]++;
      }
      setFormData(prev => ({ ...prev, daily_breakdown: breakdown }));
    }
  };

  const handleDailyChange = (index, value) => {
    const newBreakdown = [...formData.daily_breakdown];
    newBreakdown[index] = parseInt(value) || 0;
    setFormData({ ...formData, daily_breakdown: newBreakdown });
  };

  const weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
  const totalDaily = formData.daily_breakdown.reduce((a, b) => a + b, 0);

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
            Assign Weekly Targets
          </h1>
          <p className="text-sm sm:text-base text-slate-600 mt-1">
            Set weekly goals for team members with daily breakdown
          </p>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-6">
          <Card 
            className="cursor-pointer hover:shadow-lg transition-shadow border-2 border-orange-200 bg-orange-50"
            onClick={() => {
              setFormData({ ...formData, week_start_date: getNextMonday() });
              setDialogOpen(true);
            }}
          >
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-orange-500 rounded-lg flex items-center justify-center">
                  <Plus className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">Assign New Target</h3>
                  <p className="text-sm text-slate-600">For next week</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-blue-200 bg-blue-50">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-500 rounded-lg flex items-center justify-center">
                  <Users className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">{teamMembers.length}</h3>
                  <p className="text-sm text-slate-600">Team Members</p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-2 border-green-200 bg-green-50">
            <CardContent className="p-4 sm:p-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-green-500 rounded-lg flex items-center justify-center">
                  <Target className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h3 className="font-semibold text-slate-900">{projects.length}</h3>
                  <p className="text-sm text-slate-600">Active Projects</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Team Members List */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base sm:text-lg">Team Members</CardTitle>
          </CardHeader>
          <CardContent className="p-3 sm:p-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
              {teamMembers.map((member) => (
                <div 
                  key={member.id}
                  className="p-3 sm:p-4 border-2 border-slate-200 rounded-lg hover:border-orange-300 transition-colors"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-10 h-10 bg-orange-500 rounded-full flex items-center justify-center text-white font-bold">
                      {member.name?.charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sm sm:text-base text-slate-900 truncate">
                        {member.name}
                      </h4>
                      <p className="text-xs sm:text-sm text-slate-500 capitalize truncate">
                        {member.role?.replace('_', ' ')}
                      </p>
                    </div>
                  </div>
                  <Button
                    size="sm"
                    onClick={() => {
                      setFormData({ 
                        ...formData, 
                        assigned_to_id: member.id,
                        week_start_date: getNextMonday()
                      });
                      setDialogOpen(true);
                    }}
                    className="w-full bg-orange-500 hover:bg-orange-600 text-xs sm:text-sm"
                  >
                    <Plus className="w-3 h-3 sm:w-4 sm:h-4 mr-2" />
                    Assign Target
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Assign Target Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Assign Weekly Target</DialogTitle>
            </DialogHeader>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 sm:col-span-1">
                  <Label>Team Member *</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                    value={formData.assigned_to_id}
                    onChange={(e) => setFormData({ ...formData, assigned_to_id: e.target.value })}
                    required
                  >
                    <option value="">Select team member</option>
                    {teamMembers.map((member) => (
                      <option key={member.id} value={member.id}>
                        {member.name} ({member.role?.replace('_', ' ')})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="col-span-2 sm:col-span-1">
                  <Label>Week Starting (Monday) *</Label>
                  <Input
                    type="date"
                    value={formData.week_start_date}
                    onChange={(e) => setFormData({ ...formData, week_start_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Target Type *</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                    value={formData.target_type}
                    onChange={(e) => setFormData({ ...formData, target_type: e.target.value })}
                    required
                  >
                    <option value="drawing_completion">Drawing Completion</option>
                    <option value="site_visit">Site Visits</option>
                    <option value="revision">Drawing Revisions</option>
                    <option value="client_meeting">Client Meetings</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <Label>Total Quantity *</Label>
                  <Input
                    type="number"
                    min="1"
                    value={formData.target_quantity}
                    onChange={(e) => handleQuantityChange(e.target.value)}
                    placeholder="e.g., 10"
                    required
                  />
                </div>
              </div>

              <div>
                <Label>Target Description *</Label>
                <Input
                  value={formData.target_description}
                  onChange={(e) => setFormData({ ...formData, target_description: e.target.value })}
                  placeholder="e.g., Complete floor plans for Project A"
                  required
                />
              </div>

              <div>
                <Label>Project (Optional)</Label>
                <select
                  className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={formData.project_id}
                  onChange={(e) => setFormData({ ...formData, project_id: e.target.value })}
                >
                  <option value="">Not project-specific</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.code} - {project.title}
                    </option>
                  ))}
                </select>
              </div>

              {/* Daily Breakdown */}
              <div className="border-t pt-4">
                <div className="flex items-center justify-between mb-3">
                  <Label>Daily Breakdown (Mon-Fri)</Label>
                  <span className={`text-sm font-medium ${totalDaily === parseInt(formData.target_quantity) ? 'text-green-600' : 'text-red-600'}`}>
                    Total: {totalDaily} / {formData.target_quantity || 0}
                  </span>
                </div>
                <div className="grid grid-cols-5 gap-2">
                  {weekdays.map((day, index) => (
                    <div key={day}>
                      <Label className="text-xs">{day.slice(0, 3)}</Label>
                      <Input
                        type="number"
                        min="0"
                        value={formData.daily_breakdown[index]}
                        onChange={(e) => handleDailyChange(index, e.target.value)}
                        className="text-center"
                      />
                    </div>
                  ))}
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  Distribute the total quantity across weekdays. Auto-distributed evenly when you enter total quantity.
                </p>
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setDialogOpen(false);
                    resetForm();
                  }}
                >
                  Cancel
                </Button>
                <Button 
                  type="submit" 
                  className="bg-orange-500 hover:bg-orange-600"
                  disabled={totalDaily !== parseInt(formData.target_quantity)}
                >
                  <Target className="w-4 h-4 mr-2" />
                  Assign Target
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
