import React from 'react';
import { Badge } from './ui/badge';

const RecommendedActions = ({ actions }) => {
  if (!actions || actions.length === 0) {
    return null;
  }

  return (
    <div>
      <h3 className="text-base font-semibold text-zinc-100 mb-4">Recommended Actions</h3>
      <div className="space-y-3">
        {actions.map((action) => (
          <div
            key={action.id}
            className="bg-zinc-900 border border-zinc-800 rounded-xl p-5 hover:border-primary/50 transition-colors"
          >
            <h4 className="font-semibold text-zinc-100 mb-2">{action.title}</h4>
            <p className="text-sm text-zinc-400 mb-3">{action.description}</p>
            {action.related_risk_flags && action.related_risk_flags.length > 0 && (
              <div className="flex flex-wrap gap-1.5">
                {action.related_risk_flags.map(flag => (
                  <Badge key={flag} variant="outline" className="text-xs">
                    {flag.replace(/_/g, ' ')}
                  </Badge>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default RecommendedActions;
