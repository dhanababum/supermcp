import React, { useState } from 'react';
import { API_BASE_URL } from '../../../services/api';

const ServerMetricsCard = ({ server, metrics, connector }) => {
  const [logoError, setLogoError] = useState(false);
  
  const logoUrl = connector?.logo_name && typeof connector.logo_name === 'string' && connector.logo_name.trim() 
    ? `${API_BASE_URL}/api/connectors/${encodeURIComponent(connector.logo_name)}`
    : null;
  const totals = metrics?.totals || {};
  const byTool = metrics?.by_tool || [];

  const totalCalls = totals.total_calls || 0;
  const errorRate = totals.error_rate || 0;
  const avgDuration = totals.avg_duration_ms || 0;
  const activeSessions = totals.active_sessions || 0;
  const totalTools = totals.total_tools || 0;

  const mostUsedTool = byTool.length > 0 ? byTool[0] : null;
  const failingTools = byTool.filter(t => (t.total_errors || 0) > 0);
  const mostFailingTool = failingTools.length > 0 
    ? failingTools.reduce((a, b) => (a.total_errors || 0) > (b.total_errors || 0) ? a : b)
    : null;

  return (
    <div className="card p-4">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center min-w-0 flex-1">
          <div className={`w-2 h-2 rounded-full mr-2.5 flex-shrink-0 ${server.is_active ? 'bg-brand-500' : 'bg-surface-300'}`} />
          <div className="min-w-0 flex-1">
            <h3 className="font-medium text-surface-800 text-sm truncate">{server.server_name}</h3>
            <p className="text-xs text-surface-400 truncate">{server.id}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0 ml-2">
          {errorRate > 5 && (
            <span className="px-2 py-0.5 text-xs font-medium bg-error-50 text-error-700 rounded-full">
              High
            </span>
          )}
          {logoUrl && !logoError ? (
            <div className="w-8 h-8 bg-white border border-surface-200 rounded-lg flex items-center justify-center overflow-hidden flex-shrink-0">
              <img 
                src={logoUrl} 
                alt={connector?.name || 'Connector'} 
                className="w-full h-full object-contain p-1"
                onError={() => setLogoError(true)}
              />
            </div>
          ) : connector ? (
            <div className="w-8 h-8 bg-surface-100 border border-surface-200 rounded-lg flex items-center justify-center flex-shrink-0">
              <svg className="w-4 h-4 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
              </svg>
            </div>
          ) : null}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        <div className="bg-cyan-50 rounded-lg p-2.5 border border-cyan-100">
          <p className="text-xs text-cyan-600 mb-0.5">Tools</p>
          <p className="text-base font-semibold text-cyan-700">{totalTools}</p>
        </div>
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
      </div>

      {(mostUsedTool || mostFailingTool || byTool.length > 0) && (
        <div className="border-t border-surface-100 pt-2.5 mt-3 space-y-1.5">
          <div className="flex items-center justify-between text-xs">
            <span className="text-surface-400">Tools</span>
            <span className="font-medium text-surface-600">{byTool.length}</span>
          </div>
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
