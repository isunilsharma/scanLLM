import React from 'react';

const Logo = ({ size = 'default' }) => {
  const iconSize = size === 'large' ? 40 : 32;
  const textSize = size === 'large' ? 'text-2xl' : 'text-xl';
  const subtextSize = size === 'large' ? 'text-sm' : 'text-xs';

  return (
    <div className="flex items-center gap-3">
      {/* SVG Icon */}
      <svg
        width={iconSize}
        height={iconSize}
        viewBox="0 0 40 40"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Rounded square outline */}
        <rect
          x="2"
          y="2"
          width="36"
          height="36"
          rx="8"
          stroke="#22d3ee"
          strokeWidth="2"
        />

        {/* Magnifying glass */}
        <circle cx="16" cy="16" r="6" stroke="#22d3ee" strokeWidth="2" />
        <line x1="20.5" y1="20.5" x2="24" y2="24" stroke="#22d3ee" strokeWidth="2" strokeLinecap="round" />

        {/* Neural network nodes */}
        <circle cx="28" cy="12" r="2" fill="#F97316" />
        <circle cx="32" cy="20" r="2" fill="#F97316" />
        <circle cx="28" cy="28" r="2" fill="#F97316" />

        {/* Connecting lines */}
        <line x1="28" y1="14" x2="28" y2="26" stroke="#F97316" strokeWidth="1.5" />
        <line x1="28" y1="12" x2="30" y2="20" stroke="#F97316" strokeWidth="1.5" />
        <line x1="28" y1="28" x2="30" y2="20" stroke="#F97316" strokeWidth="1.5" />
      </svg>

      {/* Text */}
      <div className="flex flex-col">
        <span className={`font-bold text-zinc-100 ${textSize}`}>ScanLLM.ai</span>
        <span className={`text-zinc-400 ${subtextSize}`}>AI Dependency Intelligence</span>
      </div>
    </div>
  );
};

export default Logo;
