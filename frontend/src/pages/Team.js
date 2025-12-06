import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Users, Settings as SettingsIcon, UserPlus, CheckCircle, Clock, XCircle } from 'lucide-react';
import PhoneInput, { combinePhoneNumber } from '@/components/PhoneInput';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Role hierarchy for grouping and display order
const ROLE_HIERARCHY = {
  owner: 0,
  senior_architect: 1,
  junior_architect: 2,
  '3d_visualizer': 3,
  senior_interior_designer: 4,
  junior_interior_designer: 5,
  landscape_designer: 6,
  associate_architect: 7,
  associate_interior_designer: 7,
  site_engineer: 8,
  site_supervisor: 8,
  intern: 9,
  administrator: 10,
  human_resource: 10,
  accountant: 10,
  office_staff: 11
};

const ROLE_LABELS = {
  owner: 'Principal Architect',
  senior_architect: 'Senior Architect',
  senior_interior_designer: 'Senior Interior Designer',
  associate_architect: 'Associate Architect',
  associate_interior_designer: 'Associate Interior Designer',
  junior_architect: 'Junior Architect',
  junior_interior_designer: 'Junior Interior Designer',
  landscape_designer: 'Landscape Designer',
  '3d_visualizer': '3D Visualizer',
  site_engineer: 'Site Engineer',
  site_supervisor: 'Site Supervisor',
  intern: 'Intern',
  administrator: 'Administrator',
  human_resource: 'Human Resource',
  accountant: 'Accountant',
  office_staff: 'Office Staff'
};

