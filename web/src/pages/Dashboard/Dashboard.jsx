import React, { useEffect, useCallback } from 'react';
import { useServers, useConnectors, useAllServersMetrics } from '../../hooks';
import { LoadingSpinner, ErrorMessage } from '../../components/common';
import { StatCard } from '../../components/common/StatCard';
import { ServerIcon, ActivityIcon, PlugIcon, WrenchIcon } from '../../components/icons/DashboardIcons';
import { ServerMetricsCard, ToolUsageChart, RecentErrorsPanel } from './components';

const Dashboard = () => {
  const { servers, loading: serversLoading, error: serversError } = useServers(true);
  const { connectors, loading: connectorsLoading, error: connectorsError } = useConnectors();
  const { metricsMap, loading: metricsLoading, refetch: refetchMetrics } = useAllServersMetrics(servers, 24);

  // Auto-refresh metrics every 60 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      if (servers && servers.length > 0) {
        refetchMetrics();
      }
    }, 60000);
    return () => clearInterval(interval);
  }, [servers, refetchMetrics]);

  // Calculate statistics
  const totalServers = servers?.length || 0;
  const activeServers = servers?.filter(server => server.is_active)?.length || 0;
  const totalConnectors = connectors?.length || 0;

  // Calculate aggregated metrics
  const aggregatedMetrics = useCallback(() => {
    let totalCalls = 0;
    let totalErrors = 0;
    Object.values(metricsMap).forEach(m => {
      if (m?.totals) {
        totalCalls += m.totals.total_calls || 0;
        totalErrors += m.totals.total_errors || 0;
      }
    });
    const errorRate = totalCalls > 0 ? (totalErrors / totalCalls * 100).toFixed(1) : '0.0';
    return { totalCalls, totalErrors, errorRate };
  }, [metricsMap])();

  if (serversLoading || connectorsLoading) {
    return <LoadingSpinner message="Loading dashboard..." />;
  }

  if (serversError || connectorsError) {
    return (
      <ErrorMessage
        title="Error loading dashboard data"
        message={serversError || connectorsError}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-xl font-semibold text-surface-900">Dashboard</h1>
        <p className="text-sm text-surface-500 mt-1">Monitor your MCP servers, connectors, and tools</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          title="Total Servers" 
          value={totalServers} 
          icon={ServerIcon} 
          colorClass="blue" 
        />
        <StatCard 
          title="Active Servers" 
          value={activeServers} 
          icon={ActivityIcon} 
          colorClass="green" 
        />
        <StatCard 
          title="Connectors" 
          value={totalConnectors} 
          icon={PlugIcon} 
          colorClass="purple" 
        />
        <StatCard 
          title="Tool Calls (24h)" 
          value={aggregatedMetrics.totalCalls.toLocaleString()} 
          icon={WrenchIcon} 
          colorClass="orange" 
        />
      </div>

      {/* Server Observability Section */}
      {servers && servers.length > 0 && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-base font-semibold text-surface-800">Server Observability</h2>
            <div className="flex items-center space-x-3">
              {aggregatedMetrics.totalErrors > 0 && (
                <span className="px-2.5 py-1 text-xs font-medium bg-error-50 text-error-700 rounded-full">
                  {aggregatedMetrics.errorRate}% Error Rate
                </span>
              )}
              {metricsLoading && (
                <span className="text-xs text-surface-400">Updating...</span>
              )}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {servers.slice(0, 8).map((server) => {
              const connector = connectors?.find(c => c.id === server.connector_id);
              return (
                <ServerMetricsCard
                  key={server.id}
                  server={server}
                  metrics={metricsMap[server.id]}
                  connector={connector}
                />
              );
            })}
          </div>
          {servers.length > 8 && (
            <p className="text-xs text-surface-400 mt-3 text-center">
              Showing 8 of {servers.length} servers
            </p>
          )}
        </div>
      )}

      {/* Tool Usage & Errors Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ToolUsageChart metricsMap={metricsMap} maxTools={5} />
        <RecentErrorsPanel servers={servers} maxErrors={5} />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Recent Servers */}
        <div className="card p-5">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Recent Servers</h3>
          {servers && servers.length > 0 ? (
            <div className="space-y-2">
              {servers.slice(0, 5).map((server) => (
                <div key={server.id} className="flex items-center justify-between p-3 rounded-lg hover:bg-surface-50 transition-colors">
                  <div className="flex items-center">
                    <div className={`w-2 h-2 rounded-full mr-3 ${server.is_active ? 'bg-brand-500' : 'bg-surface-300'}`}></div>
                    <div>
                      <p className="text-sm font-medium text-surface-800">{server.server_name}</p>
                      <p className="text-xs text-surface-400">{server.connector_id}</p>
                    </div>
                  </div>
                  <span className="text-xs text-surface-400">
                    {new Date(server.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-surface-400 text-sm">No servers configured yet</p>
          )}
        </div>

        {/* Quick Actions */}
        <div className="card p-5">
          <h3 className="text-base font-semibold text-surface-800 mb-4">Quick Actions</h3>
          <div className="space-y-2">
            <button className="w-full text-left p-3 rounded-lg border border-brand-200 bg-brand-50 hover:bg-brand-100 transition-colors group">
              <div className="flex items-center">
                <div className="w-10 h-10 rounded-lg bg-white border border-brand-100 flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-brand-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-surface-800">Create New Server</p>
                  <p className="text-xs text-surface-500">Set up a new MCP server instance</p>
                </div>
              </div>
            </button>
            
            <button className="w-full text-left p-3 rounded-lg border border-surface-200 hover:bg-surface-50 transition-colors group">
              <div className="flex items-center">
                <div className="w-10 h-10 rounded-lg bg-surface-50 border border-surface-200 flex items-center justify-center mr-3">
                  <svg className="w-5 h-5 text-surface-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-medium text-surface-800">Browse Connectors</p>
                  <p className="text-xs text-surface-500">Explore available integration connectors</p>
                </div>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
