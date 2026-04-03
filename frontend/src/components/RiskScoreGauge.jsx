import React, { useState, useEffect, useRef } from 'react';

const GRADE_CONFIG = {
  A: { color: '#22c55e', bgColor: 'rgba(34,197,94,0.1)', label: 'Low Risk' },
  B: { color: '#84cc16', bgColor: 'rgba(132,204,22,0.1)', label: 'Moderate' },
  C: { color: '#eab308', bgColor: 'rgba(234,179,8,0.1)', label: 'Medium' },
  D: { color: '#f97316', bgColor: 'rgba(249,115,22,0.1)', label: 'High Risk' },
  F: { color: '#ef4444', bgColor: 'rgba(239,68,68,0.1)', label: 'Critical' },
};

function getGradeFromScore(score) {
  if (score <= 20) return 'A';
  if (score <= 40) return 'B';
  if (score <= 60) return 'C';
  if (score <= 80) return 'D';
  return 'F';
}

const RiskScoreGauge = ({ score = 0, grade, compact = false }) => {
  const [animatedScore, setAnimatedScore] = useState(0);
  const animationRef = useRef(null);
  const hasAnimated = useRef(false);

  const resolvedGrade = grade || getGradeFromScore(score);
  const config = GRADE_CONFIG[resolvedGrade] || GRADE_CONFIG.C;

  // Animate score count up on mount
  useEffect(() => {
    if (hasAnimated.current) return;
    hasAnimated.current = true;

    const duration = 1200;
    const startTime = performance.now();
    const targetScore = Math.round(score);

    const animate = (currentTime) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setAnimatedScore(Math.round(eased * targetScore));

      if (progress < 1) {
        animationRef.current = requestAnimationFrame(animate);
      }
    };

    animationRef.current = requestAnimationFrame(animate);
    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [score]);

  // SVG arc parameters
  const size = compact ? 100 : 160;
  const strokeWidth = compact ? 8 : 12;
  const radius = (size - strokeWidth) / 2;
  const circumference = Math.PI * radius; // Half circle
  const center = size / 2;

  // Arc goes from 180 to 0 degrees (bottom half inverted to top arc)
  const arcLength = (animatedScore / 100) * circumference;

  // Arc path for a semicircle (top half)
  const startAngle = Math.PI; // left
  const endAngle = 0; // right

  const describeArc = (cx, cy, r, startA, endA) => {
    const x1 = cx + r * Math.cos(startA);
    const y1 = cy - r * Math.sin(startA);
    const x2 = cx + r * Math.cos(endA);
    const y2 = cy - r * Math.sin(endA);
    return `M ${x1} ${y1} A ${r} ${r} 0 0 1 ${x2} ${y2}`;
  };

  const bgPath = describeArc(center, center, radius, Math.PI, 0);

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <div className="relative" style={{ width: size, height: size / 2 + 16 }}>
          <svg width={size} height={size / 2 + 8} viewBox={`0 0 ${size} ${size / 2 + 8}`}>
            {/* Background arc */}
            <path
              d={bgPath}
              fill="none"
              stroke="#3f3f46"
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />
            {/* Score arc */}
            <path
              d={bgPath}
              fill="none"
              stroke={config.color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
              strokeDasharray={`${arcLength} ${circumference}`}
              style={{ transition: 'stroke-dasharray 0.3s ease' }}
            />
          </svg>
          {/* Score number */}
          <div
            className="absolute inset-0 flex flex-col items-center justify-end pb-1"
            style={{ height: size / 2 + 8 }}
          >
            <span className="text-xl font-bold" style={{ color: config.color }}>
              {animatedScore}
            </span>
          </div>
        </div>
        <div>
          <span
            className="text-lg font-bold px-2 py-0.5 rounded"
            style={{ backgroundColor: config.bgColor, color: config.color }}
          >
            {resolvedGrade}
          </span>
          <p className="text-xs text-zinc-500 mt-1">{config.label}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size / 2 + 32 }}>
        <svg width={size} height={size / 2 + 12} viewBox={`0 0 ${size} ${size / 2 + 12}`}>
          {/* Background arc */}
          <path
            d={bgPath}
            fill="none"
            stroke="#3f3f46"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />
          {/* Colored score arc */}
          <path
            d={bgPath}
            fill="none"
            stroke={config.color}
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            strokeDasharray={`${arcLength} ${circumference}`}
            style={{ transition: 'stroke-dasharray 0.3s ease' }}
          />
          {/* Tick marks */}
          {[0, 25, 50, 75, 100].map((tick) => {
            const angle = Math.PI - (tick / 100) * Math.PI;
            const innerR = radius - strokeWidth / 2 - 4;
            const outerR = radius - strokeWidth / 2 - 1;
            const x1 = center + innerR * Math.cos(angle);
            const y1 = center - innerR * Math.sin(angle);
            const x2 = center + outerR * Math.cos(angle);
            const y2 = center - outerR * Math.sin(angle);
            return (
              <line
                key={tick}
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="#52525b"
                strokeWidth={1}
              />
            );
          })}
        </svg>
        {/* Center content */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-end pb-2"
          style={{ height: size / 2 + 12 }}
        >
          <span className="text-4xl font-bold leading-none" style={{ color: config.color }}>
            {animatedScore}
          </span>
          <span className="text-xs text-zinc-500 mt-1">/ 100</span>
        </div>
      </div>
      {/* Grade badge */}
      <div className="flex flex-col items-center mt-1">
        <span
          className="text-2xl font-bold px-4 py-1 rounded-lg"
          style={{ backgroundColor: config.bgColor, color: config.color }}
        >
          {resolvedGrade}
        </span>
        <p className="text-sm text-zinc-500 mt-2">{config.label}</p>
      </div>
    </div>
  );
};

export default RiskScoreGauge;
