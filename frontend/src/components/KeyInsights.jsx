import React, { useMemo } from 'react';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Alert, AlertDescription } from './ui/alert';

const KeyInsights = ({ result }) => {
  const insights = useMemo(() => {
    const insights = [];
    
    // Framework usage
    const frameworkNames = result.frameworks_summary?.map(f => f.framework).join(', ') || 'none';
    const frameworkCount = result.frameworks_summary?.length || 0;
    
    if (frameworkCount === 1) {
      insights.push(`This repo uses 1 AI framework: ${frameworkNames}.`);
    } else if (frameworkCount > 1) {
      insights.push(`This repo uses ${frameworkCount} different AI frameworks: ${frameworkNames}.`);
    }
    
    // Hotspot concentration
    if (result.hotspots && result.hotspots.length > 0) {
      const topHotspot = result.hotspots[0];
      if (result.hotspots.length === 1 || topHotspot.total_matches > result.total_occurrences * 0.5) {
        insights.push(`AI usage is concentrated in ${topHotspot.directory} (${topHotspot.files_with_ai} files, ${topHotspot.total_matches} matches).`);
      } else {
        insights.push(`AI usage is distributed across ${result.hotspots.length} directories.`);
      }
    }
    
    // Usage types
    const categories = new Set();
    result.frameworks_summary?.forEach(fw => {
      fw.categories?.forEach(cat => categories.add(cat.category));
    });
    
    const hasLLM = categories.has('llm_call');
    const hasEmbeddings = categories.has('embedding_call');
    const hasRAG = categories.has('rag_pattern');
    const hasSecrets = categories.has('secrets');
    
    const usageTypes = [];
    if (hasLLM) usageTypes.push('LLM calls');
    if (hasEmbeddings) usageTypes.push('embeddings');
    if (hasRAG) usageTypes.push('RAG patterns');
    
    if (usageTypes.length > 0) {
      insights.push(`Detected usage types: ${usageTypes.join(', ')}.`);
    }
    
    // Secrets
    if (hasSecrets) {
      insights.push('⚠️ Potential hard-coded secrets detected; immediate review recommended.');
    } else if (insights.length > 0) {
      insights.push('No potential secrets were detected.');
    }
    
    return insights;
  }, [result]);

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
      <div className="flex items-start gap-3 mb-4">
        <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <div>
          <h3 className="font-semibold text-blue-900 text-base">Key Insights</h3>
        </div>
      </div>
      <ul className="space-y-2 text-sm text-blue-900">
        {insights.map((insight, idx) => (
          <li key={idx} className="flex items-start gap-2">
            <span className="text-blue-600 mt-1">•</span>
            <span>{insight}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default KeyInsights;
