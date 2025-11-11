import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { 
  ArrowLeft, Plus, CheckCircle2, Circle, AlertCircle, 
  Calendar, Edit, Trash2, FileText
} from 'lucide-react';
import { toast } from 'sonner';
import { formatErrorMessage } from '@/utils/errorHandler';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DRAWING_CATEGORIES = ['Architecture', 'Interior', 'Landscape', 'Planning'];

export default function ProjectDetail({ user, onLogout }) {
  const { projectId } = useParams();
  const navigate = useNavigate();
  
  const [project, setProject] = useState(null);
  const [client, setClient] = useState(null);
  const [drawings, setDrawings] = useState([]);
  const [brandCategories, setBrandCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('drawings');
  
  // Drawing dialog states
  const [drawingDialogOpen, setDrawingDialogOpen] = useState(false);
  const [revisionDialogOpen, setRevisionDialogOpen] = useState(false);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [selectedDrawing, setSelectedDrawing] = useState(null);
  const [editingDrawing, setEditingDrawing] = useState(null);
  const [drawingFormData, setDrawingFormData] = useState({
    category: 'Architecture',
    name: '',
    due_date: '',
    notes: ''
  });
  const [revisionFormData, setRevisionFormData] = useState({
    revision_notes: '',
    revision_due_date: ''
  });

  useEffect(() => {
    fetchProjectData();
  }, [projectId]);

  const fetchProjectData = async () => {
    try {
      const [projectRes, drawingsRes, brandCategoriesRes] = await Promise.all([
        axios.get(`${API}/projects/${projectId}`),
        axios.get(`${API}/projects/${projectId}/drawings`),
        axios.get(`${API}/brand-categories`)
      ]);
      
      setProject(projectRes.data);
      setDrawings(drawingsRes.data);
      setBrandCategories(brandCategoriesRes.data);
      
      // Fetch client if client_id exists
      if (projectRes.data.client_id) {
        const clientRes = await axios.get(`${API}/clients/${projectRes.data.client_id}`);
        setClient(clientRes.data);
      }
    } catch (error) {
      toast.error('Failed to load project data');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddDrawing = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/projects/${projectId}/drawings`, {
        ...drawingFormData,
        project_id: projectId
      });
      toast.success('Drawing added successfully!');
      setDrawingDialogOpen(false);
      resetDrawingForm();
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to add drawing'));
    }
  };

  const handleToggleIssued = async (drawing) => {
    try {
      await axios.put(`${API}/drawings/${drawing.id}`, {
        is_issued: !drawing.is_issued
      });
      toast.success(drawing.is_issued ? 'Drawing marked as pending' : 'Drawing marked as issued!');
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to update drawing'));
    }
  };

  const handleOpenRevisionDialog = (drawing) => {
    setSelectedDrawing(drawing);
    setRevisionFormData({
      revision_notes: '',
      revision_due_date: ''
    });
    setRevisionDialogOpen(true);
  };

  const handleRequestRevision = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/drawings/${selectedDrawing.id}`, {
        has_pending_revision: true,
        revision_notes: revisionFormData.revision_notes,
        revision_due_date: revisionFormData.revision_due_date
      });
      toast.success('Revision requested successfully!');
      setRevisionDialogOpen(false);
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to request revision'));
    }
  };

  const handleResolveRevision = async (drawing) => {
    if (!window.confirm('Mark this revision as resolved?')) return;
    
    try {
      await axios.put(`${API}/drawings/${drawing.id}`, {
        has_pending_revision: false
      });
      toast.success('Revision resolved!');
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to resolve revision'));
    }
  };

  const handleShowHistory = (drawing) => {
    setSelectedDrawing(drawing);
    setHistoryDialogOpen(true);
  };

  const handleDeleteDrawing = async (drawingId) => {
    if (!window.confirm('Are you sure you want to delete this drawing?')) return;
    
    try {
      await axios.delete(`${API}/drawings/${drawingId}`);
      toast.success('Drawing deleted successfully');
      fetchProjectData();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to delete drawing'));
    }
  };

  const resetDrawingForm = () => {
    setDrawingFormData({
      category: 'Architecture',
      name: '',
      due_date: '',
      notes: ''
    });
    setEditingDrawing(null);
  };

  const getDrawingsByCategory = (category) => {
    return drawings.filter(d => d.category === category);
  };

  const getDrawingStatusIcon = (drawing) => {
    if (drawing.has_pending_revision) {
      return <AlertCircle className="w-5 h-5 text-amber-500" />;
    }
    if (drawing.is_issued) {
      return <CheckCircle2 className="w-5 h-5 text-green-500" />;
    }
    return <Circle className="w-5 h-5 text-slate-300" />;
  };

  const getDrawingStatusText = (drawing) => {
    if (drawing.has_pending_revision) return 'Revision Needed';
    if (drawing.is_issued) return 'Issued';
    return 'Pending';
  };

  const getDrawingStatusColor = (drawing) => {
    if (drawing.has_pending_revision) return 'bg-amber-50 text-amber-700 border-amber-200';
    if (drawing.is_issued) return 'bg-green-50 text-green-700 border-green-200';
    return 'bg-slate-50 text-slate-600 border-slate-200';
  };

  const DrawingCard = ({ drawing }) => (
    <Card className="hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3 flex-1">
            {getDrawingStatusIcon(drawing)}
            <div className="flex-1">
              <h4 className="font-medium text-slate-900">{drawing.name}</h4>
              <div className="flex flex-wrap gap-2 mt-2">
                <span className={`px-2 py-1 text-xs rounded border ${getDrawingStatusColor(drawing)}`}>
                  {getDrawingStatusText(drawing)}
                </span>
                {drawing.revision_count > 0 && (
                  <span className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded border border-blue-200">
                    R{drawing.revision_count}
                  </span>
                )}
                {drawing.due_date && (
                  <span className="px-2 py-1 text-xs bg-slate-100 text-slate-600 rounded border border-slate-200 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {new Date(drawing.due_date).toLocaleDateString()}
                  </span>
                )}
              </div>
              {drawing.notes && (
                <p className="text-sm text-slate-600 mt-2">{drawing.notes}</p>
              )}
            </div>
          </div>
          
          <div className="flex gap-2 ml-4">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleToggleIssued(drawing)}
              title={drawing.is_issued ? "Mark as Pending" : "Mark as Issued"}
            >
              {drawing.is_issued ? "Unissue" : "Issue"}
            </Button>
            {(drawing.is_issued || drawing.has_pending_revision) && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => drawing.has_pending_revision ? handleResolveRevision(drawing) : handleOpenRevisionDialog(drawing)}
                className={drawing.has_pending_revision ? "border-green-500 text-green-600" : "border-amber-500 text-amber-600"}
                title={drawing.has_pending_revision ? "Mark Revision Complete" : "Request Revision"}
              >
                {drawing.has_pending_revision ? "Resolve" : "Revise"}
              </Button>
            )}
            {drawing.revision_history && drawing.revision_history.length > 0 && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleShowHistory(drawing)}
                title="View Revision History"
              >
                History
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDeleteDrawing(drawing.id)}
              className="text-red-600 hover:text-red-700"
            >
              <Trash2 className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
        </div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="text-center py-12">
          <p className="text-slate-500">Project not found</p>
          <Button onClick={() => navigate('/projects')} className="mt-4">
            Back to Projects
          </Button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <Button
          variant="ghost"
          onClick={() => navigate('/projects')}
          className="mb-6"
        >
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Projects
        </Button>

        {/* Project Info Card */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-3 mb-2">
                  <span className="px-3 py-1 bg-orange-100 text-orange-700 font-mono text-sm font-medium rounded">
                    {project.code}
                  </span>
                  {project.archived && (
                    <span className="px-3 py-1 bg-amber-100 text-amber-700 text-sm rounded">
                      Archived
                    </span>
                  )}
                </div>
                <h1 className="text-3xl font-bold text-slate-900 mb-2">{project.title}</h1>
                {client && (
                  <p className="text-lg text-slate-600">{client.name}</p>
                )}
                
                {/* Project Types */}
                {project.project_types && project.project_types.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {project.project_types.map((type) => (
                      <span 
                        key={type} 
                        className="px-2 py-1 text-sm bg-orange-50 text-orange-700 rounded border border-orange-200"
                      >
                        {type}
                      </span>
                    ))}
                  </div>
                )}

                {/* Dates */}
                <div className="flex gap-6 mt-4 text-sm text-slate-600">
                  {project.start_date && (
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      <span>Started: {new Date(project.start_date).toLocaleDateString()}</span>
                    </div>
                  )}
                  {project.end_date && (
                    <div className="flex items-center gap-2">
                      <Calendar className="w-4 h-4" />
                      <span>Ended: {new Date(project.end_date).toLocaleDateString()}</span>
                    </div>
                  )}
                </div>
              </div>

              <Button
                variant="outline"
                onClick={() => navigate(`/projects/${projectId}/edit`)}
              >
                <Edit className="w-4 h-4 mr-2" />
                Edit Project
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid grid-cols-3 w-full max-w-md">
            <TabsTrigger value="drawings">Drawings</TabsTrigger>
            <TabsTrigger value="info">Project Info</TabsTrigger>
            <TabsTrigger value="brands">Brands</TabsTrigger>
          </TabsList>

          {/* Drawings Tab */}
          <TabsContent value="drawings" className="mt-6">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">Project Drawings</h2>
                <p className="text-slate-600">
                  {drawings.length} total drawings • {drawings.filter(d => d.is_issued).length} issued • {drawings.filter(d => d.has_pending_revision).length} revisions pending
                </p>
              </div>
              <Button 
                onClick={() => setDrawingDialogOpen(true)}
                className="bg-orange-500 hover:bg-orange-600"
              >
                <Plus className="w-4 h-4 mr-2" />
                Add Drawing
              </Button>
            </div>

            {/* Drawings by Category */}
            {DRAWING_CATEGORIES.filter(cat => project.project_types?.includes(cat)).map((category) => {
              const categoryDrawings = getDrawingsByCategory(category);
              
              return (
                <div key={category} className="mb-8">
                  <div className="flex items-center gap-3 mb-4">
                    <FileText className="w-5 h-5 text-orange-500" />
                    <h3 className="text-xl font-semibold text-slate-900">{category}</h3>
                    <span className="text-sm text-slate-500">({categoryDrawings.length})</span>
                  </div>
                  
                  {categoryDrawings.length > 0 ? (
                    <div className="space-y-3">
                      {categoryDrawings.map((drawing) => (
                        <DrawingCard key={drawing.id} drawing={drawing} />
                      ))}
                    </div>
                  ) : (
                    <Card>
                      <CardContent className="p-8 text-center">
                        <p className="text-slate-500">No {category.toLowerCase()} drawings yet</p>
                        <Button
                          variant="outline"
                          onClick={() => {
                            setDrawingFormData({ ...drawingFormData, category });
                            setDrawingDialogOpen(true);
                          }}
                          className="mt-3"
                        >
                          <Plus className="w-4 h-4 mr-2" />
                          Add {category} Drawing
                        </Button>
                      </CardContent>
                    </Card>
                  )}
                </div>
              );
            })}
          </TabsContent>

          {/* Project Info Tab */}
          <TabsContent value="info" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Project Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {project.site_address && (
                  <div>
                    <Label className="text-slate-600">Site Address</Label>
                    <p className="text-slate-900">{project.site_address}</p>
                  </div>
                )}
                {project.notes && (
                  <div>
                    <Label className="text-slate-600">Notes</Label>
                    <p className="text-slate-900">{project.notes}</p>
                  </div>
                )}
                <div>
                  <Label className="text-slate-600">Status</Label>
                  <p className="text-slate-900">{project.status?.replace(/_/g, ' ')}</p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Brands Tab */}
          <TabsContent value="brands" className="mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Brands Used in Project</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-slate-600">Brand management will be available soon</p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        {/* Add Drawing Dialog */}
        <Dialog open={drawingDialogOpen} onOpenChange={setDrawingDialogOpen}>
          <DialogContent className="max-w-2xl">
            <DialogHeader>
              <DialogTitle>Add New Drawing</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleAddDrawing} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Category *</Label>
                  <select
                    className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                    value={drawingFormData.category}
                    onChange={(e) => setDrawingFormData({ ...drawingFormData, category: e.target.value })}
                    required
                  >
                    {DRAWING_CATEGORIES.filter(cat => project.project_types?.includes(cat)).map((cat) => (
                      <option key={cat} value={cat}>{cat}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <Label>Due Date</Label>
                  <Input
                    type="date"
                    value={drawingFormData.due_date}
                    onChange={(e) => setDrawingFormData({ ...drawingFormData, due_date: e.target.value })}
                  />
                </div>
              </div>
              
              <div>
                <Label>Drawing Name *</Label>
                <Input
                  value={drawingFormData.name}
                  onChange={(e) => setDrawingFormData({ ...drawingFormData, name: e.target.value })}
                  placeholder="e.g., Ground Floor Plan, Elevation - North"
                  required
                />
              </div>

              <div>
                <Label>Notes</Label>
                <textarea
                  className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                  value={drawingFormData.notes}
                  onChange={(e) => setDrawingFormData({ ...drawingFormData, notes: e.target.value })}
                  placeholder="Additional notes or specifications"
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setDrawingDialogOpen(false);
                    resetDrawingForm();
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" className="bg-orange-500 hover:bg-orange-600">
                  Add Drawing
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
