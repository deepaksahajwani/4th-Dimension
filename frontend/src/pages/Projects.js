import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Plus, FolderOpen, Calendar, Users as UsersIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Projects({ user, onLogout }) {
  const [projects, setProjects] = useState([]);
  const [clients, setClients] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    client_id: '',
    project_type: 'Architecture',
    address: '',
    city: '',
    assigned_to: [],
  });
  const [showClientForm, setShowClientForm] = useState(false);
  const [newClient, setNewClient] = useState({
    name: '',
    contact: '',
    email: '',
    first_call_date: new Date().toISOString().split('T')[0],
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [projectsRes, clientsRes, usersRes] = await Promise.all([
        axios.get(`${API}/projects`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/users`),
      ]);
      setProjects(projectsRes.data);
      setClients(clientsRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/projects`, formData);
      toast.success('Project created successfully!');
      setOpen(false);
      setFormData({ name: '', client_id: '', project_type: 'Architecture', address: '', city: '', assigned_to: [] });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create project');
    }
  };

  const handleCreateClient = async () => {
    try {
      const response = await axios.post(`${API}/clients`, newClient);
      toast.success('Client created successfully!');
      setShowClientForm(false);
      setNewClient({ name: '', contact: '', email: '', first_call_date: new Date().toISOString().split('T')[0] });
      await fetchData();
      setFormData({ ...formData, client_id: response.data.id });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create client');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      consultation: 'bg-gray-100 text-gray-800',
      layout_design: 'bg-blue-100 text-blue-800',
      elevation_design: 'bg-purple-100 text-purple-800',
      structural: 'bg-yellow-100 text-yellow-800',
      execution: 'bg-orange-100 text-orange-800',
      interior: 'bg-pink-100 text-pink-800',
      completed: 'bg-green-100 text-green-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
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
      <div data-testid="projects-page">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Projects</h1>
            <p className="text-slate-600 mt-1">{projects.length} total projects</p>
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button data-testid="create-project-btn">
                <Plus className="w-4 h-4 mr-2" />
                New Project
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl">
              <DialogHeader>
                <DialogTitle>Create New Project</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4" data-testid="project-form">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Project Name</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                      data-testid="project-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="client">Client</Label>
                    <select
                      id="client"
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.client_id}
                      onChange={(e) => setFormData({ ...formData, client_id: e.target.value })}
                      required
                      data-testid="project-client-select"
                    >
                      <option value="">Select client</option>
                      {clients.map((client) => (
                        <option key={client.id} value={client.id}>
                          {client.name}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="type">Project Type</Label>
                    <select
                      id="type"
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.project_type}
                      onChange={(e) => setFormData({ ...formData, project_type: e.target.value })}
                      data-testid="project-type-select"
                    >
                      <option value="architectural">Architectural</option>
                      <option value="interior">Interior</option>
                      <option value="both">Both</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="plot">Plot Dimensions</Label>
                    <Input
                      id="plot"
                      placeholder="e.g., 50x80 ft"
                      value={formData.plot_dimensions}
                      onChange={(e) => setFormData({ ...formData, plot_dimensions: e.target.value })}
                      data-testid="project-plot-input"
                    />
                  </div>
                </div>
                <Button type="submit" className="w-full" data-testid="submit-project-btn">
                  Create Project
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => {
            const client = clients.find((c) => c.id === project.client_id);
            return (
              <Link key={project.id} to={`/projects/${project.id}`}>
                <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                          <FolderOpen className="w-6 h-6 text-blue-600" />
                        </div>
                        <div>
                          <h3 className="font-semibold text-slate-900">{project.name}</h3>
                          <p className="text-sm text-slate-500">{client?.name}</p>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-2">
                      <Badge className={getStatusColor(project.status)}>
                        {project.status.replace('_', ' ')}
                      </Badge>
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Calendar className="w-4 h-4" />
                        {new Date(project.created_at).toLocaleDateString()}
                      </div>
                      {project.assigned_to?.length > 0 && (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <UsersIcon className="w-4 h-4" />
                          {project.assigned_to.length} team members
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>

        {projects.length === 0 && (
          <div className="text-center py-12">
            <FolderOpen className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No projects yet</h3>
            <p className="text-slate-500 mb-4">Create your first project to get started</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
