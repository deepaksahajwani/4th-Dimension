import { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import axios from 'axios';
import '@/App.css';
import { Toaster, toast } from 'sonner';

// Components
import LoginPage from './pages/LoginPage';
import RegisterInfo from './pages/RegisterInfo';
import Dashboard from './pages/Dashboard';
import WorkTracker from './pages/WorkTracker';
import MyWork from './pages/MyWork';
import AssignTargets from './pages/AssignTargets';
import Projects from './pages/Projects';
import ProjectDetail from './pages/ProjectDetail';
import Clients from './pages/Clients';
import ClientDetail from './pages/ClientDetail';
import Team from './pages/Team';
import TeamMemberDetail from './pages/TeamMemberDetail';
import ManageTeam from './pages/ManageTeam';
import Accounting from './pages/Accounting';
import Drawings from './pages/Drawings';
import Tasks from './pages/Tasks';
import Settings from './pages/Settings';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
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
      window.location.href = '/';
    }
    return Promise.reject(error);
  }
);

function ProtectedRoute({ children }) {
  const token = localStorage.getItem('token');
  if (!token) {
    return <Navigate to="/" replace />;
  }
  return children;
}

function App() {
  const [user, setUser] = useState(null);
  const [isProcessingOAuth, setIsProcessingOAuth] = useState(false);

  useEffect(() => {
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
        console.log('Redirecting to dashboard');
        toast.success('Logged in successfully!');
        window.location.href = '/dashboard';
      }
    } catch (error) {
      console.error('Google auth error:', error);
      toast.error('Google authentication failed');
    } finally {
      setIsProcessingOAuth(false);
    }
  };

  const handleLogin = (userData, token) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
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
            <Route path="/register-info" element={<RegisterInfo onLogin={handleLogin} />} />
            <Route
              path="/dashboard"
              element={
                <ProtectedRoute>
                  <Dashboard user={user} onLogout={handleLogout} />
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
              path="/my-work"
              element={
                <ProtectedRoute>
                  <MyWork user={user} onLogout={handleLogout} />
                </ProtectedRoute>
              }
            />

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
              path="/accounting"
              element={
                <ProtectedRoute>
                  <Accounting user={user} onLogout={handleLogout} />
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
          </Routes>
        )}
      </BrowserRouter>
    </div>
  );
}

export default App;
