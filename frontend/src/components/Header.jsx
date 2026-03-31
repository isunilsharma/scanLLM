import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Logo from './Logo';
import { Menu, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';

const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const isActive = (path) => location.pathname === path;

  const navLinkClass = (path) => `
    text-sm font-medium transition-colors hover:text-indigo-400
    ${isActive(path) ? 'text-indigo-400 font-semibold' : 'text-zinc-300'}
  `;

  const navLinks = [
    { path: '/', label: 'Home' },
    { path: '/how-it-works', label: 'How It Works' },
    { path: '/blog', label: 'Blog' },
    { path: '/about', label: 'About' }
  ];

  const handleLinkClick = () => {
    setIsMenuOpen(false);
  };

  return (
    <header className="sticky top-0 z-50 bg-zinc-950 backdrop-blur-xl border-b border-zinc-800/50">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Logo */}
          <Link to="/" className="flex-shrink-0" onClick={handleLinkClick}>
            <Logo />
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map(({ path, label }) => (
              <Link key={path} to={path} className={navLinkClass(path)}>
                {label}
              </Link>
            ))}

            {isAuthenticated && user ? (
              <button
                onClick={() => navigate('/app/repos')}
                className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-zinc-800 transition-colors"
              >
                {user.avatar_url && (
                  <img src={user.avatar_url} alt={user.login} className="w-8 h-8 rounded-full ring-2 ring-indigo-500/50" />
                )}
                <span className="text-sm font-medium text-zinc-200">@{user.login}</span>
              </button>
            ) : (
              <Button
                onClick={() => navigate('/demo')}
                size="sm"
                className="bg-indigo-600 hover:bg-indigo-500 text-white text-sm px-4"
              >
                Try Demo
              </Button>
            )}
          </nav>

          {/* Mobile Hamburger */}
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="md:hidden p-2 text-zinc-400 hover:text-zinc-100 transition-colors"
            aria-label="Toggle navigation"
            aria-expanded={isMenuOpen}
            aria-controls="mobile-nav-menu"
          >
            {isMenuOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>

        {/* Mobile Navigation */}
        <div
          id="mobile-nav-menu"
          role="navigation"
          className={`md:hidden overflow-hidden transition-all duration-300 ease-in-out ${
            isMenuOpen ? 'max-h-screen opacity-100' : 'max-h-0 opacity-0 pointer-events-none'
          }`}
        >
          <nav className="py-4 space-y-1">
            {navLinks.map(({ path, label }) => (
              <Link
                key={path}
                to={path}
                onClick={handleLinkClick}
                className={`block py-3 px-4 rounded-lg transition-colors ${
                  isActive(path)
                    ? 'bg-indigo-500/10 text-indigo-400 font-semibold'
                    : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
                }`}
              >
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
