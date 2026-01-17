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
    <div className="card p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center min-w-0">
          <div className={`w-2 h-2 rounded-full mr-2.5 flex-shrink-0 ${server.is_active ? 'bg-brand-500' : 'bg-surface-300'}`} />
          <div className="min-w-0">
            <h3 className="font-medium text-surface-800 text-sm truncate">{server.server_name}</h3>
            <p className="text-xs text-surface-400 truncate">{server.id}</p>
          </div>
        </div>
        {errorRate > 5 && (
          <span className="px-2 py-0.5 text-xs font-medium bg-error-50 text-error-700 rounded-full flex-shrink-0 ml-2">
            High
          </span>
        )}
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-blue-50 rounded-lg p-2.5 border border-blue-100">
          <p className="text-xs text-blue-600 mb-0.5">Calls (24h)</p>
          <p className="text-base font-semibold text-blue-700">{totalCalls.toLocaleString()}</p>
        </div>
        <div className={`rounded-lg p-2.5 border ${errorRate > 5 ? 'bg-red-50 border-red-100' : errorRate > 2 ? 'bg-amber-50 border-amber-100' : 'bg-green-50 border-green-100'}`}>
          <p className={`text-xs mb-0.5 ${errorRate > 5 ? 'text-red-600' : errorRate > 2 ? 'text-amber-600' : 'text-green-600'}`}>Error Rate</p>
          <p className={`text-base font-semibold ${errorRate > 5 ? 'text-red-700' : errorRate > 2 ? 'text-amber-700' : 'text-green-700'}`}>
            {errorRate.toFixed(1)}%
          </p>
        </div>
        <div className="bg-amber-50 rounded-lg p-2.5 border border-amber-100">
          <p className="text-xs text-amber-600 mb-0.5">Avg Response</p>
          <p className="text-base font-semibold text-amber-700">{avgDuration}ms</p>
        </div>
        <div className="bg-violet-50 rounded-lg p-2.5 border border-violet-100">
          <p className="text-xs text-violet-600 mb-0.5">Tools</p>
          <p className="text-base font-semibold text-violet-700">{byTool.length}</p>
        </div>
      </div>

      {(mostUsedTool || mostFailingTool) && (
        <div className="border-t border-surface-100 pt-2.5 mt-3 space-y-1.5">
          {mostUsedTool && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-surface-400">Most Used</span>
              <span className="font-medium text-surface-600 truncate max-w-[100px]" title={mostUsedTool.tool_name}>
                {mostUsedTool.tool_name}
              </span>
            </div>
          )}
          {mostFailingTool && (
            <div className="flex items-center justify-between text-xs">
              <span className="text-surface-400">Most Errors</span>
              <span className="font-medium text-error-600 truncate max-w-[100px]" title={mostFailingTool.tool_name}>
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
