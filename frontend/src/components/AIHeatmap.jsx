import React from 'react';

const AIHeatmap = ({ heatmap }) => {
  if (!heatmap || Object.keys(heatmap).length === 0) {
    return null;
  }

  // Convert to array and sort by matches
  const directories = Object.entries(heatmap)
    .map(([dir, data]) => ({ directory: dir, ...data }))
    .sort((a, b) => b.matches - a.matches)
    .slice(0, 10);

  const maxMatches = Math.max(...directories.map(d => d.matches));

  return (
    <div>
      <h3 className="text-base font-semibold text-gray-900 mb-4">AI Heatmap</h3>
      <div className="space-y-3">
        {directories.map((dir, idx) => {
          const percentage = (dir.matches / maxMatches) * 100;
          
          return (
            <div key={idx} className="">
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="font-mono text-gray-900 truncate flex-1 pr-4">
                  {dir.directory}
                </span>
                <div className="flex items-center gap-3 flex-shrink-0">
                  <span className="text-xs text-gray-600">{dir.files} files</span>
                  <span className="text-xs font-medium text-gray-900">{dir.matches} matches</span>
                </div>
              </div>
              <div className="relative h-6 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="absolute top-0 left-0 h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-500"
                  style={{ width: `${percentage}%` }}
                ></div>
                <div className="absolute inset-0 flex items-center justify-end pr-2">
                  <span className="text-xs font-medium text-gray-700">
                    {percentage.toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <p className="text-xs text-gray-500 mt-3">
        Click on any directory to filter files in the Files tab
      </p>
    </div>
  );
};

export default AIHeatmap;
