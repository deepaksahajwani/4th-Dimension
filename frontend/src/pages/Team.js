import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { UserCircle2, Mail, Phone, Calendar, Shield, Trash2, CheckCircle, XCircle, MapPin, Heart, Cake } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Team({ user, onLogout }) {
  const [users, setUsers] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);

  const isOwner = user?.is_owner;
  const isAdmin = user?.is_admin || isOwner;

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      const validated = response.data.filter(u => u.is_validated);
      setUsers(validated);
      
      if (isAdmin) {
        try {
          const pendingResponse = await axios.get(`${API}/users/pending`);
          setPendingUsers(pendingResponse.data);
        } catch (error) {
          console.error('Error fetching pending users:', error);
        }
      }
    } catch (error) {
      toast.error('Failed to fetch team members');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleAdmin = async (userId, currentStatus) => {
    try {
      await axios.post(`${API}/users/${userId}/toggle-admin`);
      toast.success(
        !currentStatus ? 'Administrator rights granted' : 'Administrator rights revoked'
      );
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update admin rights');
    }
  };

  const handleValidateUser = async (userId) => {
    try {
      await axios.post(`${API}/users/${userId}/validate`);
      toast.success('User validated successfully!');
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to validate user');
    }
  };

  const handleRejectUser = async (userId) => {
    try {
      await axios.post(`${API}/users/${userId}/reject`);
      toast.success('User rejected and removed');
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reject user');
    }
  };

  const handleDeleteUser = async () => {
    try {
      await axios.delete(`${API}/users/${selectedUser.id}`);
      toast.success('Team member deleted successfully!');
      setDeleteDialogOpen(false);
      setSelectedUser(null);
      fetchUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete team member');
    }
  };

  const getRoleBadgeColor = (role) => {
    const colors = {
      architect: 'bg-blue-100 text-blue-800',
      interior_designer: 'bg-pink-100 text-pink-800',
      landscape_designer: 'bg-green-100 text-green-800',
      site_engineer: 'bg-orange-100 text-orange-800',
      structural_engineer: 'bg-purple-100 text-purple-800',
      site_supervisor: 'bg-yellow-100 text-yellow-800',
      intern: 'bg-gray-100 text-gray-800',
      administrator: 'bg-red-100 text-red-800',
      office_staff: 'bg-slate-100 text-slate-800',
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
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-slate-900">Manage Team</h1>
          <p className="text-slate-600 mt-1">{users.length} validated members</p>
          {isOwner && (
            <div className="flex items-center gap-2 mt-2">
              <Shield className="w-4 h-4 text-purple-600" />
              <span className="text-sm font-medium text-purple-600">Owner Access</span>
            </div>
          )}
        </div>

        {/* Pending Members Section */}
        {isAdmin && pendingUsers.length > 0 && (
          <div className="mb-8">
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4">
              <h2 className="text-lg font-semibold text-amber-900 mb-2">Pending Validation</h2>
              <p className="text-sm text-amber-700">{pendingUsers.length} member(s) awaiting approval</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {pendingUsers.map((member) => (
                <Card key={member.id} className="border-2 border-amber-200">
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4 mb-4">
                      <div className="w-16 h-16 bg-gradient-to-br from-amber-100 to-amber-200 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-2xl font-bold text-amber-600">
                          {member.name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-slate-900 text-lg truncate" title={member.name}>
                          {member.name}
                        </h3>
                        <Badge className={`${getRoleBadgeColor(member.role)} mt-2`}>
                          {member.role.replace('_', ' ')}
                        </Badge>
                      </div>
                    </div>

                    <div className="space-y-2 mb-4 text-sm">
                      <div className="flex items-center gap-2 text-slate-600">
                        <Mail className="w-4 h-4 flex-shrink-0" />
                        <span className="truncate">{member.email}</span>
                      </div>
                      {member.mobile && (
                        <div className="flex items-center gap-2 text-slate-600">
                          <Phone className="w-4 h-4 flex-shrink-0" />
                          <span>{member.mobile}</span>
                        </div>
                      )}
                      {member.date_of_birth && (
                        <div className="flex items-center gap-2 text-slate-600">
                          <Cake className="w-4 h-4 flex-shrink-0" />
                          <span>DOB: {new Date(member.date_of_birth).toLocaleDateString()}</span>
                        </div>
                      )}
                      {member.marital_status && (
                        <div className="flex items-center gap-2 text-slate-600">
                          <Heart className="w-4 h-4 flex-shrink-0" />
                          <span className="capitalize">{member.marital_status}</span>
                        </div>
                      )}
                      <div className="flex gap-2 flex-wrap mt-2">
                        <Badge variant={member.mobile_verified ? 'default' : 'secondary'} className="text-xs">
                          Mobile: {member.mobile_verified ? '✓' : '✗'}
                        </Badge>
                        <Badge variant={member.email_verified ? 'default' : 'secondary'} className="text-xs">
                          Email: {member.email_verified ? '✓' : '✗'}
                        </Badge>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button
                        size="sm"
                        className="flex-1 bg-green-600 hover:bg-green-700"
                        onClick={() => handleValidateUser(member.id)}
                      >
                        <CheckCircle className="w-4 h-4 mr-1" />
                        Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="outline"
                        className="flex-1 text-red-600 hover:bg-red-50"
                        onClick={() => handleRejectUser(member.id)}
                      >
                        <XCircle className="w-4 h-4 mr-1" />
                        Reject
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Validated Team Members */}
        <div>
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Team Members</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {users.map((member) => (
              <Card key={member.id} className="hover:shadow-lg transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-start gap-4 flex-1 min-w-0">
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
                        <h3 className="font-semibold text-slate-900 text-lg truncate" title={member.name}>
                          {member.name}
                        </h3>
                        <div className="flex flex-wrap gap-2 mt-2">
                          {member.is_owner && (
                            <Badge className="bg-purple-100 text-purple-800">
                              <Shield className="w-3 h-3 mr-1" />
                              Owner
                            </Badge>
                          )}
                          {member.is_admin && !member.is_owner && (
                            <Badge className="bg-red-100 text-red-800">
                              <Shield className="w-3 h-3 mr-1" />
                              Admin
                            </Badge>
                          )}
                          <Badge className={`${getRoleBadgeColor(member.role)}`}>
                            {member.role.replace('_', ' ')}
                          </Badge>
                        </div>
                      </div>
                    </div>
                    {isOwner && !member.is_owner && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50 ml-2"
                        onClick={() => {
                          setSelectedUser(member);
                          setDeleteDialogOpen(true);
                        }}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    )}
                  </div>

                  <div className="space-y-2 text-sm">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Mail className="w-4 h-4 flex-shrink-0" />
                      <span className="truncate">{member.email}</span>
                    </div>
                    {member.mobile && (
                      <div className="flex items-center gap-2 text-slate-600">
                        <Phone className="w-4 h-4 flex-shrink-0" />
                        <span>{member.mobile}</span>
                      </div>
                    )}
                    {member.postal_address && (
                      <div className="flex items-start gap-2 text-slate-600">
                        <MapPin className="w-4 h-4 flex-shrink-0 mt-0.5" />
                        <span className="text-xs line-clamp-2">{member.postal_address}</span>
                      </div>
                    )}
                    <div className="flex items-center gap-2 text-slate-500">
                      <Calendar className="w-4 h-4 flex-shrink-0" />
                      <span>Joined {new Date(member.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  {/* Admin Rights Toggle - Owner Only */}
                  {isOwner && !member.is_owner && (
                    <div className="mt-4 pt-4 border-t border-slate-200">
                      <Button
                        size="sm"
                        variant={member.is_admin ? 'outline' : 'default'}
                        className="w-full"
                        onClick={() => handleToggleAdmin(member.id, member.is_admin)}
                      >
                        <Shield className="w-4 h-4 mr-2" />
                        {member.is_admin ? 'Revoke Admin' : 'Make Administrator'}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>

        {/* Delete Confirmation Dialog */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete Team Member</AlertDialogTitle>
              <AlertDialogDescription>
                Are you sure you want to delete <strong>{selectedUser?.name}</strong>? This action cannot be undone and will remove all their data from the system.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDeleteUser}
                className="bg-red-600 hover:bg-red-700"
              >
                Delete Member
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>

        {users.length === 0 && pendingUsers.length === 0 && (
          <div className="text-center py-12">
            <UserCircle2 className="w-16 h-16 text-slate-300 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No team members yet</h3>
            <p className="text-slate-500">Waiting for team members to register</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
