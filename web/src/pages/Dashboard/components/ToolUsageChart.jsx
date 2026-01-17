import React from 'react';

const ToolUsageChart = ({ metricsMap, maxTools = 5 }) => {
  const aggregatedTools = {};

  Object.values(metricsMap).forEach(metrics => {
    if (!metrics?.by_tool) return;
    metrics.by_tool.forEach(tool => {
      if (!aggregatedTools[tool.tool_name]) {
        aggregatedTools[tool.tool_name] = {
          tool_name: tool.tool_name,
          total_calls: 0,
          total_errors: 0,
        };
      }
      aggregatedTools[tool.tool_name].total_calls += tool.total_calls || 0;
      aggregatedTools[tool.tool_name].total_errors += tool.total_errors || 0;
    });
  });

  const sortedTools = Object.values(aggregatedTools)
    .sort((a, b) => b.total_calls - a.total_calls)
    .slice(0, maxTools);

  const maxCalls = sortedTools.length > 0 ? sortedTools[0].total_calls : 1;

  if (sortedTools.length === 0) {
    return (
      <div className="card p-5">
        <h3 className="text-base font-semibold text-surface-800 mb-4">Tool Usage</h3>
        <p className="text-surface-400 text-sm text-center py-6">No tool usage data available</p>
      </div>
    );
  }

  return (
    <div className="card p-5">
      <h3 className="text-base font-semibold text-surface-800 mb-4">Top Tools by Usage</h3>
      <div className="space-y-4">
        {sortedTools.map((tool, index) => {
          const percentage = (tool.total_calls / maxCalls) * 100;
          const errorPercentage = tool.total_calls > 0 
            ? (tool.total_errors / tool.total_calls) * 100 
            : 0;

          return (
            <div key={tool.tool_name}>
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center min-w-0">
                  <span className="text-xs text-surface-400 w-4">{index + 1}.</span>
                  <span className="text-sm text-surface-700 truncate" title={tool.tool_name}>
                    {tool.tool_name}
                  </span>
                </div>
                <div className="flex items-center space-x-2 text-xs">
                  <span className="font-medium text-surface-800">{tool.total_calls.toLocaleString()}</span>
                  {tool.total_errors > 0 && (
                    <span className="text-error-600">
                      ({tool.total_errors})
                    </span>
                  )}
                </div>
              </div>
              <div className="h-1.5 bg-surface-100 rounded-full overflow-hidden">
                <div className="h-full flex rounded-full">
                  <div 
                    className="bg-brand-400 transition-all duration-300 rounded-full"
                    style={{ width: `${percentage - (percentage * errorPercentage / 100)}%` }}
                  />
                  {errorPercentage > 0 && (
                    <div 
                      className="bg-error-400 rounded-r-full"
                      style={{ width: `${percentage * errorPercentage / 100}%` }}
                    />
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 pt-3 border-t border-surface-100 flex items-center justify-center space-x-4 text-xs">
        <div className="flex items-center">
          <div className="w-2.5 h-2.5 bg-brand-400 rounded-full mr-1.5" />
          <span className="text-surface-500">Success</span>
        </div>
        <div className="flex items-center">
          <div className="w-2.5 h-2.5 bg-error-400 rounded-full mr-1.5" />
          <span className="text-surface-500">Errors</span>
        </div>
      </div>
    </div>
  );
};

export default ToolUsageChart;
