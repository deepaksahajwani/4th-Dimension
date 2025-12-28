import { useState, useEffect } from 'react';
import axios from 'axios';
import Layout from '@/components/Layout';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Plus, Store, Phone, Mail, MapPin, Edit, Trash2, Building2, ChevronDown, ChevronUp } from 'lucide-react';
import PhoneInput, { combinePhoneNumber } from '@/components/PhoneInput';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

// Vendor types based on industry requirements
const VENDOR_TYPES = [
  'Automation and Home Theatres',
  'Building Chemicals, Adhesives, Waterproofing',
  'Building Materials (Cement, Sand, Aggregate, Steel)',
  'Carpets',
  'Cleaning Services',
  'Decoratives and Accessories, Paintings',
  'Electrical (Wires, Switches, Lights, Fans)',
  'Electronic and Electric Appliances',
  'False Ceiling (Grid, Metal, Soffit)',
  'Gardening Equipment, Nursery, Pots',
  'Glass Work, Aluminum Interior Profile',
  'Gypsum and POP',
  'HVAC',
  'Internet Service Provider',
  'Jhula and Swing',
  'Kitchen and Modular',
  'Mandir, Decorative Stones',
  'Marble and Granite',
  'Networking Solutions',
  'Office Furniture and Chairs',
  'Outdoor Furniture',
  'Paint, Wood and Surface Finishes',
  'Plumbing Material, Faucets, Bathroom Fixtures',
  'Plywood, Hardware, Finish Material',
  'Readymade Furniture (Sofa, Dining)',
  'Security Equipment (Digital Locks, CCTV, EPABX, Fire Alarm)',
  'Solar',
  'Solid Surface, Corian',
  'Tiles',
  'Upholstery and Soft Furnishings (Curtains, Blinds, Mattress)',
  'Water Purifiers, Geysers, Softeners, Water Harvesting',
  'Window Systems (UPVC, Aluminum)'
];

