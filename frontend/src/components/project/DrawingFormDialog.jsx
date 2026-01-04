/**
 * Drawing Form Dialog Component
 * Handles creating and editing drawings
 */

import React, { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { toast } from 'sonner';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const DRAWING_CATEGORIES = ['Architecture', 'Interior', 'Landscape', 'Planning'];

export default function DrawingFormDialog({
  open,
  onOpenChange,
  projectId,
  editingDrawing = null,
  onSuccess
}) {
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    category: 'Architecture',
    name: '',
    due_date: '',
    notes: ''
  });

  // Reset form when dialog opens/closes or editing drawing changes
  useEffect(() => {
    if (open) {
      if (editingDrawing) {
        setFormData({
          category: editingDrawing.category || 'Architecture',
          name: editingDrawing.name || '',
          due_date: editingDrawing.due_date ? editingDrawing.due_date.split('T')[0] : '',
          notes: editingDrawing.notes || ''
        });
      } else {
        setFormData({
          category: 'Architecture',
          name: '',
          due_date: '',
          notes: ''
        });
      }
    }
  }, [open, editingDrawing]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name.trim()) {
      toast.error('Drawing name is required');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { Authorization: `Bearer ${token}` };

      if (editingDrawing) {
        // Update existing drawing
        await axios.put(
          `${API}/drawings/${editingDrawing.id}`,
          formData,
          { headers }
        );
        toast.success('Drawing updated successfully');
      } else {
        // Create new drawing
        await axios.post(
          `${API}/projects/${projectId}/drawings`,
          formData,
          { headers }
        );
        toast.success('Drawing created successfully');
      }

      onOpenChange(false);
      onSuccess?.();
    } catch (error) {
      console.error('Error saving drawing:', error);
      toast.error(error.response?.data?.detail || 'Failed to save drawing');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {editingDrawing ? 'Edit Drawing' : 'Add New Drawing'}
          </DialogTitle>
        </DialogHeader>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="category">Category</Label>
            <Select
              value={formData.category}
              onValueChange={(value) => setFormData({ ...formData, category: value })}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select category" />
              </SelectTrigger>
              <SelectContent>
                {DRAWING_CATEGORIES.map((cat) => (
                  <SelectItem key={cat} value={cat}>{cat}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="name">Drawing Name *</Label>
            <Input
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., Ground Floor Plan"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="due_date">Due Date</Label>
            <Input
              id="due_date"
              type="date"
              value={formData.due_date}
              onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes</Label>
            <Textarea
              id="notes"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Additional notes..."
              rows={3}
            />
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={loading}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={loading}>
              {loading ? 'Saving...' : (editingDrawing ? 'Update' : 'Create')}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
