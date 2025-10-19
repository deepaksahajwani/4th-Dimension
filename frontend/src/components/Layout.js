import { Link, useLocation } from 'react-router-dom';
import { Building2, LayoutDashboard, FolderOpen, Users, DollarSign, FileText, CheckSquare, Settings, LogOut } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Layout({ children, user, onLogout }) {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Projects', href: '/projects', icon: FolderOpen },
    { name: 'Clients', href: '/clients', icon: Users },
    { name: 'Team', href: '/team', icon: Users },
    { name: 'Tasks', href: '/tasks', icon: CheckSquare },
    { name: 'Drawings', href: '/drawings', icon: FileText },
    ...(user?.role === 'owner' ? [{ name: 'Accounting', href: '/accounting', icon: DollarSign }] : []),
    { name: 'Settings', href: '/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Sidebar */}
      <div className="fixed inset-y-0 left-0 w-64 bg-white border-r border-slate-200">
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center gap-3 px-6 py-5 border-b border-slate-200">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-600 rounded-lg">
              <Building2 className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-slate-900">4th Dimension</h1>
            </div>
          </div>

          {/* User info */}
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
            <p className="text-sm font-medium text-slate-900">{user?.name}</p>
            <p className="text-xs text-slate-500 capitalize">{user?.role?.replace('_', ' ')}</p>
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
                      ? 'bg-blue-50 text-blue-700 font-medium'
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

      {/* Main content */}
      <div className="pl-64">
        <div className="p-8">{children}</div>
      </div>
    </div>
  );
}
