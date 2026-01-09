import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { 
  Layers, Plus, Edit, Trash2, GripVertical, ArrowUp, ArrowDown, Save, X, 
  FileText, Building, Palette, Leaf, Zap, Wrench, Check, RefreshCw, Search
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

// Project categories with icons
const PROJECT_CATEGORIES = [
  { id: 'Architecture', label: 'Architecture', icon: Building, color: 'bg-blue-500' },
  { id: 'Interior', label: 'Interior', icon: Palette, color: 'bg-purple-500' },
  { id: 'Landscape', label: 'Landscape', icon: Leaf, color: 'bg-green-500' },
  { id: 'MEP', label: 'MEP', icon: Zap, color: 'bg-yellow-500' },
  { id: 'Structure', label: 'Structure', icon: Wrench, color: 'bg-orange-500' },
];

export default function DrawingTemplates({ user, onLogout }) {
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState('Architecture');
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // Dialog states
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [newDrawingName, setNewDrawingName] = useState('');
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [editDrawingName, setEditDrawingName] = useState('');
  const [templateToDelete, setTemplateToDelete] = useState(null);

  useEffect(() => {
    if (!user) return;
    
    if (!user.is_owner && user.role !== 'owner') {
      toast.error('Access denied');
      navigate('/dashboard');
      return;
    }
    fetchTemplates();
  }, [user, navigate]);

  const fetchTemplates = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/drawing-templates`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTemplates(response.data || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSeedTemplates = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/drawing-templates/seed`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Seeded ${response.data.seeded_count} drawing templates!`);
      fetchTemplates();
    } catch (error) {
      console.error('Error seeding templates:', error);
      toast.error('Failed to seed templates');
    } finally {
      setSaving(false);
    }
  };

  const handleAddDrawing = async () => {
    if (!newDrawingName.trim()) {
      toast.error('Please enter a drawing name');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(`${API}/drawing-templates`, {
        name: newDrawingName.trim(),
        category: activeCategory
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Drawing template added!');
      setNewDrawingName('');
      setAddDialogOpen(false);
      fetchTemplates();
    } catch (error) {
      console.error('Error adding template:', error);
      toast.error('Failed to add drawing template');
    } finally {
      setSaving(false);
    }
  };

  const handleEditDrawing = async () => {
    if (!editDrawingName.trim()) {
      toast.error('Please enter a drawing name');
      return;
    }

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.put(`${API}/drawing-templates/${editingTemplate.id}`, {
        name: editDrawingName.trim()
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.updated_drawings > 0) {
        toast.success(`Template renamed! Updated ${response.data.updated_drawings} project drawings.`);
      } else {
        toast.success('Template renamed!');
      }
      
      setEditDrawingName('');
      setEditingTemplate(null);
      setEditDialogOpen(false);
      fetchTemplates();
    } catch (error) {
      console.error('Error updating template:', error);
      toast.error('Failed to update drawing template');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteDrawing = async () => {
    if (!templateToDelete) return;

    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/drawing-templates/${templateToDelete.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Drawing template deleted!');
      setTemplateToDelete(null);
      setDeleteDialogOpen(false);
      fetchTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      toast.error('Failed to delete drawing template');
    } finally {
      setSaving(false);
    }
  };

  const handleMoveUp = async (template, index) => {
    const categoryTemplates = getFilteredTemplates();
    if (index === 0) return;
    
    const prevTemplate = categoryTemplates[index - 1];
    
    // Swap orders
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await Promise.all([
        axios.put(`${API}/drawing-templates/${template.id}`, { order: prevTemplate.order }, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.put(`${API}/drawing-templates/${prevTemplate.id}`, { order: template.order }, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      fetchTemplates();
    } catch (error) {
      console.error('Error reordering:', error);
      toast.error('Failed to reorder');
    } finally {
      setSaving(false);
    }
  };

  const handleMoveDown = async (template, index) => {
    const categoryTemplates = getFilteredTemplates();
    if (index === categoryTemplates.length - 1) return;
    
    const nextTemplate = categoryTemplates[index + 1];
    
    // Swap orders
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await Promise.all([
        axios.put(`${API}/drawing-templates/${template.id}`, { order: nextTemplate.order }, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.put(`${API}/drawing-templates/${nextTemplate.id}`, { order: template.order }, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      fetchTemplates();
    } catch (error) {
      console.error('Error reordering:', error);
      toast.error('Failed to reorder');
    } finally {
      setSaving(false);
    }
  };

  const openEditDialog = (template) => {
    setEditingTemplate(template);
    setEditDrawingName(template.name);
    setEditDialogOpen(true);
  };

  const openDeleteDialog = (template) => {
    setTemplateToDelete(template);
    setDeleteDialogOpen(true);
  };

  // Get templates for the active category, filtered by search
  const getFilteredTemplates = () => {
    return templates
      .filter(t => t.category === activeCategory)
      .filter(t => !searchQuery || t.name.toLowerCase().includes(searchQuery.toLowerCase()))
      .sort((a, b) => a.order - b.order);
  };

  // Get count per category
  const getCategoryCount = (categoryId) => {
    return templates.filter(t => t.category === categoryId).length;
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-600"></div>
        </div>
      </Layout>
    );
  }

  const filteredTemplates = getFilteredTemplates();

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
              <Layers className="w-6 h-6 text-orange-600" />
              Drawing Templates
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Manage master drawing lists for different project types. Renaming a template updates all projects.
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={handleSeedTemplates}
              variant="outline"
              disabled={saving}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`w-4 h-4 ${saving ? 'animate-spin' : ''}`} />
              Seed Default Templates
            </Button>
          </div>
        </div>

        {/* Category Tabs */}
        <Tabs value={activeCategory} onValueChange={setActiveCategory}>
          <TabsList className="grid grid-cols-5 w-full mb-6">
            {PROJECT_CATEGORIES.map(cat => {
              const Icon = cat.icon;
              const count = getCategoryCount(cat.id);
              return (
                <TabsTrigger 
                  key={cat.id} 
                  value={cat.id}
                  className="flex items-center gap-1 text-xs sm:text-sm"
                >
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{cat.label}</span>
                  <Badge variant="secondary" className="ml-1 text-xs">
                    {count}
                  </Badge>
                </TabsTrigger>
              );
            })}
          </TabsList>

          {/* Content for each category */}
          {PROJECT_CATEGORIES.map(cat => (
            <TabsContent key={cat.id} value={cat.id}>
              <Card>
                <CardHeader className="pb-3">
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                    <CardTitle className="text-lg flex items-center gap-2">
                      <cat.icon className={`w-5 h-5 text-white p-1 rounded ${cat.color}`} />
                      {cat.label} Drawings
                      <Badge variant="outline" className="ml-2">
                        {getCategoryCount(cat.id)} templates
                      </Badge>
                    </CardTitle>
                    <Button
                      onClick={() => setAddDialogOpen(true)}
                      size="sm"
                      className="bg-orange-600 hover:bg-orange-700"
                    >
                      <Plus className="w-4 h-4 mr-1" />
                      Add Drawing
                    </Button>
                  </div>
                  
                  {/* Search */}
                  <div className="relative mt-3">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-slate-400" />
                    <Input
                      placeholder="Search drawings..."
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="pl-10"
                    />
                  </div>
                </CardHeader>
                <CardContent>
                  {filteredTemplates.length === 0 ? (
                    <div className="text-center py-12 text-slate-500">
                      <FileText className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                      <p className="font-medium">No drawing templates yet</p>
                      <p className="text-sm mt-1">
                        {searchQuery ? 'No templates match your search' : 'Click "Seed Default Templates" or add drawings manually'}
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {filteredTemplates.map((template, index) => (
                        <div 
                          key={template.id}
                          className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border hover:bg-slate-100 transition-colors"
                        >
                          {/* Order number */}
                          <span className="text-xs text-slate-400 w-6 text-center font-mono">
                            {index + 1}
                          </span>
                          
                          {/* Drag handle (visual only for now) */}
                          <GripVertical className="w-4 h-4 text-slate-300" />
                          
                          {/* Drawing name - full display */}
                          <div className="flex-1 min-w-0">
                            <p className="font-medium text-sm text-slate-900 leading-tight break-words">
                              {template.name}
                            </p>
                            {template.is_default && (
                              <Badge variant="outline" className="mt-1 text-xs bg-blue-50 text-blue-600 border-blue-200">
                                Default
                              </Badge>
                            )}
                          </div>
                          
                          {/* Actions */}
                          <div className="flex items-center gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleMoveUp(template, index)}
                              disabled={index === 0 || saving}
                              title="Move Up"
                              className="h-8 w-8 p-0"
                            >
                              <ArrowUp className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleMoveDown(template, index)}
                              disabled={index === filteredTemplates.length - 1 || saving}
                              title="Move Down"
                              className="h-8 w-8 p-0"
                            >
                              <ArrowDown className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openEditDialog(template)}
                              title="Edit"
                              className="h-8 w-8 p-0 text-blue-600 hover:text-blue-700 hover:bg-blue-50"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openDeleteDialog(template)}
                              title="Delete"
                              className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          ))}
        </Tabs>

        {/* Add Drawing Dialog */}
        <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Add Drawing Template</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div>
                <Label>Category</Label>
                <p className="text-sm text-slate-600 mt-1">{activeCategory}</p>
              </div>
              <div>
                <Label htmlFor="new-drawing-name">Drawing Name</Label>
                <Input
                  id="new-drawing-name"
                  value={newDrawingName}
                  onChange={(e) => setNewDrawingName(e.target.value)}
                  placeholder="e.g., FLOOR PLAN GROUND LEVEL"
                  className="mt-1"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setAddDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddDrawing} disabled={saving} className="bg-orange-600 hover:bg-orange-700">
                {saving ? 'Adding...' : 'Add Drawing'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Drawing Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Drawing Template</DialogTitle>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                <p className="text-sm text-amber-800">
                  <strong>Note:</strong> Renaming this template will automatically update all project drawings with this name.
                </p>
              </div>
              <div>
                <Label htmlFor="edit-drawing-name">Drawing Name</Label>
                <Input
                  id="edit-drawing-name"
                  value={editDrawingName}
                  onChange={(e) => setEditDrawingName(e.target.value)}
                  className="mt-1"
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleEditDrawing} disabled={saving} className="bg-blue-600 hover:bg-blue-700">
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation Dialog */}
        <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Delete Drawing Template</DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <p className="text-slate-600">
                Are you sure you want to delete <strong>"{templateToDelete?.name}"</strong>?
              </p>
              <p className="text-sm text-slate-500 mt-2">
                This will only remove the template. Existing project drawings will not be affected.
              </p>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleDeleteDrawing} disabled={saving} variant="destructive">
                {saving ? 'Deleting...' : 'Delete Template'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
