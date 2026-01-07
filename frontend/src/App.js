import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';
import { Toaster, toast } from 'sonner';

// Components
import LoginPage from './pages/LoginPage';
import RegisterInfo from './pages/RegisterInfo';
import PublicRegister from './pages/PublicRegister';
import VerifyOTP from './pages/VerifyOTP';
import SetPassword from './pages/SetPassword';
import PendingApproval from './pages/PendingApproval';
import NotRegistered from './pages/NotRegistered';
import ApprovalSuccess from './pages/ApprovalSuccess';
import EmailPreview from './pages/EmailPreview';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import Dashboard from './pages/Dashboard';
import ExternalDashboard from './pages/ExternalDashboard';
import WeeklyDashboard from './pages/WeeklyDashboard';
import OwnerDashboard from './pages/OwnerDashboard';
import ClientDashboard from './pages/ClientDashboard';
import WorkTracker from './pages/WorkTracker';
import MyWork from './pages/MyWork';
import AssignTargets from './pages/AssignTargets';
import Contractors from './pages/Contractors';
import Consultants from './pages/Consultants';
import Vendors from './pages/Vendors';
import Projects from './pages/Projects';
import VerifyEmail from './pages/VerifyEmail';
import VerifyPhone from './pages/VerifyPhone';
import ProjectDetail from './pages/ProjectDetail';
import ExternalProjectDetail from './pages/ExternalProjectDetail';
import Clients from './pages/Clients';
import ClientDetail from './pages/ClientDetail';
import Team from './pages/Team';
import TeamMemberDetail from './pages/TeamMemberDetail';
import ManageTeam from './pages/ManageTeam';
import Notifications from './pages/Notifications';
import PendingRegistrations from './pages/PendingRegistrations';
import Accounting from './pages/Accounting';
import Drawings from './pages/Drawings';
import Tasks from './pages/Tasks';
import Settings from './pages/Settings';
import Resources from './pages/Resources';
import SystemLogs from './pages/SystemLogs';
import TeamLeaderDashboard from './pages/TeamLeaderDashboard';
import TeamLeaderProjectDetail from './pages/TeamLeaderProjectDetail';
import DrawingReviewPage from './pages/DrawingReviewPage';
import DrawingTemplates from './pages/DrawingTemplates';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Helper function to get cookie value
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

// Helper function to check for magic link auth (cookie-based)
function checkMagicLinkAuth() {
  // Check for user_info cookie (set by magic link - non-httponly)
  const userInfoCookie = getCookie('user_info');
  
  if (userInfoCookie) {
    try {
      const userInfo = JSON.parse(decodeURIComponent(userInfoCookie));
      
      // The auth_token cookie is httponly, so we can't read it directly
      // But it will be sent automatically with API requests as a cookie
      // We need to store a flag that tells the app to use cookie-based auth
      localStorage.setItem('use_cookie_auth', 'true');
      localStorage.setItem('user', JSON.stringify(userInfo));
      
      // Clear the user_info cookie after reading (optional - one-time read)
      // document.cookie = 'user_info=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
      
      return userInfo;
    } catch (e) {
      console.error('Error parsing magic link user info:', e);
    }
  }
  
  return null;
}

// Configure axios interceptors
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    const useCookieAuth = localStorage.getItem('use_cookie_auth');
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Only set withCredentials for authenticated requests when using cookie auth
    // Don't set it for login/register to avoid CORS preflight issues
    if (useCookieAuth && !config.url?.includes('/auth/login') && !config.url?.includes('/auth/register')) {
      config.withCredentials = true;
    }
    
    return config;
  },
  (error) => Promise.reject(error)
);

axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('use_cookie_auth');
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

