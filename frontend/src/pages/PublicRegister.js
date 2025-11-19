import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, Mail, Phone, MapPin, User, Briefcase } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const REGISTRATION_TYPES = [
  { value: 'client', label: 'Client' },
  { value: 'team_member', label: 'Office Team Member' },
  { value: 'contractor', label: 'Contractor' },
  { value: 'vendor', label: 'Vendor' },
  { value: 'consultant', label: 'Consultant' }
];

export default function PublicRegister() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [checkingEmail, setCheckingEmail] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    mobile: '',
    registration_type: '',
    address_line_1: '',
    address_line_2: '',
    city: '',
    state: '',
    pin_code: '',
    registered_via: 'email'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.name || !formData.email || !formData.mobile || !formData.registration_type || 
        !formData.address_line_1 || !formData.city || !formData.state || !formData.pin_code) {
      toast.error('Please fill in all required fields');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/public-register`, formData);
      
      toast.success('OTPs sent! Please check your email and phone.', {
        duration: 5000
      });
      
      // Navigate to OTP verification page
      navigate('/verify-otp', { 
        state: { 
          email: formData.email,
          registered_via: formData.registered_via,
          registration_id: response.data.registration_id
        } 
      });
    } catch (error) {
      console.error('Registration error:', error);
      toast.error(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-indigo-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-3xl">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center mb-4">
            <Building2 className="w-12 h-12 text-orange-500" />
          </div>
          <CardTitle className="text-3xl font-bold text-slate-900">
            Register with 4th Dimension
          </CardTitle>
          <p className="text-slate-600 mt-2">
            Architecture & Design
          </p>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <User className="w-5 h-5 text-orange-500" />
                Basic Information
              </h3>
              
              <div>
                <Label htmlFor="name">Full Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter your full name"
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="email">Email Address *</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      placeholder="your.email@example.com"
                      className="pl-10"
                      required
                    />
                  </div>
                </div>

                <div>
                  <Label htmlFor="mobile">Mobile Number *</Label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                    <Input
                      id="mobile"
                      type="tel"
                      value={formData.mobile}
                      onChange={(e) => setFormData({ ...formData, mobile: e.target.value })}
                      placeholder="+919876543210"
                      className="pl-10"
                      required
                    />
                  </div>
                  <p className="text-xs text-slate-500 mt-1">Include country code</p>
                </div>
              </div>

              <div>
                <Label htmlFor="registration_type">I am registering as *</Label>
                <div className="relative">
                  <Briefcase className="absolute left-3 top-3 w-4 h-4 text-slate-400" />
                  <select
                    id="registration_type"
                    value={formData.registration_type}
                    onChange={(e) => setFormData({ ...formData, registration_type: e.target.value })}
                    className="flex h-10 w-full rounded-md border border-slate-200 bg-white pl-10 pr-3 py-2 text-sm"
                    required
                  >
                    <option value="">Select your role</option>
                    {REGISTRATION_TYPES.map(type => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            {/* Address Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <MapPin className="w-5 h-5 text-orange-500" />
                Address Information
              </h3>

              <div>
                <Label htmlFor="address_line_1">Address Line 1 *</Label>
                <Input
                  id="address_line_1"
                  value={formData.address_line_1}
                  onChange={(e) => setFormData({ ...formData, address_line_1: e.target.value })}
                  placeholder="Street address"
                  required
                />
              </div>

              <div>
                <Label htmlFor="address_line_2">Address Line 2</Label>
                <Input
                  id="address_line_2"
                  value={formData.address_line_2}
                  onChange={(e) => setFormData({ ...formData, address_line_2: e.target.value })}
                  placeholder="Apartment, suite, etc. (optional)"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="city">City *</Label>
                  <Input
                    id="city"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    placeholder="City"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="state">State *</Label>
                  <Input
                    id="state"
                    value={formData.state}
                    onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                    placeholder="State"
                    required
                  />
                </div>

                <div>
                  <Label htmlFor="pin_code">PIN Code *</Label>
                  <Input
                    id="pin_code"
                    value={formData.pin_code}
                    onChange={(e) => setFormData({ ...formData, pin_code: e.target.value })}
                    placeholder="PIN Code"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Information Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                <strong>What happens next?</strong>
              </p>
              <ul className="text-xs text-blue-700 mt-2 space-y-1 ml-4 list-disc">
                <li>OTPs will be sent to your email and mobile number</li>
                <li>Verify both OTPs on the next screen</li>
                <li>Set your password (if registering with email)</li>
                <li>Your registration will be sent to the owner for approval</li>
                <li>You'll receive an email once approved</li>
              </ul>
            </div>

            {/* Submit Button */}
            <Button 
              type="submit" 
              disabled={loading}
              className="w-full bg-orange-500 hover:bg-orange-600 text-white py-6 text-lg"
            >
              {loading ? 'Sending OTPs...' : 'Verify & Continue'}
            </Button>

            {/* Login Link */}
            <div className="text-center">
              <p className="text-sm text-slate-600">
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => navigate('/login')}
                  className="text-orange-500 hover:text-orange-600 font-medium"
                >
                  Sign In
                </button>
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
