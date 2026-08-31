import { useState, useEffect, useCallback } from 'react';
import { fetchEvents, getExportUrl } from '../services/api';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import {
  Search, Download, MoreHorizontal, X,
  RefreshCw, Loader2, GitCommit, ChevronLeft, ChevronRight,
} from 'lucide-react';
import { cn } from '../utils/classnames';
import { useSourceContext } from '../contexts/SourceContext';

export function Events() {
  const { currentSource } = useSourceContext();
  const [events, setEvents] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedEvent, setSelectedEvent] = useState<any | null>(null);
  const [pathFilter, setPathFilter] = useState<string>('all');

  const loadEvents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchEvents({
        source_id: currentSource ? currentSource.id : undefined,
        processing_path: pathFilter !== 'all' ? pathFilter : undefined,
        page,
        page_size: 50,
      });
      setEvents(data.items || []);
      setTotal(data.total || (data.items ? data.items.length : 0));
    } catch (e) {
      console.error('Failed to load events:', e);
      setEvents([]);
    } finally {
      setLoading(false);
    }
  }, [currentSource, pathFilter, page]);

  useEffect(() => {
    loadEvents();
  }, [loadEvents]);

  const filteredEvents = events.filter((ev) =>
    !searchQuery ||
    JSON.stringify(ev).toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-6 max-w-7xl mx-auto">
      {/* LEFT: TABLE VIEW */}
      <div className={cn('flex flex-col transition-all duration-300', selectedEvent ? 'w-2/3' : 'w-full')}>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="relative w-80">
              <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Filter events or fields..."
                className="w-full bg-slate-900 border border-slate-700 rounded-md pl-9 p-2 text-sm text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan outline-none"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            <div className="flex gap-1 text-xs bg-slate-900 p-1 rounded-md border border-slate-800">
              {(['all', 'fast', 'adaptive'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPathFilter(p)}
                  className={cn(
                    'px-2.5 py-1 rounded capitalize transition-colors',
                    pathFilter === p ? 'bg-slate-800 text-brand-cyan font-medium' : 'text-slate-400 hover:text-slate-200'
                  )}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div className="flex gap-2">
            <button
              onClick={loadEvents}
              className="p-2 border border-slate-700 rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors"
              title="Refresh"
            >
              <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
            </button>
            <a
              href={getExportUrl('ndjson', currentSource?.id)}
              download="ulpf-events.ndjson"
              className="p-2 border border-slate-700 rounded-md bg-slate-800 text-slate-300 hover:bg-slate-700 transition-colors flex items-center gap-1.5 text-xs"
              title="Export NDJSON"
            >
              <Download className="w-4 h-4" />
              <span>Export</span>
            </a>
          </div>
        </div>

        <Card className="bg-slate-900 border-slate-800 flex-1 flex flex-col overflow-hidden">
          <div className="overflow-x-auto flex-1 custom-scrollbar">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-950 border-b border-slate-800 text-slate-400 sticky top-0 z-10">
                <tr>
                  <th className="p-3 font-medium">Trace ID</th>
                  <th className="p-3 font-medium">Source</th>
                  <th className="p-3 font-medium">Schema Version</th>
                  <th className="p-3 font-medium">Path</th>
                  <th className="p-3 font-medium">Timestamp</th>
                  <th className="p-3 font-medium text-right w-12"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-slate-500">
                      <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                      Loading normalized events...
                    </td>
                  </tr>
                ) : filteredEvents.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-slate-500">
                      No normalized events found. Ingest logs to see processed events.
                    </td>
                  </tr>
                ) : (
                  filteredEvents.map((ev, idx) => (
                    <tr
                      key={ev.event_id || idx}
                      onClick={() => setSelectedEvent(ev)}
                      className={cn(
                        'cursor-pointer transition-colors hover:bg-slate-800/50',
                        selectedEvent?.event_id === ev.event_id
                          ? 'bg-brand-cyan/5 border-l-2 border-l-brand-cyan'
                          : 'border-l-2 border-l-transparent'
                      )}
                    >
                      <td className="p-3 text-brand-purple font-mono text-xs">
                        {ev.trace_id ? `${ev.trace_id.slice(0, 16)}…` : '—'}
                      </td>
                      <td className="p-3 text-slate-300 text-xs font-mono">{ev.source_id}</td>
                      <td className="p-3 text-slate-400 text-xs">
                        <Badge variant="secondary" className="font-mono text-[10px]">
                          {ev.schema_version || 'ulpf-core-1.0'}
                        </Badge>
                      </td>
                      <td className="p-3 text-xs">
                        <Badge
                          variant={ev.processing_path === 'fast' ? 'success' : 'secondary'}
                          className="text-[10px] uppercase"
                        >
                          {ev.processing_path || 'adaptive'}
                        </Badge>
                      </td>
                      <td className="p-3 text-slate-400 font-mono text-xs">
                        {ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : '—'}
                      </td>
                      <td className="p-3 text-right">
                        <MoreHorizontal className="w-4 h-4 text-slate-500 inline-block" />
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          <div className="bg-slate-950 border-t border-slate-800 p-3 text-xs text-slate-500 flex justify-between items-center">
            <span>
              Showing {filteredEvents.length} of {total} events
            </span>
            <div className="flex items-center gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(p => Math.max(1, p - 1))}
                className="p-1 rounded bg-slate-900 border border-slate-800 disabled:opacity-30 hover:bg-slate-800 text-slate-300"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
              </button>
              <span>Page {page}</span>
              <button
                disabled={filteredEvents.length < 50}
                onClick={() => setPage(p => p + 1)}
                className="p-1 rounded bg-slate-900 border border-slate-800 disabled:opacity-30 hover:bg-slate-800 text-slate-300"
              >
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </Card>
      </div>

      {/* RIGHT: JSON INSPECTOR */}
      {selectedEvent && (
        <div className="w-1/3 flex flex-col">
          <Card className="bg-slate-900 border-slate-800 flex-1 flex flex-col h-full overflow-hidden shadow-2xl">
            <div className="border-b border-slate-800 p-4 flex justify-between items-center bg-slate-950">
              <div>
                <h3 className="font-bold text-slate-100 text-sm">Event Details</h3>
                <p className="text-xs font-mono text-brand-purple mt-0.5 truncate max-w-[200px]">
                  {selectedEvent.trace_id}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={`/trace`}
                  className="text-xs text-brand-cyan hover:underline flex items-center gap-1"
                >
                  <GitCommit className="w-3.5 h-3.5" />
                  Explore Trace
                </a>
                <button
                  onClick={() => setSelectedEvent(null)}
                  className="p-1 text-slate-400 hover:text-slate-200 hover:bg-slate-800 rounded-md transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="p-0 overflow-y-auto custom-scrollbar flex-1 bg-slate-950">
              <pre className="text-xs font-mono p-4 text-slate-300 leading-relaxed">
                {JSON.stringify(selectedEvent.normalized_payload || selectedEvent, null, 2)
                  .split('\n')
                  .map((line, i) => {
                    const isKey = line.includes('":');
                    if (isKey) {
                      const [key, val] = line.split('":');
                      return (
                        <div key={i} className="hover:bg-slate-900 rounded px-1 transition-colors">
                          <span className="text-brand-cyan">{key}"</span>:
                          <span className="text-slate-300">{val}</span>
                        </div>
                      );
                    }
                    return (
                      <div key={i} className="px-1 text-slate-500">
                        {line}
                      </div>
                    );
                  })}
              </pre>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
