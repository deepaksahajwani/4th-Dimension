import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { CheckCircle, Mail, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [otp, setOtp] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [autoVerifying, setAutoVerifying] = useState(false);
  const [verified, setVerified] = useState(false);
  const [userId, setUserId] = useState(null);

  const token = searchParams.get('token');

  useEffect(() => {
    // Auto-verify if token is present in URL
    if (token) {
      verifyWithToken();
    }
  }, [token]);

  const verifyWithToken = async () => {
    setAutoVerifying(true);
    try {
      const response = await axios.post(`${API}/team/verify-email`, { token });
      
      setVerified(true);
      setUserId(response.data.user_id);
      toast.success('Email verified successfully!');
      
      // Redirect to phone verification after 2 seconds
      setTimeout(() => {
        navigate(`/verify-phone?user_id=${response.data.user_id}`);
      }, 2000);
    } catch (error) {
      console.error('Verification error:', error);
      toast.error(error.response?.data?.detail || 'Verification failed');
      setAutoVerifying(false);
    }
  };

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    
    if (!otp || otp.length !== 6) {
      toast.error('Please enter a valid 6-digit OTP');
      return;
    }

    setVerifying(true);
    try {
      const response = await axios.post(`${API}/team/verify-email`, { otp });
      
      setVerified(true);
      setUserId(response.data.user_id);
      toast.success('Email verified successfully!');
      
      // Redirect to phone verification
      setTimeout(() => {
        navigate(`/verify-phone?user_id=${response.data.user_id}`);
      }, 2000);
    } catch (error) {
      console.error('OTP verification error:', error);
      toast.error(error.response?.data?.detail || 'Invalid OTP');
    } finally {
      setVerifying(false);
    }
  };

  if (autoVerifying) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <Loader2 className="w-16 h-16 mx-auto text-indigo-600 animate-spin mb-4" />
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Verifying...</h2>
            <p className="text-slate-600">Please wait while we verify your email</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (verified) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <div className="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Email Verified!</h2>
            <p className="text-slate-600 mb-4">
              Your email has been verified successfully. Redirecting to phone verification...
            </p>
            <div className="animate-pulse text-indigo-600">Please wait...</div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 to-purple-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center pb-4">
          <div className="w-16 h-16 mx-auto bg-indigo-100 rounded-full flex items-center justify-center mb-4">
            <Mail className="w-8 h-8 text-indigo-600" />
          </div>
          <CardTitle className="text-2xl">Verify Your Email</CardTitle>
          <p className="text-sm text-slate-600 mt-2">
            Enter the 6-digit OTP sent to your email
          </p>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <form onSubmit={handleVerifyOTP} className="space-y-4">
            <div>
              <Label htmlFor="otp">Email OTP</Label>
              <Input
                id="otp"
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                placeholder="123456"
                className="text-center text-2xl tracking-widest"
                maxLength={6}
                required
              />
              <p className="text-xs text-slate-500 mt-1">Check your email for the verification code</p>
            </div>

            <Button 
              type="submit" 
              className="w-full bg-indigo-600 hover:bg-indigo-700"
              disabled={verifying || otp.length !== 6}
            >
              {verifying ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Verifying...
                </>
              ) : (
                'Verify Email'
              )}
            </Button>
          </form>

          <div className="text-center">
            <p className="text-sm text-slate-600">
              Didn't receive the code?{' '}
              <button className="text-indigo-600 hover:underline font-medium">
                Resend OTP
              </button>
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-xs text-blue-800">
              <strong>Note:</strong> After email verification, you'll need to verify your phone number to complete registration.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
