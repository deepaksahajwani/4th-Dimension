import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
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
import { Label } from './ui/label';
import { Input } from './ui/input';
import { 
  Users, 
  Plus, 
  Trash2, 
  Clock, 
  Share2,
  UserPlus,
  Shield
} from 'lucide-react';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

/**
 * TeamLeaderAccess - Component for team leaders to manage temporary project access
 * Allows team leaders to grant other team members temporary access to their projects
 */
export function TeamLeaderAccess({ projectId, projectName, user, onAccessChange }) {
  const [loading, setLoading] = useState(true);
  const [accessList, setAccessList] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [shareDialogOpen, setShareDialogOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [expiryDays, setExpiryDays] = useState('7');

  useEffect(() => {
    fetchAccessData();
  }, [projectId]);

  const fetchAccessData = async () => {
    try {
      const token = localStorage.getItem('token');
      const [accessRes, teamRes] = await Promise.all([
        axios.get(`${API}/projects/${projectId}/access-list`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/users`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      setAccessList(accessRes.data || []);
      // Filter team members who can be granted access (exclude owner and already shared users)
      const sharedUserIds = (accessRes.data || []).map(a => a.user_id);
      const availableMembers = (teamRes.data || []).filter(m => 
        m.id !== user?.id && 
        !m.is_owner && 
        !sharedUserIds.includes(m.id) &&
        (m.role === 'team_member' || m.role === 'team_leader')
      );
      setTeamMembers(availableMembers);
    } catch (error) {
      console.error('Error fetching access data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleGrantAccess = async () => {
    if (!selectedUserId) {
      toast.error('Please select a team member');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API}/projects/${projectId}/share`,
        { 
          user_id: selectedUserId, 
          expiry_days: parseInt(expiryDays) 
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Temporary access granted successfully!');
      setShareDialogOpen(false);
      setSelectedUserId('');
      setExpiryDays('7');
      fetchAccessData();
      onAccessChange?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to grant access');
    }
  };

  const handleRevokeAccess = async (userId, userName) => {
    if (!window.confirm(`Are you sure you want to revoke ${userName}'s access to this project?`)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      await axios.delete(
        `${API}/projects/${projectId}/revoke-access/${userId}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      toast.success('Access revoked successfully');
      fetchAccessData();
      onAccessChange?.();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to revoke access');
    }
  };

  // Only show for team leaders and owners
  const canManageAccess = user?.is_owner || user?.role === 'team_leader';

  if (!canManageAccess) {
    return null;
  }

  if (loading) {
    return (
      <div className="text-sm text-slate-500">Loading access settings...</div>
    );
  }

  return (
    <Card className="border-blue-200 bg-blue-50/30">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-blue-600" />
            <CardTitle className="text-base">Project Access Management</CardTitle>
          </div>
          <Button
            size="sm"
            onClick={() => setShareDialogOpen(true)}
            className="bg-blue-600 hover:bg-blue-700"
            disabled={teamMembers.length === 0}
          >
            <UserPlus className="w-4 h-4 mr-2" />
            Grant Access
          </Button>
        </div>
        <p className="text-sm text-slate-600 mt-1">
          Grant temporary access to other team members to collaborate on this project.
        </p>
      </CardHeader>
      
      <CardContent>
        {accessList.length === 0 ? (
          <div className="text-center py-6 bg-white rounded-lg border border-slate-200">
            <Share2 className="w-10 h-10 text-slate-300 mx-auto mb-2" />
            <p className="text-sm text-slate-500">No shared access granted</p>
            <p className="text-xs text-slate-400 mt-1">
              Click "Grant Access" to share this project with team members
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {accessList.map((access) => (
              <div 
                key={access.user_id}
                className="flex items-center justify-between p-3 bg-white rounded-lg border border-slate-200"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                    <Users className="w-4 h-4 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-slate-900">{access.user_name}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Clock className="w-3 h-3 text-slate-400" />
                      <span className="text-xs text-slate-500">
                        {access.expires_at 
                          ? `Expires: ${new Date(access.expires_at).toLocaleDateString()}` 
                          : 'No expiry'}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-blue-600 border-blue-200">
                    Temporary
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRevokeAccess(access.user_id, access.user_name)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>

      {/* Grant Access Dialog */}
      <Dialog open={shareDialogOpen} onOpenChange={setShareDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Grant Temporary Project Access</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <p className="text-sm text-slate-600">
              Select a team member to grant temporary access to "{projectName}"
            </p>
            
            <div className="space-y-2">
              <Label>Team Member</Label>
              <Select value={selectedUserId} onValueChange={setSelectedUserId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select team member..." />
                </SelectTrigger>
                <SelectContent>
                  {teamMembers.map((member) => (
                    <SelectItem key={member.id} value={member.id}>
                      {member.name} ({member.role?.replace('_', ' ')})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {teamMembers.length === 0 && (
                <p className="text-xs text-amber-600">
                  No available team members to grant access to
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label>Access Duration (days)</Label>
              <Select value={expiryDays} onValueChange={setExpiryDays}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">1 day</SelectItem>
                  <SelectItem value="3">3 days</SelectItem>
                  <SelectItem value="7">7 days (1 week)</SelectItem>
                  <SelectItem value="14">14 days (2 weeks)</SelectItem>
                  <SelectItem value="30">30 days (1 month)</SelectItem>
                  <SelectItem value="90">90 days (3 months)</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-xs text-slate-500">
                Access will automatically expire after this duration
              </p>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShareDialogOpen(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleGrantAccess}
              className="bg-blue-600 hover:bg-blue-700"
              disabled={!selectedUserId}
            >
              Grant Access
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </Card>
  );
}

export default TeamLeaderAccess;
