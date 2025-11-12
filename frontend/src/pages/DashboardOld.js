import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FolderOpen, Users, AlertCircle, CheckSquare, TrendingUp } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Badge } from '@/components/ui/badge';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Dashboard({ user, onLogout }) {
  const [stats, setStats] = useState(null);
  const [reminders, setReminders] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, remindersRes] = await Promise.all([
        axios.get(`${API}/dashboard/stats`),
        axios.get(`${API}/reminders/pending`),
      ]);
      setStats(statsRes.data);
      setReminders(remindersRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div data-testid="dashboard-page">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-600 mt-1">Welcome back, {user?.name}</p>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Total Projects</CardTitle>
              <FolderOpen className="w-5 h-5 text-blue-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{stats?.total_projects || 0}</div>
              <p className="text-xs text-slate-500 mt-1">{stats?.active_projects || 0} active</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Clients</CardTitle>
              <Users className="w-5 h-5 text-green-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{stats?.total_clients || 0}</div>
              <p className="text-xs text-slate-500 mt-1">Total registered</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Pending Tasks</CardTitle>
              <CheckSquare className="w-5 h-5 text-amber-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{stats?.pending_tasks || 0}</div>
              <p className="text-xs text-slate-500 mt-1">Requires attention</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-slate-600">Red Flags</CardTitle>
              <AlertCircle className="w-5 h-5 text-red-600" />
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-slate-900">{stats?.red_flags || 0}</div>
              <p className="text-xs text-slate-500 mt-1">Critical issues</p>
            </CardContent>
          </Card>
        </div>

        {/* Reminders */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Pending Reminders</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between p-3 bg-amber-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-slate-900">Overdue Tasks</p>
                    <p className="text-xs text-slate-500">Tasks past their due date</p>
                  </div>
                  <Badge variant="destructive">{reminders?.overdue_tasks || 0}</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-blue-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-slate-900">Pending Drawings</p>
                    <p className="text-xs text-slate-500">Drawings awaiting issuance</p>
                  </div>
                  <Badge>{reminders?.pending_drawings || 0}</Badge>
                </div>
                <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                  <div>
                    <p className="text-sm font-medium text-slate-900">Projects Need Attention</p>
                    <p className="text-xs text-slate-500">Plans pending finalization</p>
                  </div>
                  <Badge variant="outline">{reminders?.projects_needing_attention || 0}</Badge>
                </div>
              </div>
              <Link to="/tasks" className="block mt-4">
                <button className="w-full text-sm text-blue-600 hover:text-blue-700 font-medium">View All Tasks →</button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Link to="/projects">
                  <button className="w-full flex items-center gap-3 p-3 bg-blue-50 hover:bg-blue-100 rounded-lg transition-colors text-left">
                    <FolderOpen className="w-5 h-5 text-blue-600" />
                    <div>
                      <p className="text-sm font-medium text-slate-900">Create New Project</p>
                      <p className="text-xs text-slate-500">Start a new project</p>
                    </div>
                  </button>
                </Link>
                <Link to="/clients">
                  <button className="w-full flex items-center gap-3 p-3 bg-green-50 hover:bg-green-100 rounded-lg transition-colors text-left">
                    <Users className="w-5 h-5 text-green-600" />
                    <div>
                      <p className="text-sm font-medium text-slate-900">Add New Client</p>
                      <p className="text-xs text-slate-500">Register a new client</p>
                    </div>
                  </button>
                </Link>
                <Link to="/tasks">
                  <button className="w-full flex items-center gap-3 p-3 bg-amber-50 hover:bg-amber-100 rounded-lg transition-colors text-left">
                    <CheckSquare className="w-5 h-5 text-amber-600" />
                    <div>
                      <p className="text-sm font-medium text-slate-900">Create Task</p>
                      <p className="text-xs text-slate-500">Add a new task or issue</p>
                    </div>
                  </button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </Layout>
  );
}
