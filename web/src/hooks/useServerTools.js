import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export const useServerTools = (serverId, shouldFetch) => {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchTools = useCallback(async () => {
    if (!serverId) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await api.getServerTools(serverId);
      setTools(data.tools || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [serverId]);

  useEffect(() => {
    if (!shouldFetch || !serverId) return;
    fetchTools();
  }, [serverId, shouldFetch, fetchTools]);

  return { tools, loading, error, refetch: fetchTools };
};

