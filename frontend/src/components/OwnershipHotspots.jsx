import React from 'react';
import { Badge } from './ui/badge';

const OwnershipHotspots = ({ ownershipSummary }) => {
  if (!ownershipSummary || ownershipSummary.length === 0) {
    return null;
  }

  return (
    <div>
      <h3 className="text-base font-semibold text-gray-900 mb-4">Ownership Hotspots</h3>
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left text-xs font-medium text-gray-600 px-4 py-3">Owner</th>
              <th className="text-right text-xs font-medium text-gray-600 px-4 py-3">AI Files</th>
              <th className="text-right text-xs font-medium text-gray-600 px-4 py-3">Total Matches</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {ownershipSummary.slice(0, 5).map((owner, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900">
                  {owner.owner_name || 'Unknown'}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                  {owner.ai_files_count}
                </td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">
                  {owner.total_matches}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs text-gray-500 mt-2 italic">
        Based on GitHub commit history (unauthenticated API, may be incomplete)
      </p>
    </div>
  );
};

export default OwnershipHotspots;
