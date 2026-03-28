import React from 'react';
import { Link } from 'react-router-dom';
import { Github, Linkedin } from 'lucide-react';

const Footer = () => {
  return (
    <footer className="bg-zinc-950 border-t border-zinc-800/50">
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-2 md:col-span-1">
            <div className="font-bold text-zinc-100 text-lg mb-3">ScanLLM</div>
            <p className="text-sm text-zinc-500 leading-relaxed">
              AI Dependency Intelligence. Know what AI is in your code.
            </p>
            <div className="flex items-center gap-3 mt-4">
              <a
                href="https://github.com/isunilsharma/scanllm"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-600 hover:text-zinc-300 transition-colors"
                aria-label="GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
              <a
                href="https://www.linkedin.com/company/scanllm-ai/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-zinc-600 hover:text-zinc-300 transition-colors"
                aria-label="LinkedIn"
              >
                <Linkedin className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Product */}
          <div>
            <div className="font-medium text-zinc-300 text-sm mb-3">Product</div>
            <div className="space-y-2 text-sm">
              <div><Link to="/demo" className="text-zinc-500 hover:text-zinc-300 transition-colors">Demo</Link></div>
              <div><Link to="/how-it-works" className="text-zinc-500 hover:text-zinc-300 transition-colors">How it Works</Link></div>
              <div><Link to="/blog" className="text-zinc-500 hover:text-zinc-300 transition-colors">Blog</Link></div>
              <div><Link to="/about" className="text-zinc-500 hover:text-zinc-300 transition-colors">About</Link></div>
            </div>
          </div>

          {/* Developers */}
          <div>
            <div className="font-medium text-zinc-300 text-sm mb-3">Developers</div>
            <div className="space-y-2 text-sm">
              <div><a href="https://github.com/isunilsharma/scanllm" className="text-zinc-500 hover:text-zinc-300 transition-colors" target="_blank" rel="noreferrer">GitHub</a></div>
              <div><a href="https://github.com/isunilsharma/scanllm/issues" className="text-zinc-500 hover:text-zinc-300 transition-colors" target="_blank" rel="noreferrer">Issues</a></div>
              <div><a href="https://github.com/isunilsharma/scanllm/blob/main/CONTRIBUTING.md" className="text-zinc-500 hover:text-zinc-300 transition-colors" target="_blank" rel="noreferrer">Contributing</a></div>
            </div>
          </div>

          {/* Legal */}
          <div>
            <div className="font-medium text-zinc-300 text-sm mb-3">Legal</div>
            <div className="space-y-2 text-sm">
              <div><Link to="/privacy" className="text-zinc-500 hover:text-zinc-300 transition-colors">Privacy Policy</Link></div>
              <div><Link to="/terms" className="text-zinc-500 hover:text-zinc-300 transition-colors">Terms of Service</Link></div>
            </div>
          </div>
        </div>

        <div className="mt-10 pt-8 border-t border-zinc-800/50 text-center text-xs text-zinc-600">
          &copy; {new Date().getFullYear()} ScanLLM. All rights reserved.
        </div>
      </div>
    </footer>
  );
};

export default Footer;
