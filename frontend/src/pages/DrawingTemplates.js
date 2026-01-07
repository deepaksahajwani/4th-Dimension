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
import { 
  Layers, Plus, Edit, Trash2, GripVertical, ArrowUp, ArrowDown, Save, X, 
  FileText, Building, Palette, Leaf, Zap, Wrench, Check
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

// Project categories with icons
const PROJECT_CATEGORIES = [
  { id: 'Architecture', label: 'Architecture', icon: Building },
  { id: 'Interior', label: 'Interior', icon: Palette },
  { id: 'Landscape', label: 'Landscape', icon: Leaf },
  { id: 'MEP', label: 'MEP (Mechanical, Electrical, Plumbing)', icon: Zap },
  { id: 'Structure', label: 'Structure', icon: Wrench },
];

export default function DrawingTemplates({ user, onLogout }) {
  const navigate = useNavigate();
  const [activeCategory, setActiveCategory] = useState('Interior');
  const [templates, setTemplates] = useState({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  
  // Dialog states
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [newDrawingName, setNewDrawingName] = useState('');
  const [editingDrawing, setEditingDrawing] = useState(null);
  const [editDrawingName, setEditDrawingName] = useState('');

  useEffect(() => {
    if (!user?.is_owner) {
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
      
      // Convert array to object by category
      const templatesByCategory = {};
      PROJECT_CATEGORIES.forEach(cat => {
        templatesByCategory[cat.id] = [];
      });
      
      if (response.data && Array.isArray(response.data)) {
        response.data.forEach(template => {
          if (templatesByCategory[template.category]) {
            templatesByCategory[template.category] = template.drawings || [];
          }
        });
      }
      
      setTemplates(templatesByCategory);
    } catch (error) {
      console.error('Error fetching templates:', error);
      // Initialize empty templates
      const emptyTemplates = {};
      PROJECT_CATEGORIES.forEach(cat => {
        emptyTemplates[cat.id] = [];
      });
      setTemplates(emptyTemplates);
    } finally {
      setLoading(false);
    }
  };

  const saveTemplates = async (category, drawings) => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.put(`${API}/drawing-templates/${category}`, {
        category,
        drawings
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Templates saved!');
    } catch (error) {
      console.error('Error saving templates:', error);
      toast.error('Failed to save templates');
    } finally {
      setSaving(false);
    }
  };

  const handleAddDrawing = () => {
    if (!newDrawingName.trim()) {
      toast.error('Please enter a drawing name');
      return;
    }
    
    const currentDrawings = templates[activeCategory] || [];
    const newDrawings = [
      ...currentDrawings,
      { id: Date.now().toString(), name: newDrawingName.trim(), order: currentDrawings.length }
    ];
    
    setTemplates(prev => ({
      ...prev,
      [activeCategory]: newDrawings
    }));
    
    saveTemplates(activeCategory, newDrawings);
    setNewDrawingName('');
    setAddDialogOpen(false);
  };

  const handleEditDrawing = () => {
    if (!editDrawingName.trim()) {
      toast.error('Please enter a drawing name');
      return;
    }
    
    const currentDrawings = templates[activeCategory] || [];
    const newDrawings = currentDrawings.map(d => 
      d.id === editingDrawing.id ? { ...d, name: editDrawingName.trim() } : d
    );
    
    setTemplates(prev => ({
      ...prev,
      [activeCategory]: newDrawings
    }));
    
    saveTemplates(activeCategory, newDrawings);
    setEditingDrawing(null);
    setEditDrawingName('');
    setEditDialogOpen(false);
  };

  const handleDeleteDrawing = (drawingId) => {
    if (!window.confirm('Delete this drawing from the template?')) return;
    
    const currentDrawings = templates[activeCategory] || [];
    const newDrawings = currentDrawings.filter(d => d.id !== drawingId);
    
    setTemplates(prev => ({
      ...prev,
      [activeCategory]: newDrawings
    }));
    
    saveTemplates(activeCategory, newDrawings);
  };

  const handleMoveDrawing = (index, direction) => {
    const currentDrawings = [...(templates[activeCategory] || [])];
    const newIndex = direction === 'up' ? index - 1 : index + 1;
    
    if (newIndex < 0 || newIndex >= currentDrawings.length) return;
    
    // Swap
    [currentDrawings[index], currentDrawings[newIndex]] = [currentDrawings[newIndex], currentDrawings[index]];
    
    // Update order
    currentDrawings.forEach((d, i) => d.order = i);
    
    setTemplates(prev => ({
      ...prev,
      [activeCategory]: currentDrawings
    }));
    
    saveTemplates(activeCategory, currentDrawings);
  };

  const openEditDialog = (drawing) => {
    setEditingDrawing(drawing);
    setEditDrawingName(drawing.name);
    setEditDialogOpen(true);
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
        </div>
      </Layout>
    );
  }

  const currentDrawings = templates[activeCategory] || [];
  const CategoryIcon = PROJECT_CATEGORIES.find(c => c.id === activeCategory)?.icon || FileText;

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-7 h-7 text-orange-600" />
            Drawing Templates
          </h1>
          <p className="text-sm text-slate-600 mt-1">
            Manage master drawing lists for each project type. These will auto-populate when creating new projects.
          </p>
        </div>

        {/* Category Tabs */}
        <Tabs value={activeCategory} onValueChange={setActiveCategory}>
          <TabsList className="grid grid-cols-5 w-full mb-6">
            {PROJECT_CATEGORIES.map(cat => {
              const Icon = cat.icon;
              return (
                <TabsTrigger key={cat.id} value={cat.id} className="flex items-center gap-1 text-xs sm:text-sm">
                  <Icon className="w-4 h-4" />
                  <span className="hidden sm:inline">{cat.label.split(' ')[0]}</span>
                </TabsTrigger>
              );
            })}
          </TabsList>

          {PROJECT_CATEGORIES.map(cat => (
            <TabsContent key={cat.id} value={cat.id}>
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-4">
                  <CardTitle className="text-lg flex items-center gap-2">
                    <CategoryIcon className="w-5 h-5 text-orange-600" />
                    {cat.label} Drawings
                    <span className="text-sm font-normal text-slate-500">
                      ({currentDrawings.length} drawings)
                    </span>
                  </CardTitle>
                  <Button 
                    onClick={() => setAddDialogOpen(true)}
                    className="bg-orange-500 hover:bg-orange-600"
                    size="sm"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Add Drawing
                  </Button>
                </CardHeader>
                <CardContent>
                  {currentDrawings.length === 0 ? (
                    <div className="text-center py-12 bg-slate-50 rounded-lg">
                      <FileText className="w-12 h-12 text-slate-300 mx-auto mb-3" />
                      <p className="text-slate-500">No drawings in this template</p>
                      <p className="text-xs text-slate-400 mt-1">
                        Add drawings that should be created for {cat.label} projects
                      </p>
                      <Button 
                        onClick={() => setAddDialogOpen(true)}
                        className="mt-4"
                        variant="outline"
                      >
                        <Plus className="w-4 h-4 mr-1" />
                        Add First Drawing
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {currentDrawings.map((drawing, index) => (
                        <div 
                          key={drawing.id}
                          className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-200 hover:border-orange-300 transition-colors"
                        >
                          {/* Order number */}
                          <span className="w-6 h-6 bg-orange-100 text-orange-700 rounded-full flex items-center justify-center text-xs font-medium">
                            {index + 1}
                          </span>
                          
                          {/* Drawing name */}
                          <span className="flex-1 text-sm font-medium text-slate-700">
                            {drawing.name}
                          </span>
                          
                          {/* Actions */}
                          <div className="flex items-center gap-1">
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleMoveDrawing(index, 'up')}
                              disabled={index === 0}
                              className="h-8 w-8 p-0"
                            >
                              <ArrowUp className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleMoveDrawing(index, 'down')}
                              disabled={index === currentDrawings.length - 1}
                              className="h-8 w-8 p-0"
                            >
                              <ArrowDown className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => openEditDialog(drawing)}
                              className="h-8 w-8 p-0"
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => handleDeleteDrawing(drawing.id)}
                              className="h-8 w-8 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {saving && (
                    <div className="mt-4 flex items-center justify-center gap-2 text-sm text-orange-600">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-orange-600"></div>
                      Saving...
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
              <DialogTitle className="flex items-center gap-2">
                <Plus className="w-5 h-5 text-orange-600" />
                Add Drawing to {activeCategory} Template
              </DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <Label>Drawing Name</Label>
              <Input
                value={newDrawingName}
                onChange={(e) => setNewDrawingName(e.target.value)}
                placeholder="e.g., Floor Plan, Elevation, Section..."
                className="mt-2"
                onKeyDown={(e) => e.key === 'Enter' && handleAddDrawing()}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setAddDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleAddDrawing} className="bg-orange-500 hover:bg-orange-600">
                Add Drawing
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Edit Drawing Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle className="flex items-center gap-2">
                <Edit className="w-5 h-5 text-orange-600" />
                Edit Drawing
              </DialogTitle>
            </DialogHeader>
            <div className="py-4">
              <Label>Drawing Name</Label>
              <Input
                value={editDrawingName}
                onChange={(e) => setEditDrawingName(e.target.value)}
                placeholder="Drawing name"
                className="mt-2"
                onKeyDown={(e) => e.key === 'Enter' && handleEditDrawing()}
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditDialogOpen(false)}>
                Cancel
              </Button>
              <Button onClick={handleEditDrawing} className="bg-orange-500 hover:bg-orange-600">
                Save Changes
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
