import React, { useState, useEffect } from 'react';
import { Check, X, AlertCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import { Textarea } from './ui/textarea';
import { Label } from './ui/label';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

/**
 * ContractorProgressTracker - Shows task checklist for a contractor on a specific drawing
 * Contractors can mark tasks complete, Owner/Client can remove marks with reason
 */
export function ContractorProgressTracker({ 
  drawingId, 
  contractorId, 
  contractorName,
  contractorType,
  user,
  onProgressUpdate 
}) {
  const [loading, setLoading] = useState(true);
  const [progress, setProgress] = useState(null);
  const [expanded, setExpanded] = useState(false);
  const [removeDialogOpen, setRemoveDialogOpen] = useState(false);
  const [taskToRemove, setTaskToRemove] = useState(null);
  const [removeReason, setRemoveReason] = useState('');

  useEffect(() => {
    fetchProgress();
  }, [drawingId, contractorId]);

  const fetchProgress = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API}/drawings/${drawingId}/contractor-progress/${contractorId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setProgress(response.data);
    } catch (error) {
      console.error('Error fetching progress:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleTask = async (taskId, currentlyCompleted) => {
    // If removing a completed task, Owner/Client needs to provide reason
    if (currentlyCompleted && (user?.is_owner || user?.role === 'client')) {
      setTaskToRemove(taskId);
      setRemoveReason('');
      setRemoveDialogOpen(true);
      return;
    }

    // Contractors can only mark as complete, not remove
    if (currentlyCompleted && user?.role === 'contractor') {
      toast.error('Only owner or client can remove completed task marks');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/drawings/${drawingId}/contractor-progress/${contractorId}/update`,
        { task_id: taskId, completed: !currentlyCompleted },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(currentlyCompleted ? 'Task mark removed' : 'Task marked complete');
      fetchProgress();
      onProgressUpdate?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update task');
    }
  };

  const handleRemoveWithReason = async () => {
    if (!removeReason.trim() || removeReason.length < 10) {
      toast.error('Please provide a reason (at least 10 characters)');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/drawings/${drawingId}/contractor-progress/${contractorId}/remove-task`,
        { task_id: taskToRemove, reason: removeReason },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Task mark removed with comment');
      setRemoveDialogOpen(false);
      setTaskToRemove(null);
      setRemoveReason('');
      fetchProgress();
      onProgressUpdate?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to remove task');
    }
  };

  if (loading) {
    return <div className="text-sm text-slate-500">Loading progress...</div>;
  }

  if (!progress) {
    return null;
  }

  const completedCount = progress.completed_tasks?.length || 0;
  const totalTasks = progress.tasks?.length || 0;
  const percentage = progress.progress_percentage || 0;

  return (
    <div className="border rounded-lg bg-slate-50 p-3 mt-2">
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <span className="font-medium text-sm">{contractorName}</span>
          <Badge variant="outline" className="text-xs">
            {contractorType}
          </Badge>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Progress value={percentage} className="w-20 h-2" />
            <span className="text-sm font-medium">{percentage}%</span>
          </div>
          <span className="text-xs text-slate-500">
            {completedCount}/{totalTasks}
          </span>
          {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </div>

      {expanded && (
        <div className="mt-3 space-y-2">
          {progress.tasks?.map((task) => {
            const isCompleted = progress.completed_tasks?.includes(task.id);
            const canToggle = user?.is_owner || user?.role === 'client' || 
              (user?.role === 'contractor' && !isCompleted);

            return (
              <div 
                key={task.id}
                className={`flex items-center justify-between p-2 rounded border ${
                  isCompleted ? 'bg-green-50 border-green-200' : 'bg-white border-slate-200'
                }`}
              >
                <div className="flex items-center gap-2">
                  <div 
                    className={`w-5 h-5 rounded flex items-center justify-center cursor-pointer ${
                      isCompleted 
                        ? 'bg-green-500 text-white' 
                        : 'border-2 border-slate-300 hover:border-green-400'
                    } ${!canToggle ? 'opacity-50 cursor-not-allowed' : ''}`}
                    onClick={() => canToggle && handleToggleTask(task.id, isCompleted)}
                  >
                    {isCompleted && <Check className="w-3 h-3" />}
                  </div>
                  <div>
                    <span className={`text-sm ${isCompleted ? 'text-green-700' : 'text-slate-700'}`}>
                      {task.name}
                    </span>
                    <p className="text-xs text-slate-500">{task.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Remove Task Dialog */}
      <Dialog open={removeDialogOpen} onOpenChange={setRemoveDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-amber-500" />
              Remove Task Completion
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              You are about to remove a completed task mark. Please provide a reason 
              for why this work is not satisfactory.
            </p>
            <div>
              <Label>Reason for removal *</Label>
              <Textarea
                value={removeReason}
                onChange={(e) => setRemoveReason(e.target.value)}
                placeholder="Explain why this task completion is being removed..."
                className="min-h-[100px]"
              />
              <p className="text-xs text-slate-500 mt-1">Minimum 10 characters required</p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRemoveDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleRemoveWithReason}
              className="bg-amber-500 hover:bg-amber-600"
            >
              Remove with Comment
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

/**
 * ContractorProgressSummary - Shows a contractor's progress across all their projects
 * Used in the Contractors page when clicking on a contractor name
 */
export function ContractorProgressSummary({ contractorId, contractorName }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [expandedProject, setExpandedProject] = useState(null);

  useEffect(() => {
    fetchContractorProgress();
  }, [contractorId]);

  const fetchContractorProgress = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(
        `${API}/contractors/${contractorId}/projects-progress`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setData(response.data);
    } catch (error) {
      console.error('Error fetching contractor progress:', error);
      toast.error('Failed to load contractor progress');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="text-slate-500">Loading progress report...</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="text-center py-8 text-slate-500">
        No progress data available
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary Header */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-lg">{data.contractor_name}</h3>
            <Badge variant="outline">{data.contractor_type} Contractor</Badge>
          </div>
          <div className="text-right">
            <div className="text-2xl font-bold text-blue-600">{data.total_projects}</div>
            <div className="text-sm text-slate-500">Active Projects</div>
          </div>
        </div>
      </div>

      {/* Projects List */}
      {data.projects?.length === 0 ? (
        <div className="text-center py-8 text-slate-500">
          No active projects assigned
        </div>
      ) : (
        <div className="space-y-3">
          {data.projects?.map((project) => (
            <Card key={project.project_id} className="overflow-hidden">
              <div 
                className="p-4 cursor-pointer hover:bg-slate-50"
                onClick={() => setExpandedProject(
                  expandedProject === project.project_id ? null : project.project_id
                )}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{project.project_name}</h4>
                    {project.project_code && (
                      <span className="text-sm text-slate-500">{project.project_code}</span>
                    )}
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="flex items-center gap-2">
                        <Progress value={project.overall_progress} className="w-24 h-2" />
                        <span className="font-medium">{project.overall_progress}%</span>
                      </div>
                      <span className="text-xs text-slate-500">
                        {project.issued_drawings_count} issued drawings
                      </span>
                    </div>
                    {expandedProject === project.project_id ? (
                      <ChevronUp className="w-5 h-5 text-slate-400" />
                    ) : (
                      <ChevronDown className="w-5 h-5 text-slate-400" />
                    )}
                  </div>
                </div>
              </div>

              {expandedProject === project.project_id && project.drawing_progress?.length > 0 && (
                <div className="border-t bg-slate-50 p-4">
                  <h5 className="text-sm font-medium mb-3">Drawing Progress</h5>
                  <div className="space-y-2">
                    {project.drawing_progress.map((drawing) => (
                      <div 
                        key={drawing.drawing_id}
                        className="flex items-center justify-between bg-white p-2 rounded border"
                      >
                        <span className="text-sm">{drawing.drawing_name}</span>
                        <div className="flex items-center gap-2">
                          <Progress value={drawing.progress_percentage} className="w-16 h-1.5" />
                          <span className="text-xs font-medium w-10 text-right">
                            {drawing.progress_percentage}%
                          </span>
                          <span className="text-xs text-slate-500">
                            ({drawing.completed_tasks}/{drawing.total_tasks})
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}

export default ContractorProgressTracker;
