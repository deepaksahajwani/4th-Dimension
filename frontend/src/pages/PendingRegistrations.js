import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Users, CheckCircle, XCircle, Clock, Mail, Phone, MapPin, Briefcase } from 'lucide-react';
import { toast } from 'sonner';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/components/ui/alert-dialog';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ROLE_LABELS = {
  client: 'Client',
  team_member: 'Office Team Member',
  contractor: 'Contractor',
  vendor: 'Vendor',
  consultant: 'Consultant'
};

export default function PendingRegistrations({ user, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [actionType, setActionType] = useState(null); // 'approve' or 'reject'
  const [dialogOpen, setDialogOpen] = useState(false);

  useEffect(() => {
    // Temporarily bypass access control for testing
    console.log('User object:', user);
    console.log('User role:', user?.role);
    console.log('Is owner:', user?.is_owner);
    
    if (user?.role !== 'owner') {
      console.log('Access denied - user role is not owner');
      toast.error('Access denied. Owner only.');
      navigate('/dashboard');
      return;
    }
    console.log('Access granted - fetching pending registrations');
    fetchPendingRegistrations();
    
    // Check for success/error messages from URL params
    const params = new URLSearchParams(location.search);
    const successType = params.get('success');
    const userName = params.get('user');
    const error = params.get('error');
    
    if (successType === 'approved' && userName) {
      toast.success(`${decodeURIComponent(userName)} has been approved successfully!`, {
        duration: 5000
      });
      // Clean URL
      window.history.replaceState({}, '', '/pending-registrations');
    } else if (successType === 'rejected' && userName) {
      toast.info(`${decodeURIComponent(userName)}'s registration has been rejected.`, {
        duration: 5000
      });
      // Clean URL
      window.history.replaceState({}, '', '/pending-registrations');
    } else if (error) {
      toast.error('An error occurred during the approval process.');
      window.history.replaceState({}, '', '/pending-registrations');
    }
  }, [user, navigate, location]);

  const fetchPendingRegistrations = async () => {
    try {
      const response = await axios.get(`${API}/auth/pending-registrations`);
      setPendingUsers(response.data);
    } catch (error) {
      console.error('Error fetching pending registrations:', error);
      toast.error('Failed to load pending registrations');
    } finally {
      setLoading(false);
    }
  };

  const handleApproveClick = (user) => {
    setSelectedUser(user);
    setActionType('approve');
    setDialogOpen(true);
  };

  const handleRejectClick = (user) => {
    setSelectedUser(user);
    setActionType('reject');
    setDialogOpen(true);
  };

  const confirmAction = async () => {
    if (!selectedUser || !actionType) return;

    try {
      await axios.post(`${API}/auth/approve-user-dashboard`, null, {
        params: {
          user_id: selectedUser.id,
          action: actionType
        }
      });

      toast.success(
        actionType === 'approve' 
          ? `${selectedUser.name} has been approved!` 
          : `${selectedUser.name}'s registration has been rejected`
      );

      // Immediately remove the user from the UI
      setPendingUsers(prevUsers => prevUsers.filter(u => u.id !== selectedUser.id));
      
      setDialogOpen(false);
      setSelectedUser(null);
      setActionType(null);
    } catch (error) {
      console.error('Action error:', error);
      toast.error(error.response?.data?.detail || `Failed to ${actionType} user`);
    }
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <p className="text-slate-500">Loading pending registrations...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Pending Registrations</h1>
            <p className="text-slate-600 mt-1">
              Review and approve new user registrations
            </p>
          </div>
          <Badge variant="outline" className="text-lg px-4 py-2">
            <Clock className="w-4 h-4 mr-2" />
            {pendingUsers.length} Pending
          </Badge>
        </div>

        {/* No Pending Registrations */}
        {pendingUsers.length === 0 ? (
          <Card>
            <CardContent className="py-16 text-center">
              <Users className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-slate-900 mb-2">
                No Pending Registrations
              </h3>
              <p className="text-slate-600">
                All registrations have been reviewed. New registrations will appear here.
              </p>
            </CardContent>
          </Card>
        ) : (
          /* Pending Users List */
          <div className="space-y-4">
            {pendingUsers.map((pendingUser) => (
              <Card key={pendingUser.id} className="hover:shadow-lg transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="text-xl">{pendingUser.name}</CardTitle>
                      <Badge className="mt-2 bg-orange-100 text-orange-700 hover:bg-orange-100">
                        <Briefcase className="w-3 h-3 mr-1" />
                        {ROLE_LABELS[pendingUser.role] || pendingUser.role}
                      </Badge>
                    </div>
                    <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-300">
                      <Clock className="w-3 h-3 mr-1" />
                      Pending
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    {/* Contact Information */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-sm text-slate-600">
                        <Mail className="w-4 h-4 text-slate-400" />
                        <span>{pendingUser.email}</span>
                      </div>
                      {pendingUser.mobile && (
                        <div className="flex items-center gap-2 text-sm text-slate-600">
                          <Phone className="w-4 h-4 text-slate-400" />
                          <span>{pendingUser.mobile}</span>
                        </div>
                      )}
                    </div>

                    {/* Address */}
                    {pendingUser.address_line_1 && (
                      <div className="space-y-2">
                        <div className="flex items-start gap-2 text-sm text-slate-600">
                          <MapPin className="w-4 h-4 text-slate-400 mt-0.5" />
                          <div>
                            <div>{pendingUser.address_line_1}</div>
                            {pendingUser.address_line_2 && <div>{pendingUser.address_line_2}</div>}
                            <div>{pendingUser.city}, {pendingUser.state} - {pendingUser.pin_code}</div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Verification Status */}
                  <div className="flex items-center gap-3 mb-4 pb-4 border-b">
                    <Badge variant={pendingUser.email_verified ? 'default' : 'secondary'} className="text-xs">
                      {pendingUser.email_verified ? '✓ Email Verified' : '○ Email Not Verified'}
                    </Badge>
                    <Badge variant={pendingUser.mobile_verified ? 'default' : 'secondary'} className="text-xs">
                      {pendingUser.mobile_verified ? '✓ Phone Verified' : '○ Phone Not Verified'}
                    </Badge>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex gap-3">
                    <Button
                      onClick={() => handleApproveClick(pendingUser)}
                      className="flex-1 bg-green-600 hover:bg-green-700"
                    >
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Approve
                    </Button>
                    <Button
                      onClick={() => handleRejectClick(pendingUser)}
                      variant="outline"
                      className="flex-1 text-red-600 border-red-300 hover:bg-red-50"
                    >
                      <XCircle className="w-4 h-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Confirmation Dialog */}
        <AlertDialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>
                {actionType === 'approve' ? 'Approve Registration?' : 'Reject Registration?'}
              </AlertDialogTitle>
              <AlertDialogDescription>
                {actionType === 'approve' ? (
                  <>
                    Are you sure you want to approve <strong>{selectedUser?.name}</strong>'s registration?
                    <br /><br />
                    They will receive an email notification and will be able to log in immediately.
                  </>
                ) : (
                  <>
                    Are you sure you want to reject <strong>{selectedUser?.name}</strong>'s registration?
                    <br /><br />
                    They will receive an email notification about the rejection.
                  </>
                )}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmAction}
                className={actionType === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
              >
                {actionType === 'approve' ? 'Approve' : 'Reject'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </Layout>
  );
}
