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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ROLE_LABELS = {
  client: 'Client',
  team_member: 'Office Team Member',
  contractor: 'Contractor',
  vendor: 'Vendor',
  consultant: 'Consultant'
};

// Specific roles for team members (complete list)
const TEAM_MEMBER_ROLES = {
  senior_architect: 'Senior Architect',
  senior_interior_designer: 'Senior Interior Designer',
  associate_architect: 'Associate Architect',
  associate_interior_designer: 'Associate Interior Designer',
  junior_architect: 'Junior Architect',
  junior_interior_designer: 'Junior Interior Designer',
  architect: 'Architect',
  interior_designer: 'Interior Designer',
  landscape_designer: 'Landscape Designer',
  '3d_visualizer': '3D Visualizer',
  drafter: 'Drafter',
  site_engineer: 'Site Engineer',
  site_supervisor: 'Site Supervisor',
  project_manager: 'Project Manager',
  team_leader: 'Team Leader',
  intern: 'Intern',
  administrator: 'Administrator',
  human_resource: 'Human Resource',
  accountant: 'Accountant',
  office_staff: 'Office Staff',
  team_member: 'Team Member (General)'
};

// Specific roles for contractors
const CONTRACTOR_ROLES = {
  civil_contractor: 'Civil Contractor',
  electrical_contractor: 'Electrical Contractor',
  plumbing_contractor: 'Plumbing Contractor',
  hvac_contractor: 'HVAC Contractor',
  structural_contractor: 'Structural Contractor',
  interior_contractor: 'Interior Contractor',
  painting_contractor: 'Painting Contractor',
  flooring_contractor: 'Flooring Contractor',
  contractor: 'Contractor (General)'
};

// Specific roles for consultants
const CONSULTANT_ROLES = {
  structural_consultant: 'Structural Consultant',
  mep_consultant: 'MEP Consultant',
  electrical_consultant: 'Electrical Consultant',
  plumbing_consultant: 'Plumbing Consultant',
  landscape_consultant: 'Landscape Consultant',
  interior_consultant: 'Interior Design Consultant',
  sustainability_consultant: 'Sustainability Consultant',
  fire_safety_consultant: 'Fire Safety Consultant',
  consultant: 'Consultant (General)'
};