export default function Vendors({ user, onLogout }) {
  const [vendors, setVendors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [inviteDialogOpen, setInviteDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingVendor, setEditingVendor] = useState(null);
  const [expandedType, setExpandedType] = useState(null);
  const [inviteForm, setInviteForm] = useState({
    name: '',
    countryCode: '+91',
    phoneNumber: ''
  });
  const [formData, setFormData] = useState({
    company_name: '',
    vendor_type: '',
    contact_person_name: '',
    contact_person_email: '',
    contact_person_phone: '',
    company_address: '',
    gst_number: '',
    notes: ''
  });

  useEffect(() => {
    fetchVendors();
  }, []);

  const fetchVendors = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/vendors`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVendors(response.data);
    } catch (error) {
      console.error('Error fetching vendors:', error);
      toast.error('Failed to fetch vendors');
    } finally {
      setLoading(false);
    }
  };

  const handleInviteVendor = async (e) => {
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
          invitee_type: 'vendor'
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
      
      await axios.put(`${API}/vendors/${editingVendor.id}`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Vendor updated successfully!');
      
      setEditDialogOpen(false);
      resetForm();
      fetchVendors();
    } catch (error) {
      toast.error('Failed to update vendor');
    }
  };

  const handleEdit = (vendor) => {
    setEditingVendor(vendor);
    setFormData({
      company_name: vendor.company_name || '',
      vendor_type: vendor.vendor_type || '',
      contact_person_name: vendor.contact_person_name || '',
      contact_person_email: vendor.contact_person_email || '',
      contact_person_phone: vendor.contact_person_phone || '',
      company_address: vendor.company_address || '',
      gst_number: vendor.gst_number || '',
      notes: vendor.notes || ''
    });
    setEditDialogOpen(true);
  };

  const handleDelete = async (vendorId) => {
    if (!window.confirm('Are you sure you want to delete this vendor?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/vendors/${vendorId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Vendor deleted successfully');
      fetchVendors();
    } catch (error) {
      toast.error('Failed to delete vendor');
    }
  };

  const resetForm = () => {
    setFormData({
      company_name: '',
      vendor_type: '',
      contact_person_name: '',
      contact_person_email: '',
      contact_person_phone: '',
      company_address: '',
      gst_number: '',
      notes: ''
    });
    setEditingVendor(null);
  };

  // Group vendors by type
  const groupedVendors = vendors.reduce((acc, vendor) => {
    const type = vendor.vendor_type || 'Uncategorized';
    if (!acc[type]) acc[type] = [];
    acc[type].push(vendor);
    return acc;
  }, {});

  if (loading) {
    return (
      <Layout user={user} onLogout={onLogout}>
        <div className="flex justify-center items-center h-64">
          <div className="text-slate-600">Loading vendors...</div>
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
            <h1 className="text-3xl font-bold text-slate-900">Vendors</h1>
            <p className="text-slate-600 mt-1">Manage your material and service vendors</p>
          </div>
          {user?.is_owner && (
            <Button
              onClick={() => setInviteDialogOpen(true)}
              className="bg-orange-500 hover:bg-orange-600"
            >
              <Plus className="w-4 h-4 mr-2" />
              Invite Vendor
            </Button>
          )}
        </div>

        {/* Empty State */}
        {vendors.length === 0 ? (
          <div className="bg-white rounded-lg shadow-sm p-12 text-center">
            <Store className="w-16 h-16 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No Vendors Yet</h3>
            <p className="text-slate-600 mb-4">Invite your first vendor to get started</p>
            {user?.is_owner && (
              <Button onClick={() => setInviteDialogOpen(true)} className="bg-orange-500 hover:bg-orange-600">
                <Plus className="w-4 h-4 mr-2" />
                Invite Vendor
              </Button>
            )}
          </div>
        ) : (
          /* Vendor List by Type */
          <div className="space-y-4">
            {Object.entries(groupedVendors).map(([type, vendorsList]) => (
              <div key={type} className="bg-white rounded-lg shadow-sm overflow-hidden">
                <div 
                  className="bg-slate-50 px-6 py-3 border-b flex items-center justify-between cursor-pointer hover:bg-slate-100"
                  onClick={() => setExpandedType(expandedType === type ? null : type)}
                >
                  <div className="flex items-center gap-3">
                    <Store className="w-5 h-5 text-orange-500" />
                    <h2 className="font-semibold text-slate-900">{type}</h2>
                    <Badge variant="outline">{vendorsList.length}</Badge>
                  </div>
                  {expandedType === type ? (
                    <ChevronUp className="w-5 h-5 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-5 h-5 text-slate-400" />
                  )}
                </div>
                
                {expandedType === type && (
                  <div className="divide-y">
                    {vendorsList.map((vendor) => (
                      <div key={vendor.id} className="p-6 hover:bg-slate-50 transition-colors">
                        <div className="flex justify-between items-start">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <Building2 className="w-5 h-5 text-orange-500" />
                              <h3 className="text-lg font-semibold text-slate-900">{vendor.company_name}</h3>
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                              <div>
                                <p className="text-sm text-slate-500 mb-1">Contact Person</p>
                                <p className="text-sm font-medium text-slate-900">{vendor.contact_person_name}</p>
                              </div>
                              {vendor.contact_person_email && (
                                <div className="flex items-center gap-2 text-slate-600">
                                  <Mail className="w-4 h-4" />
                                  <span className="text-sm">{vendor.contact_person_email}</span>
                                </div>
                              )}
                              {vendor.contact_person_phone && (
                                <div className="flex items-center gap-2 text-slate-600">
                                  <Phone className="w-4 h-4" />
                                  <span className="text-sm">{vendor.contact_person_phone}</span>
                                </div>
                              )}
                              {vendor.company_address && (
                                <div className="flex items-center gap-2 text-slate-600">
                                  <MapPin className="w-4 h-4" />
                                  <span className="text-sm">{vendor.company_address}</span>
                                </div>
                              )}
                            </div>

                            {vendor.gst_number && (
                              <p className="text-sm text-slate-500 mt-2">GST: {vendor.gst_number}</p>
                            )}

                            {vendor.notes && (
                              <p className="text-sm text-slate-600 mt-3 italic">{vendor.notes}</p>
                            )}
                          </div>

                          {user?.is_owner && (
                            <div className="flex gap-2 ml-4">
                              <Button variant="ghost" size="sm" onClick={() => handleEdit(vendor)}>
                                <Edit className="w-4 h-4" />
                              </Button>
                              <Button variant="ghost" size="sm" onClick={() => handleDelete(vendor.id)}>
                                <Trash2 className="w-4 h-4 text-red-500" />
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Create/Add Vendor Dialog */}
        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Add New Vendor</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateSubmit}>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <Label>Company Name *</Label>
                    <Input
                      value={formData.company_name}
                      onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                      required
                      placeholder="ABC Suppliers Pvt. Ltd."
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Vendor Type *</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.vendor_type}
                      onChange={(e) => setFormData({ ...formData, vendor_type: e.target.value })}
                      required
                    >
                      <option value="">Select type</option>
                      {VENDOR_TYPES.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label>Contact Person Name *</Label>
                    <Input
                      value={formData.contact_person_name}
                      onChange={(e) => setFormData({ ...formData, contact_person_name: e.target.value })}
                      required
                      placeholder="John Doe"
                    />
                  </div>
                  <div>
                    <Label>Contact Person Phone *</Label>
                    <Input
                      value={formData.contact_person_phone}
                      onChange={(e) => setFormData({ ...formData, contact_person_phone: e.target.value })}
                      required
                      placeholder="+91 9876543210"
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Contact Person Email</Label>
                    <Input
                      type="email"
                      value={formData.contact_person_email}
                      onChange={(e) => setFormData({ ...formData, contact_person_email: e.target.value })}
                      placeholder="contact@company.com"
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Company Address</Label>
                    <textarea
                      className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.company_address}
                      onChange={(e) => setFormData({ ...formData, company_address: e.target.value })}
                      placeholder="Full address..."
                    />
                  </div>
                  <div>
                    <Label>GST Number</Label>
                    <Input
                      value={formData.gst_number}
                      onChange={(e) => setFormData({ ...formData, gst_number: e.target.value })}
                      placeholder="22AAAAA0000A1Z5"
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Notes</Label>
                    <textarea
                      className="flex min-h-[60px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.notes}
                      onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                      placeholder="Additional notes..."
                    />
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => {
                  setCreateDialogOpen(false);
                  resetForm();
                }}>
                  Cancel
                </Button>
                <Button type="submit" className="bg-orange-500 hover:bg-orange-600">
                  Add Vendor
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Invite Vendor Dialog */}
        <Dialog open={inviteDialogOpen} onOpenChange={setInviteDialogOpen}>
          <DialogContent className="max-w-md">
            <DialogHeader>
              <DialogTitle>Invite Vendor to Register</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleInviteVendor} className="space-y-4">
              <p className="text-sm text-slate-600">
                Send a WhatsApp invitation to the vendor to register themselves with complete details.
              </p>
              <div>
                <Label>Contact Person Name *</Label>
                <Input
                  value={inviteForm.name}
                  onChange={(e) => setInviteForm({ ...inviteForm, name: e.target.value })}
                  required
                  placeholder="John Doe"
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

        {/* Edit Vendor Dialog */}
        <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Edit Vendor</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleEditSubmit}>
              <div className="grid gap-4 py-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="col-span-2">
                    <Label>Company Name *</Label>
                    <Input
                      value={formData.company_name}
                      onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                      required
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Vendor Type *</Label>
                    <select
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.vendor_type}
                      onChange={(e) => setFormData({ ...formData, vendor_type: e.target.value })}
                      required
                    >
                      <option value="">Select type</option>
                      {VENDOR_TYPES.map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <Label>Contact Person Name *</Label>
                    <Input
                      value={formData.contact_person_name}
                      onChange={(e) => setFormData({ ...formData, contact_person_name: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label>Contact Person Phone *</Label>
                    <Input
                      value={formData.contact_person_phone}
                      onChange={(e) => setFormData({ ...formData, contact_person_phone: e.target.value })}
                      required
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Contact Person Email</Label>
                    <Input
                      type="email"
                      value={formData.contact_person_email}
                      onChange={(e) => setFormData({ ...formData, contact_person_email: e.target.value })}
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>Company Address</Label>
                    <textarea
                      className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 text-sm"
                      value={formData.company_address}
                      onChange={(e) => setFormData({ ...formData, company_address: e.target.value })}
                    />
                  </div>
                  <div>
                    <Label>GST Number</Label>
                    <Input
                      value={formData.gst_number}
                      onChange={(e) => setFormData({ ...formData, gst_number: e.target.value })}
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
                  Update Vendor
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </Layout>
  );
}
