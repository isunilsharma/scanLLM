import React, { useState, useEffect } from 'react';

const SCAN_PHASES = [
  {
    title: 'Initializing scan...',
    subtitle: 'Preparing repository metadata and scan environment.',
    duration: 3000
  },
  {
    title: 'Indexing repository structure',
    subtitle: 'Mapping files, languages, and dependency graph.',
    duration: 4000
  },
  {
    title: 'Detecting AI frameworks and model integrations',
    subtitle: 'Identifying LLM providers, agent frameworks, and inference layers.',
    duration: 5000
  },
  {
    title: 'Locating AI entry points',
    subtitle: 'Tracing where AI is invoked across APIs, jobs, and internal functions.',
    duration: 5000
  },
  {
    title: 'Analyzing prompt surface area',
    subtitle: 'Extracting prompts from code, templates, and configuration files.',
    duration: 5000
  },
  {
    title: 'Inspecting retrieval and data flows',
    subtitle: 'Inferring embedding usage, vector stores, and retrieval logic.',
    duration: 5000
  },
  {
    title: 'Characterizing AI-generated code patterns',
    subtitle: 'Evaluating structural signals and code evolution patterns.',
    duration: 5000
  },
  {
    title: 'Evaluating AI risk and governance signals',
    subtitle: 'Checking for unsafe patterns, sensitive data exposure, and configuration risks.',
    duration: 4000
  },
  {
    title: 'Finalizing scan results',
    subtitle: 'Preparing insights for review.',
    duration: 3000
  }
];

const REASSURANCE_MESSAGES = [
  'Large repositories may take longer to analyze.',
  'ScanLLM analyzes AI usage deeply—not just dependencies.',
  'You can safely navigate away. This scan will continue.'
];

const ScanLoader = ({ repoName, branch, commit, startTime }) => {
  const [currentPhase, setCurrentPhase] = useState(0);
  const [reassuranceIndex, setReassuranceIndex] = useState(0);
  const [showReassurance, setShowReassurance] = useState(false);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    // Cycle through phases
    const phaseTimer = setTimeout(() => {
      if (currentPhase < SCAN_PHASES.length - 1) {
        setCurrentPhase(prev => prev + 1);
      } else {
        // Loop back through phases if scan is still running
        setCurrentPhase(0);
      }
    }, SCAN_PHASES[currentPhase].duration);

    return () => clearTimeout(phaseTimer);
  }, [currentPhase]);

  useEffect(() => {
    // Show reassurance after 60 seconds
    const reassuranceTimer = setTimeout(() => {
      setShowReassurance(true);
    }, 60000);

    return () => clearTimeout(reassuranceTimer);
  }, []);

  useEffect(() => {
    // Rotate reassurance messages every 15 seconds
    if (showReassurance) {
      const interval = setInterval(() => {
        setReassuranceIndex(prev => (prev + 1) % REASSURANCE_MESSAGES.length);
      }, 15000);
      return () => clearInterval(interval);
    }
  }, [showReassurance]);

  useEffect(() => {
    // Update elapsed time
    const interval = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startTime) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  const phase = SCAN_PHASES[currentPhase];

  return (
    <div className="min-h-[600px] flex items-center justify-center">
      <div className="max-w-3xl w-full">
        {/* Animated Graphic */}
        <div className="mb-8 flex justify-center">
          <div className="relative">
            {/* Pulsing circles */}
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-32 h-32 bg-blue-500 rounded-full opacity-20 animate-ping"></div>
            </div>
            <div className="relative w-24 h-24 bg-gradient-to-br from-blue-600 to-purple-600 rounded-full flex items-center justify-center">
              <svg className="w-12 h-12 text-white animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Phase Text */}
        <div className="text-center mb-8 min-h-[120px]">
          <h2 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3 transition-opacity duration-500">
            {phase.title}
          </h2>
          <p className="text-lg text-gray-600 transition-opacity duration-500">
            {phase.subtitle}
          </p>
        </div>

        {/* Horizontal Shimmer Bar */}
        <div className="relative w-full h-2 bg-gray-200 rounded-full overflow-hidden mb-6">
          <div className="absolute inset-0">
            <div className="h-full bg-gradient-to-r from-transparent via-blue-500 to-transparent shimmer"></div>
          </div>
        </div>

        {/* Metadata Footer */}
        <div className="text-center space-y-2 text-sm text-gray-600">
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <span className="font-mono">{repoName}</span>
            {branch && (
              <>
                <span>•</span>
                <span>Branch: {branch}</span>
              </>
            )}
            {commit && (
              <>
                <span>•</span>
                <span className="font-mono text-xs">{commit.substring(0, 7)}</span>
              </>
            )}
          </div>
          <p className="text-xs">Elapsed: {elapsed}s</p>
          {showReassurance && (
            <p className="text-sm text-blue-600 font-medium mt-4 transition-opacity duration-500">
              {REASSURANCE_MESSAGES[reassuranceIndex]}
            </p>
          )}
          <p className="text-xs text-gray-500 mt-4">
            This may take a few minutes for larger repositories
          </p>
        </div>
      </div>
    </div>
  );
};

export default ScanLoader;
