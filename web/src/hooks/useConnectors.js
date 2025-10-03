import { useState, useEffect } from 'react';
import { api } from '../services/api';

export const useConnectors = (shouldFetch) => {
  const [connectors, setConnectors] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!shouldFetch) return;

    const fetchConnectors = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.getConnectors();
        // Transform the data into a flat array
        const connectorsList = data.flatMap(connectorObj => 
          Object.entries(connectorObj).map(([key, value]) => ({
            id: key,
            name: value.name,
            description: value.description,
            version: value.version,
            author: value.author,
            status: 'Active'
          }))
        );
        setConnectors(connectorsList);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchConnectors();
  }, [shouldFetch]);

  return { connectors, loading, error };
};

