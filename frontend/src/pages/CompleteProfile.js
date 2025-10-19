import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Building2, User, Mail, Phone, MapPin, Calendar, Heart, Briefcase, UserCircle } from 'lucide-react';
import { formatErrorMessage } from '@/utils/errorHandler';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function CompleteProfile() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  
  // Get user data from localStorage
  const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
  
  const [formData, setFormData] = useState({
    full_name: storedUser.name || '',
    postal_address: '',
    email: storedUser.email || '',
    mobile: '+91',
    date_of_birth: '',
    gender: 'male',
    marital_status: 'single',
    role: 'architect',
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/profile/complete`, formData);
      
      // Update user in localStorage to reflect validation
      const updatedUser = JSON.parse(localStorage.getItem('user') || '{}');
      updatedUser.is_validated = true;
      updatedUser.registration_completed = true;
      localStorage.setItem('user', JSON.stringify(updatedUser));
      
      toast.success('Profile completed! Welcome to 4th Dimension!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Failed to complete profile'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 p-4">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4 shadow-lg">
            <Building2 className="w-9 h-9 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Complete Your Profile</h1>
          <p className="text-slate-600">Please provide your complete information</p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader>
            <CardTitle>Personal Details</CardTitle>
            <CardDescription>
              Fill in your details to complete registration
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="full_name">Full Name (up to 30 characters)</Label>
                <div className="relative">
                  <User className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <Input
                    id="full_name"
                    placeholder="Your complete name"
                    className="pl-10"
                    maxLength={30}
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    required
                    data-testid="full-name-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="your@email.com"
                    className="pl-10 bg-slate-50"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                    readOnly
                    data-testid="email-input"
                  />
                </div>
                <p className="text-xs text-slate-500">Email from your account</p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="mobile">Mobile Number</Label>
                <div className="relative">
                  <Phone className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <Input
                    id="mobile"
                    type="tel"
                    placeholder="+91 98765 43210"
                    className="pl-10"
                    value={formData.mobile}
                    onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                    required
                    data-testid="mobile-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="postal_address">Postal Address</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <textarea
                    id="postal_address"
                    placeholder="Your complete address"
                    className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 pl-10 text-sm ring-offset-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.postal_address}
                    onChange={(e) => setFormData({ ...formData, postal_address: e.target.value })}
                    required
                    data-testid="address-input"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="date_of_birth">Date of Birth</Label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input
                      id="date_of_birth"
                      type="date"
                      className="pl-10"
                      value={formData.date_of_birth}
                      onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                      required
                      data-testid="dob-input"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="gender">Gender</Label>
                  <div className="relative">
                    <UserCircle className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <select
                      id="gender"
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 pl-10 text-sm ring-offset-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                      value={formData.gender}
                      onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                      data-testid="gender-select"
                    >
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="marital_status">Marital Status</Label>
                <div className="relative">
                  <Heart className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <select
                    id="marital_status"
                    className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 pl-10 text-sm ring-offset-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.marital_status}
                    onChange={(e) => setFormData({ ...formData, marital_status: e.target.value })}
                    data-testid="marital-status-select"
                  >
                    <option value="single">Single</option>
                    <option value="married">Married</option>
                    <option value="divorced">Divorced</option>
                    <option value="widowed">Widowed</option>
                  </select>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="role">Team Role</Label>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <select
                    id="role"
                    className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 pl-10 text-sm ring-offset-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.role}
                    onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                    data-testid="role-select"
                  >
                    <option value="architect">Architect</option>
                    <option value="interior_designer">Interior Designer</option>
                    <option value="landscape_designer">Landscape Designer</option>
                    <option value="site_engineer">Site Engineer</option>
                    <option value="structural_engineer">Structural Engineer</option>
                    <option value="site_supervisor">Site Supervisor</option>
                    <option value="intern">Intern</option>
                    <option value="administrator">Administrator</option>
                    <option value="office_staff">Office Staff</option>
                  </select>
                </div>
              </div>

              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-sm text-amber-800">
                  <strong>Note:</strong> After submitting, your registration will be reviewed by the owner or administrator before you can access the system.
                </p>
              </div>

              <Button 
                type="submit" 
                className="w-full" 
                disabled={loading} 
                data-testid="complete-profile-btn"
              >
                {loading ? 'Submitting...' : 'Complete Registration'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
