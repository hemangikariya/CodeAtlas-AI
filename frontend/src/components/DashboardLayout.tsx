import React from 'react';
import { Outlet, useNavigate, NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LayoutDashboard, LogOut, Code, FolderGit2, ShieldCheck, User as UserIcon } from 'lucide-react';

export const DashboardLayout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-background">
      {/* Sidebar navigation */}
      <aside className="w-64 border-r border-border bg-surface flex flex-col justify-between">
        <div>
          {/* Logo container */}
          <div className="h-16 flex items-center px-6 gap-3 border-b border-border">
            <span className="text-2xl">🗺️</span>
            <h1 className="font-bold text-lg tracking-wider text-textPrimary bg-gradient-to-r from-primary to-violet-400 bg-clip-text text-transparent">
              CodeAtlas AI
            </h1>
          </div>

          {/* Nav Items */}
          <nav className="p-4 space-y-1">
            <NavLink
              to="/dashboard"
              end
              className={({ isActive }) =>
                `flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-primary text-white shadow-lg shadow-primary/20'
                    : 'text-textSecondary hover:bg-border/40 hover:text-textPrimary'
                }`
              }
            >
              <LayoutDashboard size={18} />
              Projects Hub
            </NavLink>
          </nav>
        </div>

        {/* Footer profile & logout */}
        <div className="p-4 border-t border-border space-y-3 bg-background/20">
          <div className="flex items-center gap-3 px-2">
            <div className="w-10 h-10 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center text-primary font-bold">
              <UserIcon size={16} />
            </div>
            <div className="overflow-hidden">
              <p className="text-xs text-textSecondary truncate font-medium">{user?.email}</p>
              <span className={`inline-block mt-0.5 text-[10px] font-bold px-2 py-0.5 rounded-full ${
                user?.role === 'ADMIN' 
                  ? 'bg-danger/10 text-danger border border-danger/20' 
                  : 'bg-primary/10 text-primary border border-primary/20'
              }`}>
                {user?.role}
              </span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-2.5 rounded-lg text-sm font-medium text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-all duration-200"
          >
            <LogOut size={18} />
            Logout
          </button>
        </div>
      </aside>

      {/* Main content display */}
      <main className="flex-1 flex flex-col overflow-hidden bg-background">
        {/* Top Header */}
        <header className="h-16 border-b border-border bg-surface/50 backdrop-blur-md flex items-center justify-between px-8">
          <h2 className="text-sm font-semibold text-textSecondary uppercase tracking-wider">
            Enterprise Management Console
          </h2>
          <div className="flex items-center gap-4 text-xs font-semibold text-textSecondary bg-border/40 px-3 py-1.5 rounded-lg border border-border">
            <ShieldCheck size={14} className="text-success" />
            VPC Isolated Session
          </div>
        </header>

        {/* Dynamic page content container */}
        <section className="flex-1 overflow-y-auto p-8 scrollbar-hide">
          <Outlet />
        </section>
      </main>
    </div>
  );
};
