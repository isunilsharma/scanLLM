import React from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';

const Settings = () => {
  const { user, logout } = useAuth();

  return (
    <div className="p-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-zinc-100 mb-6">Settings</h1>

        {/* GitHub Connection */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6 mb-6">
          <h2 className="text-xl font-semibold text-zinc-100 mb-4">GitHub Connection</h2>

          {user ? (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                {user.avatar_url && (
                  <img src={user.avatar_url} alt={user.login} className="w-16 h-16 rounded-full" />
                )}
                <div>
                  <p className="font-medium text-zinc-100">Connected as @{user.login}</p>
                  <p className="text-sm text-zinc-400">{user.email || 'No email provided'}</p>
                </div>
              </div>

              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium text-zinc-100">Active</span>
                  </div>
                  <p className="text-xs text-zinc-400">Your GitHub connection is active and working</p>
                </div>
                <Button onClick={logout} variant="destructive">
                  Disconnect GitHub
                </Button>
              </div>

              <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4 mt-4">
                <h4 className="text-sm font-semibold text-blue-300 mb-2">Permissions</h4>
                <ul className="text-sm text-blue-400 space-y-1">
                  <li>Read repository contents (read-only)</li>
                  <li>Read organization membership</li>
                  <li>No write access to any repositories</li>
                </ul>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-zinc-400 mb-4">No GitHub connection found</p>
              <Button onClick={() => window.location.href = '/'}>
                Connect GitHub
              </Button>
            </div>
          )}
        </div>

        {/* Account Info */}
        <div className="bg-zinc-900 rounded-lg border border-zinc-800 p-6">
          <h2 className="text-xl font-semibold text-zinc-100 mb-4">Account</h2>
          <div className="space-y-2 text-sm text-zinc-400">
            <p>User ID: {user?.id || 'Not available'}</p>
            <p>GitHub ID: {user?.github_user_id || 'Not available'}</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
