import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { FolderOpen, Calendar, User, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ROLE_LABELS = {
  client: 'Client',
  contractor: 'Contractor',
  consultant: 'Consultant',
  vendor: 'Vendor'
};

export default function ExternalDashboard({ user, onLogout }) {
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
      
      // Fetch drawing stats for each project to calculate % completed
      const projectsWithStats = await Promise.all(
        response.data.map(async (project) => {
          try {
            const drawingsRes = await axios.get(`${API}/projects/${project.id}/drawings`, {
              headers: { Authorization: `Bearer ${token}` }
            });
            const drawings = drawingsRes.data || [];
            const totalDrawings = drawings.length;
            const issuedDrawings = drawings.filter(d => d.is_issued).length;
            const percentComplete = totalDrawings > 0 
              ? Math.round((issuedDrawings / totalDrawings) * 100) 
              : 0;
            
            return {
              ...project,
              totalDrawings,
              issuedDrawings,
              percentComplete
            };
          } catch (err) {
            return { ...project, totalDrawings: 0, issuedDrawings: 0, percentComplete: 0 };
          }
        })
      );
      
      setProjects(projectsWithStats);
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
        {/* Welcome Header - Mobile friendly */}
        <div className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
            Welcome, {user?.name?.split(' ')[0]}
          </h1>
          <p className="text-slate-600 mt-1 text-sm sm:text-base">
            {ROLE_LABELS[user?.role] || 'User'} Portal • {projects.length} {projects.length === 1 ? 'Project' : 'Projects'}
          </p>
        </div>

        {/* Projects List */}
        {projects.length === 0 ? (
          <div className="text-center py-12 px-4">
            <div className="bg-gradient-to-br from-orange-50 to-amber-50 rounded-2xl p-8 border border-orange-100 max-w-md mx-auto">
              <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <FolderOpen className="w-8 h-8 text-orange-600" />
              </div>
              
              <h3 className="text-xl font-bold text-slate-900 mb-3">
                Welcome to 4th Dimension! 🎉
              </h3>
              
              <p className="text-slate-600 mb-4 text-sm leading-relaxed">
                Your account is active. Our team will notify you once your project is ready for review.
              </p>
              
              <div className="bg-white rounded-lg p-4 text-left text-sm">
                <p className="font-medium text-slate-900 mb-2">Need help?</p>
                <p className="text-slate-600">📧 contact@4thdimensionarchitect.com</p>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {projects.map((project) => (
              <Card 
                key={project.id} 
                className="hover:shadow-md transition-all cursor-pointer border-l-4 border-l-orange-500 active:scale-[0.99]"
                onClick={() => navigate(`/project/${project.id}`)}
              >
                <CardContent className="p-4 sm:p-6">
                  {/* Project Header */}
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-lg font-semibold text-slate-900 truncate">
                        {project.title || project.name}
                      </h3>
                      <p className="text-sm text-slate-500 font-mono">
                        {project.project_code || 'No Code'}
                      </p>
                    </div>
                    <Badge className="bg-orange-100 text-orange-700 border-orange-200 ml-2 shrink-0">
                      {project.percentComplete}% Complete
                    </Badge>
                  </div>

                  {/* Progress Bar */}
                  <div className="mb-4">
                    <Progress 
                      value={project.percentComplete} 
                      className="h-2 bg-slate-100"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      {project.issuedDrawings} of {project.totalDrawings} drawings issued
                    </p>
                  </div>

                  {/* Project Details - Grid for mobile */}
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Calendar className="w-4 h-4 text-slate-400 shrink-0" />
                      <span className="truncate">{formatDate(project.start_date)}</span>
                    </div>
                    
                    {project.team_leader_name && (
                      <div className="flex items-center gap-2 text-slate-600">
                        <User className="w-4 h-4 text-slate-400 shrink-0" />
                        <span className="truncate">{project.team_leader_name}</span>
                      </div>
                    )}
                  </div>

                  {/* Tap to view indicator */}
                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-between">
                    <span className="text-xs text-slate-400">Tap to view project</span>
                    <TrendingUp className="w-4 h-4 text-orange-500" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </Layout>
  );
}
