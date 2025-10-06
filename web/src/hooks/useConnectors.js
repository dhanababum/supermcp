import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';

export const useConnectors = (shouldFetch) => {
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchConnectors = useCallback(async () => {
    if (!shouldFetch) return;
    
    setLoading(true);
    setError(null);
    try {
      const data = await api.getConnectors();
      // Transform the data to match frontend expectations
      const connectorsList = data.map(connector => ({
        id: connector.id,
        name: connector.name,
        description: connector.description,
        version: connector.version,
        url: connector.url,
        status: connector.is_active ? 'Active' : 'Inactive',
        created_at: connector.created_at,
        updated_at: connector.updated_at
      }));
      setConnectors(connectorsList);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [shouldFetch]);

  useEffect(() => {
    fetchConnectors();
  }, [fetchConnectors]);

  return { connectors, loading, error, refetch: fetchConnectors };
};

