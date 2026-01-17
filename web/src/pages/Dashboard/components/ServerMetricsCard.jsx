import React from 'react';

const ServerMetricsCard = ({ server, metrics }) => {
  const totals = metrics?.totals || {};
  const byTool = metrics?.by_tool || [];

  const totalCalls = totals.total_calls || 0;
  const errorRate = totals.error_rate || 0;
  const avgDuration = totals.avg_duration_ms || 0;

  const mostUsedTool = byTool.length > 0 ? byTool[0] : null;
  const failingTools = byTool.filter(t => (t.total_errors || 0) > 0);
  const mostFailingTool = failingTools.length > 0 
    ? failingTools.reduce((a, b) => (a.total_errors || 0) > (b.total_errors || 0) ? a : b)
    : null;

  return (
    <div className="card p-5 hover:shadow-lg transition-all duration-200 border-surface-200">
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center">
          <div className={`w-2.5 h-2.5 rounded-full mr-3 ${server.is_active ? 'bg-success-500' : 'bg-surface-400'}`} />
          <div>
            <h3 className="font-semibold text-surface-900 text-sm">{server.server_name}</h3>
            <p className="text-xs text-surface-500 truncate max-w-[180px]">{server.id}</p>
          </div>
        </div>
        {errorRate > 5 && (
          <span className="px-2 py-0.5 text-xs font-medium bg-danger-50 text-danger-700 rounded-full">
            High Errors
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-surface-50 rounded-lg p-3">
          <p className="text-xs text-surface-500 mb-1">Calls (24h)</p>
          <p className="text-lg font-semibold text-surface-900">{totalCalls.toLocaleString()}</p>
        </div>
        <div className="bg-surface-50 rounded-lg p-3">
          <p className="text-xs text-surface-500 mb-1">Error Rate</p>
          <p className={`text-lg font-semibold ${errorRate > 5 ? 'text-danger-600' : errorRate > 2 ? 'text-warning-600' : 'text-success-600'}`}>
            {errorRate.toFixed(1)}%
          </p>
        </div>
        <div className="bg-surface-50 rounded-lg p-3">
          <p className="text-xs text-surface-500 mb-1">Avg Response</p>
          <p className="text-lg font-semibold text-surface-900">{avgDuration}ms</p>
        </div>
        <div className="bg-surface-50 rounded-lg p-3">
          <p className="text-xs text-surface-500 mb-1">Tools</p>
          <p className="text-lg font-semibold text-surface-900">{byTool.length}</p>
        </div>
      </div>

      {(mostUsedTool || mostFailingTool) && (
        <div className="border-t border-surface-100 pt-3 mt-3 space-y-2">
          {mostUsedTool && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-surface-500">Most Used</span>
              <span className="font-medium text-surface-700 truncate max-w-[120px]" title={mostUsedTool.tool_name}>
                {mostUsedTool.tool_name}
              </span>
            </div>
          )}
          {mostFailingTool && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-surface-500">Most Errors</span>
              <span className="font-medium text-danger-600 truncate max-w-[120px]" title={mostFailingTool.tool_name}>
                {mostFailingTool.tool_name} ({mostFailingTool.total_errors})
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ServerMetricsCard;
