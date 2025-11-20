import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, Mail, Smartphone, Shield } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function VerifyOTP() {
  const navigate = useNavigate();
  const location = useLocation();
  const [loading, setLoading] = useState(false);
  const [emailOTP, setEmailOTP] = useState('');
  const [phoneOTP, setPhoneOTP] = useState('');
  
  const email = location.state?.email;
  const registered_via = location.state?.registered_via;

  useEffect(() => {
    if (!email) {
      toast.error('Invalid access. Please register first.');
      navigate('/register');
    }
  }, [email, navigate]);

  const handleVerify = async (e) => {
    e.preventDefault();
    
    if (!emailOTP || !phoneOTP) {
      toast.error('Please enter both OTPs');
      return;
    }

    if (emailOTP.length !== 6 || phoneOTP.length !== 6) {
      toast.error('OTPs must be 6 digits');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/verify-registration-otp`, {
        email: email,
        email_otp: emailOTP,
        phone_otp: phoneOTP
      });
      
      toast.success('OTPs verified successfully!');
      
      // If email registration, go to password setup
      if (response.data.requires_password) {
        navigate('/set-password', { 
          state: { 
            email: email,
            registered_via: registered_via
          } 
        });
      } else {
        // Google registration - directly create account
        navigate('/pending-approval', {
          state: {
            email: email
          }
        });
      }
    } catch (error) {
      console.error('OTP verification error:', error);
      toast.error(error.response?.data?.detail || 'Invalid OTPs. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOTP = async () => {
    toast.info('Resend OTP functionality coming soon');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-indigo-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center mb-4">
            <Shield className="w-12 h-12 text-orange-500" />
          </div>
          <CardTitle className="text-2xl font-bold text-slate-900">
            Verify Your Identity
          </CardTitle>
          <p className="text-slate-600 mt-2">
            Enter the OTP sent to your email
          </p>
          <p className="text-xs text-slate-500 mt-1">
            (Phone verification temporarily disabled)
          </p>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleVerify} className="space-y-6">
            {/* Email OTP */}
            <div className="space-y-2">
              <Label htmlFor="email_otp" className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-orange-500" />
                Email OTP
              </Label>
              <Input
                id="email_otp"
                type="text"
                maxLength="6"
                value={emailOTP}
                onChange={(e) => setEmailOTP(e.target.value.replace(/\D/g, ''))}
                placeholder="Enter 6-digit OTP"
                className="text-center text-2xl tracking-widest font-bold"
                required
              />
              <p className="text-xs text-slate-500">
                Check your email: <strong>{email}</strong>
              </p>
            </div>

            {/* Phone OTP */}
            <div className="space-y-2">
              <Label htmlFor="phone_otp" className="flex items-center gap-2">
                <Smartphone className="w-4 h-4 text-orange-500" />
                Phone OTP
              </Label>
              <Input
                id="phone_otp"
                type="text"
                maxLength="6"
                value={phoneOTP}
                onChange={(e) => setPhoneOTP(e.target.value.replace(/\D/g, ''))}
                placeholder="Enter 6-digit OTP"
                className="text-center text-2xl tracking-widest font-bold"
                required
              />
              <p className="text-xs text-slate-500">
                Check your phone for SMS
              </p>
            </div>

            {/* Info Box */}
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3">
              <p className="text-xs text-yellow-800">
                <strong>Note:</strong> OTPs are valid for 1 hour. If you don't receive them, please check your spam folder or contact support.
              </p>
            </div>

            {/* Verify Button */}
            <Button 
              type="submit" 
              disabled={loading || emailOTP.length !== 6 || phoneOTP.length !== 6}
              className="w-full bg-orange-500 hover:bg-orange-600 text-white py-6"
            >
              {loading ? 'Verifying...' : 'Verify OTPs'}
            </Button>

            {/* Resend Link */}
            <div className="text-center">
              <button
                type="button"
                onClick={handleResendOTP}
                className="text-sm text-orange-500 hover:text-orange-600 font-medium"
              >
                Didn't receive OTPs? Resend
              </button>
            </div>

            {/* Back Link */}
            <div className="text-center">
              <button
                type="button"
                onClick={() => navigate('/register')}
                className="text-sm text-slate-600 hover:text-slate-900"
              >
                ← Back to Registration
              </button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
