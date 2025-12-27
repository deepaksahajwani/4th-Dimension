import { useState, useEffect } from 'react';
import { 
  Book, FileText, Video, Download, ExternalLink, Search,
  FolderOpen, Bookmark, CheckCircle, Clock, Star,
  FileImage, File, FileSpreadsheet, Presentation, Plus, Trash2, Edit, Upload, PenTool, Eye
} from 'lucide-react';
import { Card, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const CATEGORIES = {
  onboarding: { label: 'Onboarding', icon: CheckCircle, color: 'bg-green-100 text-green-700' },
  standards: { label: 'Company Standards', icon: Book, color: 'bg-blue-100 text-blue-700' },
  templates: { label: 'Templates', icon: FileText, color: 'bg-purple-100 text-purple-700' },
  tutorials: { label: 'Tutorials', icon: Video, color: 'bg-orange-100 text-orange-700' },
  policies: { label: 'Policies', icon: FolderOpen, color: 'bg-red-100 text-red-700' },
  tools: { label: 'Tools & Software', icon: ExternalLink, color: 'bg-cyan-100 text-cyan-700' }
};

const RESOURCE_TYPES = [
  { value: 'pdf', label: 'PDF Document' },
  { value: 'document', label: 'Word Document' },
  { value: 'spreadsheet', label: 'Spreadsheet' },
  { value: 'presentation', label: 'Presentation' },
  { value: 'cad', label: 'CAD File (DWG/DXF)' },
  { value: 'video', label: 'Video' },
  { value: 'image', label: 'Image' },
  { value: 'link', label: 'External Link' }
];

const getFileIcon = (type) => {
  switch(type) {
    case 'pdf': return File;
    case 'image': return FileImage;
    case 'spreadsheet': return FileSpreadsheet;
    case 'presentation': return Presentation;
    case 'video': return Video;
    case 'cad': return PenTool;
    default: return FileText;
  }
};

export default function Resources({ user }) {
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [bookmarked, setBookmarked] = useState([]);
  const [showAddDialog, setShowAddDialog] = useState(false);
  const [editingResource, setEditingResource] = useState(null);
  const [uploadingFile, setUploadingFile] = useState(null);
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'onboarding',
    type: 'pdf',
    external_link: '',
    featured: false
  });

  useEffect(() => {
    fetchResources();
  }, []);

  const fetchResources = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/resources`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setResources(response.data);
    } catch (error) {
      console.error('Error fetching resources:', error);
      if (error.response?.status === 404) {
        setResources([]);
      } else {
        toast.error('Failed to load resources');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSeedDefaults = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/resources/seed-defaults`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (response.data.success) {
        toast.success(response.data.message);
        fetchResources();
      } else {
        toast.error(response.data.message);
      }
    } catch (error) {
      toast.error('Failed to seed default resources');
    }
  };

  const handleCreateResource = async () => {
    try {
      if (!formData.title) {
        toast.error('Title is required');
        return;
      }
      
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API_URL}/api/resources`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Resource created successfully');
      setShowAddDialog(false);
      resetForm();
      fetchResources();
      
      if (uploadingFile) {
        await handleFileUpload(response.data.id, uploadingFile);
      }
    } catch (error) {
      toast.error('Failed to create resource');
    }
  };

  const handleUpdateResource = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API_URL}/api/resources/${editingResource.id}`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Resource updated successfully');
      setEditingResource(null);
      resetForm();
      fetchResources();
    } catch (error) {
      toast.error('Failed to update resource');
    }
  };

  const handleDeleteResource = async (resourceId) => {
    if (!window.confirm('Are you sure you want to delete this resource?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/resources/${resourceId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Resource deleted successfully');
      fetchResources();
    } catch (error) {
      toast.error('Failed to delete resource');
    }
  };

  const handleFileUpload = async (resourceId, file) => {
    try {
      const token = localStorage.getItem('token');
      const uploadData = new FormData();
      uploadData.append('file', file);
      
      await axios.post(`${API_URL}/api/resources/${resourceId}/upload`, uploadData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data' 
        }
      });
      
      toast.success('File uploaded successfully');
      fetchResources();
    } catch (error) {
      toast.error('Failed to upload file');
    }
  };

  const handleDownload = async (resource) => {
    if (resource.external_link) {
      window.open(resource.external_link, '_blank');
      return;
    }
    
    if (resource.url) {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`${API_URL}${resource.url}`, { 
          responseType: 'blob',
          headers: { Authorization: `Bearer ${token}` }
        });
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', resource.file_name || 'download');
        document.body.appendChild(link);
        link.click();
        link.remove();
      } catch (error) {
        toast.error('Failed to download file');
      }
    } else {
      toast.info('No file attached to this resource yet');
    }
  };

  const resetForm = () => {
    setFormData({
      title: '',
      description: '',
      category: 'onboarding',
      type: 'pdf',
      external_link: '',
      featured: false
    });
    setUploadingFile(null);
  };

  const openEditDialog = (resource) => {
    setEditingResource(resource);
    setFormData({
      title: resource.title,
      description: resource.description || '',
      category: resource.category,
      type: resource.type,
      external_link: resource.external_link || '',
      featured: resource.featured
    });
  };

  const filteredResources = resources.filter(resource => {
    const matchesSearch = resource.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         (resource.description || '').toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || resource.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const featuredResources = resources.filter(r => r.featured);
  const isOwner = user?.is_owner;

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 p-6 flex items-center justify-center">
        <div className="text-slate-500">Loading resources...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 p-4 md:p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900 mb-2">📚 Resources</h1>
            <p className="text-slate-600">Access company documents, templates, tutorials, and more</p>
          </div>
          
          {isOwner && (
            <div className="flex gap-2">
              {resources.length === 0 && (
                <Button onClick={handleSeedDefaults} variant="outline">
                  <Plus className="w-4 h-4 mr-2" />
                  Load Defaults
                </Button>
              )}
              <Button onClick={() => setShowAddDialog(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Add Resource
              </Button>
            </div>
          )}
        </div>

        {/* Search */}
        <div className="mb-6">
          <div className="relative max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-5 h-5" />
            <Input
              placeholder="Search resources..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>

        {/* Empty State */}
        {resources.length === 0 && (
          <Card className="p-12 text-center">
            <FolderOpen className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-slate-700 mb-2">No Resources Yet</h3>
            <p className="text-slate-500 mb-4">Get started by loading default resources or adding your own.</p>
            {isOwner && (
              <Button onClick={handleSeedDefaults}>
                <Plus className="w-4 h-4 mr-2" />
                Load Default Resources
              </Button>
            )}
          </Card>
        )}

        {/* Featured Resources */}
        {resources.length > 0 && selectedCategory === 'all' && !searchQuery && featuredResources.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-slate-800 mb-4 flex items-center gap-2">
              <Star className="w-5 h-5 text-yellow-500" />
              Getting Started
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {featuredResources.slice(0, 4).map(resource => {
                const CategoryIcon = CATEGORIES[resource.category]?.icon || FileText;
                const FileIcon = getFileIcon(resource.type);
                return (
                  <Card key={resource.id} className="hover:shadow-md transition-shadow border-l-4 border-l-indigo-500">
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className={`p-2 rounded-lg ${CATEGORIES[resource.category]?.color}`}>
                          <CategoryIcon className="w-5 h-5" />
                        </div>
                        <FileIcon className="w-4 h-4 text-slate-400" />
                      </div>
                      <h3 className="font-semibold text-slate-800 mb-1 line-clamp-1">{resource.title}</h3>
                      <p className="text-sm text-slate-500 line-clamp-2 mb-3">{resource.description}</p>
                      <Button variant="outline" size="sm" className="w-full" onClick={() => handleDownload(resource)}>
                        <Download className="w-4 h-4 mr-2" />
                        {resource.url || resource.external_link ? 'Download' : 'View'}
                      </Button>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Category Tabs */}
        {resources.length > 0 && (
          <Tabs defaultValue="all" className="w-full" onValueChange={setSelectedCategory}>
            <TabsList className="flex flex-wrap h-auto gap-2 bg-transparent p-0 mb-6">
              <TabsTrigger value="all" className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
                All Resources
              </TabsTrigger>
              {Object.entries(CATEGORIES).map(([key, { label, icon: Icon }]) => (
                <TabsTrigger key={key} value={key} className="data-[state=active]:bg-indigo-600 data-[state=active]:text-white">
                  <Icon className="w-4 h-4 mr-1" />
                  {label}
                </TabsTrigger>
              ))}
            </TabsList>

            <TabsContent value={selectedCategory} className="mt-0">
              {filteredResources.length === 0 ? (
                <Card className="p-8 text-center">
                  <FolderOpen className="w-12 h-12 text-slate-300 mx-auto mb-4" />
                  <p className="text-slate-500">No resources found</p>
                </Card>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {filteredResources.map(resource => {
                    const CategoryIcon = CATEGORIES[resource.category]?.icon || FileText;
                    const FileIcon = getFileIcon(resource.type);
                    
                    return (
                      <Card key={resource.id} className="hover:shadow-md transition-shadow">
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between mb-3">
                            <Badge className={CATEGORIES[resource.category]?.color}>
                              {CATEGORIES[resource.category]?.label}
                            </Badge>
                            <div className="flex items-center gap-1">
                              {isOwner && (
                                <>
                                  <button onClick={() => openEditDialog(resource)} className="p-1 rounded hover:bg-slate-100 text-slate-400">
                                    <Edit className="w-4 h-4" />
                                  </button>
                                  <button onClick={() => handleDeleteResource(resource.id)} className="p-1 rounded hover:bg-slate-100 text-red-400">
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </>
                              )}
                              <FileIcon className="w-4 h-4 text-slate-400" />
                            </div>
                          </div>
                          
                          <h3 className="font-semibold text-slate-800 mb-2">{resource.title}</h3>
                          <p className="text-sm text-slate-500 mb-4 line-clamp-2">{resource.description}</p>
                          
                          <div className="flex items-center justify-between">
                            <span className="text-xs text-slate-400 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {resource.download_count || 0} downloads
                            </span>
                            <Button variant="outline" size="sm" onClick={() => handleDownload(resource)}>
                              <Download className="w-4 h-4 mr-1" />
                              {resource.url || resource.external_link ? 'Download' : 'View'}
                            </Button>
                          </div>
                        </CardContent>
                      </Card>
                    );
                  })}
                </div>
              )}
            </TabsContent>
          </Tabs>
        )}
      </div>

      {/* Add/Edit Resource Dialog */}
      <Dialog open={showAddDialog || !!editingResource} onOpenChange={(open) => {
        if (!open) {
          setShowAddDialog(false);
          setEditingResource(null);
          resetForm();
        }
      }}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>{editingResource ? 'Edit Resource' : 'Add New Resource'}</DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label>Title *</Label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                placeholder="Resource title"
              />
            </div>
            
            <div>
              <Label>Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Brief description"
                rows={2}
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Category</Label>
                <Select value={formData.category} onValueChange={(v) => setFormData({...formData, category: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {Object.entries(CATEGORIES).map(([key, { label }]) => (
                      <SelectItem key={key} value={key}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <Label>Type</Label>
                <Select value={formData.type} onValueChange={(v) => setFormData({...formData, type: v})}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {RESOURCE_TYPES.map(({ value, label }) => (
                      <SelectItem key={value} value={value}>{label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            
            {formData.type === 'link' && (
              <div>
                <Label>External Link</Label>
                <Input
                  value={formData.external_link}
                  onChange={(e) => setFormData({...formData, external_link: e.target.value})}
                  placeholder="https://..."
                />
              </div>
            )}
            
            {!editingResource && formData.type !== 'link' && (
              <div>
                <Label>Upload File</Label>
                <Input
                  type="file"
                  onChange={(e) => setUploadingFile(e.target.files[0])}
                  className="cursor-pointer"
                />
                <p className="text-xs text-slate-500 mt-1">You can also upload a file after creating the resource</p>
              </div>
            )}
            
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="featured"
                checked={formData.featured}
                onChange={(e) => setFormData({...formData, featured: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="featured" className="cursor-pointer">Featured (show in Getting Started)</Label>
            </div>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowAddDialog(false);
              setEditingResource(null);
              resetForm();
            }}>
              Cancel
            </Button>
            <Button onClick={editingResource ? handleUpdateResource : handleCreateResource}>
              {editingResource ? 'Save Changes' : 'Create Resource'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