function ProtectedRoute({ children }) {
  // Check localStorage first for regular token-based auth
  let token = localStorage.getItem('token');
  
  // Check if we should use cookie-based auth (magic link)
  const useCookieAuth = localStorage.getItem('use_cookie_auth');
  const userInfoCookie = getCookie('user_info');
  
  // If no token in localStorage, check for magic link cookie auth
  if (!token && userInfoCookie) {
    try {
      const userInfo = JSON.parse(decodeURIComponent(userInfoCookie));
      localStorage.setItem('use_cookie_auth', 'true');
      localStorage.setItem('user', JSON.stringify(userInfo));
      
      // For cookie-based auth, we don't have a token in localStorage
      // but the httponly auth_token cookie will be sent with requests
      return children;
    } catch (e) {
      console.error('Error processing magic link auth in ProtectedRoute:', e);
    }
  }
  
  // Allow access if we have either a token or cookie-based auth
  if (token || useCookieAuth) {
    return children;
  }
  
  return <Navigate to="/" replace />;
}

function App() {
  const [user, setUser] = useState(null);
  const [isProcessingOAuth, setIsProcessingOAuth] = useState(false);

  useEffect(() => {
    // First check for magic link auth (cookie-based)
    const magicLinkUser = checkMagicLinkAuth();
    if (magicLinkUser) {
      setUser(magicLinkUser);
      return;
    }
    
    // Then check localStorage
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }

    // Check for Google OAuth session_id in URL fragment
    const hash = window.location.hash;
    if (hash.includes('session_id=')) {
      setIsProcessingOAuth(true);
      const sessionId = hash.split('session_id=')[1].split('&')[0];
      handleGoogleAuth(sessionId);
    }
  }, []);

  const handleGoogleAuth = async (sessionId) => {
    console.log('Google auth started with session:', sessionId);
    try {
      const response = await axios.post(`${API}/auth/google/session?session_id=${sessionId}`);
      console.log('Google auth response:', response.data);
      
      // Check approval status
      if (response.data.user.approval_status === 'pending') {
        toast.warning('Your account is pending approval');
        window.location.href = '/pending-approval';
        return;
      }
      
      if (response.data.user.approval_status === 'rejected') {
        toast.error('Your registration was not approved. Please contact support.');
        window.location.href = '/login';
        return;
      }
      
      localStorage.setItem('token', response.data.session_token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
      setUser(response.data.user);
      window.location.hash = '';
      
      // Check if profile completion is required
      if (response.data.requires_profile_completion) {
        console.log('Redirecting to register-info');
        toast.success('Please complete your registration!');
        window.location.href = '/register-info';
      } else {
        // Role-based redirection
        const userRole = response.data.user.role;
        const isInternalTeamMember = ['senior_architect', 'junior_architect', 'senior_interior_designer', 
          'junior_interior_designer', 'associate_architect', 'associate_interior_designer',
          'landscape_designer', '3d_visualizer', 'site_engineer', 'site_supervisor', 'intern'].includes(userRole);
        
        if (userRole === 'client' || userRole === 'contractor' || userRole === 'consultant' || userRole === 'vendor') {
          console.log('Redirecting to external dashboard');
          toast.success('Logged in successfully!');
          window.location.href = '/external-dashboard';
        } else if (isInternalTeamMember || userRole === 'team_member' || userRole === 'team_leader') {
          console.log('Redirecting to team leader dashboard');
          toast.success('Logged in successfully!');
          window.location.href = '/team-leader';
        } else {
          console.log('Redirecting to dashboard');
          toast.success('Logged in successfully!');
          window.location.href = '/dashboard';
        }
      }
    } catch (error) {
      console.error('Google auth error:', error);
      toast.error('Google authentication failed');
    } finally {
      setIsProcessingOAuth(false);
    }
  };

  const handleLogin = (userData, token, keepLoggedIn = false) => {
    if (keepLoggedIn) {
      // Store in localStorage for persistent login
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(userData));
      localStorage.setItem('keepLoggedIn', 'true');
    } else {
      // Store only in sessionStorage for session-based login
      sessionStorage.setItem('token', token);
      sessionStorage.setItem('user', JSON.stringify(userData));
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(userData));
    }
    setUser(userData);
  };

  const handleLogout = async () => {
    try {
      await axios.post(`${API}/auth/logout`);
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      localStorage.removeItem('use_cookie_auth');
      setUser(null);
      window.location.href = '/';
    }
  };

  return (
    <div className="App">
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        {isProcessingOAuth ? (
          <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900">
            <div className="text-center">
              <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-orange-500 mx-auto mb-4"></div>
              <p className="text-white text-lg">Processing authentication...</p>
            </div>
          </div>
        ) : (
          <Routes>
            <Route path="/" element={<LoginPage onLogin={handleLogin} />} />
            <Route path="/login" element={<LoginPage onLogin={handleLogin} />} />
            <Route path="/register" element={<PublicRegister />} />
            <Route path="/verify-otp" element={<VerifyOTP />} />
            <Route path="/set-password" element={<SetPassword />} />
            <Route path="/pending-approval" element={<PendingApproval />} />
            <Route path="/not-registered" element={<NotRegistered />} />
            <Route path="/approval-success" element={<ApprovalSuccess />} />
            <Route path="/email-preview" element={<EmailPreview />} />
            <Route path="/forgot-password" element={<ForgotPassword />} />
            <Route path="/reset-password" element={<ResetPassword />} />
            <Route path="/register-info" element={<RegisterInfo onLogin={handleLogin} />} />
            <Route path="/verify-email" element={<VerifyEmail />} />
            <Route path="/verify-phone" element={<VerifyPhone />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/external-dashboard"
              element={
                <ProtectedRoute>
                  <ExternalDashboard user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/project/:projectId"
              element={
                <ProtectedRoute>
                  <ExternalProjectDetail user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/weekly-dashboard"
              element={
                <ProtectedRoute>
                  <WeeklyDashboard user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/owner-dashboard"
              element={
                <ProtectedRoute>
                  <OwnerDashboard user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/client-dashboard"
              element={
                <ProtectedRoute>
                  <ClientDashboard user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/work-tracker"
              element={
                <ProtectedRoute>
                  <WorkTracker user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/my-work"
              element={
                <ProtectedRoute>
                  <MyWork user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/assign-targets"
              element={
                <ProtectedRoute>
                  <AssignTargets user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/contractors"
              element={
                <ProtectedRoute>
                  <Contractors user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />

            <Route
              path="/consultants"
              element={
                <ProtectedRoute>
                  <Consultants user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />

            <Route
              path="/vendors"
              element={
                <ProtectedRoute>
                  <Vendors user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />

            <Route
              path="/projects"
              element={
                <ProtectedRoute>
                  <Projects user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects/:projectId"
              element={
                <ProtectedRoute>
                  <ProjectDetail user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/clients"
              element={
                <ProtectedRoute>
                  <Clients user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/clients/:clientId"
              element={
                <ProtectedRoute>
                  <ClientDetail user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/team"
              element={
                <ProtectedRoute>
                  <Team user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />

            <Route
              path="/notifications"
              element={
                <ProtectedRoute>
                  <Notifications user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />

            <Route
              path="/team/manage"
              element={
                <ProtectedRoute>
                  <ManageTeam user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/team/:memberId"
              element={
                <ProtectedRoute>
                  <TeamMemberDetail user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/pending-registrations"
              element={
                <ProtectedRoute>
                  <PendingRegistrations user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />

            <Route
              path="/accounting"
              element={
                <ProtectedRoute>
                  <Accounting user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/system-logs"
              element={
                <ProtectedRoute>
                  <SystemLogs user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/drawings"
              element={
                <ProtectedRoute>
                  <Drawings user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/tasks"
              element={
                <ProtectedRoute>
                  <Tasks user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute>
                  <Settings user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/resources"
              element={
                <ProtectedRoute>
                  <Resources user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/team-leader"
              element={
                <ProtectedRoute>
                  <TeamLeaderDashboard user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/team-leader/project/:projectId"
              element={
                <ProtectedRoute>
                  <TeamLeaderProjectDetail user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            {/* Single-Item Review Routes for Notification Deep-Links */}
            <Route
              path="/projects/:projectId/drawing/:drawingId"
              element={
                <ProtectedRoute>
                  <DrawingReviewPage user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
            <Route
              path="/projects/:projectId/3d-image/:imageId"
              element={
                <ProtectedRoute>
                  <DrawingReviewPage user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />
          </Routes>
        )}
      </BrowserRouter>
    </div>
  );
}

export default App;
