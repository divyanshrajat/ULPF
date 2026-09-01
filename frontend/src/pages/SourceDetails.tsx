import { useState, useEffect, useCallback } from 'react';
import {
  fetchSource, fetchSourceTemplates, fetchSourceMappings,
  fetchSourceFiles, fetchSourceDrift,
} from '../services/api';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { useSourceContext } from '../contexts/SourceContext';
import { useSources } from '../hooks/useSources';
import {
  Server, RefreshCw, ArrowRight, ArrowLeft, Search,
  Network, Database, ShieldCheck,
  CheckCircle2, Plus,
} from 'lucide-react';
import { cn } from '../utils/classnames';

export function SourceDetails() {
  const { currentSource, setCurrentSource } = useSourceContext();
  const { sources, refetch: refetchSources } = useSources();

  const [details, setDetails] = useState<any | null>(null);
  const [templates, setTemplates] = useState<any[]>([]);
  const [mappings, setMappings] = useState<any[]>([]);
  const [files, setFiles] = useState<any[]>([]);
  const [drift, setDrift] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [protocolFilter, setProtocolFilter] = useState('all');

  const loadData = useCallback(async () => {
    if (!currentSource) return;
    const srcId = currentSource.id || currentSource.source_id || '';
    if (!srcId) return;

    setLoading(true);
    try {
      const [src, tpls, maps, fls, dft] = await Promise.allSettled([
        fetchSource(srcId),
        fetchSourceTemplates(srcId),
        fetchSourceMappings(srcId),
        fetchSourceFiles(srcId),
        fetchSourceDrift(srcId),
      ]);

      if (src.status === 'fulfilled') setDetails(src.value);
      if (tpls.status === 'fulfilled') setTemplates(tpls.value || []);
      if (maps.status === 'fulfilled') setMappings(maps.value || []);
      if (fls.status === 'fulfilled') setFiles(fls.value || []);
      if (dft.status === 'fulfilled') setDrift(dft.value || []);
    } catch (e) {
      console.error('Failed to load source details:', e);
    } finally {
      setLoading(false);
    }
  }, [currentSource]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Filter sources for directory view
  const filteredSources = sources.filter((s) => {
    const matchesSearch =
      !searchQuery ||
      s.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.vendor?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.product?.toLowerCase().includes(searchQuery.toLowerCase());

    const matchesProtocol =
      protocolFilter === 'all' ||
      (s.transport && s.transport.toLowerCase() === protocolFilter.toLowerCase());

    return matchesSearch && matchesProtocol;
  });

  // ─── DIRECTORY VIEW (When no source is selected) ───────────────────────────
  if (!currentSource) {
    return (
      <div className="space-y-6 max-w-7xl mx-auto pb-12">
        {/* DIRECTORY HEADER */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2.5">
              <Server className="w-6 h-6 text-brand-cyan" />
              Sources Directory & Inventory
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Registered log emitters, active OCSF mapping versions, and ingestion telemetry.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchSources()}
              className="bg-white/10 text-white hover:bg-white hover:text-slate-950 font-semibold border border-white/20"
            >
              <RefreshCw className="w-3.5 h-3.5 mr-1.5" />
              Refresh
            </Button>
            <Button
              size="sm"
              onClick={() => (window.location.href = '/onboarding')}
              className="bg-white text-slate-950 hover:bg-slate-100 font-bold shadow-md shadow-white/10"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Onboard New Source
            </Button>
          </div>
        </div>

        {/* METRICS SUMMARY */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Card className="bg-slate-900 border-slate-800 p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Registered Sources</div>
                <div className="text-2xl font-bold font-mono text-slate-100 mt-1">{sources.length}</div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-brand-cyan/10 text-brand-cyan flex items-center justify-center">
                <Server className="w-5 h-5" />
              </div>
            </div>
          </Card>

          <Card className="bg-slate-900 border-slate-800 p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Active Fast Path Emitters</div>
                <div className="text-2xl font-bold font-mono text-brand-green mt-1">{sources.length}</div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-brand-green/10 text-brand-green flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            </div>
          </Card>

          <Card className="bg-slate-900 border-slate-800 p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Normalization Schema</div>
                <div className="text-sm font-bold font-mono text-brand-purple mt-2">ulpf-core-1.0 (OCSF)</div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-brand-purple/10 text-brand-purple flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>
          </Card>
        </div>

        {/* SEARCH & FILTERS */}
        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between bg-slate-900 p-3 rounded-xl border border-slate-800">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search by name, ID, vendor, or product..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-100 focus:outline-none focus:ring-1 focus:ring-brand-cyan"
            />
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            {['all', 'syslog', 'http', 'file_upload'].map((proto) => (
              <button
                key={proto}
                onClick={() => setProtocolFilter(proto)}
                className={cn(
                  'px-3 py-1.5 rounded-lg capitalize font-semibold transition-all border',
                  protocolFilter === proto
                    ? 'bg-white text-slate-950 border-white shadow-sm'
                    : 'text-white bg-white/10 border-white/20 hover:bg-white/20'
                )}
              >
                {proto.replace('_', ' ')}
              </button>
            ))}
          </div>
        </div>

        {/* SOURCES GRID */}
        {filteredSources.length === 0 ? (
          <Card className="bg-slate-900 border-slate-800 p-12 text-center">
            <Server className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-300">No sources match your filter</h3>
            <p className="text-sm text-slate-500 mt-1 max-w-sm mx-auto">
              Try adjusting your search terms or onboard a new log source.
            </p>
            <Button
              size="sm"
              onClick={() => (window.location.href = '/onboarding')}
              className="mt-4 bg-white text-slate-950 font-bold hover:bg-slate-100 shadow-md"
            >
              <Plus className="w-4 h-4 mr-1.5" />
              Onboard a Source
            </Button>
          </Card>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredSources.map((s) => (
              <Card
                key={s.id}
                className="bg-slate-900 border-slate-800 hover:border-slate-600 transition-all group flex flex-col justify-between"
              >
                <CardContent className="p-5 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-brand-cyan shrink-0 group-hover:border-brand-cyan/50 transition-colors">
                        <Server className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-100 truncate max-w-[180px]">{s.name}</h3>
                        <div className="text-xs font-mono text-brand-cyan">{s.id}</div>
                      </div>
                    </div>
                    <Badge variant="success" className="text-[10px]">
                      Active
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-950 p-2.5 rounded-lg border border-slate-800/80">
                    <div>
                      <span className="text-slate-500 block">Vendor</span>
                      <span className="text-slate-200 font-medium truncate block">{s.vendor || 'Generic'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Product</span>
                      <span className="text-slate-200 font-medium truncate block">{s.product || 'Log'}</span>
                    </div>
                    <div className="col-span-2 pt-1 border-t border-slate-800/50 flex justify-between items-center">
                      <span className="text-slate-500">Transport:</span>
                      <span className="font-mono text-slate-300 uppercase">{s.transport || 'syslog'}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-800">
                    <Button
                      size="sm"
                      onClick={() => setCurrentSource(s)}
                      className="w-full bg-white hover:bg-slate-100 text-slate-950 font-bold text-xs py-1.5 h-auto shadow-sm flex items-center justify-center gap-1.5"
                    >
                      <span>Inspect Source Details</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    );
  }

  // ─── SOURCE DRILLDOWN VIEW (When a source is selected) ─────────────────────
  const srcId = currentSource.id || currentSource.source_id || '';

  return (
    <div className="max-w-7xl mx-auto space-y-6 pb-12">
      {/* NAVIGATION BAR */}
      <div className="flex items-center justify-between">
        <button
          onClick={() => setCurrentSource(null)}
          className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-white border border-white/20 transition-all shadow-sm"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to All Sources
        </button>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            disabled={loading}
            className="bg-white/10 text-white hover:bg-white hover:text-slate-950 font-semibold border border-white/20"
          >
            <RefreshCw className={cn('w-3.5 h-3.5 mr-1.5', loading && 'animate-spin')} />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => (window.location.href = `/events`)}
            className="bg-white text-slate-950 hover:bg-slate-100 font-bold shadow-md shadow-white/10"
          >
            <Database className="w-3.5 h-3.5 mr-1.5" />
            Explore Normalized Events
          </Button>
        </div>
      </div>

      {/* HEADER CARD */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 bg-slate-900 p-6 rounded-xl border border-slate-800 shadow-xl">
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700 text-brand-cyan shrink-0">
            <Server className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center gap-3 mb-1.5">
              <h1 className="text-2xl font-bold text-slate-100">{details?.name || currentSource.name}</h1>
              <Badge variant={details?.status === 'active' ? 'success' : 'secondary'}>
                {details?.status || 'Active'} (Fast Path)
              </Badge>
            </div>
            <div className="flex flex-wrap gap-4 text-xs font-mono text-slate-400">
              <span>
                <strong className="text-slate-300">ID:</strong> {srcId}
              </span>
              <span>
                <strong className="text-slate-300">Vendor:</strong> {details?.vendor || currentSource.vendor || '—'}
              </span>
              <span>
                <strong className="text-slate-300">Product:</strong> {details?.product || currentSource.product || '—'}
              </span>
              <span>
                <strong className="text-slate-300">Transport:</strong> {details?.transport || currentSource.transport || '—'}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* METRICS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-xs text-slate-400 uppercase tracking-wider">Preserved Files in Vault</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono text-slate-100 mb-1">{files.length}</div>
            <p className="text-xs text-slate-500">Raw immutable log payloads sealed with SHA-256</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-xs text-slate-400 uppercase tracking-wider">Discovered Log Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono text-brand-cyan mb-1">{templates.length}</div>
            <p className="text-xs text-slate-500">Drain3 clusters mined for deterministic parsing</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-xs text-slate-400 uppercase tracking-wider">Active Schema Version</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono text-brand-green mb-1 flex items-baseline gap-2">
              v{details?.active_mapping_version || (mappings.length ? mappings[0].version : 1)}
              {drift.length > 0 && <span className="text-xs text-brand-amber font-sans">({drift.length} drift events)</span>}
            </div>
            <p className="text-xs text-slate-500">Canonical standard: {details?.active_schema_version || 'ulpf-core-1.0'}</p>
          </CardContent>
        </Card>
      </div>

      {/* TEMPLATES TABLE */}
      <Card className="bg-slate-900 border-slate-800 shadow-xl overflow-hidden">
        <CardHeader className="border-b border-slate-800 pb-4">
          <CardTitle className="text-slate-100 text-sm flex items-center gap-2">
            <Network className="w-4 h-4 text-brand-purple" />
            Discovered Log Templates ({templates.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                <tr>
                  <th className="p-3.5 font-medium">Template ID</th>
                  <th className="p-3.5 font-medium">Pattern Signature</th>
                  <th className="p-3.5 font-medium">Occurrences</th>
                  <th className="p-3.5 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {templates.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-slate-500">
                      No templates mined yet for this source. Upload samples via Onboarding.
                    </td>
                  </tr>
                ) : (
                  templates.map((tpl) => (
                    <tr key={tpl.template_id} className="hover:bg-slate-800/40 transition-colors">
                      <td className="p-3.5 font-mono text-xs text-brand-purple font-semibold">{tpl.template_id}</td>
                      <td className="p-3.5 font-mono text-xs text-brand-cyan max-w-lg truncate" title={tpl.pattern}>
                        {tpl.pattern}
                      </td>
                      <td className="p-3.5 font-mono text-xs text-slate-300">{tpl.occurrence_count || 1}</td>
                      <td className="p-3.5">
                        <Badge variant="success" className="text-[10px]">
                          {tpl.status || 'Active'}
                        </Badge>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
