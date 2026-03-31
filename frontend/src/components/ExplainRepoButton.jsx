import React, { useState } from 'react';
import { Button } from './ui/button';
import { toast } from 'sonner';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ExplainRepoButton = ({ scanId }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [explanation, setExplanation] = useState(null);

  const handleExplain = async () => {
    setIsGenerating(true);
    try {
      const response = await axios.post(`${API}/explain-scan`, {
        scan_id: scanId
      });
      setExplanation(response.data.explanation);
      toast.success('AI explanation generated!');
    } catch (err) {
      toast.error('Failed to generate explanation');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div>
      {!explanation ? (
        <Button
          onClick={handleExplain}
          disabled={isGenerating}
          className="w-full bg-gradient-to-r from-indigo-600 to-indigo-500 hover:from-indigo-700 hover:to-indigo-600 text-white relative z-10"
          data-testid="explain-repo-button"
        >
          {isGenerating ? (
            <>
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
              Generating AI Explanation...
            </>
          ) : (
            <>
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
              Explain My Repo (AI)
            </>
          )}
        </Button>
      ) : (
        <div className="bg-indigo-50/70 border border-indigo-200 rounded-xl p-6">
          <div className="flex items-start gap-3 mb-4">
            <svg className="w-6 h-6 text-indigo-600 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
            </svg>
            <div className="flex-1">
              <h3 className="font-semibold text-indigo-900 mb-2">AI-Generated Repository Analysis</h3>
              <div className="prose prose-sm max-w-none text-gray-800 whitespace-pre-wrap">
                {explanation}
              </div>
            </div>
          </div>
          <Button
            onClick={() => setExplanation(null)}
            variant="outline"
            size="sm"
            className="mt-4"
          >
            Generate New Explanation
          </Button>
        </div>
      )}
    </div>
  );
};

export default ExplainRepoButton;
