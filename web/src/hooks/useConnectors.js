import { useState, useEffect, useCallback, useRef } from 'react';
import { api } from '../services/api';

export const useConnectors = (shouldFetch = true) => {
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const isFetchingRef = useRef(false);

  const fetchConnectors = useCallback(async () => {
    // Prevent duplicate fetches
    if (isFetchingRef.current) {
      return;
    }

    isFetchingRef.current = true;
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
        mode: connector.mode, // Include mode field for proper mode display
        status: connector.is_active ? 'Active' : 'Inactive',
        created_at: connector.created_at,
        updated_at: connector.updated_at
      }));
      setConnectors(connectorsList);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      isFetchingRef.current = false;
    }
  }, []); // Remove shouldFetch from dependencies

  useEffect(() => {
    if (shouldFetch) {
      fetchConnectors();
    }
  }, [shouldFetch, fetchConnectors]);

  return { connectors, loading, error, refetch: fetchConnectors };
};

