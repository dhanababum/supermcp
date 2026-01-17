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
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-surface-900 mb-2">Dashboard</h1>
        <p className="text-surface-500">Monitor your MCP servers, connectors, and tools</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
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
        <div className="mb-8">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-surface-900">Server Observability</h2>
            <div className="flex items-center space-x-3">
              {aggregatedMetrics.totalErrors > 0 && (
                <span className="px-3 py-1 text-sm font-medium bg-danger-50 text-danger-700 rounded-full">
                  {aggregatedMetrics.errorRate}% Error Rate
                </span>
              )}
              {metricsLoading && (
                <span className="text-xs text-surface-500">Updating...</span>
              )}
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {servers.slice(0, 8).map((server) => (
              <ServerMetricsCard
                key={server.id}
                server={server}
                metrics={metricsMap[server.id]}
              />
            ))}
          </div>
          {servers.length > 8 && (
            <p className="text-sm text-surface-500 mt-3 text-center">
              Showing 8 of {servers.length} servers
            </p>
          )}
        </div>
      )}

      {/* Tool Usage & Errors Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        <ToolUsageChart metricsMap={metricsMap} maxTools={5} />
        <RecentErrorsPanel servers={servers} maxErrors={5} />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Servers */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-surface-900 mb-4">Recent Servers</h3>
          {servers && servers.length > 0 ? (
            <div className="space-y-3">
              {servers.slice(0, 5).map((server) => (
                <div key={server.id} className="flex items-center justify-between p-3 bg-surface-50 rounded-lg border border-surface-100">
                  <div className="flex items-center">
                    <div className={`w-2.5 h-2.5 rounded-full mr-3 ${server.is_active ? 'bg-success-500' : 'bg-surface-400'}`}></div>
                    <div>
                      <p className="text-sm font-medium text-surface-900">{server.server_name}</p>
                      <p className="text-xs text-surface-500">{server.connector_id}</p>
                    </div>
                  </div>
                  <span className="text-xs text-surface-400 font-mono">
                    {new Date(server.created_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-surface-500 text-sm">No servers configured yet</p>
          )}
        </div>

        {/* Quick Actions */}
        <div className="card p-6">
          <h3 className="text-lg font-semibold text-surface-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button className="w-full text-left p-4 bg-brand-50 hover:bg-brand-100 border border-brand-100 rounded-lg transition-colors group">
              <div className="flex items-center">
                <div className="p-2 bg-white rounded-md shadow-sm mr-4 group-hover:scale-105 transition-transform">
                  <svg className="w-5 h-5 text-brand-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-surface-900">Create New Server</p>
                  <p className="text-xs text-surface-600">Set up a new MCP server instance</p>
                </div>
              </div>
            </button>
            
            <button className="w-full text-left p-4 bg-surface-50 hover:bg-surface-100 border border-surface-200 rounded-lg transition-colors group">
              <div className="flex items-center">
                <div className="p-2 bg-white rounded-md shadow-sm mr-4 group-hover:scale-105 transition-transform">
                  <svg className="w-5 h-5 text-surface-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm font-semibold text-surface-900">Browse Connectors</p>
                  <p className="text-xs text-surface-600">Explore available integration connectors</p>
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
