import React from 'react';
import { Badge } from './ui/badge';

const ModelContracts = ({ contracts }) => {
  if (!contracts) {
    return null;
  }

  const { unique_models = [], temperature_range = {}, max_tokens_range = {}, streaming_usage = 0, tools_usage = 0 } = contracts;

  if (unique_models.length === 0) {
    return null;
  }

  return (
    <div>
      <h3 className="text-base font-semibold text-gray-900 mb-4">Model & Prompt Contracts</h3>
      <div className="bg-gray-50 rounded-lg p-5 border border-gray-200">
        {/* Models */}
        <div className="mb-4">
          <h4 className="text-sm font-medium text-gray-700 mb-2">Models in Use</h4>
          <div className="flex flex-wrap gap-2">
            {unique_models.map((model, idx) => (
              <Badge key={idx} variant="secondary" className="text-sm">
                {model}
              </Badge>
            ))}
          </div>
        </div>

        {/* Temperature */}
        {(temperature_range.min !== null || temperature_range.max !== null) && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Temperature Range</h4>
            <p className="text-sm text-gray-900">
              Min: {temperature_range.min?.toFixed(2) || 'N/A'} | 
              Max: {temperature_range.max?.toFixed(2) || 'N/A'} | 
              Avg: {temperature_range.avg?.toFixed(2) || 'N/A'}
            </p>
          </div>
        )}

        {/* Max Tokens */}
        {(max_tokens_range.min !== null || max_tokens_range.max !== null) && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Max Tokens Range</h4>
            <p className="text-sm text-gray-900">
              Min: {max_tokens_range.min || 'N/A'} | 
              Max: {max_tokens_range.max || 'N/A'} | 
              Avg: {Math.round(max_tokens_range.avg || 0)}
            </p>
          </div>
        )}

        {/* Usage Flags */}
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-2">
            <Badge variant={streaming_usage > 0 ? 'default' : 'secondary'}>
              Streaming: {streaming_usage}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant={tools_usage > 0 ? 'default' : 'secondary'}>
              Tools/Functions: {tools_usage}
            </Badge>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModelContracts;
