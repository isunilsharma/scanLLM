import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../components/ui/button';

const AppRepos = () => {
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center max-w-md">
        <svg className="w-24 h-24 mx-auto text-zinc-600 mb-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        <h2 className="text-2xl font-bold text-zinc-100 mb-3">Select a repository to get started</h2>
        <p className="text-zinc-400 mb-6">
          Choose a repository from the sidebar to view details and run scans
        </p>
      </div>
    </div>
  );
};

export default AppRepos;
