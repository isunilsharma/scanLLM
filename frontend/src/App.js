import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Header from './components/Header';
import Footer from './components/Footer';
import Home from './pages/Home';
import HowItWorks from './pages/HowItWorks';
import About from './pages/About';
import Blog from './pages/Blog';
import BlogPost from './pages/BlogPost';
import { Toaster } from './components/ui/sonner';
import './App.css';

function App() {
  useEffect(() => {
    // Hide "Made with Emergent" badge injected by platform
    const hideEmergentBadge = () => {
      const badges = document.querySelectorAll('p, a, div');
      badges.forEach(el => {
        if (el.textContent && el.textContent.includes('Made with Emergent')) {
          const parent = el.closest('a') || el.closest('div') || el;
          if (parent) {
            parent.style.display = 'none';
            parent.style.visibility = 'hidden';
          }
        }
      });
    };
    
    // Run immediately and periodically in case badge is injected later
    hideEmergentBadge();
    const interval = setInterval(hideEmergentBadge, 1000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <BrowserRouter>
      <div className="App flex flex-col min-h-screen">
        <Toaster position="top-right" />
        <Header />
        <main className="flex-1">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/blog" element={<Blog />} />
            <Route path="/blog/:id" element={<BlogPost />} />
            <Route path="/about" element={<About />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </BrowserRouter>
  );
}

export default App;
