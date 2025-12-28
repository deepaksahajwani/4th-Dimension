import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Building2, LayoutDashboard, FolderOpen, Users, DollarSign, FileText, CheckSquare, Settings, LogOut, Menu, X, Target, Clock, BookOpen, Store } from 'lucide-react';
import { Button } from '@/components/ui/button';
import NotificationBell from './NotificationBell';

export default function Layout({ children, user, onLogout }) {
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Check if user is external (client, contractor, consultant, vendor)
  const isExternalUser = user?.role && ['client', 'contractor', 'consultant', 'vendor'].includes(user.role);
  
  const navigation = isExternalUser ? [
    // Simplified menu for external users
    { name: 'Dashboard', href: '/external-dashboard', icon: LayoutDashboard },
    { name: 'Projects', href: '/projects', icon: FolderOpen },
  ] : [
    // Full menu for internal users (owner, team members)
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    ...(user?.is_owner ? [{ name: 'Pending Approvals', href: '/pending-registrations', icon: Clock }] : []),
    ...(user?.is_owner ? [{ name: 'Work Tracker', href: '/work-tracker', icon: CheckSquare }] : []),
    ...(user?.is_owner ? [{ name: 'Assign Targets', href: '/assign-targets', icon: Target }] : []),
    ...(!user?.is_owner ? [{ name: 'My Work', href: '/my-work', icon: CheckSquare }] : []),
    { name: 'Projects', href: '/projects', icon: FolderOpen },
    { name: 'Clients', href: '/clients', icon: Users },
    { name: 'Contractors', href: '/contractors', icon: Building2 },
    { name: 'Consultants', href: '/consultants', icon: FileText },
    { name: 'Vendors', href: '/vendors', icon: Store },
    { name: 'Team', href: '/team', icon: Users },
    { name: 'Resources', href: '/resources', icon: BookOpen },
    ...(user?.is_owner ? [{ name: 'Accounting', href: '/accounting', icon: DollarSign }] : []),
  ];

  const mobileBottomNav = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Projects', href: '/projects', icon: FolderOpen },
    { name: 'Clients', href: '/clients', icon: Users },
    { name: 'Team', href: '/team', icon: Users },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 z-50 bg-white border-b border-slate-200">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2">
            <div className="flex items-center justify-center w-8 h-8 bg-orange-600 rounded-lg">
              <Building2 className="w-5 h-5 text-white" />
            </div>
            <h1 className="text-base font-bold text-slate-900">4th Dimension</h1>
          </div>
          <div className="flex items-center gap-2">
            <NotificationBell user={user} />
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 text-slate-600 hover:bg-slate-100 rounded-lg"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu Overlay */}
      {mobileMenuOpen && (
        <div className="lg:hidden fixed inset-0 z-40 bg-black bg-opacity-50" onClick={() => setMobileMenuOpen(false)} />
      )}

      {/* Mobile Slide-out Menu */}
      <div className={`lg:hidden fixed top-0 right-0 bottom-0 z-50 w-64 bg-white transform transition-transform duration-300 ${
        mobileMenuOpen ? 'translate-x-0' : 'translate-x-full'
      }`}>
        <div className="flex flex-col h-full">
          {/* User info */}
          <div className="px-4 py-6 border-b border-slate-200">
            <p className="text-sm font-medium text-slate-900 truncate">{user?.name}</p>
            <p className="text-xs text-slate-500 capitalize mt-1">
              {user?.is_owner ? 'Owner' : user?.is_admin ? 'Administrator' : user?.role?.replace('_', ' ')}
            </p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/');
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center gap-3 px-3 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-orange-50 text-orange-700 font-medium'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Logout */}
          <div className="p-3 border-t border-slate-200">
            <Button
              variant="ghost"
              className="w-full justify-start text-slate-600 hover:text-red-600 hover:bg-red-50"
              onClick={() => {
                setMobileMenuOpen(false);
                onLogout();
              }}
            >
              <LogOut className="w-5 h-5 mr-3" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Desktop Sidebar */}
      <div className="hidden lg:block fixed inset-y-0 left-0 w-64 bg-white border-r border-slate-200">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-200">
            <div className="flex items-center justify-center w-10 h-10 bg-orange-600 rounded-lg">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">4th Dimension</h1>
            </div>
          </div>

          {/* User info */}
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-medium text-slate-900 truncate" title={user?.name}>
              {user?.name}
            </p>
            <p className="text-xs text-slate-500 capitalize">
              {user?.is_owner ? 'Owner' : user?.is_admin ? 'Administrator' : user?.role?.replace('_', ' ')}
            </p>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/');
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  data-testid={`nav-${item.name.toLowerCase()}`}
                  className={`flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-orange-50 text-orange-700 font-medium'
                      : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Logout */}
          <div className="p-3 border-t border-slate-200">
            <Button
              variant="ghost"
              className="w-full justify-start text-slate-600 hover:text-red-600 hover:bg-red-50"
              onClick={onLogout}
              data-testid="logout-btn"
            >
              <LogOut className="w-5 h-5 mr-3" />
              Logout
            </Button>
          </div>
        </div>
      </div>

      {/* Mobile Bottom Navigation */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 safe-area-inset-bottom">
        <nav className="flex items-center justify-around px-2 py-2">
          {mobileBottomNav.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href || location.pathname.startsWith(item.href + '/');
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex flex-col items-center gap-1 px-3 py-2 rounded-lg min-w-[60px] ${
                  isActive
                    ? 'text-orange-600'
                    : 'text-slate-500'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span className="text-xs font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Desktop Top Bar */}
      <div className="hidden lg:block fixed top-0 left-64 right-0 z-30 bg-white border-b border-slate-200">
        <div className="flex items-center justify-end px-6 py-3">
          <NotificationBell user={user} />
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64 pt-14 lg:pt-14 pb-16 lg:pb-0">
        <div className="p-4 sm:p-6 lg:p-8">{children}</div>
      </div>
    </div>
  );
}
