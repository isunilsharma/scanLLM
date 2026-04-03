import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { Menu, X, LogOut, Settings as SettingsIcon } from 'lucide-react';
import Logo from './Logo';

const AppHeader = ({ onMenuClick, sidebarOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);

  return (
    <header className="bg-zinc-950 border-b border-zinc-800/50 px-4 md:px-6 py-3 md:py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2 md:gap-4">
          {/* Mobile Menu Button */}
          <button
            onClick={onMenuClick}
            className="md:hidden p-2 text-zinc-400 hover:text-zinc-100 -ml-2"
            aria-label="Toggle menu"
          >
            {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>

          {/* Logo - Use actual Logo component, hide text on mobile */}
          <button onClick={() => navigate('/')} className="flex items-center">
            <div className="scale-75 md:scale-100 origin-left">
              <Logo />
            </div>
          </button>
        </div>

        {/* User Avatar with Dropdown Menu */}
        {user && (
          <div className="relative">
            <button
              onClick={() => setAccountMenuOpen(!accountMenuOpen)}
              className="flex items-center gap-2 p-1 rounded-lg hover:bg-zinc-800"
            >
              {user.avatar_url && (
                <img src={user.avatar_url} alt={user.login} className="w-8 h-8 rounded-full" />
              )}
            </button>

            {/* Account Dropdown Menu */}
            {accountMenuOpen && (
              <>
                {/* Backdrop */}
                <div
                  className="fixed inset-0 z-40"
                  onClick={() => setAccountMenuOpen(false)}
                />

                {/* Menu */}
                <div className="absolute right-0 mt-2 w-64 bg-zinc-900 rounded-lg shadow-lg shadow-black/30 border border-zinc-800 z-50">
                  <div className="p-4 border-b border-zinc-800">
                    <div className="flex items-center gap-3">
                      {user.avatar_url && (
                        <img src={user.avatar_url} alt={user.login} className="w-10 h-10 rounded-full" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="font-medium text-zinc-100 truncate">@{user.login}</p>
                        <p className="text-xs text-zinc-500 truncate">{user.email}</p>
                      </div>
                    </div>
                  </div>

                  <div className="p-2">
                    <button
                      onClick={() => {
                        setAccountMenuOpen(false);
                        navigate('/app/settings');
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm text-zinc-300 hover:bg-zinc-800 rounded"
                    >
                      <SettingsIcon className="w-4 h-4" />
                      Settings
                    </button>
                    <button
                      onClick={() => {
                        setAccountMenuOpen(false);
                        logout();
                      }}
                      className="w-full flex items-center gap-3 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded"
                    >
                      <LogOut className="w-4 h-4" />
                      Disconnect GitHub
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </header>
  );
};

export default AppHeader;
