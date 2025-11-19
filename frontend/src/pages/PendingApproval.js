import { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Building2, Clock, Mail, CheckCircle } from 'lucide-react';

export default function PendingApproval() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email;
  const message = location.state?.message;

  useEffect(() => {
    // If accessed directly without registration, redirect
    if (!email && !localStorage.getItem('token')) {
      navigate('/register');
    }
  }, [email, navigate]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-indigo-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="relative">
              <Clock className="w-16 h-16 text-orange-500" />
              <div className="absolute -top-1 -right-1 bg-yellow-400 rounded-full p-1">
                <Mail className="w-5 h-5 text-white" />
              </div>
            </div>
          </div>
          <CardTitle className="text-3xl font-bold text-slate-900">
            Registration Pending Approval
          </CardTitle>
          <p className="text-slate-600 mt-2">
            Thank you for registering with 4th Dimension!
          </p>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Success Message */}
          {message && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-start gap-3">
              <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
              <div>
                <p className="text-green-800 font-medium">{message}</p>
              </div>
            </div>
          )}

          {/* Status Information */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-yellow-900 mb-3">
              What's happening now?
            </h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-yellow-200 flex items-center justify-center flex-shrink-0">
                  <span className="text-yellow-800 font-bold">1</span>
                </div>
                <div>
                  <p className="font-medium text-yellow-900">Registration Submitted</p>
                  <p className="text-sm text-yellow-700">Your details have been sent to the owner</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-yellow-200 flex items-center justify-center flex-shrink-0">
                  <span className="text-yellow-800 font-bold">2</span>
                </div>
                <div>
                  <p className="font-medium text-yellow-900">Under Review</p>
                  <p className="text-sm text-yellow-700">The owner will review your registration</p>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-yellow-100 flex items-center justify-center flex-shrink-0">
                  <span className="text-yellow-600 font-bold">3</span>
                </div>
                <div>
                  <p className="font-medium text-yellow-800">Approval Decision</p>
                  <p className="text-sm text-yellow-600">You'll receive an email notification</p>
                </div>
              </div>
            </div>
          </div>

          {/* Email Notification Info */}
          {email && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Mail className="w-5 h-5 text-blue-600 mt-0.5" />
                <div>
                  <p className="text-sm text-blue-800">
                    <strong>Check your email:</strong> {email}
                  </p>
                  <p className="text-xs text-blue-700 mt-1">
                    You'll receive a confirmation email with your login credentials once your account is approved.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Welcome Message */}
          <div className="text-center py-6 border-t border-slate-200">
            <Building2 className="w-12 h-12 text-orange-500 mx-auto mb-4" />
            <h3 className="text-xl font-bold text-slate-900 mb-2">
              Welcome to the 4th Dimension Family!
            </h3>
            <p className="text-slate-600">
              We're excited to have you on board and look forward to your valuable contribution.
            </p>
            <p className="text-sm text-slate-500 mt-4 italic">
              "Building Dreams, Creating Realities"
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <Button 
              onClick={() => navigate('/login')}
              className="flex-1 bg-orange-500 hover:bg-orange-600"
            >
              Go to Login Page
            </Button>
            <Button 
              onClick={handleLogout}
              variant="outline"
              className="flex-1"
            >
              Back to Home
            </Button>
          </div>

          {/* Support Info */}
          <div className="text-center">
            <p className="text-xs text-slate-500">
              Questions? Contact us at contact@4thdimensionarchitect.com
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
