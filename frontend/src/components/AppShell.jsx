import React, { useEffect, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import AppSidebar from './AppSidebar';
import AppHeader from './AppHeader';

const AppShell = () => {
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  // Lock body scroll when sidebar is open on mobile
  useEffect(() => {
    if (sidebarOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [sidebarOpen]);

  // Cmd/Ctrl+K keyboard shortcut to focus search
  const handleKeyDown = useCallback((e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      // Find and focus the search input in the sidebar
      const searchInput = document.querySelector('[placeholder="Search repos..."]');
      if (searchInput) {
        searchInput.focus();
        // Open sidebar on mobile if needed
        setSidebarOpen(true);
      }
    }
  }, []);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  return (
    <div className="flex h-screen bg-zinc-950 overflow-hidden">
      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 md:hidden transition-opacity duration-300 ease-in-out"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Left Sidebar - Responsive Drawer */}
      <div className={`
        fixed md:static inset-y-0 left-0 z-50
        w-[90vw] max-w-[420px] md:w-80
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
      `}>
        <AppSidebar onRepoSelect={() => setSidebarOpen(false)} onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col overflow-hidden transition-all duration-300 ease-in-out">
        <AppHeader onMenuClick={() => setSidebarOpen(!sidebarOpen)} sidebarOpen={sidebarOpen} />
        <main className="flex-1 overflow-y-auto transition-all duration-200 ease-in-out">
          <Outlet />
        </main>
      </div>
    </div>
  );
};

export default AppShell;
