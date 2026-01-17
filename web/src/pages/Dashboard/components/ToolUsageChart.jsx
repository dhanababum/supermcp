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
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-surface-900 mb-4">Tool Usage</h3>
        <p className="text-surface-500 text-sm text-center py-8">No tool usage data available</p>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <h3 className="text-lg font-semibold text-surface-900 mb-4">Top Tools by Usage</h3>
      <div className="space-y-3">
        {sortedTools.map((tool, index) => {
          const percentage = (tool.total_calls / maxCalls) * 100;
          const errorPercentage = tool.total_calls > 0 
            ? (tool.total_errors / tool.total_calls) * 100 
            : 0;

          return (
            <div key={tool.tool_name} className="group">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center min-w-0">
                  <span className="text-xs font-medium text-surface-400 w-5">{index + 1}.</span>
                  <span className="text-sm font-medium text-surface-700 truncate" title={tool.tool_name}>
                    {tool.tool_name}
                  </span>
                </div>
                <div className="flex items-center space-x-3 text-xs">
                  <span className="font-semibold text-surface-900">{tool.total_calls.toLocaleString()}</span>
                  {tool.total_errors > 0 && (
                    <span className="text-danger-600 font-medium">
                      {tool.total_errors} errors
                    </span>
                  )}
                </div>
              </div>
              <div className="h-2 bg-surface-100 rounded-full overflow-hidden">
                <div className="h-full flex rounded-full">
                  <div 
                    className="bg-brand-500 transition-all duration-300"
                    style={{ width: `${percentage - (percentage * errorPercentage / 100)}%` }}
                  />
                  {errorPercentage > 0 && (
                    <div 
                      className="bg-danger-400"
                      style={{ width: `${percentage * errorPercentage / 100}%` }}
                    />
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
      <div className="mt-4 pt-3 border-t border-surface-100 flex items-center justify-center space-x-6 text-xs">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-brand-500 rounded mr-2" />
          <span className="text-surface-600">Success</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-danger-400 rounded mr-2" />
          <span className="text-surface-600">Errors</span>
        </div>
      </div>
    </div>
  );
};

export default ToolUsageChart;
