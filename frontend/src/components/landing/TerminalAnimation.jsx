import React, { useState, useEffect, useRef } from 'react';

const SCAN_LINES = [
  { text: '$ pip install scanllm', delay: 0, type: 'command' },
  { text: 'Successfully installed scanllm', delay: 800, type: 'success' },
  { text: '', delay: 1200, type: 'blank' },
  { text: '$ scanllm scan .', delay: 1400, type: 'command' },
  { text: '', delay: 1800, type: 'blank' },
  { text: '  Scanning 847 files...', delay: 2000, type: 'dim' },
  { text: '  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2591\u2591\u2591\u2591 85%', delay: 2400, type: 'progress' },
  { text: '  \u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588\u2588 100%', delay: 2800, type: 'progress' },
  { text: '', delay: 3200, type: 'blank' },
  { text: '  \u250c\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2510', delay: 3400, type: 'border' },
  { text: '  \u2502  Risk Score: 62/100 (Grade D)                \u2502', delay: 3500, type: 'result-warn' },
  { text: '  \u2502  AI Components: 12 across 34 files            \u2502', delay: 3600, type: 'result' },
  { text: '  \u2502  Providers: OpenAI, Anthropic, Pinecone       \u2502', delay: 3700, type: 'result-cyan' },
  { text: '  \u2502  Policy Violations: 3 errors, 2 warnings      \u2502', delay: 3800, type: 'result-error' },
  { text: '  \u2502  OWASP Issues: LLM01 (High), LLM06 (Med)     \u2502', delay: 3900, type: 'result-warn' },
  { text: '  \u2514\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2518', delay: 4000, type: 'border' },
  { text: '', delay: 4200, type: 'blank' },
  { text: '  Run scanllm ui to explore the interactive dashboard \u2192', delay: 4400, type: 'hint' },
];

const typeColors = {
  command: 'text-green-400',
  success: 'text-green-500',
  dim: 'text-zinc-500',
  progress: 'text-cyan-400',
  border: 'text-zinc-600',
  result: 'text-zinc-300',
  'result-warn': 'text-amber-400',
  'result-cyan': 'text-cyan-400',
  'result-error': 'text-red-400',
  hint: 'text-blue-400',
  blank: '',
};

const TerminalAnimation = () => {
  const [visibleLines, setVisibleLines] = useState([]);
  const [started, setStarted] = useState(false);
  const terminalRef = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started) {
          setStarted(true);
        }
      },
      { threshold: 0.3 }
    );

    if (terminalRef.current) {
      observer.observe(terminalRef.current);
    }

    return () => observer.disconnect();
  }, [started]);

  useEffect(() => {
    if (!started) return;

    const timers = SCAN_LINES.map((line, index) =>
      setTimeout(() => {
        setVisibleLines((prev) => [...prev, line]);
      }, line.delay)
    );

    return () => timers.forEach(clearTimeout);
  }, [started]);

  return (
    <div
      ref={terminalRef}
      className="w-full max-w-2xl mx-auto rounded-xl overflow-hidden shadow-2xl shadow-cyan-500/10 border border-zinc-800"
    >
      {/* Title bar */}
      <div className="flex items-center gap-2 px-4 py-3 bg-zinc-900 border-b border-zinc-800">
        <div className="flex gap-1.5">
          <div className="w-3 h-3 rounded-full bg-red-500/80" />
          <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
          <div className="w-3 h-3 rounded-full bg-green-500/80" />
        </div>
        <span className="text-xs text-zinc-500 ml-2 font-mono">scanllm</span>
      </div>

      {/* Terminal content */}
      <div className="bg-zinc-950 p-4 font-mono text-sm leading-relaxed min-h-[420px]">
        {visibleLines.map((line, i) => (
          <div
            key={i}
            className={`${typeColors[line.type] || 'text-zinc-400'} animate-fade-in`}
            style={{ animationDelay: `${i * 50}ms` }}
          >
            {line.text || '\u00A0'}
          </div>
        ))}
        {visibleLines.length < SCAN_LINES.length && started && (
          <span className="inline-block w-2 h-4 bg-green-400 animate-pulse" />
        )}
      </div>
    </div>
  );
};

export default TerminalAnimation;
