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
  Server, RefreshCw, ArrowRight,
  Network,
} from 'lucide-react';
import { cn } from '../utils/classnames';

export function SourceDetails() {
  const { currentSource, setCurrentSource } = useSourceContext();
  const { sources } = useSources();

  const [details, setDetails] = useState<any | null>(null);
  const [templates, setTemplates] = useState<any[]>([]);
  const [mappings, setMappings] = useState<any[]>([]);
  const [files, setFiles] = useState<any[]>([]);
  const [drift, setDrift] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

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

  if (!currentSource) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] max-w-lg mx-auto text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500">
          <Server className="w-8 h-8 opacity-50" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-slate-200">Select a Source</h2>
          <p className="text-sm text-slate-400 mt-1">
            Choose a log source to view its templates, active mappings, files, and drift telemetry.
          </p>
        </div>
        <div className="w-full space-y-2">
          {sources.map((s) => (
            <button
              key={s.id}
              onClick={() => setCurrentSource(s)}
              className="w-full p-3 bg-slate-900 border border-slate-800 hover:border-brand-cyan/40 rounded-lg flex items-center justify-between text-left transition-colors"
            >
              <div>
                <div className="text-sm font-semibold text-slate-200">{s.name}</div>
                <div className="text-xs font-mono text-slate-500">{s.id}</div>
              </div>
              <ArrowRight className="w-4 h-4 text-slate-500" />
            </button>
          ))}
          {sources.length === 0 && (
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 text-sm">
              No sources registered yet.{' '}
              <a href="/onboarding" className="text-brand-cyan underline">
                Onboard a source
              </a>
            </div>
          )}
        </div>
      </div>
    );
  }

  const srcId = currentSource.id || currentSource.source_id || '';

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-12">
      {/* HEADER */}
      <div className="flex items-start justify-between bg-slate-900 p-6 rounded-xl border border-slate-800">
        <div className="flex items-center gap-6">
          <div className="w-16 h-16 rounded-xl bg-slate-800 flex items-center justify-center border border-slate-700">
            <Server className="w-8 h-8 text-brand-cyan" />
          </div>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-2xl font-bold text-slate-100">{details?.name || currentSource.name}</h1>
              <Badge variant={details?.status === 'active' ? 'success' : 'secondary'} className="animate-pulse">
                {details?.status || 'Active'}
              </Badge>
            </div>
            <p className="text-slate-400 text-xs flex gap-4 font-mono">
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
                <strong className="text-slate-300">Transport:</strong> {details?.transport || '—'}
              </span>
            </p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadData} disabled={loading}>
            <RefreshCw className={cn('w-4 h-4 mr-1', loading && 'animate-spin')} />
            Refresh
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-6">
        {/* METRICS */}
        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-xs text-slate-400 uppercase">Preserved Files</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono text-slate-100 mb-1">{files.length}</div>
            <p className="text-xs text-slate-500">Log files ingested & archived in Vault</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-xs text-slate-400 uppercase">Discovered Templates</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono text-brand-cyan mb-1">{templates.length}</div>
            <p className="text-xs text-slate-500">Drain3 log clusters mined</p>
          </CardContent>
        </Card>

        <Card className="bg-slate-900 border-slate-800">
          <CardHeader>
            <CardTitle className="text-xs text-slate-400 uppercase">Active Mappings / Drift</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-mono text-brand-green mb-1 flex items-baseline gap-2">
              v{details?.active_mapping_version || (mappings.length ? mappings[0].version : 1)}
              {drift.length > 0 && <span className="text-xs text-brand-amber font-sans">({drift.length} drift items)</span>}
            </div>
            <p className="text-xs text-slate-500">Schema version: {details?.active_schema_version || 'ulpf-core-1.0'}</p>
          </CardContent>
        </Card>
      </div>

      {/* TEMPLATES */}
      <Card className="bg-slate-900 border-slate-800">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-slate-100 text-sm flex items-center gap-2">
            <Network className="w-4 h-4 text-brand-purple" />
            Discovered Log Templates ({templates.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-950 border-b border-slate-800 text-slate-400">
                <tr>
                  <th className="p-3 font-medium">Template ID</th>
                  <th className="p-3 font-medium">Pattern / Signature</th>
                  <th className="p-3 font-medium">Occurrences</th>
                  <th className="p-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {templates.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="p-6 text-center text-slate-500">
                      No templates mined yet. Upload log samples to discover patterns.
                    </td>
                  </tr>
                ) : (
                  templates.map((tpl) => (
                    <tr key={tpl.template_id} className="hover:bg-slate-800/50 transition-colors">
                      <td className="p-3 font-mono text-xs text-brand-purple">{tpl.template_id}</td>
                      <td className="p-3 font-mono text-xs text-brand-cyan truncate max-w-md" title={tpl.pattern}>
                        {tpl.pattern}
                      </td>
                      <td className="p-3 font-mono text-xs text-slate-300">{tpl.occurrence_count || 1}</td>
                      <td className="p-3">
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
