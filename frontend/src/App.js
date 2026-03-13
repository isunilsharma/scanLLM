import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Header from './components/Header';
import Footer from './components/Footer';
import AppShell from './components/AppShell';
import Home from './pages/Home';
import HowItWorks from './pages/HowItWorks';
import About from './pages/About';
import Blog from './pages/Blog';
import BlogPost from './pages/BlogPost';
import DemoPage from './pages/DemoPage';
import ScanPage from './pages/ScanPage';
import AppRepos from './pages/AppRepos';
import RepoDashboard from './pages/RepoDashboard';
import ScanHistory from './pages/ScanHistory';
import AuthCallback from './pages/AuthCallback';
import OAuthCallback from './pages/OAuthCallback';
import Settings from './pages/Settings';
import ProtectedRoute from './components/ProtectedRoute';
import ErrorBoundary from './components/ErrorBoundary';
import { Toaster } from './components/ui/sonner';
import './App.css';
import './shimmer.css';

function App() {
  return (
    <ErrorBoundary>
    <AuthProvider>
      <BrowserRouter>
        <Toaster position="top-right" />
        <Routes>
          {/* Marketing Routes */}
          <Route path="/" element={
            <div className="flex flex-col min-h-screen">
              <Header />
              <main className="flex-1"><Home /></main>
              <Footer />
            </div>
          } />
          <Route path="/how-it-works" element={
            <div className="flex flex-col min-h-screen">
              <Header />
              <main className="flex-1"><HowItWorks /></main>
              <Footer />
            </div>
          } />
          <Route path="/blog" element={
            <div className="flex flex-col min-h-screen">
              <Header />
              <main className="flex-1"><Blog /></main>
              <Footer />
            </div>
          } />
          <Route path="/blog/:id" element={
            <div className="flex flex-col min-h-screen">
              <Header />
              <main className="flex-1"><BlogPost /></main>
              <Footer />
            </div>
          } />
          <Route path="/about" element={
            <div className="flex flex-col min-h-screen">
              <Header />
              <main className="flex-1"><About /></main>
              <Footer />
            </div>
          } />
          <Route path="/demo" element={
            <div className="flex flex-col min-h-screen">
              <Header />
              <main className="flex-1"><DemoPage /></main>
              <Footer />
            </div>
          } />
          <Route path="/scan/:scanId" element={
            <div className="flex flex-col min-h-screen">
              <Header />
              <main className="flex-1"><ScanPage /></main>
              <Footer />
            </div>
          } />
          
          {/* OAuth Callback Handlers */}
          <Route path="/auth/callback" element={<AuthCallback />} />
          <Route path="/api/auth/github/callback" element={<OAuthCallback />} />
          
          {/* App Routes with Sidebar */}
          <Route path="/app" element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/app/repos" replace />} />
            <Route path="repos" element={<AppRepos />} />
            <Route path="repo/:owner/:repo" element={<RepoDashboard />} />
            <Route path="repo/:owner/:repo/scan/:scanId" element={<ScanPage />} />
            <Route path="history" element={<ScanHistory />} />
            <Route path="settings" element={<Settings />} />
          </Route>
          
          {/* Legacy redirect */}
          <Route path="/private/repos" element={<Navigate to="/app/repos" replace />} />
          
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
    </ErrorBoundary>
  );
}

export default App;
