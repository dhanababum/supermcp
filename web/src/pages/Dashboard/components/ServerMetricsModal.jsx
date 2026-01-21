import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useServerMetrics, useServerLogs } from '../../../hooks';

const ServerMetricsModal = ({ server, onClose }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [logsFilter, setLogsFilter] = useState({ status: '', tool_name: '' });
  const [selectedLog, setSelectedLog] = useState(null);
  const logsContainerRef = useRef(null);
  
  const { metrics, loading: metricsLoading } = useServerMetrics(server.id, 24);
  const { logs, loading: logsLoading, loadingMore, hasMore, refetch: refetchLogs, loadMore } = useServerLogs(server.id, { 
    limit: 10, 
    status: logsFilter.status || undefined,
    tool_name: logsFilter.tool_name || undefined
  });

  useEffect(() => {
    setSelectedLog(null);
    refetchLogs();
  }, [logsFilter]);

  const handleLogsScroll = useCallback((e) => {
    const { scrollTop, scrollHeight, clientHeight } = e.target;
    if (scrollHeight - scrollTop - clientHeight < 100 && hasMore && !loadingMore) {
      loadMore();
    }
  }, [hasMore, loadingMore, loadMore]);

  const totals = metrics?.totals || {};
  const byTool = metrics?.by_tool || [];

  const formatTime = (dateStr) => {
    return new Date(dateStr).toLocaleString();
  };

  const formatContent = (data) => {
    if (data === null || data === undefined) {
      return 'null';
    }
    
    // Handle arrays (including empty arrays)
    if (Array.isArray(data)) {
      try {
        return JSON.stringify(data, null, 2);
      } catch (e) {
        return String(data);
      }
    }
    
    // Handle objects (including Date, Error, etc.)
    if (typeof data === 'object') {
      // Check if it's a plain object (not a class instance)
      if (data.constructor === Object) {
        try {
          return JSON.stringify(data, null, 2);
        } catch (e) {
          return String(data);
        }
      } else {
        // For class instances, try to stringify, fallback to toString
        try {
          const jsonStr = JSON.stringify(data, null, 2);
          // If stringification worked but might be empty object, show toString
          if (jsonStr === '{}' || jsonStr === '[]') {
            return String(data);
          }
          return jsonStr;
        } catch (e) {
          return String(data);
        }
      }
    }
    
    // Handle strings - try to parse as JSON first
    if (typeof data === 'string') {
      // Check if it's a JSON string (starts with {, [, or " and is parseable)
      const trimmed = data.trim();
      if ((trimmed.startsWith('{') || trimmed.startsWith('[') || trimmed.startsWith('"')) && trimmed.length > 1) {
        try {
          const parsed = JSON.parse(data);
          // If parsed successfully, format it
          return JSON.stringify(parsed, null, 2);
        } catch (e) {
          // Not valid JSON, return as plain text
          return data;
        }
      }
      // Plain text string
      return data;
    }
    
    // Handle numbers, booleans, etc.
    if (typeof data === 'number' || typeof data === 'boolean') {
      return String(data);
    }
    
    // Fallback to string conversion
    return String(data);
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      // Could add a toast notification here
    }).catch(err => {
      console.error('Failed to copy:', err);
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-surface-200 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-surface-900">{server.server_name}</h2>
            <p className="text-sm text-surface-500">Server Metrics & Logs</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-surface-100 rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Tabs */}
        <div className="px-6 border-b border-surface-200">
          <div className="flex space-x-6">
            {['overview', 'tools', 'logs'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-3 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab
                    ? 'border-brand-600 text-brand-600'
                    : 'border-transparent text-surface-500 hover:text-surface-700'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {metricsLoading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-brand-600 border-t-transparent" />
            </div>
          ) : (
            <>
              {/* Overview Tab */}
              {activeTab === 'overview' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="bg-surface-50 rounded-lg p-4">
                      <p className="text-sm text-surface-500 mb-1">Total Calls</p>
                      <p className="text-2xl font-semibold text-surface-900">
                        {(totals.total_calls || 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-surface-50 rounded-lg p-4">
                      <p className="text-sm text-surface-500 mb-1">Errors</p>
                      <p className="text-2xl font-semibold text-danger-600">
                        {(totals.total_errors || 0).toLocaleString()}
                      </p>
                    </div>
                    <div className="bg-surface-50 rounded-lg p-4">
                      <p className="text-sm text-surface-500 mb-1">Error Rate</p>
                      <p className={`text-2xl font-semibold ${
                        (totals.error_rate || 0) > 5 ? 'text-danger-600' : 'text-success-600'
                      }`}>
                        {(totals.error_rate || 0).toFixed(1)}%
                      </p>
                    </div>
                    <div className="bg-surface-50 rounded-lg p-4">
                      <p className="text-sm text-surface-500 mb-1">Avg Duration</p>
                      <p className="text-2xl font-semibold text-surface-900">
                        {totals.avg_duration_ms || 0}ms
                      </p>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-surface-900 mb-3">Tool Usage Summary</h3>
                    {byTool.length > 0 ? (
                      <div className="space-y-2">
                        {byTool.slice(0, 10).map((tool) => {
                          const maxCalls = byTool[0].total_calls || 1;
                          const percentage = (tool.total_calls / maxCalls) * 100;
                          return (
                            <div key={tool.tool_name} className="flex items-center space-x-3">
                              <div className="w-32 truncate text-sm text-surface-700" title={tool.tool_name}>
                                {tool.tool_name}
                              </div>
                              <div className="flex-1 h-4 bg-surface-100 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-brand-500 rounded-full transition-all"
                                  style={{ width: `${percentage}%` }}
                                />
                              </div>
                              <div className="w-20 text-right text-sm font-medium text-surface-700">
                                {tool.total_calls}
                              </div>
                              {tool.total_errors > 0 && (
                                <span className="text-xs text-danger-600">
                                  {tool.total_errors} err
                                </span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-sm text-surface-500">No tool usage data</p>
                    )}
                  </div>
                </div>
              )}

              {/* Tools Tab */}
              {activeTab === 'tools' && (
                <div>
                  {byTool.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-surface-200">
                            <th className="text-left py-3 px-4 font-medium text-surface-500">Tool Name</th>
                            <th className="text-right py-3 px-4 font-medium text-surface-500">Calls</th>
                            <th className="text-right py-3 px-4 font-medium text-surface-500">Errors</th>
                            <th className="text-right py-3 px-4 font-medium text-surface-500">Error Rate</th>
                            <th className="text-right py-3 px-4 font-medium text-surface-500">Avg (ms)</th>
                            <th className="text-right py-3 px-4 font-medium text-surface-500">Max (ms)</th>
                          </tr>
                        </thead>
                        <tbody>
                          {byTool.map((tool) => (
                            <tr key={tool.tool_name} className="border-b border-surface-100 hover:bg-surface-50">
                              <td className="py-3 px-4 font-medium text-surface-900">{tool.tool_name}</td>
                              <td className="py-3 px-4 text-right text-surface-700">{tool.total_calls}</td>
                              <td className="py-3 px-4 text-right text-danger-600">{tool.total_errors || 0}</td>
                              <td className="py-3 px-4 text-right">
                                <span className={tool.total_calls > 0 && (tool.total_errors / tool.total_calls * 100) > 5 
                                  ? 'text-danger-600' 
                                  : 'text-surface-700'
                                }>
                                  {tool.total_calls > 0 
                                    ? ((tool.total_errors / tool.total_calls) * 100).toFixed(1) 
                                    : '0.0'}%
                                </span>
                              </td>
                              <td className="py-3 px-4 text-right text-surface-700">{tool.avg_duration_ms || 0}</td>
                              <td className="py-3 px-4 text-right text-surface-700">{tool.max_duration_ms || 0}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <p className="text-sm text-surface-500 text-center py-8">No tools data available</p>
                  )}
                </div>
              )}

              {/* Logs Tab */}
              {activeTab === 'logs' && (
                <div className="flex flex-col h-full">
                  <div className="flex items-center space-x-4 mb-4">
                    <select
                      value={logsFilter.status}
                      onChange={(e) => setLogsFilter(f => ({ ...f, status: e.target.value }))}
                      className="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="">All Status</option>
                      <option value="success">Success</option>
                      <option value="error">Error</option>
                    </select>
                    <select
                      value={logsFilter.tool_name}
                      onChange={(e) => setLogsFilter(f => ({ ...f, tool_name: e.target.value }))}
                      className="px-3 py-2 border border-surface-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
                    >
                      <option value="">All Tools</option>
                      {byTool.map(t => (
                        <option key={t.tool_name} value={t.tool_name}>{t.tool_name}</option>
                      ))}
                    </select>
                  </div>

                  {logsLoading ? (
                    <div className="flex items-center justify-center py-8">
                      <div className="animate-spin rounded-full h-6 w-6 border-2 border-brand-600 border-t-transparent" />
                    </div>
                  ) : logs.length > 0 ? (
                    <div className="flex gap-4 h-96">
                      {/* Left Panel - Log List */}
                      <div 
                        ref={logsContainerRef}
                        onScroll={handleLogsScroll}
                        className="w-2/5 space-y-2 overflow-auto border-r border-surface-200 pr-4"
                      >
                        {logs.map((log, idx) => (
                          <div 
                            key={`${log.called_at}-${idx}`}
                            onClick={() => setSelectedLog(log)}
                            className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                              selectedLog === log
                                ? 'ring-2 ring-brand-500 border-brand-300'
                                : log.status === 'error' 
                                  ? 'bg-danger-50/50 border-danger-100 hover:border-danger-200' 
                                  : 'bg-surface-50 border-surface-100 hover:border-surface-200'
                            }`}
                          >
                            <div className="flex items-center justify-between mb-1">
                              <div className="flex items-center space-x-2">
                                <span className={`px-1.5 py-0.5 text-xs font-medium rounded ${
                                  log.status === 'error' 
                                    ? 'bg-danger-100 text-danger-700' 
                                    : 'bg-success-100 text-success-700'
                                }`}>
                                  {log.status === 'error' ? 'ERR' : 'OK'}
                                </span>
                                <span className="font-medium text-sm text-surface-900 truncate max-w-[120px]">{log.tool_name}</span>
                              </div>
                            </div>
                            <div className="text-xs text-surface-500">
                              {formatTime(log.called_at)}
                            </div>
                          </div>
                        ))}
                        {loadingMore && (
                          <div className="flex items-center justify-center py-4">
                            <div className="animate-spin rounded-full h-5 w-5 border-2 border-brand-600 border-t-transparent" />
                          </div>
                        )}
                        {!hasMore && logs.length > 0 && (
                          <p className="text-xs text-surface-400 text-center py-2">No more logs</p>
                        )}
                      </div>

                      {/* Right Panel - Detail View */}
                      <div className="w-3/5 flex flex-col h-full">
                        {selectedLog ? (
                          <div className="flex flex-col h-full space-y-4 overflow-hidden">
                            <div className="flex items-center justify-between flex-shrink-0">
                              <div className="flex items-center space-x-2">
                                <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                                  selectedLog.status === 'error' 
                                    ? 'bg-danger-100 text-danger-700' 
                                    : 'bg-success-100 text-success-700'
                                }`}>
                                  {selectedLog.status}
                                </span>
                                <span className="font-semibold text-surface-900">{selectedLog.tool_name}</span>
                              </div>
                              <span className="text-xs text-surface-500">{selectedLog.duration_ms}ms</span>
                            </div>

                            {selectedLog.error_message && (
                              <div className="flex-shrink-0">
                                <h4 className="text-xs font-medium text-danger-700 mb-1">Error</h4>
                                <p className="text-sm text-danger-700 bg-danger-50 p-3 rounded-lg">
                                  {selectedLog.error_message}
                                </p>
                              </div>
                            )}

                            <div className="flex-shrink-0">
                              <div className="flex items-center justify-between mb-1">
                                <h4 className="text-xs font-medium text-surface-500">Arguments</h4>
                                {selectedLog.arguments && (
                                  <button
                                    onClick={() => copyToClipboard(formatContent(selectedLog.arguments) || '')}
                                    className="text-xs text-brand-600 hover:text-brand-700 px-2 py-1 rounded hover:bg-brand-50 transition-colors"
                                    title="Copy to clipboard"
                                  >
                                    Copy
                                  </button>
                                )}
                              </div>
                              <pre className="text-xs bg-surface-50 p-4 rounded-lg overflow-auto max-h-64 text-surface-700 font-mono whitespace-pre-wrap break-words border border-surface-200">
                                {selectedLog.arguments 
                                  ? formatContent(selectedLog.arguments)
                                  : 'No arguments'}
                              </pre>
                            </div>

                            <div className="flex flex-col flex-1 min-h-0 overflow-hidden">
                              <div className="flex items-center justify-between mb-1 flex-shrink-0">
                                <h4 className="text-xs font-medium text-surface-500">Response</h4>
                                {selectedLog.result_summary && (
                                  <button
                                    onClick={() => copyToClipboard(formatContent(selectedLog.result_summary) || '')}
                                    className="text-xs text-brand-600 hover:text-brand-700 px-2 py-1 rounded hover:bg-brand-50 transition-colors"
                                    title="Copy to clipboard"
                                  >
                                    Copy
                                  </button>
                                )}
                              </div>
                              <pre className="text-xs bg-surface-50 p-4 rounded-lg overflow-auto flex-1 text-surface-700 font-mono whitespace-pre-wrap break-words border border-surface-200">
                                {selectedLog.result_summary 
                                  ? formatContent(selectedLog.result_summary)
                                  : 'No response data'}
                              </pre>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center h-full text-surface-400">
                            <p className="text-sm">Select a log to view details</p>
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <p className="text-sm text-surface-500 text-center py-8">No logs found</p>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-surface-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-surface-700 hover:bg-surface-100 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ServerMetricsModal;
