import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Label } from '../ui/label';

export const ArchiveProjectDialog = ({ 
  open, 
  onOpenChange, 
  project, 
  archiveDate,
  setArchiveDate,
  onConfirm 
}) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Archive Project</DialogTitle>
      </DialogHeader>
      <div className="space-y-4 py-4">
        <p className="text-slate-700">
          Archiving this project will mark it as completed. Please enter the project completion date.
        </p>
        <div>
          <Label>Completion Date *</Label>
          <Input
            type="date"
            value={archiveDate}
            onChange={(e) => setArchiveDate(e.target.value)}
            required
          />
        </div>
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
          <p className="text-sm text-orange-800">
            <strong>{project?.code}</strong> - {project?.title}
          </p>
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => {
          onOpenChange(false);
          setArchiveDate('');
        }}>
          Cancel
        </Button>
        <Button 
          onClick={onConfirm}
          className="bg-orange-600 hover:bg-orange-700 text-white"
        >
          Archive Project
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);
