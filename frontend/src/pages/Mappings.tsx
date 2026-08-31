import { useState, useEffect, useCallback } from 'react';
import { fetchMappings } from '../services/api';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Search, ShieldCheck, AlertTriangle, RefreshCw, Loader2, Network } from 'lucide-react';
import { useSourceContext } from '../contexts/SourceContext';
import { cn } from '../utils/classnames';

export function Mappings() {
  const { currentSource } = useSourceContext();
  const [mappings, setMappings] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  const loadMappings = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchMappings();
      setMappings(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Failed to fetch mappings:', e);
      setMappings([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadMappings();
  }, [loadMappings]);

  // Flatten mappings to individual field bindings for granular exploration
  const flattenedBindings: any[] = [];
  mappings.forEach((m) => {
    if (currentSource && m.source_id !== currentSource.id) return;
    if (statusFilter !== 'all' && m.status !== statusFilter) return;

    const bindings = m.field_bindings || {};
    const confSummary = m.confidence_summary || {};

    Object.entries(bindings).forEach(([rawKey, targetKey]) => {
      flattenedBindings.push({
        mappingId: m.mapping_id,
        sourceId: m.source_id,
        templateId: m.template_id,
        version: m.version,
        rawField: rawKey,
        targetField: targetKey,
        confidence: typeof confSummary[rawKey] === 'number' ? Math.round(confSummary[rawKey] * 100) : 95,
        status: m.status === 'active' ? 'Approved' : m.status,
        approvedBy: m.approved_by || 'system',
        approvedAt: m.approved_at,
      });
    });
  });

  const filtered = flattenedBindings.filter((item) => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.sourceId?.toLowerCase().includes(q) ||
      item.rawField?.toLowerCase().includes(q) ||
      item.targetField?.toLowerCase().includes(q)
    );
  });

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Network className="w-6 h-6 text-brand-purple" />
            Mappings Explorer
          </h1>
          <p className="text-slate-400 mt-1">Browse and manage semantic field mappings across all sources.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex gap-1 bg-slate-900 border border-slate-800 p-1 rounded-md text-xs">
            {(['all', 'active', 'superseded'] as const).map((s) => (
              <button
                key={s}
                onClick={() => setStatusFilter(s)}
                className={cn(
                  'px-2.5 py-1 rounded capitalize transition-colors',
                  statusFilter === s ? 'bg-slate-800 text-brand-cyan font-medium' : 'text-slate-400 hover:text-slate-200'
                )}
              >
                {s}
              </button>
            ))}
          </div>
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search field or source..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="bg-slate-900 border border-slate-800 rounded-md pl-9 pr-4 py-1.5 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-cyan"
            />
          </div>
          <button
            onClick={loadMappings}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-md border border-slate-700 text-sm font-medium text-slate-200 transition-colors"
          >
            <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
            Refresh
          </button>
        </div>
      </div>

      <Card className="p-0 overflow-hidden border-slate-800">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-900 text-slate-400 border-b border-slate-800">
              <tr>
                <th className="px-6 py-4 font-medium">Source</th>
                <th className="px-6 py-4 font-medium">Version</th>
                <th className="px-6 py-4 font-medium">Raw Field</th>
                <th className="px-6 py-4 font-medium">Target Schema Field</th>
                <th className="px-6 py-4 font-medium">Confidence</th>
                <th className="px-6 py-4 font-medium">Status</th>
                <th className="px-6 py-4 font-medium">Approved By</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/50">
              {loading ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2" />
                    Loading active mappings...
                  </td>
                </tr>
              ) : filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} className="px-6 py-8 text-center text-slate-500">
                    No active mappings found. Complete onboarding for a source to generate mappings.
                  </td>
                </tr>
              ) : (
                filtered.map((map, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                    <td className="px-6 py-4 font-mono text-xs text-slate-200">{map.sourceId}</td>
                    <td className="px-6 py-4">
                      <Badge variant="secondary" className="font-mono text-[10px]">
                        v{map.version || 1}
                      </Badge>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-brand-purple">{map.rawField}</td>
                    <td className="px-6 py-4 font-mono text-xs text-brand-cyan">{map.targetField}</td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <div className="w-16 bg-slate-800 rounded-full h-1.5">
                          <div className="bg-brand-cyan h-1.5 rounded-full" style={{ width: `${map.confidence}%` }} />
                        </div>
                        <span className="text-xs text-slate-400">{map.confidence}%</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {map.status === 'Approved' || map.status === 'active' ? (
                        <span className="flex items-center gap-1.5 text-brand-green text-xs font-medium">
                          <ShieldCheck className="w-3.5 h-3.5" /> Active
                        </span>
                      ) : (
                        <span className="flex items-center gap-1.5 text-brand-amber text-xs font-medium">
                          <AlertTriangle className="w-3.5 h-3.5" /> {map.status}
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-400 font-mono">{map.approvedBy}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
