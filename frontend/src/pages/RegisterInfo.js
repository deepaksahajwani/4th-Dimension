import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { User, Mail, Phone, MapPin, Calendar, Heart, Briefcase, UserCircle } from 'lucide-react';
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
  { value: 'site_engineer', label: 'Site Engineer' },
  { value: 'site_supervisor', label: 'Site Supervisor' },
  { value: 'intern', label: 'Intern' },
  { value: 'administrator', label: 'Administrator' },
  { value: 'human_resource', label: 'Human Resource' },
  { value: 'accountant', label: 'Accountant' },
  { value: 'office_staff', label: 'Office Staff' }
];

export default function RegisterInfo({ onLogin }) {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  // Check if coming from login with credentials or fresh registration
  const hasCredentials = location.state?.email && location.state?.password;
  
  const [formData, setFormData] = useState({
    full_name: '',
    email: location.state?.email || '',
    password: location.state?.password || '',
    confirmPassword: '',
    mobile: '+91',
    postal_address: '',
    date_of_birth: '',
    date_of_joining: '',
    gender: 'male',
    marital_status: 'single',
    role: 'junior_architect'
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Step 1: Register user with email and password
      let token = localStorage.getItem('token');
      
      if (!token && formData.email && formData.password) {
        const registerResponse = await axios.post(`${API}/auth/register`, {
          email: formData.email,
          password: formData.password,
          name: formData.full_name
        });
        token = registerResponse.data.access_token;
        localStorage.setItem('token', token);
      }
      
      // Step 2: Complete profile
      const profileData = {
        full_name: formData.full_name,
        postal_address: formData.postal_address,
        email: formData.email,
        mobile: formData.mobile,
        date_of_birth: formData.date_of_birth,
        date_of_joining: formData.date_of_joining,
        gender: formData.gender,
        marital_status: formData.marital_status,
        role: formData.role
      };
      
      const profileResponse = await axios.post(`${API}/profile/complete`, profileData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Step 3: Login to get full user data
      const loginResponse = await axios.post(`${API}/auth/login`, {
        email: formData.email,
        password: formData.password
      });
      
      onLogin(loginResponse.data.user, loginResponse.data.access_token);
      toast.success('Registration successful! Welcome to 4th Dimension!');
      navigate('/dashboard');
      
    } catch (error) {
      toast.error(formatErrorMessage(error, 'Registration failed'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 p-4">
      <div className="w-full max-w-3xl">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center mb-4">
            <div className="grid grid-cols-2 gap-1 w-16 h-16">
              <div className="bg-slate-600 rounded-tl-lg"></div>
              <div className="bg-slate-600 rounded-tr-lg"></div>
              <div className="bg-slate-600 rounded-bl-lg"></div>
              <div className="bg-orange-500 rounded-br-lg"></div>
            </div>
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">Join 4th Dimension</h1>
          <p className="text-slate-600">Complete your registration to get started</p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader>
            <CardTitle>Registration Information</CardTitle>
            <CardDescription>Please fill in all your details</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="full_name">Full Name *</Label>
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
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email Address *</Label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input
                      id="email"
                      type="email"
                      placeholder="your@email.com"
                      className="pl-10"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      required
                    />
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="mobile">Mobile Number *</Label>
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
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="role">Team Role *</Label>
                  <div className="relative">
                    <Briefcase className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <select
                      id="role"
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 pl-10 text-sm ring-offset-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                      value={formData.role}
                      onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                      required
                    >
                      {TEAM_ROLES.map(role => (
                        <option key={role.value} value={role.value}>{role.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="postal_address">Address *</Label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <textarea
                    id="postal_address"
                    placeholder="Your complete address"
                    className="flex min-h-[80px] w-full rounded-md border border-slate-200 bg-white px-3 py-2 pl-10 text-sm ring-offset-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-orange-500"
                    value={formData.postal_address}
                    onChange={(e) => setFormData({ ...formData, postal_address: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="date_of_birth">Date of Birth *</Label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input
                      id="date_of_birth"
                      type="date"
                      className="pl-10"
                      value={formData.date_of_birth}
                      onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                      required
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="date_of_joining">Date of Joining Firm *</Label>
                  <div className="relative">
                    <Calendar className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <Input
                      id="date_of_joining"
                      type="date"
                      className="pl-10"
                      value={formData.date_of_joining}
                      onChange={(e) => setFormData({ ...formData, date_of_joining: e.target.value })}
                      required
                    />
                  </div>
                </div>
              </div>

              <div className="grid md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="gender">Gender *</Label>
                  <div className="relative">
                    <UserCircle className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <select
                      id="gender"
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 pl-10 text-sm ring-offset-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                      value={formData.gender}
                      onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                      required
                    >
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="marital_status">Marital Status *</Label>
                  <div className="relative">
                    <Heart className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                    <select
                      id="marital_status"
                      className="flex h-10 w-full rounded-md border border-slate-200 bg-white px-3 py-2 pl-10 text-sm ring-offset-white focus:outline-none focus:ring-2 focus:ring-orange-500"
                      value={formData.marital_status}
                      onChange={(e) => setFormData({ ...formData, marital_status: e.target.value })}
                      required
                    >
                      <option value="single">Single</option>
                      <option value="married">Married</option>
                      <option value="divorced">Divorced</option>
                      <option value="widowed">Widowed</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  className="flex-1"
                  onClick={() => navigate('/')}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  className="flex-1 bg-orange-500 hover:bg-orange-600"
                  disabled={loading}
                >
                  {loading ? 'Registering...' : 'Register'}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
