import React, { useState, useEffect, useCallback } from 'react';
import { api } from '../../../services/api';

const RecentErrorsPanel = ({ servers, maxErrors = 5 }) => {
  const [errors, setErrors] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchErrors = useCallback(async () => {
    if (!servers || servers.length === 0) return;

    setLoading(true);
    try {
      const results = await Promise.allSettled(
        servers.slice(0, 5).map(server =>
          api.getServerLogs(server.id, { limit: 10, status: 'error' })
            .then(logs => logs.map(log => ({ ...log, server_name: server.server_name })))
            .catch(() => [])
        )
      );

      const allErrors = results
        .filter(r => r.status === 'fulfilled')
        .flatMap(r => r.value)
        .sort((a, b) => new Date(b.called_at) - new Date(a.called_at))
        .slice(0, maxErrors);

      setErrors(allErrors);
    } catch (err) {
      console.error('Failed to fetch errors:', err);
    } finally {
      setLoading(false);
    }
  }, [servers, maxErrors]);

  useEffect(() => {
    fetchErrors();
  }, [fetchErrors]);

  const formatTime = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    const today = new Date();
    if (date.toDateString() === today.toDateString()) {
      return 'Today';
    }
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    if (date.toDateString() === yesterday.toDateString()) {
      return 'Yesterday';
    }
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  };

  if (loading) {
    return (
      <div className="card p-6">
        <h3 className="text-lg font-semibold text-surface-900 mb-4">Recent Errors</h3>
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-6 w-6 border-2 border-brand-600 border-t-transparent" />
        </div>
      </div>
    );
  }

  return (
    <div className="card p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-surface-900">Recent Errors</h3>
        {errors.length > 0 && (
          <span className="px-2 py-0.5 text-xs font-medium bg-danger-50 text-danger-700 rounded-full">
            {errors.length}
          </span>
        )}
      </div>

      {errors.length === 0 ? (
        <div className="text-center py-8">
          <div className="w-12 h-12 mx-auto mb-3 bg-success-50 rounded-full flex items-center justify-center">
            <svg className="w-6 h-6 text-success-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-sm text-surface-500">No recent errors</p>
        </div>
      ) : (
        <div className="space-y-3">
          {errors.map((error, index) => (
            <div 
              key={`${error.server_id}-${error.called_at}-${index}`}
              className="p-3 bg-danger-50/50 border border-danger-100 rounded-lg"
            >
              <div className="flex items-start justify-between mb-1">
                <span className="text-sm font-medium text-surface-900 truncate max-w-[200px]" title={error.tool_name}>
                  {error.tool_name}
                </span>
                <span className="text-xs text-surface-500 whitespace-nowrap ml-2">
                  {formatDate(error.called_at)} {formatTime(error.called_at)}
                </span>
              </div>
              <p className="text-xs text-danger-700 line-clamp-2 mb-1" title={error.error_message}>
                {error.error_message || 'Unknown error'}
              </p>
              <p className="text-xs text-surface-500">
                Server: {error.server_name}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecentErrorsPanel;
