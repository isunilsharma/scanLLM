import React from 'react';
import { Badge } from './ui/badge';

const OwnershipHotspots = ({ ownershipSummary }) => {
  if (!ownershipSummary || ownershipSummary.length === 0) {
    return (
      <div>
        <h3 className="text-base font-semibold text-zinc-100 mb-4">Ownership Hotspots</h3>
        <div className="bg-zinc-800/50 border border-zinc-800 rounded-lg p-6 text-center">
          <p className="text-sm text-zinc-400">
            No ownership data available. GitHub API may be rate-limited or repository has insufficient commit history.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div>
      <h3 className="text-base font-semibold text-zinc-100 mb-4">Ownership Hotspots</h3>
      <div className="border border-zinc-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-800/50">
            <tr>
              <th className="text-left text-xs font-medium text-zinc-400 px-4 py-3">Owner</th>
              <th className="text-right text-xs font-medium text-zinc-400 px-4 py-3">AI Files</th>
              <th className="text-right text-xs font-medium text-zinc-400 px-4 py-3">Total Matches</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {ownershipSummary.slice(0, 5).map((owner, idx) => (
              <tr key={idx} className="hover:bg-zinc-800/30">
                <td className="px-4 py-3 text-sm text-zinc-100">
                  {owner.owner_name || 'Unknown'}
                </td>
                <td className="px-4 py-3 text-sm text-zinc-100 text-right font-medium">
                  {owner.ai_files_count}
                </td>
                <td className="px-4 py-3 text-sm text-zinc-100 text-right font-medium">
                  {owner.total_matches}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-zinc-500 mt-2 italic">
        Based on GitHub commit history (unauthenticated API, may be incomplete)
      </p>
    </div>
  );
};

export default OwnershipHotspots;
