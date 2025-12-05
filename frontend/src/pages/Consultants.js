import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Plus, UserCheck, Phone, Mail, Edit, Trash2, Briefcase } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CONSULTANT_TYPES = [
  "Structure", "Landscape", "Plumbing", "Electrical", 
  "Air Conditioning", "Styling", "Green", "Other"
];

export default function Consultants({ user, onLogout }) {
  const [consultants, setConsultants] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingConsultant, setEditingConsultant] = useState(null);
  const [inviteForm, setInviteForm] = useState({
    name: '',
    phone: ''
  });
  const [formData, setFormData] = useState({
    name: '',
    type: '',
    company_name: '',
    email: '',
    phone: '',
    alternate_phone: '',
    address: '',
    specialization: '',
    license_number: '',
    notes: ''
  });

  useEffect(() => {
    fetchConsultants();
  }, []);

  const fetchConsultants = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/consultants`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setConsultants(response.data);
    } catch (error) {
      console.error('Error fetching consultants:', error);
      toast.error('Failed to load consultants');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteConsultant = async (e) => {
    e.preventDefault();
    
    if (!inviteForm.name || !inviteForm.phone) {
      toast.error('Please enter name and phone number');
      return;
    }

    const phoneRegex = /^\+?[1-9]\d{9,14}$/;
    if (!phoneRegex.test(inviteForm.phone.replace(/\s/g, ''))) {
      toast.error('Please enter a valid phone number with country code (e.g., +919876543210)');
      return;
    }

    try:
      await axios.post(`${API}/invite/send`, null, {
        params: {
          name: inviteForm.name,
          phone: inviteForm.phone,
          invitee_type: 'consultant'
        }
      });
      
      toast.success(`WhatsApp invite sent to ${inviteForm.name}!`, { duration: 5000 });
      setInviteDialogOpen(false);
      setInviteForm({ name: '', phone: '' });
    } catch (error) {
      console.error('Invite error:', error);
      toast.error(error.response?.data?.detail || 'Failed to send invite');
    }
  };

  const handleOpenEditDialog = (consultant) => {
    setEditingConsultant(consultant);
    setFormData({
      name: consultant.name || '',
      type: consultant.type || '',
      company_name: consultant.company_name || '',
      email: consultant.email || '',
      phone: consultant.phone || '',
      alternate_phone: consultant.alternate_phone || '',
      address: consultant.address || '',
      specialization: consultant.specialization || '',
      license_number: consultant.license_number || '',
      notes: consultant.notes || ''
    });
    setEditDialogOpen(true);
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.type) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      const token = localStorage.getItem('token');
      
      await axios.put(`${API}/consultants/${editingConsultant.id}`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Consultant updated successfully');
      
      setEditDialogOpen(false);
      fetchConsultants();
    } catch (error) {
      console.error('Error saving consultant:', error);
      toast.error('Failed to save consultant');
    }
  };

  const handleDelete = async (consultantId) => {
    if (!window.confirm('Are you sure you want to delete this consultant?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/consultants/${consultantId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Consultant deleted successfully');
      fetchConsultants();
    } catch (error) {
      console.error('Error deleting consultant:', error);
      toast.error('Failed to delete consultant');
    }
  };

  // Group consultants by type
  const groupedConsultants = CONSULTANT_TYPES.reduce((acc, type) => {
    acc[type] = consultants.filter(c => c.type === type);
    return acc;
  }, {});

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="space-y-6 p-6">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Consultants</h1>
            <p className="text-slate-600 mt-1">Manage your project consultants and specialists</p>
          </div>
          <Button onClick={() => setInviteDialogOpen(true)} className="bg-blue-500 hover:bg-blue-600">
            <Plus className="w-4 h-4 mr-2" />
            Invite Consultant
          </Button>
        </div>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
          </div>
        ) : (
          <div className="grid gap-6">
            {CONSULTANT_TYPES.map(type => {
              const typeConsultants = groupedConsultants[type] || [];
              if (typeConsultants.length === 0) return null;

              return (
                <Card key={type}>
                  <CardHeader className="bg-gradient-to-r from-indigo-50 to-purple-50">
                    <CardTitle className="flex items-center gap-2">
                      <Briefcase className="w-5 h-5 text-indigo-600" />
                      {type} Consultants
                      <span className="ml-2 px-2 py-1 text-xs bg-indigo-600 text-white rounded-full">
                        {typeConsultants.length}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-6">
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {typeConsultants.map(consultant => (
                        <Card key={consultant.id} className="border-l-4 border-l-indigo-500">
                          <CardContent className="p-4">
                            <div className="flex justify-between items-start mb-3">
                              <div className="flex-1">
                                <h3 className="font-semibold text-lg text-slate-900">{consultant.name}</h3>
                                {consultant.company_name && (
                                  <p className="text-sm text-slate-600">{consultant.company_name}</p>
                                )}
                                {consultant.specialization && (
                                  <p className="text-xs text-indigo-600 mt-1">{consultant.specialization}</p>
                                )}
                              </div>
                              <div className="flex gap-1">
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleOpenEditDialog(consultant)}
                                >
                                  <Edit className="w-4 h-4" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDelete(consultant.id)}
                                  className="text-red-600 hover:text-red-700"
                                >
                                  <Trash2 className="w-4 h-4" />
                                </Button>
                              </div>
                            </div>
                            
                            <div className="space-y-2 text-sm">
                              {consultant.email && (
                                <div className="flex items-center gap-2 text-slate-600">
                                  <Mail className="w-4 h-4" />
                                  <span>{consultant.email}</span>
                                </div>
                              )}
                              {consultant.phone && (
                                <div className="flex items-center gap-2 text-slate-600">
                                  <Phone className="w-4 h-4" />
                                  <span>{consultant.phone}</span>
                                </div>
                              )}
                              {consultant.license_number && (
                                <div className="flex items-center gap-2 text-slate-600">
                                  <UserCheck className="w-4 h-4" />
                                  <span className="text-xs">License: {consultant.license_number}</span>
                                </div>
                              )}
                            </div>
                            
                            {consultant.notes && (
                              <p className="mt-3 text-xs text-slate-500 italic border-t pt-2">
                                {consultant.notes}
                              </p>
                            )}
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              );
            })}
            
            {consultants.length === 0 && (
              <Card>
                <CardContent className="p-12 text-center">
                  <Briefcase className="w-16 h-16 mx-auto text-slate-300 mb-4" />
                  <h3 className="text-lg font-medium text-slate-900 mb-2">No consultants yet</h3>
                  <p className="text-slate-600 mb-4">Start by adding your first consultant</p>
                  <Button onClick={() => handleOpenDialog()}>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Consultant
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Add/Edit Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingConsultant ? 'Edit Consultant' : 'Add New Consultant'}
              </DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit}>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name">Name *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="type">Type *</Label>
                    <select
                      id="type"
                      value={formData.type}
                      onChange={(e) => setFormData({...formData, type: e.target.value})}
                      className="w-full h-10 px-3 rounded-md border border-input bg-background"
                      required
                    >
                      <option value="">Select Type</option>
                      {CONSULTANT_TYPES.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="company_name">Company Name</Label>
                    <Input
                      id="company_name"
                      value={formData.company_name}
                      onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="specialization">Specialization</Label>
                    <Input
                      id="specialization"
                      value={formData.specialization}
                      onChange={(e) => setFormData({...formData, specialization: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="email">Email</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="phone">Phone</Label>
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="alternate_phone">Alternate Phone</Label>
                    <Input
                      id="alternate_phone"
                      value={formData.alternate_phone}
                      onChange={(e) => setFormData({...formData, alternate_phone: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="license_number">License Number</Label>
                    <Input
                      id="license_number"
                      value={formData.license_number}
                      onChange={(e) => setFormData({...formData, license_number: e.target.value})}
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="address">Address</Label>
                  <Input
                    id="address"
                    value={formData.address}
                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                  />
                </div>

                <div>
                  <Label htmlFor="notes">Notes</Label>
                  <textarea
                    id="notes"
                    value={formData.notes}
                    onChange={(e) => setFormData({...formData, notes: e.target.value})}
                    className="w-full min-h-[80px] px-3 py-2 rounded-md border border-input bg-background"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingConsultant ? 'Update' : 'Add'} Consultant
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
