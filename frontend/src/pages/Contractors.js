import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '../layouts/Layout';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Plus, Briefcase, Phone, Mail, MapPin, Edit, Trash2 } from 'lucide-react';
import PhoneInput, { combinePhoneNumber, splitPhoneNumber } from '@/components/PhoneInput';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

const CONTRACTOR_TYPES = [
  'Civil Contractor',
  'Electrical Contractor',
  'Plumbing Contractor',
  'HVAC Contractor',
  'Painting Contractor',
  'Carpentry Contractor',
  'Interior Contractor',
  'Landscape Contractor',
  'False Ceiling Contractor',
  'Flooring Contractor',
  'Waterproofing Contractor',
  'Other'
];

export default function Contractors({ user, onLogout }) {
  const [contractors, setContractors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingContractor, setEditingContractor] = useState(null);
  const [inviteForm, setInviteForm] = useState({
    name: '',
    countryCode: '+91',
    phoneNumber: ''
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
      console.error('Error fetching contractors:', error);
      toast.error('Failed to fetch contractors');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteContractor = async (e) => {
    e.preventDefault();
    
    if (!inviteForm.name || !inviteForm.phoneNumber) {
      toast.error('Please enter name and phone number');
      return;
    }

    if (inviteForm.phoneNumber.length !== 10) {
      toast.error('Please enter a valid 10-digit phone number');
      return;
    }

    try {
      const fullPhone = combinePhoneNumber(inviteForm.countryCode, inviteForm.phoneNumber);
      
      await axios.post(`${API}/invite/send`, null, {
        params: {
          name: inviteForm.name,
          phone: fullPhone,
          invitee_type: 'contractor'
        }
      });
      
      toast.success(`WhatsApp invite sent to ${inviteForm.name}!`, { duration: 5000 });
      setInviteDialogOpen(false);
      setInviteForm({ name: '', countryCode: '+91', phoneNumber: '' });
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
      toast.success('Contractor deleted successfully');
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
        <div className="flex justify-center items-center h-64">
          <div className="text-slate-600">Loading contractors...</div>
        </div>
      </Layout>
    );
  }

  return (
    <Layout user={user} onLogout={onLogout}>
      <div className="max-w-7xl mx-auto p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-3xl font-bold text-slate-900">Contractors</h1>
            <p className="text-slate-600 mt-1">Manage your project contractors</p>
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

        {/* Empty State */}
        {contractors.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <Briefcase className="w-16 h-16 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No Contractors Yet</h3>
            <p className="text-slate-600 mb-4">Invite your first contractor to get started</p>
            {user?.is_owner && (
              <Button onClick={() => setInviteDialogOpen(true)} className="bg-orange-500 hover:bg-orange-600">
                <Plus className="w-4 h-4 mr-2" />
                Invite Contractor
              </Button>
            )}
          </div>
        ) : (
          /* Contractor List by Type */
          <div className="space-y-6">
            {Object.entries(groupedContractors).map(([type, contractorsList]) => (
              <div key={type} className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div className="bg-slate-50 px-6 py-3 border-b">
                  <h2 className="font-semibold text-slate-900">{type} ({contractorsList.length})</h2>
                </div>
                <div className="divide-y">
                  {contractorsList.map((contractor) => (
                    <div key={contractor.id} className="p-6 hover:bg-slate-50 transition-colors">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h3 className="text-lg font-semibold text-slate-900">{contractor.name}</h3>
                            {contractor.company_name && (
                              <span className="text-sm text-slate-500">({contractor.company_name})</span>
                            )}
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 mt-3">
                            {contractor.email && (
                              <div className="flex items-center gap-2 text-slate-600">
                                <Mail className="w-4 h-4" />
                                <span className="text-sm">{contractor.email}</span>
                              </div>
                            )}
                            {contractor.phone && (
                              <div className="flex items-center gap-2 text-slate-600">
                                <Phone className="w-4 h-4" />
                                <span className="text-sm">{contractor.phone}</span>
                              </div>
                            )}
                            {contractor.address && (
                              <div className="flex items-center gap-2 text-slate-600">
                                <MapPin className="w-4 h-4" />
                                <span className="text-sm">{contractor.address}</span>
                              </div>
                            )}
                          </div>

                          {contractor.notes && (
                            <p className="text-sm text-slate-600 mt-3 italic">{contractor.notes}</p>
                          )}
                        </div>

                        {user?.is_owner && (
                          <div className="flex gap-2 ml-4">
                            <Button variant="ghost" size="sm" onClick={() => handleEdit(contractor)}>
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button variant="ghost" size="sm" onClick={() => handleDelete(contractor.id)}>
                              <Trash2 className="w-4 h-4 text-red-500" />
                            </Button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
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
              <PhoneInput
                label="Phone Number"
                countryCode={inviteForm.countryCode}
                phoneNumber={inviteForm.phoneNumber}
                onCountryCodeChange={(code) => setInviteForm({ ...inviteForm, countryCode: code })}
                onPhoneNumberChange={(number) => setInviteForm({ ...inviteForm, phoneNumber: number })}
                required
                placeholder="9876543210"
              />
              <p className="text-xs text-slate-500">
                WhatsApp invitation will be sent to this number
              </p>
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
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Name *</Label>
                    <Input
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label>Contractor Type *</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.contractor_type}
                      onChange={(e) => setFormData({ ...formData, contractor_type: e.target.value })}
                      required
                    >
                      <option value="">Select type</option>
                      {CONTRACTOR_TYPES.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label>Company Name</Label>
                    <Input
                      value={formData.company_name}
                      onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Email</Label>
                    <Input
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Phone</Label>
                    <Input
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>Alternate Phone</Label>
                    <Input
                      value={formData.alternate_phone}
                      onChange={(e) => setFormData({ ...formData, alternate_phone: e.target.value })}
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Address</Label>
                    <textarea
                      className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.address}
                      onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>GST Number</Label>
                    <Input
                      value={formData.gst_number}
                      onChange={(e) => setFormData({ ...formData, gst_number: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>PAN Number</Label>
                    <Input
                      value={formData.pan_number}
                      onChange={(e) => setFormData({ ...formData, pan_number: e.target.value })}
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Notes</Label>
                    <textarea
                      className="flex min-h-[60px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    />
                  </div>
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
