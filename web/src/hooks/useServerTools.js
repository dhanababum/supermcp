import { useState, useEffect } from 'react';
import { api } from '../services/api';

export const useServerTools = (serverId, shouldFetch) => {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!shouldFetch || !serverId) return;

    const fetchTools = async () => {
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
    };

    fetchTools();
  }, [serverId, shouldFetch]);

  return { tools, loading, error };
};

