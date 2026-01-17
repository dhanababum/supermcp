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
      <div className="card p-5">
        <h3 className="text-base font-semibold text-surface-800 mb-4">Recent Errors</h3>
        <div className="flex items-center justify-center py-6">
          <div className="animate-spin rounded-full h-5 w-5 border-2 border-brand-500 border-t-transparent" />
        </div>
      </div>
    );
  }

  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-surface-800">Recent Errors</h3>
        {errors.length > 0 && (
          <span className="px-2 py-0.5 text-xs font-medium bg-error-50 text-error-600 rounded-full">
            {errors.length}
          </span>
        )}
      </div>

      {errors.length === 0 ? (
        <div className="text-center py-6">
          <div className="w-10 h-10 mx-auto mb-2 bg-brand-50 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <p className="text-sm text-surface-400">No recent errors</p>
        </div>
      ) : (
        <div className="space-y-2">
          {errors.map((error, index) => (
            <div 
              key={`${error.server_id}-${error.called_at}-${index}`}
              className="p-3 bg-error-50/50 border border-error-100 rounded-lg"
            >
              <div className="flex items-start justify-between mb-1">
                <span className="text-sm font-medium text-surface-800 truncate max-w-[180px]" title={error.tool_name}>
                  {error.tool_name}
                </span>
                <span className="text-xs text-surface-400 whitespace-nowrap ml-2">
                  {formatDate(error.called_at)} {formatTime(error.called_at)}
                </span>
              </div>
              <p className="text-xs text-error-600 line-clamp-2 mb-1" title={error.error_message}>
                {error.error_message || 'Unknown error'}
              </p>
              <p className="text-xs text-surface-400">
                {error.server_name}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default RecentErrorsPanel;
