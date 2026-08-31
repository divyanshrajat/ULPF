import { createContext, useContext, useState, useEffect } from 'react';
import type { ReactNode } from 'react';

export interface Source {
  id: string;
  source_id?: string;
  name: string;
  vendor?: string;
  product?: string;
  transport?: string;
  status?: string;
  format_hint?: string;
  namespace?: string;
  active_mapping_version?: number;
  active_schema_version?: string;
  last_seen_at?: string;
  created_at?: string;
}

interface SourceContextType {
  currentSource: Source | null;
  setCurrentSource: (source: Source | null) => void;
  sources: Source[];
  setSources: (sources: Source[]) => void;
}

const SourceContext = createContext<SourceContextType | undefined>(undefined);

export function SourceProvider({ children }: { children: ReactNode }) {
  const [sources, setSources] = useState<Source[]>([]);
  const [currentSource, setCurrentSource] = useState<Source | null>(null);

  // Load from local storage initially
  useEffect(() => {
    const saved = localStorage.getItem('ulpf_current_source');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        // Normalize id / source_id
        if (!parsed.id && parsed.source_id) parsed.id = parsed.source_id;
        setCurrentSource(parsed);
      } catch (e) {
        console.error("Failed to parse saved source");
      }
    }
  }, []);

  // Save to local storage when changed
  useEffect(() => {
    if (currentSource) {
      localStorage.setItem('ulpf_current_source', JSON.stringify(currentSource));
    } else {
      localStorage.removeItem('ulpf_current_source');
    }
  }, [currentSource]);

  return (
    <SourceContext.Provider value={{ currentSource, setCurrentSource, sources, setSources }}>
      {children}
    </SourceContext.Provider>
  );
}

export function useSourceContext() {
  const context = useContext(SourceContext);
  if (context === undefined) {
    throw new Error('useSourceContext must be used within a SourceProvider');
  }
  return context;
}
