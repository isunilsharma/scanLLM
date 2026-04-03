import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import Logo from './Logo';
import { Menu, X, ChevronDown, BookOpen, GitBranch, BarChart3, FileText } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { Button } from './ui/button';

const docsLinks = [
  { path: '/how-it-works', label: 'How It Works', icon: GitBranch, description: 'Scan engine architecture and workflow' },
  { path: '/workflow', label: 'User Workflow', icon: FileText, description: 'Personas and use-case walkthroughs' },
  { path: '/docs/grading', label: 'Risk Grading', icon: BarChart3, description: 'Score formula and grade definitions' },
];

const Header = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { isAuthenticated, user } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [docsOpen, setDocsOpen] = useState(false);
  const [mobileDocsOpen, setMobileDocsOpen] = useState(false);
  const docsRef = useRef(null);

  const isActive = (path) => location.pathname === path;
  const isDocsActive = docsLinks.some(d => isActive(d.path));

  // Close dropdown on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (docsRef.current && !docsRef.current.contains(e.target)) {
        setDocsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Close dropdown on route change
  useEffect(() => {
    setDocsOpen(false);
    setIsMenuOpen(false);
  }, [location.pathname]);

  const navLinkClass = (path) => `
    text-sm font-medium transition-colors hover:text-indigo-400
    ${isActive(path) ? 'text-indigo-400 font-semibold' : 'text-zinc-300'}
  `;

  const topLinks = [
    { path: '/', label: 'Home' },
    { path: '/blog', label: 'Blog' },
    { path: '/about', label: 'About' },
  ];

  const handleLinkClick = () => {
    setIsMenuOpen(false);
    setMobileDocsOpen(false);
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
            <Link to="/" className={navLinkClass('/')}>Home</Link>

            {/* Docs Dropdown */}
            <div ref={docsRef} className="relative">
              <button
                onClick={() => setDocsOpen(!docsOpen)}
                className={`flex items-center gap-1 text-sm font-medium transition-colors hover:text-indigo-400 ${
                  isDocsActive ? 'text-indigo-400 font-semibold' : 'text-zinc-300'
                }`}
              >
                Developer Docs
                <ChevronDown className={`w-3.5 h-3.5 transition-transform ${docsOpen ? 'rotate-180' : ''}`} />
              </button>

              {docsOpen && (
                <div className="absolute top-full left-1/2 -translate-x-1/2 mt-3 w-72 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl shadow-black/30 overflow-hidden">
                  <div className="p-2">
                    {docsLinks.map(({ path, label, icon: Icon, description }) => (
                      <Link
                        key={path}
                        to={path}
                        className={`flex items-start gap-3 px-3 py-2.5 rounded-md transition-colors ${
                          isActive(path)
                            ? 'bg-indigo-500/10 text-indigo-400'
                            : 'text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100'
                        }`}
                      >
                        <Icon className="w-4 h-4 mt-0.5 shrink-0 text-zinc-500" />
                        <div>
                          <p className="text-sm font-medium">{label}</p>
                          <p className="text-xs text-zinc-500 mt-0.5">{description}</p>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <Link to="/blog" className={navLinkClass('/blog')}>Blog</Link>
            <Link to="/about" className={navLinkClass('/about')}>About</Link>

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
            {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
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
            <Link to="/" onClick={handleLinkClick} className={`block py-3 px-4 rounded-lg transition-colors ${
              isActive('/') ? 'bg-indigo-500/10 text-indigo-400 font-semibold' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
            }`}>Home</Link>

            {/* Mobile Docs Accordion */}
            <div>
              <button
                onClick={() => setMobileDocsOpen(!mobileDocsOpen)}
                className={`w-full flex items-center justify-between py-3 px-4 rounded-lg transition-colors ${
                  isDocsActive ? 'bg-indigo-500/10 text-indigo-400 font-semibold' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
                }`}
              >
                Developer Docs
                <ChevronDown className={`w-4 h-4 transition-transform ${mobileDocsOpen ? 'rotate-180' : ''}`} />
              </button>
              {mobileDocsOpen && (
                <div className="ml-4 mt-1 space-y-1 border-l border-zinc-800 pl-3">
                  {docsLinks.map(({ path, label, icon: Icon }) => (
                    <Link
                      key={path}
                      to={path}
                      onClick={handleLinkClick}
                      className={`flex items-center gap-2 py-2 px-3 rounded-md text-sm transition-colors ${
                        isActive(path)
                          ? 'text-indigo-400 font-medium'
                          : 'text-zinc-500 hover:text-zinc-200'
                      }`}
                    >
                      <Icon className="w-3.5 h-3.5" />
                      {label}
                    </Link>
                  ))}
                </div>
              )}
            </div>

            <Link to="/blog" onClick={handleLinkClick} className={`block py-3 px-4 rounded-lg transition-colors ${
              isActive('/blog') ? 'bg-indigo-500/10 text-indigo-400 font-semibold' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
            }`}>Blog</Link>

            <Link to="/about" onClick={handleLinkClick} className={`block py-3 px-4 rounded-lg transition-colors ${
              isActive('/about') ? 'bg-indigo-500/10 text-indigo-400 font-semibold' : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
            }`}>About</Link>
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
