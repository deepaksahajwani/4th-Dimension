import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from '@/components/ui/alert-dialog';
import { ArrowLeft, Edit, Trash2, Plus, User, DollarSign, FileText } from 'lucide-react';
import { toast } from 'sonner';
import { formatErrorMessage } from '@/utils/errorHandler';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const TEAM_ROLES = [
  { value: 'junior_architect', label: 'Junior Architect' },
  { value: 'senior_architect', label: 'Senior Architect' },
  { value: 'associate_architect', label: 'Associate Architect' },
  { value: 'junior_interior_designer', label: 'Junior Interior Designer' },
  { value: 'senior_interior_designer', label: 'Senior Interior Designer' },
  { value: 'associate_interior_designer', label: 'Associate Interior Designer' },
  { value: 'landscape_designer', label: 'Landscape Designer' },
  { value: '3d_visualizer', label: '3D Visualizer' },
  { value: 'site_engineer', label: 'Site Engineer' },
  { value: 'site_supervisor', label: 'Site Supervisor' },
  { value: 'intern', label: 'Intern' },
  { value: 'administrator', label: 'Administrator' },
  { value: 'human_resource', label: 'Human Resource' },
  { value: 'accountant', label: 'Accountant' },
  { value: 'office_staff', label: 'Office Staff' }
];

