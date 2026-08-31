import { useState, useEffect, useCallback } from 'react';
import { fetchSources as apiFetchSources } from '../services/api';
import { useSourceContext } from '../contexts/SourceContext';
import type { Source } from '../contexts/SourceContext';

export function useSources() {
  const { sources, setSources, currentSource, setCurrentSource } = useSourceContext();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSources = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiFetchSources();
      const normalized: Source[] = (Array.isArray(data) ? data : []).map((s: any) => ({
        ...s,
        id: s.source_id || s.id,
      }));
      setSources(normalized);
    } catch (err: any) {
      setError(err?.message || 'Failed to fetch sources');
    } finally {
      setLoading(false);
    }
  }, [setSources]);

  useEffect(() => {
    if (sources.length === 0) {
      fetchSources();
    }
  }, [fetchSources, sources.length]);

  return {
    sources,
    currentSource,
    setCurrentSource,
    loading,
    error,
    refetch: fetchSources,
  };
}
