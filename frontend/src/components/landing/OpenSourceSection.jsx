import React from 'react';
import { Github, Star, Users, Database } from 'lucide-react';
import { Button } from '../ui/button';

const stats = [
  { icon: Database, value: '200+', label: 'Detection patterns' },
  { icon: Users, value: '30+', label: 'AI providers covered' },
  { icon: Star, value: '7', label: 'Specialized scanners' },
];

const OpenSourceSection = () => {
  return (
    <div className="text-center">
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-800 text-zinc-400 text-xs font-medium mb-6">
        <Github className="w-3.5 h-3.5" />
        Open Source
      </div>

      <h2 className="text-3xl md:text-4xl font-bold text-zinc-100 mb-4">
        Built by engineers, for engineers
      </h2>
      <p className="text-zinc-400 text-lg max-w-2xl mx-auto mb-8">
        The core scanning engine, CLI, and signature database are open source.
        Community contributions make detection better for everyone.
      </p>

      <div className="flex justify-center gap-8 md:gap-16 mb-10">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="text-center">
              <Icon className="w-5 h-5 text-zinc-500 mx-auto mb-2" />
              <div className="text-2xl font-bold text-zinc-100">{stat.value}</div>
              <div className="text-xs text-zinc-500">{stat.label}</div>
            </div>
          );
        })}
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
        <Button
          size="lg"
          className="bg-zinc-100 hover:bg-white text-zinc-900 px-8 font-semibold"
          onClick={() => window.open('https://github.com/isunilsharma/scanllm', '_blank')}
        >
          <Github className="w-4 h-4 mr-2" />
          Star on GitHub
        </Button>
        <Button
          variant="outline"
          size="lg"
          className="border-zinc-700 text-zinc-300 hover:bg-zinc-800 px-8"
          onClick={() => window.open('https://github.com/isunilsharma/scanllm/blob/main/CONTRIBUTING.md', '_blank')}
        >
          Contribute
        </Button>
      </div>
    </div>
  );
};

export default OpenSourceSection;
