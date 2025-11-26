import React from 'react';
import { Badge } from './ui/badge';

const UsageTypes = ({ frameworksSummary }) => {
  if (!frameworksSummary || frameworksSummary.length === 0) {
    return null;
  }

  const getCategoryLabel = (category) => {
    const labels = {
      'llm_call': 'LLM Calls',
      'embedding_call': 'Embeddings',
      'client_init': 'Client Init',
      'rag_pattern': 'RAG Patterns',
      'secrets': 'Secrets',
      'gateway_bypass': 'Gateway Bypass',
      'misc': 'Misc'
    };
    return labels[category] || category;
  };

  return (
    <div>
      <h3 className="text-base font-semibold text-gray-900 mb-4">Framework Usage Breakdown</h3>
      <div className="space-y-4">
        {frameworksSummary.map((fw) => (
          <div key={fw.framework} className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold text-gray-900 capitalize">{fw.framework}</h4>
              <div className="flex items-center gap-3 text-sm">
                <span className="text-gray-600">{fw.files_count} files</span>
                <Badge className="bg-gray-900 text-white">{fw.total_matches} matches</Badge>
              </div>
            </div>
            
            {fw.categories && fw.categories.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {fw.categories.map((cat) => (
                  <Badge key={cat.category} variant="secondary" className="text-xs">
                    {getCategoryLabel(cat.category)}: {cat.count}
                  </Badge>
                ))}
              </div>
            )}
            
            {/* Usage description */}
            <p className="text-xs text-gray-600 mt-3">
              {fw.categories?.map(c => getCategoryLabel(c.category)).join(', ') || 'Various usage patterns'}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default UsageTypes;
