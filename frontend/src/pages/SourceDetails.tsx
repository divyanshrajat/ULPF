import { useState, useEffect, useCallback } from 'react';
import {
  fetchSource, fetchJobs, fetchEvents
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
import { formatIST } from '../utils/date';

export function SourceDetails() {
  const { currentSource, setCurrentSource } = useSourceContext();
  const { sources, refetch: refetchSources } = useSources();

  const [details, setDetails] = useState<any | null>(null);
  const [jobs, setJobs] = useState<any[]>([]);
  const [eventsData, setEventsData] = useState<any>({ total: 0, items: [] });
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [protocolFilter, setProtocolFilter] = useState('all');

  const loadData = useCallback(async () => {
    if (!currentSource) return;
    const srcId = currentSource.id || currentSource.source_id || '';
    if (!srcId) return;

    setLoading(true);
    try {
      const [src, jbs, evts] = await Promise.allSettled([
        fetchSource(srcId),
        fetchJobs({ source_id: srcId, page_size: 5 }),
        fetchEvents({ source_id: srcId, page_size: 1 }),
      ]);

      if (src.status === 'fulfilled') setDetails(src.value);
      if (jbs.status === 'fulfilled') setJobs(jbs.value.items || []);
      if (evts.status === 'fulfilled') setEventsData(evts.value || { total: 0, items: [] });
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
            <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2.5 font-serif">
              <Server className="w-6 h-6 text-slate-900" />
              Sources Directory & Inventory
            </h1>
            <p className="text-slate-600 text-sm mt-1">
              Registered log emitters, active OCSF mapping versions, and ingestion telemetry.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetchSources()}
              className="bg-white/10 text-slate-900 hover:bg-white hover:text-slate-950 font-semibold border border-white/20"
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
          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Total Registered Sources</div>
                <div className="text-2xl font-bold font-mono text-slate-900 mt-1">{sources.length}</div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-brand-cyan/10 text-slate-900 flex items-center justify-center">
                <Server className="w-5 h-5" />
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Active Fast Path Emitters</div>
                <div className="text-2xl font-bold font-mono text-brand-green mt-1">{sources.length}</div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-brand-green/10 text-brand-green flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5" />
              </div>
            </div>
          </Card>

          <Card className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs font-semibold text-slate-600 uppercase tracking-wider">Normalization Schema</div>
                <div className="text-sm font-bold font-mono text-brand-purple mt-2">ulpf-core-1.0 (OCSF)</div>
              </div>
              <div className="w-10 h-10 rounded-lg bg-brand-purple/10 text-brand-purple flex items-center justify-center">
                <ShieldCheck className="w-5 h-5" />
              </div>
            </div>
          </Card>
        </div>

        {/* SEARCH & FILTERS */}
        <Card className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between p-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search by name, ID, vendor, or product..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-cyan"
            />
          </div>

          <div className="flex items-center gap-1.5 text-xs">
            {['all', 'syslog', 'http', 'file_upload'].map((proto) => {
              return (
                <button
                  key={proto}
                  onClick={() => setProtocolFilter(proto)}
                  className={cn(
                    'px-3 py-1.5 rounded-lg capitalize font-semibold transition-all border',
                    protocolFilter === proto
                      ? 'bg-white text-slate-950 border-white shadow-sm'
                      : 'text-slate-900 bg-white/10 border-white/20 hover:bg-white/20'
                  )}
                >
                  {proto.replace('_', ' ')}
                </button>
              );
            })}
          </div>
        </Card>

        {/* SOURCES GRID */}
        {filteredSources.length === 0 ? (
          <Card className="p-12 text-center">
            <Server className="w-12 h-12 text-slate-600 mx-auto mb-3" />
            <h3 className="text-lg font-bold text-slate-700">No sources match your filter</h3>
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
                className="hover:border-slate-600 transition-all group flex flex-col justify-between"
              >
                <CardContent className="p-5 space-y-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-slate-100 border border-slate-700 flex items-center justify-center text-slate-900 shrink-0 group-hover:border-brand-cyan/50 transition-colors">
                        <Server className="w-5 h-5" />
                      </div>
                      <div>
                        <h3 className="text-sm font-bold text-slate-900 truncate max-w-[180px]">{s.name}</h3>
                        <div className="text-xs font-mono text-slate-900">{s.id}</div>
                      </div>
                    </div>
                    <Badge variant="success" className="text-[10px]">
                      Active
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50 p-2.5 rounded-lg border border-slate-200/80">
                    <div>
                      <span className="text-slate-500 block">Vendor</span>
                      <span className="text-slate-800 font-medium truncate block">{s.vendor || 'Generic'}</span>
                    </div>
                    <div>
                      <span className="text-slate-500 block">Product</span>
                      <span className="text-slate-800 font-medium truncate block">{s.product || 'Log'}</span>
                    </div>
                    <div className="col-span-2 pt-1 border-t border-slate-200/50 flex justify-between items-center">
                      <span className="text-slate-500">Transport:</span>
                      <span className="font-mono text-slate-700 uppercase">{s.transport || 'syslog'}</span>
                    </div>
                  </div>

                  <div className="flex items-center justify-between pt-2 border-t border-slate-200">
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
          className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5 rounded-lg bg-white/10 hover:bg-white/20 text-slate-900 border border-white/20 transition-all shadow-sm"
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
            className="bg-white/10 text-slate-900 hover:bg-white hover:text-slate-950 font-semibold border border-white/20"
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
      <Card className="flex flex-col md:flex-row md:items-center justify-between gap-6 p-6 shadow-xl">
        <div className="flex items-center gap-5">
          <div className="w-16 h-16 rounded-xl bg-slate-100 flex items-center justify-center border border-slate-700 text-slate-900 shrink-0">
            <Server className="w-8 h-8" />
          </div>
          <div>
            <div className="flex items-center gap-3 mb-1.5">
              <h1 className="text-2xl font-bold text-slate-900 font-serif">{details?.name || currentSource.name}</h1>
              <Badge variant={details?.status === 'active' ? 'success' : 'secondary'}>
                {details?.status || 'Active'} (Fast Path)
              </Badge>
            </div>
            <div className="flex flex-wrap gap-4 text-xs font-mono text-slate-600">
              <span>
                <strong className="text-slate-700">ID:</strong> {srcId}
              </span>
              <span>
                <strong className="text-slate-700">Vendor:</strong> {details?.vendor || currentSource.vendor || '—'}
              </span>
              <span>
                <strong className="text-slate-700">Product:</strong> {details?.product || currentSource.product || '—'}
              </span>
              <span>
                <strong className="text-slate-700">Transport:</strong> {details?.transport || currentSource.transport || '—'}
              </span>
            </div>
          </div>
        </div>
      </Card>

      {/* METRICS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="">
          <CardHeader>
            <CardTitle className="text-xs text-slate-600 uppercase tracking-wider">Normalized Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono text-slate-900 mb-1">{eventsData.total}</div>
            <p className="text-xs text-slate-500">Successfully mapped to OCSF</p>
          </CardContent>
        </Card>

        <Card className="">
          <CardHeader>
            <CardTitle className="text-xs text-slate-600 uppercase tracking-wider">Recent Ingestion Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono text-slate-900 mb-1">{jobs.length}</div>
            <p className="text-xs text-slate-500">Batch processing cycles</p>
          </CardContent>
        </Card>

        <Card className="">
          <CardHeader>
            <CardTitle className="text-xs text-slate-600 uppercase tracking-wider">Active Schema Version</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono text-brand-green mb-1 flex items-baseline gap-2">
              v1
            </div>
            <p className="text-xs text-slate-500">Canonical standard: ulpf-core-1.0</p>
          </CardContent>
        </Card>
      </div>

      {/* JOBS TABLE */}
      <Card className="shadow-xl overflow-hidden">
        <CardHeader className="border-b border-slate-200 pb-4">
          <CardTitle className="text-slate-900 text-sm flex items-center gap-2">
            <Network className="w-4 h-4 text-brand-purple" />
            Recent Ingestion Jobs
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm whitespace-nowrap">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-600">
                <tr>
                  <th className="p-3.5 font-medium">Job ID</th>
                  <th className="p-3.5 font-medium">Status</th>
                  <th className="p-3.5 font-medium">Progress</th>
                  <th className="p-3.5 font-medium">Started At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {jobs.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-slate-500">
                      No jobs found for this source.
                    </td>
                  </tr>
                ) : (
                  jobs.map((job) => (
                    <tr key={job.id} className="hover:bg-slate-100/40 transition-colors">
                      <td className="p-3.5 font-mono text-xs text-brand-purple font-semibold">{job.id}</td>
                      <td className="p-3.5 font-mono text-xs text-slate-700">{job.status}</td>
                      <td className="p-3.5 font-mono text-xs text-slate-700">{job.processed_events} / {job.total_events}</td>
                      <td className="p-3.5 font-mono text-xs text-slate-700">{formatIST(job.started_at)}</td>
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
