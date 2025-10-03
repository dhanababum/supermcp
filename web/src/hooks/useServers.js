import { useState, useEffect } from 'react';
import { api } from '../services/api';

export const useServers = (shouldFetch) => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchServers = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getServers();
      setServers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (shouldFetch) {
      fetchServers();
    }
  }, [shouldFetch]);

  return { servers, loading, error, refetch: fetchServers };
};

