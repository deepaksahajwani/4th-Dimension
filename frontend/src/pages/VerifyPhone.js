import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { CheckCircle, Smartphone, Loader2, ArrowRight } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function VerifyPhone() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [otp, setOtp] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);
  const [verified, setVerified] = useState(false);

  const userId = searchParams.get('user_id');

  useEffect(() => {
    if (!userId) {
      toast.error('Invalid verification link');
      navigate('/login');
    }
  }, [userId, navigate]);

  const handleVerifyOTP = async (e) => {
    e.preventDefault();
    
    if (!otp || otp.length !== 6) {
      toast.error('Please enter a valid 6-digit OTP');
      return;
    }

    setVerifying(true);
    try {
      const response = await axios.post(`${API}/team/verify-phone`, {
        user_id: userId,
        otp
      });
      
      setVerified(true);
      toast.success('Phone verified successfully! Your account is now active.');
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (error) {
      console.error('Phone verification error:', error);
      toast.error(error.response?.data?.detail || 'Invalid OTP');
    } finally {
      setVerifying(false);
    }
  };

  const handleResendOTP = async () => {
    setResending(true);
    try {
      await axios.post(`${API}/team/resend-otp`, {
        user_id: userId,
        type: 'phone'
      });
      toast.success('OTP resent to your phone!');
    } catch (error) {
      console.error('Resend OTP error:', error);
      toast.error('Failed to resend OTP');
    } finally {
      setResending(false);
    }
  };

  if (verified) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-blue-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center">
            <div className="w-20 h-20 mx-auto bg-green-100 rounded-full flex items-center justify-center mb-4">
              <CheckCircle className="w-12 h-12 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900 mb-2">All Verified!</h2>
            <p className="text-slate-600 mb-4">
              Your email and phone have been verified successfully.
            </p>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <p className="text-sm text-green-800">
                <strong>✅ Account Activated</strong><br />
                You can now log in to access the 4th Dimension team portal.
              </p>
            </div>
            <p className="text-sm text-slate-500 animate-pulse">
              Redirecting to login page...
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 to-pink-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center pb-4">
          <div className="w-16 h-16 mx-auto bg-purple-100 rounded-full flex items-center justify-center mb-4">
            <Smartphone className="w-8 h-8 text-purple-600" />
          </div>
          <CardTitle className="text-2xl">Verify Your Phone</CardTitle>
          <p className="text-sm text-slate-600 mt-2">
            Enter the 6-digit OTP sent via SMS
          </p>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-center">
            <CheckCircle className="w-5 h-5 text-green-600 inline-block mr-2" />
            <span className="text-sm text-green-800 font-medium">Email Verified</span>
          </div>

          <form onSubmit={handleVerifyOTP} className="space-y-4">
            <div>
              <Label htmlFor="otp">Phone OTP</Label>
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
              <p className="text-xs text-slate-500 mt-1">Check your phone for the SMS code</p>
            </div>

            <Button 
              type="submit" 
              className="w-full bg-purple-600 hover:bg-purple-700"
              disabled={verifying || otp.length !== 6}
            >
              {verifying ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Verifying...
                </>
              ) : (
                <>
                  Complete Verification
                  <ArrowRight className="w-4 h-4 ml-2" />
                </>
              )}
            </Button>
          </form>

          <div className="text-center">
            <p className="text-sm text-slate-600">
              Didn't receive the code?{' '}
              <button 
                onClick={handleResendOTP}
                disabled={resending}
                className="text-purple-600 hover:underline font-medium disabled:opacity-50"
              >
                {resending ? 'Sending...' : 'Resend OTP'}
              </button>
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-xs text-blue-800">
              <strong>Final Step:</strong> After phone verification, your account will be activated and you can log in.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
