import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';

export const useServers = (shouldFetch = true) => {
  const [servers, setServers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isFetchingRef = useRef(false);

  const fetchServers = useCallback(async () => {
    // Prevent duplicate fetches
    if (isFetchingRef.current) {
      return;
    }

    isFetchingRef.current = true;
    setLoading(true);
    setError(null);
    
    try {
      const data = await api.getServers();
      setServers(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  }, []); // Empty dependencies - stable function

  useEffect(() => {
    if (shouldFetch) {
      fetchServers();
    }
  }, [shouldFetch, fetchServers]);

  return { servers, loading, error, refetch: fetchServers };
};

