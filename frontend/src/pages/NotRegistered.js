import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Building2, UserX, ArrowRight } from 'lucide-react';

export default function NotRegistered() {
  const navigate = useNavigate();
  const location = useLocation();
  const email = location.state?.email || '';

  return (
    <div className="min-h-screen bg-gradient-to-br from-orange-50 to-indigo-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className="flex items-center justify-center mb-4">
            <div className="relative">
              <Building2 className="w-16 h-16 text-orange-500" />
              <div className="absolute -bottom-1 -right-1 bg-red-500 rounded-full p-1">
                <UserX className="w-5 h-5 text-white" />
              </div>
            </div>
          </div>
          <CardTitle className="text-2xl font-bold text-slate-900">
            Account Not Found
          </CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Message */}
          <div className="text-center space-y-3">
            <p className="text-slate-700">
              {email ? (
                <>The email <strong>{email}</strong> is not registered with 4th Dimension.</>
              ) : (
                <>You don't have an account with 4th Dimension yet.</>
              )}
            </p>
            <p className="text-sm text-slate-600">
              Please register to get started with our platform.
            </p>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800 font-medium mb-2">
              What happens after registration?
            </p>
            <ul className="text-xs text-blue-700 space-y-1 ml-4 list-disc">
              <li>Complete the registration form</li>
              <li>Verify your email and phone number</li>
              <li>Wait for owner approval</li>
              <li>Receive confirmation email when approved</li>
            </ul>
          </div>

          {/* Action Buttons */}
          <div className="space-y-3">
            <Button 
              onClick={() => navigate('/register', { state: { email } })}
              className="w-full bg-orange-500 hover:bg-orange-600 text-white py-6"
            >
              Register Now
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>

            <Button 
              onClick={() => navigate('/login')}
              variant="outline"
              className="w-full"
            >
              Back to Login
            </Button>
          </div>

          {/* Support Info */}
          <div className="text-center pt-4 border-t">
            <p className="text-xs text-slate-500">
              Need help? Contact us at<br />
              <a href="mailto:contact@4thdimensionarchitect.com" className="text-orange-500 hover:text-orange-600">
                contact@4thdimensionarchitect.com
              </a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
