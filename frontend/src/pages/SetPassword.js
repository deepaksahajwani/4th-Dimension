import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, Lock, Eye, EyeOff } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function SetPassword() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const email = location.state?.email;

  useEffect(() => {
    if (!email) {
      toast.error('Invalid access. Please complete OTP verification first.');
      navigate('/register');
    }
  }, [email, navigate]);

  const validatePassword = () => {
    if (password.length < 8) {
      toast.error('Password must be at least 8 characters long');
      return false;
    }
    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validatePassword()) {
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/auth/set-password-after-otp`, {
        email: email,
        password: password
      });
      
      toast.success('Registration complete! Awaiting approval.', {
        duration: 5000
      });
      
      // Navigate to pending approval page
      navigate('/pending-approval', {
        state: {
          email: email,
          message: 'Registration submitted successfully!'
        }
      });
    } catch (error) {
      console.error('Password setup error:', error);
      toast.error(error.response?.data?.detail || 'Failed to set password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-indigo-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center mb-4">
            <Lock className="w-12 h-12 text-orange-500" />
          </div>
          <CardTitle className="text-2xl font-bold text-slate-900">
            Set Your Password
          </CardTitle>
          <p className="text-slate-600 mt-2">
            Create a strong password for your account
          </p>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Password Field */}
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              <p className="text-xs text-slate-500">
                Must be at least 8 characters long
              </p>
            </div>

            {/* Confirm Password Field */}
            <div className="space-y-2">
              <Label htmlFor="confirm_password">Confirm Password</Label>
              <div className="relative">
                <Input
                  id="confirm_password"
                  type={showConfirmPassword ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-3 text-slate-400 hover:text-slate-600"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Password Strength Indicators */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <p className="text-xs text-blue-800 font-medium mb-2">
                Password Requirements:
              </p>
              <ul className="text-xs text-blue-700 space-y-1">
                <li className={password.length >= 8 ? 'text-green-600' : ''}>
                  {password.length >= 8 ? '✓' : '○'} At least 8 characters
                </li>
                <li className={password === confirmPassword && password ? 'text-green-600' : ''}>
                  {password === confirmPassword && password ? '✓' : '○'} Passwords match
                </li>
              </ul>
            </div>

            {/* Submit Button */}
            <Button 
              type="submit" 
              disabled={loading || password.length < 8 || password !== confirmPassword}
              className="w-full bg-orange-500 hover:bg-orange-600 text-white py-6"
            >
              {loading ? 'Completing Registration...' : 'Complete Registration'}
            </Button>

            {/* Info Box */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-xs text-yellow-800">
                <strong>After setting your password:</strong><br />
                Your registration will be sent to the owner for approval. You'll receive an email notification once your account is approved.
              </p>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
