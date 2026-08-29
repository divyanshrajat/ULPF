import { useState, useEffect } from 'react';
import { API_BASE } from '../services/api';
import { useSourceContext } from '../contexts/SourceContext';

export function useSources() {
  const { sources, setSources, currentSource, setCurrentSource } = useSourceContext();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSources = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE}/sources`);
      if (!res.ok) throw new Error('Failed to fetch sources');
      const data = await res.json();
      setSources(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (sources.length === 0) {
      fetchSources();
    }
  }, []);

  return {
    sources,
    currentSource,
    setCurrentSource,
    loading,
    error,
    refetch: fetchSources
  };
}
