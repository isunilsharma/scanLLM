import React from 'react';
import { Badge } from './ui/badge';

const AIHotspots = ({ hotspots }) => {
  if (!hotspots || hotspots.length === 0) {
    return null;
  }

  return (
    <div>
      <h3 className="text-base font-semibold text-zinc-100 mb-4">AI Hotspots</h3>
      <div className="border border-zinc-800 rounded-lg overflow-hidden">
        <table className="w-full">
          <thead className="bg-zinc-800/50">
            <tr>
              <th className="text-left text-xs font-medium text-zinc-400 px-4 py-3">Directory</th>
              <th className="text-right text-xs font-medium text-zinc-400 px-4 py-3">Files with AI</th>
              <th className="text-right text-xs font-medium text-zinc-400 px-4 py-3">Total Matches</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/50">
            {hotspots.map((hotspot, idx) => (
              <tr key={idx} className="hover:bg-zinc-800/30">
                <td className="px-4 py-3 text-sm text-zinc-100 font-mono">
                  {hotspot.directory}
                </td>
                <td className="px-4 py-3 text-sm text-zinc-100 text-right font-medium">
                  {hotspot.files_with_ai}
                </td>
                <td className="px-4 py-3 text-sm text-zinc-100 text-right font-medium">
                  {hotspot.total_matches}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AIHotspots;