export default function PendingRegistrations({ user, onLogout }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState(null);
  const [actionType, setActionType] = useState(null); // 'approve' or 'reject'
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedRole, setSelectedRole] = useState('');
  const [showProjectPrompt, setShowProjectPrompt] = useState(false);
  const [approvedClient, setApprovedClient] = useState(null);

  useEffect(() => {
    if (user?.role !== 'owner') {
      toast.error('Access denied. Owner only.');
      navigate('/dashboard');
      return;
    }
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
    setSelectedRole(user.role); // Default to current role
    setDialogOpen(true);
  };

  const handleRejectClick = (user) => {
    setSelectedUser(user);
    setActionType('reject');
    setDialogOpen(true);
  };

  const handlePromptDismiss = async () => {
    // Send notification to client now that owner has made a decision
    if (approvedClient) {
      try {
        await axios.post(`${API}/auth/send-approval-notification`, null, {
          params: { user_id: approvedClient.id }
        });
        console.log('Approval notification sent to:', approvedClient.name);
      } catch (error) {
        console.error('Failed to send notification:', error);
        // Non-critical error, don't show to user
      }
      setApprovedClient(null);
    }
  };

  const confirmAction = async () => {
    if (!selectedUser || !actionType) return;

    // For clients/vendors, role assignment is not needed
    const needsRoleSelection = selectedUser.role === 'team_member' || selectedUser.role === 'contractor' || selectedUser.role === 'consultant';
    
    // Validate role selection for approval (only for team members, contractors, consultants)
    if (actionType === 'approve' && needsRoleSelection && !selectedRole) {
      toast.error('Please select a specific role for the user');
      return;
    }

    const userIdToRemove = selectedUser.id;
    const userName = selectedUser.name;
    
    // For clients and vendors, use their registration role as-is
    const finalRole = needsRoleSelection ? selectedRole : selectedUser.role;

    try {
      // Close dialog immediately for better UX
      setDialogOpen(false);
      
      await axios.post(`${API}/auth/approve-user-dashboard`, null, {
        params: {
          user_id: userIdToRemove,
          action: actionType,
          role: actionType === 'approve' ? finalRole : undefined
        }
      });

      // Immediately remove the user from the UI
      setPendingUsers(prevUsers => {
        const filtered = prevUsers.filter(u => u.id !== userIdToRemove);
        console.log('Removing user:', userIdToRemove, 'Remaining:', filtered.length);
        return filtered;
      });

      if (actionType === 'approve') {
        toast.success(`${userName} has been approved as ${getRoleLabel(finalRole)}!`);
        
        // If approved user is a client, show project creation prompt
        if (selectedUser.role === 'client') {
          setApprovedClient({
            id: userIdToRemove,
            name: userName,
            email: selectedUser.email
          });
          setShowProjectPrompt(true);
        }
      } else {
        toast.success(`${userName}'s registration has been rejected`);
      }
      
      setSelectedUser(null);
      setActionType(null);
      setSelectedRole('');
    } catch (error) {
      console.error('Action error:', error);
      toast.error(error.response?.data?.detail || `Failed to ${actionType} user`);
      setDialogOpen(false);
      setSelectedUser(null);
      setActionType(null);
      setSelectedRole('');
    }
  };

  // Helper function to get role label
  const getRoleLabel = (role) => {
    return TEAM_MEMBER_ROLES[role] || CONTRACTOR_ROLES[role] || CONSULTANT_ROLES[role] || role;
  };

  // Get available roles based on user type
  const getAvailableRoles = (userRole) => {
    if (userRole === 'team_member') {
      return TEAM_MEMBER_ROLES;
    } else if (userRole === 'contractor') {
      return CONTRACTOR_ROLES;
    } else if (userRole === 'consultant') {
      return CONSULTANT_ROLES;
    }
    return {};
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

        {/* Project Creation Prompt Dialog (After Client Approval) */}
        <AlertDialog open={showProjectPrompt} onOpenChange={(open) => {
          if (!open) {
            handlePromptDismiss();
          }
          setShowProjectPrompt(open);
        }}>
          <AlertDialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>✅ Client Approved Successfully!</DialogTitle>
              <p className="text-slate-600 mt-2">
                <strong>{approvedClient?.name}</strong> has been approved as a client.
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-3">
                <p className="text-sm text-blue-900 font-medium mb-2">
                  Would you like to create their project now?
                </p>
                <p className="text-xs text-blue-700">
                  Creating a project immediately will give them something to see when they log in.
                </p>
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mt-2">
                <p className="text-xs text-amber-800">
                  <strong>Note:</strong> Approval notification will be sent after you make a choice. Until a project is created, they'll see a professional welcome screen.
                </p>
              </div>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={async () => {
                  await handlePromptDismiss();
                  setShowProjectPrompt(false);
                }}
              >
                I'll Do It Later
              </Button>
              <Button
                onClick={async () => {
                  await handlePromptDismiss();
                  setShowProjectPrompt(false);
                  // Navigate to projects page with client pre-selected
                  navigate('/projects', { 
                    state: { 
                      createProject: true, 
                      preSelectedClient: approvedClient,
                      returnTo: '/pending-registrations'
                    } 
                  });
                }}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Create Project Now
              </Button>
            </DialogFooter>
          </DialogContent>
        </AlertDialog>

        {/* Confirmation Dialog */}
        <AlertDialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <AlertDialogContent className="max-w-md">
            <AlertDialogHeader>
              <AlertDialogTitle>
                {actionType === 'approve' ? 'Approve Registration' : 'Reject Registration?'}
              </AlertDialogTitle>
              <AlertDialogDescription asChild>
                <div>
                  {actionType === 'approve' ? (
                    <>
                      {/* For clients and vendors - simple approval */}
                      {selectedUser?.role === 'client' || selectedUser?.role === 'vendor' ? (
                        <>
                          <p className="mb-4">
                            Approve <strong>{selectedUser?.name}</strong> as a <strong>{ROLE_LABELS[selectedUser?.role]}</strong>?
                          </p>
                          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
                            <p className="text-sm text-blue-800">
                              ✓ They will have access to their projects and can view/comment on drawings.
                            </p>
                          </div>
                          <p className="text-sm text-slate-600">
                            They will receive an email notification and can log in immediately.
                          </p>
                        </>
                      ) : (
                        /* For team members, contractors, consultants - role selection needed */
                        <>
                          <p className="mb-4">
                            Approve <strong>{selectedUser?.name}</strong> and assign their specific role.
                          </p>
                          
                          {/* Role Selection */}
                          <div className="space-y-3 mb-4">
                            <Label htmlFor="role-select" className="text-sm font-medium text-slate-900">
                              Assign Specific Role *
                            </Label>
                            <Select value={selectedRole} onValueChange={setSelectedRole}>
                              <SelectTrigger id="role-select" className="w-full">
                                <SelectValue placeholder="Select role..." />
                              </SelectTrigger>
                              <SelectContent>
                                {Object.entries(getAvailableRoles(selectedUser?.role)).map(([key, label]) => (
                                  <SelectItem key={key} value={key}>
                                    {label}
                                  </SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                            <p className="text-xs text-slate-500">
                              This will help track their responsibilities and appear on their profile.
                            </p>
                          </div>

                          <p className="text-sm text-slate-600">
                            They will receive an email notification and can log in immediately.
                          </p>
                        </>
                      )}
                    </>
                  ) : (
                    <>
                      <p>
                        Are you sure you want to reject <strong>{selectedUser?.name}</strong>'s registration?
                      </p>
                      <p className="mt-2 text-sm text-slate-600">
                        They will receive an email notification about the rejection.
                      </p>
                    </>
                  )}
                </div>
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel onClick={() => setSelectedRole('')}>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={confirmAction}
                className={actionType === 'approve' ? 'bg-green-600 hover:bg-green-700' : 'bg-red-600 hover:bg-red-700'}
              >
                {actionType === 'approve' 
                  ? (selectedUser?.role === 'client' || selectedUser?.role === 'vendor' ? 'Approve' : 'Approve & Assign')
                  : 'Reject'}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </Layout>
  );
}
