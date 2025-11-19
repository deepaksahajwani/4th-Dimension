import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Mail, Lock, Eye, EyeOff } from 'lucide-react';
import { formatErrorMessage } from '@/utils/errorHandler';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LoginPage({ onLogin }) {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [keepLoggedIn, setKeepLoggedIn] = useState(false);
  const [loginData, setLoginData] = useState({ email: '', password: '' });

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const response = await axios.post(`${API}/auth/login`, loginData);
      
      // Check approval status
      if (response.data.user.approval_status === 'pending') {
        toast.warning('Your account is pending approval');
        navigate('/pending-approval', { 
          state: { 
            email: response.data.user.email 
          } 
        });
        return;
      }
      
      if (response.data.user.approval_status === 'rejected') {
        toast.error('Your registration was not approved. Please contact support.');
        return;
      }
      
      // User is approved, proceed with login
      onLogin(response.data.user, response.data.access_token, keepLoggedIn);
      toast.success('Welcome back!');
      
      if (response.data.requires_profile_completion) {
        navigate('/register-info');
      } else {
        // Role-based redirection
        const userRole = response.data.user.role;
        if (userRole === 'client' || userRole === 'contractor' || userRole === 'consultant') {
          navigate('/projects'); // External users go directly to projects
        } else {
          navigate('/dashboard'); // Internal users go to dashboard
        }
      }
    } catch (error) {
      // If user doesn't exist, redirect to register
      if (error.response?.status === 401) {
        toast.info('Account not found. Please register.');
        navigate('/register', { state: { email: loginData.email } });
      } else {
        toast.error(formatErrorMessage(error, 'Login failed'));
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = () => {
    const redirectUrl = encodeURIComponent(`${window.location.origin}/`);
    window.location.href = `https://auth.emergentagent.com/?redirect=${redirectUrl}`;
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900 p-4">
      <div className="w-full max-w-md">
        {/* Logo and Branding */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center mb-4">
            <div className="grid grid-cols-2 gap-1 w-16 h-16">
              <div className="bg-slate-200 rounded-tl-lg"></div>
              <div className="bg-slate-200 rounded-tr-lg"></div>
              <div className="bg-slate-200 rounded-bl-lg"></div>
              <div className="bg-orange-500 rounded-br-lg"></div>
            </div>
          </div>
          <h1 className="text-4xl font-bold mb-2">
            <span className="text-white">4</span>
            <span className="text-orange-500 align-super text-2xl">th</span>
            <span className="text-white"> Dimension</span>
          </h1>
          <p className="text-orange-400 text-sm font-medium">Architects & Interior Designers</p>
        </div>

        <Card className="shadow-2xl border-0 bg-white/95 backdrop-blur">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center">Welcome Back</CardTitle>
            <CardDescription className="text-center">
              Sign in to your account to continue
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="your@email.com"
                    className="pl-10"
                    value={loginData.email}
                    onChange={(e) => setLoginData({ ...loginData, email: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-3 h-4 w-4 text-slate-400" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    className="pl-10 pr-10"
                    value={loginData.password}
                    onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-600"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </div>

              {/* Keep me logged in checkbox */}
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="keepLoggedIn"
                  checked={keepLoggedIn}
                  onChange={(e) => setKeepLoggedIn(e.target.checked)}
                  className="w-4 h-4 text-orange-500 border-slate-300 rounded focus:ring-orange-500"
                />
                <Label htmlFor="keepLoggedIn" className="text-sm text-slate-600 cursor-pointer">
                  Keep me logged in
                </Label>
              </div>

              <Button 
                type="submit" 
                className="w-full bg-orange-500 hover:bg-orange-600" 
                disabled={loading}
              >
                {loading ? 'Signing in...' : 'Sign In'}
              </Button>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t border-slate-300" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-white px-2 text-slate-500">Or continue with</span>
                </div>
              </div>

              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={handleGoogleLogin}
              >
                <svg className="mr-2 h-4 w-4" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Sign in with Google
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-slate-600">
                New here?{' '}
                <button
                  onClick={() => navigate('/register-info')}
                  className="text-orange-500 hover:text-orange-600 font-medium"
                >
                  Register now
                </button>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
