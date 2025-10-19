import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { Plus, UserCircle2, Mail, Trash2, Calendar, Shield } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Team({ user, onLogout }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [otpDialogOpen, setOtpDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [otpCode, setOtpCode] = useState('');
  const [generatedOtp, setGeneratedOtp] = useState('');
  const [otpAction, setOtpAction] = useState('');
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    role: 'architect',
  });

  const isOwner = user?.role === 'owner';

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setUsers(response.data);
    } catch (error) {
      toast.error('Failed to fetch team members');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    // First generate OTP
    setOtpAction('add_member');
    try {
      const otpResponse = await axios.post(`${API}/users/generate-otp`, { action: 'add_member' });
      setGeneratedOtp(otpResponse.data.otp_code);
      setOtpDialogOpen(true);
      toast.success(`OTP generated: ${otpResponse.data.otp_code}`);
    } catch (error) {
      toast.error('Failed to generate OTP');
    }
  };

  const handleOtpVerifyAndAdd = async () => {
    try {
      // Verify OTP
      await axios.post(`${API}/users/verify-otp`, {
        otp_code: otpCode,
        action: 'add_member'
      });

      // Add team member
      await axios.post(`${API}/auth/register`, formData);
      toast.success('Team member added successfully!');
      setOtpDialogOpen(false);
      setOpen(false);
      setOtpCode('');
      setFormData({ name: '', email: '', password: '', role: 'architect' });
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add team member');
    }
  };

  const handleDeleteClick = (member) => {
    setSelectedUser(member);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    setDeleteDialogOpen(false);
    setOtpAction('delete_member');
    
    try {
      // Generate OTP for deletion
      const otpResponse = await axios.post(`${API}/users/generate-otp`, {
        action: 'delete_member',
        target_user_id: selectedUser.id
      });
      setGeneratedOtp(otpResponse.data.otp_code);
      setOtpDialogOpen(true);
      toast.success(`OTP generated: ${otpResponse.data.otp_code}`);
    } catch (error) {
      toast.error('Failed to generate OTP');
    }
  };

  const handleOtpVerifyAndDelete = async () => {
    try {
      // Verify OTP
      await axios.post(`${API}/users/verify-otp`, {
        otp_code: otpCode,
        action: 'delete_member',
        target_user_id: selectedUser.id
      });

      // Delete user
      await axios.delete(`${API}/users/${selectedUser.id}?otp_code=${otpCode}`);
      toast.success('Team member deleted successfully!');
      setOtpDialogOpen(false);
      setOtpCode('');
      setSelectedUser(null);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete team member');
    }
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      owner: 'bg-purple-100 text-purple-800',
      architect: 'bg-blue-100 text-blue-800',
      interior_designer: 'bg-pink-100 text-pink-800',
      visualizer: 'bg-green-100 text-green-800',
      office_boy: 'bg-gray-100 text-gray-800',
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div data-testid="team-page">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Team</h1>
            <p className="text-slate-600 mt-1">{users.length} team members</p>
            {isOwner && (
              <div className="flex items-center gap-2 mt-2">
                <Shield className="w-4 h-4 text-purple-600" />
                <span className="text-sm font-medium text-purple-600">Owner Access</span>
              </div>
            )}
          </div>
          {isOwner && (
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button data-testid="add-team-member-btn">
                  <Plus className="w-4 h-4 mr-2" />
                  Add Team Member
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add New Team Member</DialogTitle>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4" data-testid="team-member-form">
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                      data-testid="team-name-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      required
                      data-testid="team-email-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="password">Password</Label>
                    <Input
                      id="password"
                      type="password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      required
                      minLength={6}
                      data-testid="team-password-input"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="role">Role</Label>
                    <select
                      id="role"
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm ring-offset-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                      data-testid="team-role-select"
                    >
                      <option value="architect">Architect</option>
                      <option value="interior_designer">Interior Designer</option>
                      <option value="visualizer">3D Visualizer</option>
                      <option value="office_boy">Office Assistant</option>
                    </select>
                  </div>
                  <Button type="submit" className="w-full" data-testid="submit-team-member-btn">
                    Generate OTP & Add Member
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {users.map((member) => (
            <Card key={member.id} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start gap-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-blue-100 to-blue-200 rounded-full flex items-center justify-center flex-shrink-0">
                    {member.picture ? (
                      <img
                        src={member.picture}
                        alt={member.name}
                        className="w-16 h-16 rounded-full object-cover"
                      />
                    ) : (
                      <span className="text-2xl font-bold text-blue-600">
                        {member.name.charAt(0).toUpperCase()}
                      </span>
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-slate-900 text-lg truncate">{member.name}</h3>
                    <Badge className={`${getRoleBadgeColor(member.role)} mt-2`}>
                      {member.role.replace('_', ' ')}
                    </Badge>
                  </div>
                </div>

                <div className="mt-4 space-y-2">
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <Mail className="w-4 h-4 flex-shrink-0" />
                    <span className="truncate">{member.email}</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm text-slate-500">
                    <Calendar className="w-4 h-4 flex-shrink-0" />
                    <span>Joined {new Date(member.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {users.length === 0 && (
          <div className="text-center py-12">
            <UserCircle2 className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No team members yet</h3>
            <p className="text-slate-500 mb-4">Add your first team member to get started</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