export default function ManageTeam({ user, onLogout }) {
  const navigate = useNavigate();
  const [teamMembers, setTeamMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedMember, setSelectedMember] = useState(null);
  const [formData, setFormData] = useState({});

  useEffect(() => {
    if (!user?.is_owner) {
      toast.error('Access denied');
      navigate('/team');
      return;
    }
    fetchTeamMembers();
  }, []);

  const fetchTeamMembers = async () => {
    try {
      const response = await axios.get(`${API}/users`);
      setTeamMembers(response.data);
    } catch (error) {
      toast.error('Failed to load team members');
    } finally {
      setLoading(false);
    }
  };

  const handleEdit = (member) => {
    setSelectedMember(member);
    setFormData({
      full_name: member.name,
      address_line_1: member.address_line_1 || '',
      address_line_2: member.address_line_2 || '',
      landmark: member.landmark || '',
      city: member.city || '',
      state: member.state || '',
      pin_code: member.pin_code || '',
      mobile: member.mobile || '',
      date_of_birth: member.date_of_birth ? member.date_of_birth.split('T')[0] : '',
      date_of_joining: member.date_of_joining ? member.date_of_joining.split('T')[0] : '',
      gender: member.gender || 'male',
      marital_status: member.marital_status || 'single',
      role: member.role,
      salary: member.salary || '',
      writeup: member.writeup || '',
      passions: member.passions || '',
      contribution: member.contribution || ''
    });
    setEditDialogOpen(true);
  };

  const handleDelete = (member) => {
    console.log('handleDelete called for:', member.name);
    setSelectedMember(member);
    setDeleteDialogOpen(true);
  };

  const handleSave = async () => {
    try {
      await axios.put(`${API}/users/${selectedMember.id}`, formData);
      toast.success('Team member updated successfully');
      setEditDialogOpen(false);
      fetchTeamMembers();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to update team member'));
    }
  };

  const confirmDelete = async () => {
    try {
      await axios.delete(`${API}/users/${selectedMember.id}`);
      toast.success('Team member removed');
      setDeleteDialogOpen(false);
      fetchTeamMembers();
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to delete team member'));
    }
  };

  const handleAddMember = () => {
    navigate('/register-info');
  };

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex items-center justify-center h-64">
          <p className="text-slate-500">Loading...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              onClick={() => navigate('/team')}
            >
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-slate-900">Manage Team</h1>
              <p className="text-slate-600 mt-1">Edit team member details and information</p>
            </div>
          </div>
          <Button onClick={handleAddMember} className="bg-orange-500 hover:bg-orange-600">
            <Plus className="w-4 h-4 mr-2" />
            Add Member
          </Button>
        </div>

        {/* Team Members List */}
        <div className="grid gap-4">
          {teamMembers.map((member) => (
            <Card key={member.id}>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 bg-gradient-to-br from-orange-400 to-orange-600 rounded-full flex items-center justify-center text-white text-lg font-bold">
                      {member.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold text-slate-900">{member.name}</h3>
                      <p className="text-sm text-slate-600">{member.role.replace(/_/g, ' ')}</p>
                      {member.salary && (
                        <p className="text-sm text-green-600 font-medium">₹{member.salary.toLocaleString()}/month</p>
                      )}
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleEdit(member)}
                    >
                      <Edit className="w-4 h-4 mr-1" />
                      Edit
                    </Button>
                    {!member.is_owner && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleDelete(member)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </Button>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Edit Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Team Member</DialogTitle>
            </DialogHeader>
            <div className="space-y-6 py-4">
              {/* Basic Info */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900">Basic Information</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Full Name</Label>
                    <Input
                      value={formData.full_name}
                      onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Email (Read-only)</Label>
                    <Input value={selectedMember?.email} disabled />
                  </div>
                  <div>
                    <Label>Mobile</Label>
                    <Input
                      value={formData.mobile}
                      onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Team Role</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    >
                      {TEAM_ROLES.map(role => (
                        <option key={role.value} value={role.value}>{role.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label>Date of Birth</Label>
                    <Input
                      type="date"
                      value={formData.date_of_birth}
                      onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Date of Joining</Label>
                    <Input
                      type="date"
                      value={formData.date_of_joining}
                      onChange={(e) => setFormData({ ...formData, date_of_joining: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Gender</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.gender}
                      onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                    >
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <Label>Marital Status</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.marital_status}
                      onChange={(e) => setFormData({ ...formData, marital_status: e.target.value })}
                    >
                      <option value="single">Single</option>
                      <option value="married">Married</option>
                      <option value="divorced">Divorced</option>
                      <option value="widowed">Widowed</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Address */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900">Address</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Address Line 1</Label>
                    <Input
                      value={formData.address_line_1}
                      onChange={(e) => setFormData({ ...formData, address_line_1: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Address Line 2</Label>
                    <Input
                      value={formData.address_line_2}
                      onChange={(e) => setFormData({ ...formData, address_line_2: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Landmark</Label>
                    <Input
                      value={formData.landmark}
                      onChange={(e) => setFormData({ ...formData, landmark: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>City</Label>
                    <Input
                      value={formData.city}
                      onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>State</Label>
                    <Input
                      value={formData.state}
                      onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>PIN Code</Label>
                    <Input
                      value={formData.pin_code}
                      onChange={(e) => setFormData({ ...formData, pin_code: e.target.value })}
                    />
                  </div>
                </div>
              </div>

              {/* Salary */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <DollarSign className="w-5 h-5 text-green-600" />
                  Salary (Confidential)
                </h3>
                <div>
                  <Label>Monthly Salary (₹)</Label>
                  <Input
                    type="number"
                    placeholder="e.g., 50000"
                    value={formData.salary}
                    onChange={(e) => setFormData({ ...formData, salary: parseFloat(e.target.value) || '' })}
                  />
                </div>
              </div>

              {/* Profile Info */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-orange-600" />
                  Profile Information (Visible to all)
                </h3>
                <div>
                  <Label>Brief Writeup</Label>
                  <textarea
                    className="flex min-h-[100px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                    placeholder="Write a brief introduction about this team member..."
                    value={formData.writeup}
                    onChange={(e) => setFormData({ ...formData, writeup: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Passions & Hobbies</Label>
                  <textarea
                    className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                    placeholder="What are their passions and hobbies?"
                    value={formData.passions}
                    onChange={(e) => setFormData({ ...formData, passions: e.target.value })}
                  />
                </div>
                <div>
                  <Label>Contribution to Firm</Label>
                  <textarea
                    className="flex min-h-[100px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                    placeholder="Describe their contribution to the growth of the firm..."
                    value={formData.contribution}
                    onChange={(e) => setFormData({ ...formData, contribution: e.target.value })}
                  />
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setEditDialogOpen(false)}>Cancel</Button>
              <Button onClick={handleSave} className="bg-orange-500 hover:bg-orange-600">Save Changes</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* Delete Confirmation */}
        <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Are you sure?</AlertDialogTitle>
              <AlertDialogDescription>
                This will permanently delete {selectedMember?.name} from the team. This action cannot be undone.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction onClick={confirmDelete} className="bg-red-600 hover:bg-red-700">
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </Layout>
  );
}
