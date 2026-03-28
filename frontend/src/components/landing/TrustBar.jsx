import React from 'react';
import { Lock, Eye, Clock, Github } from 'lucide-react';

const trustItems = [
  { icon: Lock, text: 'Open source' },
  { icon: Eye, text: 'No code leaves your machine' },
  { icon: Clock, text: '2 min setup' },
  { icon: Github, text: '200+ AI detection patterns' },
];

const TrustBar = () => {
  return (
    <div className="flex flex-wrap justify-center gap-6 md:gap-8">
      {trustItems.map((item) => {
        const Icon = item.icon;
        return (
          <div key={item.text} className="flex items-center gap-2 text-sm text-zinc-400">
            <Icon className="w-4 h-4 text-zinc-500" />
            <span>{item.text}</span>
          </div>
        );
      })}
    </div>
  );
};

export default TrustBar;
