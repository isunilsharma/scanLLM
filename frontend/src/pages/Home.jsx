import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import LoginButton from '../components/LoginButton';
import { Button } from '../components/ui/button';
import { ArrowRight, Terminal } from 'lucide-react';
import TerminalAnimation from '../components/landing/TerminalAnimation';
import FeatureGrid from '../components/landing/FeatureGrid';
import HowItWorksSection from '../components/landing/HowItWorks';
import ForTeams from '../components/landing/ForTeams';
import OpenSourceSection from '../components/landing/OpenSourceSection';
import TrustBar from '../components/landing/TrustBar';

const Home = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        {/* Gradient background */}
        <div className="absolute inset-0 bg-gradient-to-b from-zinc-950 via-zinc-950 to-zinc-900" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-cyan-900/20 via-transparent to-transparent" />

        <div className="relative max-w-7xl mx-auto px-6 pt-20 pb-16">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            {/* Left: Copy */}
            <div className="text-center lg:text-left">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 text-cyan-400 text-xs font-medium mb-6 border border-cyan-500/20">
                <Terminal className="w-3.5 h-3.5" />
                Now available: scanllm v2.0
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold tracking-tight mb-6 leading-[1.1]">
                Know every AI dependency.{' '}
                <span className="bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
                  Enforce every policy.
                </span>
              </h1>

              <p className="text-lg md:text-xl text-zinc-400 mb-8 max-w-xl mx-auto lg:mx-0 leading-relaxed">
                Scan your codebase for AI/LLM frameworks, visualize the dependency graph,
                enforce policies in CI/CD, and generate AI-BOMs for compliance.
              </p>

              {/* CTA */}
              <div className="flex flex-col sm:flex-row items-center lg:items-start gap-4 mb-8">
                <Button
                  onClick={() => navigate('/demo')}
                  size="lg"
                  className="bg-cyan-600 hover:bg-cyan-500 text-white px-8 py-6 text-lg font-semibold shadow-lg shadow-cyan-600/20"
                >
                  Try the demo
                  <ArrowRight className="w-5 h-5 ml-2" />
                </Button>
                <LoginButton
                  size="lg"
                  className="px-8 py-6 text-lg border-zinc-700 text-zinc-300 hover:bg-zinc-800"
                  variant="outline"
                />
              </div>

              {/* Install command */}
              <div className="inline-flex items-center gap-3 px-4 py-2.5 rounded-lg bg-zinc-900 border border-zinc-800 font-mono text-sm">
                <span className="text-green-400">$</span>
                <span className="text-zinc-300">pip install scanllm</span>
                <button
                  onClick={() => navigator.clipboard.writeText('pip install scanllm')}
                  className="text-xs text-zinc-500 hover:text-zinc-300 transition-colors ml-2"
                >
                  Copy
                </button>
              </div>
            </div>

            {/* Right: Terminal Animation */}
            <div className="hidden lg:block">
              <TerminalAnimation />
            </div>
          </div>

          {/* Trust bar */}
          <div className="mt-16 pt-8 border-t border-zinc-800/50">
            <TrustBar />
          </div>
        </div>
      </section>

      {/* Mobile terminal (shown below hero on mobile) */}
      <section className="lg:hidden px-6 pb-16">
        <TerminalAnimation />
      </section>

      {/* How It Works */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-zinc-100 mb-4">
            Three commands. Full visibility.
          </h2>
          <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
            No config files. No dashboard signup. Just install, scan, and govern.
          </p>
        </div>
        <HowItWorksSection />
      </section>

      {/* What You Get */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-zinc-100 mb-4">
            Everything you need to govern AI in code
          </h2>
          <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
            Scan, graph, score, enforce, export. One tool replaces five.
          </p>
        </div>
        <FeatureGrid />
      </section>

      {/* Comparison / Why ScanLLM */}
      <section className="max-w-5xl mx-auto px-6 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold text-zinc-100 mb-4">
            Why not just use Snyk or Cycode?
          </h2>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-zinc-800">
                <th className="text-left py-3 px-4 text-zinc-400 font-medium">Capability</th>
                <th className="text-center py-3 px-4 text-cyan-400 font-semibold">ScanLLM</th>
                <th className="text-center py-3 px-4 text-zinc-500 font-medium">Snyk</th>
                <th className="text-center py-3 px-4 text-zinc-500 font-medium">Cycode</th>
                <th className="text-center py-3 px-4 text-zinc-500 font-medium">Promptfoo</th>
              </tr>
            </thead>
            <tbody className="text-zinc-400">
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 px-4">Code-level AI discovery (AST)</td>
                <td className="text-center text-green-400">Yes</td>
                <td className="text-center text-zinc-600">Partial</td>
                <td className="text-center text-green-400">Yes</td>
                <td className="text-center text-zinc-600">No</td>
              </tr>
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 px-4">Interactive dependency graph</td>
                <td className="text-center text-green-400">Yes</td>
                <td className="text-center text-zinc-600">No</td>
                <td className="text-center text-zinc-600">No</td>
                <td className="text-center text-zinc-600">No</td>
              </tr>
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 px-4">OWASP LLM Top 10 mapping</td>
                <td className="text-center text-green-400">Yes</td>
                <td className="text-center text-zinc-600">No</td>
                <td className="text-center text-zinc-600">Partial</td>
                <td className="text-center text-green-400">Yes</td>
              </tr>
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 px-4">AI-BOM (CycloneDX ML)</td>
                <td className="text-center text-green-400">Yes</td>
                <td className="text-center text-zinc-600">No</td>
                <td className="text-center text-zinc-600">No</td>
                <td className="text-center text-zinc-600">No</td>
              </tr>
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 px-4">Policy as code (YAML)</td>
                <td className="text-center text-green-400">Yes</td>
                <td className="text-center text-green-400">Yes</td>
                <td className="text-center text-green-400">Yes</td>
                <td className="text-center text-zinc-600">No</td>
              </tr>
              <tr className="border-b border-zinc-800/50">
                <td className="py-3 px-4">Free CLI (full features)</td>
                <td className="text-center text-green-400">Yes</td>
                <td className="text-center text-zinc-600">Limited</td>
                <td className="text-center text-zinc-600">No</td>
                <td className="text-center text-green-400">Yes</td>
              </tr>
              <tr>
                <td className="py-3 px-4 font-medium text-zinc-300">Starting price</td>
                <td className="text-center text-cyan-400 font-medium">Free / $49/mo</td>
                <td className="text-center text-zinc-500">$98/dev/mo</td>
                <td className="text-center text-zinc-500">Enterprise only</td>
                <td className="text-center text-zinc-500">Free / custom</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* For Teams */}
      <section className="max-w-7xl mx-auto px-6 py-20">
        <ForTeams />
      </section>

      {/* Open Source */}
      <section className="max-w-5xl mx-auto px-6 py-20 border-t border-zinc-800/50">
        <OpenSourceSection />
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800/50 mt-20">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="font-bold text-zinc-100 text-lg mb-3">ScanLLM</div>
              <p className="text-sm text-zinc-500">
                AI Dependency Intelligence. Know what AI is in your code.
              </p>
            </div>
            <div>
              <div className="font-medium text-zinc-300 text-sm mb-3">Product</div>
              <div className="space-y-2 text-sm text-zinc-500">
                <div><a href="/demo" className="hover:text-zinc-300 transition-colors">Demo</a></div>
                <div><a href="/how-it-works" className="hover:text-zinc-300 transition-colors">How it Works</a></div>
                <div><a href="/blog" className="hover:text-zinc-300 transition-colors">Blog</a></div>
              </div>
            </div>
            <div>
              <div className="font-medium text-zinc-300 text-sm mb-3">Developers</div>
              <div className="space-y-2 text-sm text-zinc-500">
                <div><a href="https://github.com/isunilsharma/scanllm" className="hover:text-zinc-300 transition-colors" target="_blank" rel="noreferrer">GitHub</a></div>
                <div><a href="https://github.com/isunilsharma/scanllm/issues" className="hover:text-zinc-300 transition-colors" target="_blank" rel="noreferrer">Issues</a></div>
                <div><a href="https://github.com/isunilsharma/scanllm/blob/main/CONTRIBUTING.md" className="hover:text-zinc-300 transition-colors" target="_blank" rel="noreferrer">Contributing</a></div>
              </div>
            </div>
            <div>
              <div className="font-medium text-zinc-300 text-sm mb-3">Legal</div>
              <div className="space-y-2 text-sm text-zinc-500">
                <div><a href="#" className="hover:text-zinc-300 transition-colors">Privacy</a></div>
                <div><a href="#" className="hover:text-zinc-300 transition-colors">Terms</a></div>
              </div>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-zinc-800/50 text-center text-xs text-zinc-600">
            &copy; {new Date().getFullYear()} ScanLLM. Built with care.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;
