import React, { useState, useEffect, useRef } from 'react';
import { Building2, History, GitPullRequest, Users, Bell, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';

const teamFeatures = [
  { icon: Building2, text: 'Multi-repo dashboard', description: 'Org-wide AI inventory across all repositories' },
  { icon: History, text: 'Historical trends', description: 'Track risk score over time, catch drift early' },
  { icon: GitPullRequest, text: 'CI/CD enforcement', description: 'Block PRs that violate policies automatically' },
  { icon: Users, text: 'Team management', description: 'RBAC, ownership mapping, approval workflows' },
  { icon: Bell, text: 'Notifications', description: 'Slack/Teams alerts on new critical findings' },
];

const ForTeams = () => {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setIsVisible(true);
      },
      { threshold: 0.2 }
    );

    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`relative rounded-2xl border border-zinc-800 bg-gradient-to-b from-zinc-900/80 to-zinc-950 p-8 md:p-12
                  transition-all duration-700
                  ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'}`}
    >
      <div className="max-w-3xl mx-auto text-center mb-10">
        <span className="inline-block px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 text-xs font-medium mb-4">
          For Teams & Enterprise
        </span>
        <h2 className="text-3xl md:text-4xl font-bold text-zinc-100 mb-4">
          From dev tool to governance platform
        </h2>
        <p className="text-zinc-400 text-lg">
          Everything in the open-source CLI, plus the features your security team needs.
        </p>
      </div>

      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4 mb-10">
        {teamFeatures.map((feature, i) => {
          const Icon = feature.icon;
          return (
            <div
              key={feature.text}
              className={`flex items-start gap-3 p-4 rounded-lg bg-zinc-900/50 border border-zinc-800/50
                          transition-all duration-500 delay-${i * 100}
                          ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'}`}
              style={{ transitionDelay: `${i * 100}ms` }}
            >
              <Icon className="w-5 h-5 text-blue-400 mt-0.5 shrink-0" />
              <div>
                <div className="text-sm font-medium text-zinc-200">{feature.text}</div>
                <div className="text-xs text-zinc-500 mt-0.5">{feature.description}</div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <Button
          onClick={() => navigate('/demo')}
          size="lg"
          className="bg-blue-600 hover:bg-blue-500 text-white px-8"
        >
          Try the demo
          <ArrowRight className="w-4 h-4 ml-2" />
        </Button>
        <Button
          variant="outline"
          size="lg"
          className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 px-8"
          onClick={() => window.open('mailto:hello@scanllm.ai', '_blank')}
        >
          Talk to us
        </Button>
      </div>
    </div>
  );
};

export default ForTeams;
