import React from 'react';
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import { Button } from '../ui/button';

export const DeleteProjectDialog = ({ open, onOpenChange, project, onConfirm }) => (
  <Dialog open={open} onOpenChange={onOpenChange}>
    <DialogContent>
      <DialogHeader>
        <DialogTitle className="text-red-600">⚠️ Delete Project</DialogTitle>
      </DialogHeader>
      <div className="py-4 space-y-4">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-sm text-red-800 font-medium mb-2">
            <strong>{project?.code}</strong> - {project?.title}
          </p>
          <p className="text-xs text-red-700">
            This action cannot be undone. All drawings, comments, and project data will be permanently removed.
          </p>
        </div>

        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <p className="text-sm text-yellow-800 font-medium">
            Are you sure you want to delete this project?
          </p>
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={() => onOpenChange(false)}>
          Cancel
        </Button>
        
        <Button 
          onClick={onConfirm}
          className="bg-red-600 hover:bg-red-700 text-white"
        >
          Delete Project
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
);
