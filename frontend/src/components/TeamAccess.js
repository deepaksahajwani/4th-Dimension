import React, { useState, useEffect } from 'react';
import { UserPlus, Clock, Check, X, Users, Calendar, AlertCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from './ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

/**
 * GrantAccessDialog - Dialog for team leader/owner to grant temporary project access
 */
export function GrantAccessDialog({ projectId, projectName, open, onOpenChange, onAccessGranted }) {
  const [teamMembers, setTeamMembers] = useState([]);
  const [selectedUser, setSelectedUser] = useState('');
  const [expiryDate, setExpiryDate] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      fetchTeamMembers();
      // Default expiry to 30 days from now
      const defaultExpiry = new Date();
      defaultExpiry.setDate(defaultExpiry.getDate() + 30);
      setExpiryDate(defaultExpiry.toISOString().split('T')[0]);
    }
  }, [open]);

  const fetchTeamMembers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Filter to only team members (not clients, contractors, etc.)
      const members = response.data.filter(u => 
        u.role === 'team_member' || u.role === 'team_leader' || u.designation?.includes('Leader')
      );
      setTeamMembers(members);
    } catch (error) {
      console.error('Error fetching team members:', error);
    }
  };

  const handleGrantAccess = async () => {
    if (!selectedUser || !expiryDate) {
      toast.error('Please select a team member and expiry date');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/projects/${projectId}/grant-access`,
        { 
          user_id: selectedUser, 
          expires_at: new Date(expiryDate).toISOString() 
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Access granted successfully');
      onOpenChange(false);
      onAccessGranted?.();
      setSelectedUser('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to grant access');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="w-5 h-5 text-blue-500" />
            Grant Project Access
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="bg-blue-50 p-3 rounded-lg">
            <p className="text-sm text-blue-700">
              <strong>Project:</strong> {projectName}
            </p>
          </div>

          <div>
            <Label>Select Team Member *</Label>
            <Select value={selectedUser} onValueChange={setSelectedUser}>
              <SelectTrigger>
                <SelectValue placeholder="Choose a team member..." />
              </SelectTrigger>
              <SelectContent>
                {teamMembers.map((member) => (
                  <SelectItem key={member.id} value={member.id}>
                    {member.name} ({member.designation || member.role})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div>
            <Label>Access Until *</Label>
            <Input
              type="date"
              value={expiryDate}
              onChange={(e) => setExpiryDate(e.target.value)}
              min={new Date().toISOString().split('T')[0]}
            />
            <p className="text-xs text-slate-500 mt-1">
              Access will automatically expire after this date
            </p>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleGrantAccess} disabled={loading}>
            {loading ? 'Granting...' : 'Grant Access'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/**
 * RequestAccessDialog - Dialog for team members to request access to a project
 */
export function RequestAccessDialog({ projectId, projectName, open, onOpenChange }) {
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRequestAccess = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/projects/${projectId}/request-access`,
        { message },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Access request sent! The team leader will review your request.');
      onOpenChange(false);
      setMessage('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-amber-500" />
            Request Project Access
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <div className="bg-amber-50 p-3 rounded-lg">
            <p className="text-sm text-amber-700">
              <strong>Project:</strong> {projectName}
            </p>
          </div>

          <div>
            <Label>Message (Optional)</Label>
            <Textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              placeholder="Explain why you need access to this project..."
              className="min-h-[80px]"
            />
          </div>

          <p className="text-sm text-slate-600">
            Your request will be sent to the project team leader and owner for approval.
          </p>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleRequestAccess} disabled={loading} className="bg-amber-500 hover:bg-amber-600">
            {loading ? 'Sending...' : 'Send Request'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/**
 * AccessRequestsList - Shows pending access requests for team leader/owner to review
 */
export function AccessRequestsList({ onRequestHandled }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [respondingTo, setRespondingTo] = useState(null);
  const [expiryDate, setExpiryDate] = useState('');

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/project-access-requests`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRequests(response.data);
    } catch (error) {
      console.error('Error fetching requests:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRespond = async (requestId, approved) => {
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/project-access-requests/${requestId}/respond`,
        { 
          approved, 
          expires_at: approved ? new Date(expiryDate).toISOString() : null 
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success(approved ? 'Access granted' : 'Request denied');
      setRespondingTo(null);
      fetchRequests();
      onRequestHandled?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to respond');
    }
  };

  if (loading) {
    return <div className="text-sm text-slate-500">Loading requests...</div>;
  }

  if (requests.length === 0) {
    return (
      <div className="text-center py-4 text-slate-500">
        No pending access requests
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {requests.map((request) => (
        <Card key={request.id} className="border-l-4 border-l-amber-400">
          <CardContent className="p-4">
            <div className="flex items-start justify-between">
              <div>
                <h4 className="font-medium">{request.requester_name}</h4>
                <p className="text-sm text-slate-600">
                  Requesting access to: <strong>{request.project_name}</strong>
                </p>
                {request.message && (
                  <p className="text-sm text-slate-500 mt-1 italic">
                    "{request.message}"
                  </p>
                )}
                <p className="text-xs text-slate-400 mt-2">
                  Requested: {new Date(request.created_at).toLocaleDateString()}
                </p>
              </div>
              
              {respondingTo === request.id ? (
                <div className="flex flex-col gap-2">
                  <Input
                    type="date"
                    value={expiryDate}
                    onChange={(e) => setExpiryDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    className="w-40"
                  />
                  <div className="flex gap-1">
                    <Button 
                      size="sm" 
                      onClick={() => handleRespond(request.id, true)}
                      className="bg-green-500 hover:bg-green-600"
                    >
                      <Check className="w-4 h-4" />
                    </Button>
                    <Button 
                      size="sm" 
                      variant="outline"
                      onClick={() => setRespondingTo(null)}
                    >
                      Cancel
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex gap-2">
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => {
                      const defaultExpiry = new Date();
                      defaultExpiry.setDate(defaultExpiry.getDate() + 30);
                      setExpiryDate(defaultExpiry.toISOString().split('T')[0]);
                      setRespondingTo(request.id);
                    }}
                    className="text-green-600 border-green-300"
                  >
                    <Check className="w-4 h-4 mr-1" />
                    Approve
                  </Button>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => handleRespond(request.id, false)}
                    className="text-red-600 border-red-300"
                  >
                    <X className="w-4 h-4 mr-1" />
                    Deny
                  </Button>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

/**
 * ProjectAccessList - Shows users with temporary access to a project
 */
export function ProjectAccessList({ projectId, canManage = false }) {
  const [accessList, setAccessList] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAccessList();
  }, [projectId]);

  const fetchAccessList = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/projects/${projectId}/access-list`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAccessList(response.data);
    } catch (error) {
      console.error('Error fetching access list:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeAccess = async (userId) => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/projects/${projectId}/revoke-access/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Access revoked');
      fetchAccessList();
    } catch (error) {
      toast.error('Failed to revoke access');
    }
  };

  if (loading) {
    return <div className="text-sm text-slate-500">Loading...</div>;
  }

  if (accessList.length === 0) {
    return (
      <div className="text-sm text-slate-500 py-2">
        No temporary access grants
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {accessList.map((access) => (
        <div 
          key={access.id}
          className="flex items-center justify-between bg-slate-50 p-2 rounded border"
        >
          <div>
            <span className="font-medium text-sm">{access.user_name}</span>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Calendar className="w-3 h-3" />
              Until {new Date(access.expires_at).toLocaleDateString()}
            </div>
          </div>
          {canManage && (
            <Button 
              size="sm" 
              variant="ghost"
              onClick={() => handleRevokeAccess(access.user_id)}
              className="text-red-500 h-7"
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      ))}
    </div>
  );
}

export default { GrantAccessDialog, RequestAccessDialog, AccessRequestsList, ProjectAccessList };
