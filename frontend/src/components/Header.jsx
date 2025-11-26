import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import Logo from './Logo';

const Header = () => {
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;
  
  const navLinkClass = (path) => `
    text-sm font-medium transition-colors hover:text-primary
    ${isActive(path) ? 'text-primary font-semibold' : 'text-gray-600'}
  `;

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex-shrink-0">
            <Logo />
          </Link>
          
          {/* Navigation */}
          <nav className="flex items-center gap-8">
            <Link to="/" className={navLinkClass('/')}>
              Home
            </Link>
            <Link to="/how-it-works" className={navLinkClass('/how-it-works')}>
              How It Works
            </Link>
            <Link to="/blog" className={navLinkClass('/blog')}>
              Blog
            </Link>
            <Link to="/about" className={navLinkClass('/about')}>
              About Us
            </Link>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