export default function Team({ user, onLogout }) {
  const navigate = useNavigate();
  const [teamMembers, setTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [inviting, setInviting] = useState(false);
  const [inviteForm, setInviteForm] = useState({
    name: '',
    phone: '',
    invitee_type: 'team_member'
  });

  useEffect(() => {
    fetchTeamMembers();
  }, []);

  const fetchTeamMembers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      
      // Separate owner from other members
      const owner = response.data.find(m => m.is_owner || m.email === 'deepaksahajwani@gmail.com');
      const otherMembers = response.data.filter(m => !m.is_owner && m.email !== 'deepaksahajwani@gmail.com');
      
      // Sort other members: first by role hierarchy, then by joining date within each role
      const sortedOthers = otherMembers.sort((a, b) => {
        const roleA = ROLE_HIERARCHY[a.role] || 99;
        const roleB = ROLE_HIERARCHY[b.role] || 99;
        
        // If different roles, sort by role hierarchy
        if (roleA !== roleB) {
          return roleA - roleB;
        }
        
        // Same role - sort by joining date (earliest first)
        const dateA = new Date(a.date_of_joining || a.created_at);
        const dateB = new Date(b.date_of_joining || b.created_at);
        return dateA - dateB;
      });
      
      // Put owner first, then others
      const finalList = owner ? [owner, ...sortedOthers] : sortedOthers;
      setTeamMembers(finalList);
    } catch (error) {
      toast.error('Failed to load team members');
    } finally {
      setLoading(false);
    }
  };

  // Group members by role while preserving the sort order
  const groupedMembers = {};
  const roleOrder = []; // Track the order roles appear in the sorted list
  
  teamMembers.forEach(member => {
    const role = member.role;
    if (!groupedMembers[role]) {
      groupedMembers[role] = [];
      roleOrder.push(role);
    }
    groupedMembers[role].push(member);
  });
  
  // Use roleOrder (which preserves the intended sort) instead of re-sorting by hierarchy
  const sortedRoleGroups = roleOrder;

  const handleMemberClick = (memberId) => {
    navigate(`/team/${memberId}`);
  };

  const handleManageTeam = () => {
    navigate('/team/manage');
  };

  const handleInviteTeamMember = async (e) => {
    e.preventDefault();
    
    if (!inviteForm.name || !inviteForm.phone) {
      toast.error('Please enter name and phone number');
      return;
    }

    // Validate phone number format
    const phoneRegex = /^\+?[1-9]\d{9,14}$/;
    if (!phoneRegex.test(inviteForm.phone.replace(/\s/g, ''))) {
      toast.error('Please enter a valid phone number with country code (e.g., +919876543210)');
      return;
    }

    setInviting(true);
    try {
      await axios.post(`${API}/invite/send`, null, {
        params: {
          name: inviteForm.name,
          phone: inviteForm.phone,
          invitee_type: inviteForm.invitee_type
        }
      });
      
      const typeLabels = {
        'team_member': 'team member',
        'client': 'client',
        'contractor': 'contractor',
        'consultant': 'consultant'
      };
      
      toast.success(`WhatsApp invite sent to ${inviteForm.name} (${typeLabels[inviteForm.invitee_type]})!`, {
        duration: 5000
      });
      
      setInviteDialogOpen(false);
      setInviteForm({ name: '', phone: '', invitee_type: 'team_member' });
    } catch (error) {
      console.error('Invite error:', error);
      toast.error(error.response?.data?.detail || 'Failed to send invite');
    } finally {
      setInviting(false);
    }
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <p className="text-slate-500">Loading team...</p>
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
            <h1 className="text-3xl font-bold text-slate-900">Our Team</h1>
            <p className="text-slate-600 mt-1">Meet the talented people behind 4th Dimension</p>
          </div>
          {user?.is_owner && (
            <div className="flex gap-2">
              <Button onClick={() => setInviteDialogOpen(true)} className="bg-indigo-600 hover:bg-indigo-700">
                <UserPlus className="w-4 h-4 mr-2" />
                Invite Member
              </Button>
              <Button onClick={handleManageTeam} className="bg-orange-500 hover:bg-orange-600">
                <SettingsIcon className="w-4 h-4 mr-2" />
                Manage Team
              </Button>
            </div>
          )}
        </div>

        {/* Team Members Grid */}
        <div className="space-y-8">
          {sortedRoleGroups.map((role) => (
            <div key={role}>
              {/* Role section header (optional - can be removed if you don't want section titles) */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {groupedMembers[role].map((member) => (
                  <Card
                    key={member.id}
                    className="cursor-pointer hover:shadow-lg transition-shadow"
                    onClick={() => handleMemberClick(member.id)}
                  >
                    <CardContent className="p-6 text-center relative">
                      {/* Verification Status Badge */}
                      {member.email_verified && member.mobile_verified ? (
                        <div className="absolute top-2 right-2 bg-green-100 text-green-700 px-2 py-1 rounded-full text-xs flex items-center gap-1">
                          <CheckCircle className="w-3 h-3" />
                          Verified
                        </div>
                      ) : member.email_verified || member.mobile_verified ? (
                        <div className="absolute top-2 right-2 bg-yellow-100 text-yellow-700 px-2 py-1 rounded-full text-xs flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Partial
                        </div>
                      ) : member.is_validated ? null : (
                        <div className="absolute top-2 right-2 bg-orange-100 text-orange-700 px-2 py-1 rounded-full text-xs flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          Pending
                        </div>
                      )}
                      
                      <div className="w-20 h-20 mx-auto mb-4 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center text-white text-2xl font-bold">
                        {member.name.charAt(0).toUpperCase()}
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-1">
                        {member.name}
                      </h3>
                      <p className="text-sm text-slate-600">
                        {ROLE_LABELS[member.role] || member.role}
                      </p>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          ))}
        </div>

        {teamMembers.length === 0 && (
          <div className="text-center py-12">
            <Users className="w-16 h-16 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500">No team members yet</p>
          </div>
        )}
      </div>

      {/* Invite Person Dialog */}
      <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Send Registration Invite</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleInviteTeamMember}>
            <div className="space-y-4 py-4">
              <div>
                <Label htmlFor="invitee_type">Invite As *</Label>
                <select
                  id="invitee_type"
                  value={inviteForm.invitee_type}
                  onChange={(e) => setInviteForm({...inviteForm, invitee_type: e.target.value})}
                  className="w-full h-10 px-3 rounded-md border border-input bg-background"
                  required
                >
                  <option value="team_member">Team Member</option>
                  <option value="client">Client</option>
                  <option value="contractor">Contractor</option>
                  <option value="consultant">Consultant</option>
                </select>
                <p className="text-xs text-slate-500 mt-1">They will register with this role</p>
              </div>

              <div>
                <Label htmlFor="name">Full Name *</Label>
                <Input
                  id="name"
                  value={inviteForm.name}
                  onChange={(e) => setInviteForm({...inviteForm, name: e.target.value})}
                  placeholder="e.g., Priya Sharma"
                  required
                />
              </div>

              <div>
                <Label htmlFor="phone">Phone Number *</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={inviteForm.phone}
                  onChange={(e) => setInviteForm({...inviteForm, phone: e.target.value})}
                  placeholder="+919876543210"
                  required
                />
                <p className="text-xs text-slate-500 mt-1">Include country code (e.g., +91 for India)</p>
              </div>

              <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                <p className="text-sm text-green-800">
                  <strong>📱 What happens next:</strong>
                </p>
                <ul className="text-xs text-green-700 mt-2 space-y-1 ml-4 list-disc">
                  <li>Personalized WhatsApp invite sent instantly</li>
                  <li>Registration link included in message</li>
                  <li>They complete registration on their own</li>
                  <li>You approve their account after registration</li>
                </ul>
              </div>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setInviteDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={inviting} className="bg-indigo-600 hover:bg-indigo-700">
                {inviting ? 'Sending...' : 'Send Invite'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </Layout>
  );
}
