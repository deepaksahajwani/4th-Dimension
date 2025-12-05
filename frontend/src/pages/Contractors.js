import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../components/Layout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../components/ui/dialog';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Plus, Building2, Phone, Mail, Edit, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CONTRACTOR_TYPES = [
  "Civil", "Plumbing", "Electrical", "Air Conditioning", 
  "Marble and Tile", "False Ceiling", "Furniture", "Modular", 
  "Kitchen", "Landscape", "Glass", "Profile", "Gardner", "Fabricator"
];

export default function Contractors({ user, onLogout }) {
  const [contractors, setContractors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingContractor, setEditingContractor] = useState(null);
  const [inviteForm, setInviteForm] = useState({
    name: '',
    phone: ''
  });
  const [formData, setFormData] = useState({
    name: '',
    contractor_type: '',
    company_name: '',
    email: '',
    phone: '',
    alternate_phone: '',
    address: '',
    gst_number: '',
    pan_number: '',
    notes: ''
  });

  useEffect(() => {
    fetchContractors();
  }, []);

  const fetchContractors = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/contractors`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setContractors(response.data);
    } catch (error) {
      toast.error('Failed to load contractors');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteContractor = async (e) => {
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

    try {
      await axios.post(`${API}/invite/send`, null, {
        params: {
          name: inviteForm.name,
          phone: inviteForm.phone,
          invitee_type: 'contractor'
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

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      
      await axios.put(`${API}/contractors/${editingContractor.id}`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Contractor updated successfully!');
      
      setEditDialogOpen(false);
      resetForm();
      fetchContractors();
    } catch (error) {
      toast.error('Failed to update contractor');
    }
  };

  const handleEdit = (contractor) => {
    setEditingContractor(contractor);
    setFormData({
      name: contractor.name || '',
      contractor_type: contractor.contractor_type || '',
      company_name: contractor.company_name || '',
      email: contractor.email || '',
      phone: contractor.phone || '',
      alternate_phone: contractor.alternate_phone || '',
      address: contractor.address || '',
      gst_number: contractor.gst_number || '',
      pan_number: contractor.pan_number || '',
      notes: contractor.notes || ''
    });
    setEditDialogOpen(true);
  };

  const handleDelete = async (contractorId) => {
    if (!window.confirm('Are you sure you want to delete this contractor?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/contractors/${contractorId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Contractor deleted successfully!');
      fetchContractors();
    } catch (error) {
      toast.error('Failed to delete contractor');
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      contractor_type: '',
      company_name: '',
      email: '',
      phone: '',
      alternate_phone: '',
      address: '',
      gst_number: '',
      pan_number: '',
      notes: ''
    });
    setEditingContractor(null);
  };

  const formatErrorMessage = (error, defaultMessage) => {
    if (error.response?.data?.detail) {
      if (Array.isArray(error.response.data.detail)) {
        return error.response.data.detail[0].msg;
      }
      return error.response.data.detail;
    }
    return defaultMessage;
  };

  // Group contractors by type
  const groupedContractors = contractors.reduce((acc, contractor) => {
    const type = contractor.contractor_type || 'Other';
    if (!acc[type]) acc[type] = [];
    acc[type].push(contractor);
    return acc;
  }, {});

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
      <div className="p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900">
              Contractors & Consultants
            </h1>
            <p className="text-sm text-slate-600 mt-1">
              Manage all contractors and consultants
            </p>
          </div>
          {user?.is_owner && (
            <Button
              onClick={() => setInviteDialogOpen(true)}
              className="bg-orange-500 hover:bg-orange-600"
            >
              <Plus className="w-4 h-4 mr-2" />
              Invite Contractor
            </Button>
          )}
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Total Contractors</p>
                  <p className="text-2xl font-bold text-slate-900">{contractors.length}</p>
                </div>
                <Building2 className="w-8 h-8 text-orange-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-600">Categories</p>
                  <p className="text-2xl font-bold text-slate-900">{Object.keys(groupedContractors).length}</p>
                </div>
                <Building2 className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Contractors by Category */}
        {Object.keys(groupedContractors).length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <Building2 className="w-16 h-16 text-slate-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">No Contractors Yet</h3>
              <p className="text-slate-600 mb-4">Invite your first contractor to get started</p>
              {user?.is_owner && (
                <Button onClick={() => setInviteDialogOpen(true)} className="bg-orange-500 hover:bg-orange-600">
                  <Plus className="w-4 h-4 mr-2" />
                  Invite Contractor
                </Button>
              )}
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-6">
            {Object.entries(groupedContractors).map(([type, contractorsList]) => (
              <Card key={type}>
                <CardHeader>
                  <CardTitle className="text-lg">{type}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {contractorsList.map((contractor) => (
                      <div 
                        key={contractor.id}
                        className="p-4 border-2 border-slate-200 rounded-lg hover:border-orange-300 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex-1">
                            <h4 className="font-medium text-slate-900">{contractor.name}</h4>
                            {contractor.company_name && (
                              <p className="text-sm text-slate-600">{contractor.company_name}</p>
                            )}
                          </div>
                          {user?.is_owner && (
                            <div className="flex gap-1">
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleEdit(contractor)}
                                className="h-8 w-8 p-0"
                              >
                                <Edit className="w-3 h-3" />
                              </Button>
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => handleDelete(contractor.id)}
                                className="h-8 w-8 p-0 border-red-300 text-red-600"
                              >
                                <Trash2 className="w-3 h-3" />
                              </Button>
                            </div>
                          )}
                        </div>
                        
                        <div className="space-y-2 text-sm">
                          {contractor.phone && (
                            <div className="flex items-center gap-2 text-slate-600">
                              <Phone className="w-3 h-3" />
                              <span>{contractor.phone}</span>
                            </div>
                          )}
                          {contractor.email && (
                            <div className="flex items-center gap-2 text-slate-600">
                              <Mail className="w-3 h-3" />
                              <span className="truncate">{contractor.email}</span>
                            </div>
                          )}
                          {contractor.unique_code && (
                            <div className="mt-2 pt-2 border-t">
                              <span className="text-xs text-slate-500">Access Code:</span>
                              <p className="text-xs font-mono bg-slate-100 px-2 py-1 rounded mt-1">
                                {contractor.unique_code}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {/* Invite Contractor Dialog */}
        <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Invite Contractor to Register</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleInviteContractor} className="space-y-4">
              <p className="text-sm text-slate-600">
                Send a WhatsApp invitation to the contractor to register themselves with complete details.
              </p>
              <div>
                <Label>Contractor Name *</Label>
                <Input
                  value={inviteForm.name}
                  onChange={(e) => setInviteForm({ ...inviteForm, name: e.target.value })}
                  required
                  placeholder="John Contractor"
                />
              </div>
              <div>
                <Label>Phone Number (with country code) *</Label>
                <Input
                  value={inviteForm.phone}
                  onChange={(e) => setInviteForm({ ...inviteForm, phone: e.target.value })}
                  required
                  placeholder="+919876543210"
                />
                <p className="text-xs text-slate-500 mt-1">
                  WhatsApp invitation will be sent to this number
                </p>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setInviteDialogOpen(false)}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-orange-500 hover:bg-orange-600">
                  Send Invitation
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Edit Contractor Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Contractor</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleEditSubmit}>
              <div className="space-y-4 py-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label>Name *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <Label>Type *</Label>
                    <select
                      value={formData.contractor_type}
                      onChange={(e) => setFormData({...formData, contractor_type: e.target.value})}
                      className="w-full p-2 border rounded"
                      required
                    >
                      <option value="">Select Type</option>
                      {CONTRACTOR_TYPES.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label>Company Name</Label>
                    <Input
                      value={formData.company_name}
                      onChange={(e) => setFormData({...formData, company_name: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Phone *</Label>
                    <Input
                      value={formData.phone}
                      onChange={(e) => setFormData({...formData, phone: e.target.value})}
                      required
                    />
                  </div>
                  <div>
                    <Label>Alternate Phone</Label>
                    <Input
                      value={formData.alternate_phone}
                      onChange={(e) => setFormData({...formData, alternate_phone: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({...formData, email: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>GST Number</Label>
                    <Input
                      value={formData.gst_number}
                      onChange={(e) => setFormData({...formData, gst_number: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>PAN Number</Label>
                    <Input
                      value={formData.pan_number}
                      onChange={(e) => setFormData({...formData, pan_number: e.target.value})}
                    />
                  </div>
                </div>
                <div>
                  <Label>Address</Label>
                  <Input
                    value={formData.address}
                    onChange={(e) => setFormData({...formData, address: e.target.value})}
                  />
                </div>
                <div>
                  <Label>Notes</Label>
                  <textarea
                    value={formData.notes}
                    onChange={(e) => setFormData({...formData, notes: e.target.value})}
                    className="w-full p-2 border rounded min-h-[80px]"
                  />
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => {
                  setEditDialogOpen(false);
                  resetForm();
                }}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-orange-500 hover:bg-orange-600">
                  Update Contractor
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
