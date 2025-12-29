import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import Header from './components/Header';
import Footer from './components/Footer';
import Home from './pages/Home';
import HowItWorks from './pages/HowItWorks';
import About from './pages/About';
import Blog from './pages/Blog';
import BlogPost from './pages/BlogPost';
import DemoPage from './pages/DemoPage';
import ScanPage from './pages/ScanPage';
import PrivateRepos from './pages/PrivateRepos';
import ProtectedRoute from './components/ProtectedRoute';
import { Toaster } from './components/ui/sonner';
import './App.css';
import './shimmer.css';

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="App flex flex-col min-h-screen">
          <Toaster position="top-right" />
          <Header />
          <main className="flex-1">
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/demo" element={<DemoPage />} />
              <Route path="/scan/:scanId" element={<ScanPage />} />
              <Route path="/how-it-works" element={<HowItWorks />} />
              <Route path="/blog" element={<Blog />} />
              <Route path="/blog/:id" element={<BlogPost />} />
              <Route path="/about" element={<About />} />
              <Route 
                path="/private/repos" 
                element={
                  <ProtectedRoute>
                    <PrivateRepos />
                  </ProtectedRoute>
                } 
              />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </main>
          <Footer />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
