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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-blue-50 to-slate-100 p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-600 rounded-2xl mb-4 shadow-lg">
            <Building2 className="w-9 h-9 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-2">4th Dimension</h1>
        </div>

        <Card className="shadow-xl border-0">
          <CardContent className="p-8">
            <div className="text-center space-y-6">
              <div className="inline-flex items-center justify-center w-20 h-20 bg-amber-100 rounded-full">
                <Clock className="w-10 h-10 text-amber-600" />
              </div>

              <div>
                <h2 className="text-2xl font-bold text-slate-900 mb-2">Registration Complete!</h2>
                <p className="text-slate-600">Your account is pending approval</p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left space-y-3">
                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">Profile Completed</p>
                    <p className="text-xs text-slate-600">Your details have been submitted successfully</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-green-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">Mobile & Email Verified</p>
                    <p className="text-xs text-slate-600">Both verifications completed</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-sm font-medium text-slate-900">Awaiting Administrator Approval</p>
                    <p className="text-xs text-slate-600">The owner or administrator will review your registration</p>
                  </div>
                </div>
              </div>

              <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
                <p className="text-sm text-slate-700">
                  <strong>What happens next?</strong>
                </p>
                <p className="text-xs text-slate-600 mt-2">
                  The owner (Deepak Sahajwani) or an administrator will review your registration details and approve your account. You'll receive an email once your account is activated.
                </p>
              </div>

              <Button 
                variant="outline" 
                className="w-full" 
                onClick={handleLogout}
                data-testid="logout-btn"
              >
                Back to Login
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
