import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';

export const useServerMetrics = (serverId, hours = 24) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isFetchingRef = useRef(false);

  const fetchMetrics = useCallback(async () => {
    if (!serverId || isFetchingRef.current) return;

    isFetchingRef.current = true;
    setLoading(true);
    setError(null);

    try {
      const data = await api.getServerMetricsSummary(serverId, hours);
      setMetrics(data);
    } catch (err) {
      setError(err.message);
      setMetrics(null);
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  }, [serverId, hours]);

  useEffect(() => {
    if (serverId) {
      fetchMetrics();
    }
  }, [serverId, fetchMetrics]);

  return { metrics, loading, error, refetch: fetchMetrics };
};

export const useAllServersMetrics = (servers, hours = 24) => {
  const [metricsMap, setMetricsMap] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchAllMetrics = useCallback(async () => {
    if (!servers || servers.length === 0) {
      setMetricsMap({});
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const results = await Promise.allSettled(
        servers.map(server => 
          api.getServerMetricsSummary(server.id, hours)
            .then(data => ({ serverId: server.id, data }))
            .catch(() => ({ serverId: server.id, data: null }))
        )
      );

      const newMetricsMap = {};
      results.forEach(result => {
        if (result.status === 'fulfilled' && result.value) {
          newMetricsMap[result.value.serverId] = result.value.data;
        }
      });
      setMetricsMap(newMetricsMap);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [servers, hours]);

  useEffect(() => {
    fetchAllMetrics();
  }, [fetchAllMetrics]);

  return { metricsMap, loading, error, refetch: fetchAllMetrics };
};

export const useServerLogs = (serverId, options = {}) => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState(null);
  const [hasMore, setHasMore] = useState(true);
  const offsetRef = useRef(0);
  const limit = options.limit || 50;

  const fetchLogs = useCallback(async () => {
    if (!serverId) return;

    setLoading(true);
    setError(null);
    offsetRef.current = 0;

    try {
      const data = await api.getServerLogs(serverId, { 
        ...options, 
        limit, 
        offset: 0 
      });
      setLogs(data);
      setHasMore(data.length >= limit);
      offsetRef.current = data.length;
    } catch (err) {
      setError(err.message);
      setLogs([]);
      setHasMore(false);
    } finally {
      setLoading(false);
    }
  }, [serverId, limit, options.tool_name, options.status]);

  const loadMore = useCallback(async () => {
    if (!serverId || loadingMore || !hasMore) return;

    setLoadingMore(true);

    try {
      const data = await api.getServerLogs(serverId, { 
        ...options, 
        limit, 
        offset: offsetRef.current 
      });
      if (data.length > 0) {
        setLogs(prev => [...prev, ...data]);
        offsetRef.current += data.length;
      }
      setHasMore(data.length >= limit);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoadingMore(false);
    }
  }, [serverId, loadingMore, hasMore, limit, options.tool_name, options.status]);

  useEffect(() => {
    fetchLogs();
  }, [fetchLogs]);

  return { logs, loading, loadingMore, error, hasMore, refetch: fetchLogs, loadMore };
};
