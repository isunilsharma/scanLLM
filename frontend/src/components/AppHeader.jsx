import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';
import { Menu, X } from 'lucide-react';
import Logo from './Logo';

const AppHeader = ({ onMenuClick, sidebarOpen }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          {/* Mobile Menu Button */}
          <button
            onClick={onMenuClick}
            className="md:hidden p-2 text-gray-600 hover:text-gray-900"
            aria-label="Toggle menu"
          >
            {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
          
          <button onClick={() => navigate('/')} className="flex items-center gap-2">
            <Logo size="default" />
          </button>
        </div>
        
        <div className="flex items-center gap-4">
          {user && (
            <div className="flex items-center gap-3">
              {user.avatar_url && (
                <img src={user.avatar_url} alt={user.login} className="w-8 h-8 rounded-full" />
              )}
              <span className="text-sm font-medium text-gray-900 hidden sm:block">@{user.login}</span>
            </div>
          )}
          <Button onClick={logout} variant="outline" size="sm">
            Disconnect
          </Button>
        </div>
      </div>
    </header>
  );
};

export default AppHeader;
