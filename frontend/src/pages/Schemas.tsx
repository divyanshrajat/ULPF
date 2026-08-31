import { useState, useEffect, useCallback } from 'react';
import { fetchSchemas, fetchSchema } from '../services/api';
import { Card } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Database, FolderTree, BookOpen, Loader2 } from 'lucide-react';

export function Schemas() {
  const [schemas, setSchemas] = useState<any[]>([]);
  const [activeVersion, setActiveVersion] = useState<string>('ulpf-core-1.0');
  const [schemaDetail, setSchemaDetail] = useState<any | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [activeGroup, setActiveGroup] = useState<string>('all');

  const loadSchemas = useCallback(async () => {
    try {
      const data = await fetchSchemas();
      const list = Array.isArray(data) ? data : [];
      setSchemas(list);
      if (list.length > 0) {
        setActiveVersion(list[0].schema_version || 'ulpf-core-1.0');
      }
    } catch (e) {
      console.error('Failed to load schemas:', e);
    }
  }, []);

  useEffect(() => {
    loadSchemas();
  }, [loadSchemas]);

  useEffect(() => {
    if (!activeVersion) return;
    (async () => {
      setDetailLoading(true);
      try {
        const detail = await fetchSchema(activeVersion);
        setSchemaDetail(detail);
      } catch (e) {
        console.error('Failed to load schema detail:', e);
      } finally {
        setDetailLoading(false);
      }
    })();
  }, [activeVersion]);

  const fields: any[] = schemaDetail?.field_definitions || [];

  // Group fields by namespace prefix (e.g. event., network., source., time., etc.)
  const groups: Record<string, any[]> = { all: fields };
  fields.forEach((f) => {
    const prefix = f.name?.includes('.') ? f.name.split('.')[0] : 'core';
    if (!groups[prefix]) groups[prefix] = [];
    groups[prefix].push(f);
  });

  const displayedFields = groups[activeGroup] || fields;

  return (
    <div className="space-y-6 h-full flex flex-col max-w-6xl mx-auto pb-12">
      <div className="flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-brand-cyan" />
            Core Schema Registry
          </h1>
          <p className="text-slate-400 mt-1">Explore canonical schemas, version checksums, and field definitions.</p>
        </div>
        <div className="flex items-center gap-2">
          {schemas.map((s) => (
            <button
              key={s.schema_version}
              onClick={() => setActiveVersion(s.schema_version)}
              className={`px-3 py-1.5 rounded-md text-xs font-mono transition-colors border ${
                activeVersion === s.schema_version
                  ? 'bg-brand-cyan/10 border-brand-cyan/40 text-brand-cyan'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
              }`}
            >
              {s.schema_version}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 flex-1 min-h-0">
        {/* LEFT: NAMESPACES */}
        <div className="lg:col-span-1 space-y-3 overflow-y-auto pr-2 custom-scrollbar">
          <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider sticky top-0 bg-slate-950 py-2 z-10">
            Field Groups ({Object.keys(groups).length - 1})
          </h3>
          <div className="space-y-1">
            {Object.entries(groups).map(([groupName, groupFields]) => {
              const isActive = activeGroup === groupName;
              return (
                <div
                  key={groupName}
                  onClick={() => setActiveGroup(groupName)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors flex items-center justify-between ${
                    isActive
                      ? 'bg-slate-800 border-brand-cyan text-brand-cyan'
                      : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-800'
                  }`}
                >
                  <div className="flex items-center gap-2.5">
                    <FolderTree className="w-4 h-4 text-brand-purple" />
                    <span className="font-mono text-xs uppercase">{groupName}</span>
                  </div>
                  <Badge variant="secondary" className="text-[10px]">
                    {groupFields.length}
                  </Badge>
                </div>
              );
            })}
          </div>

          {schemaDetail?.checksum && (
            <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 mt-4 space-y-1">
              <div className="text-[10px] text-slate-500 uppercase">Schema Checksum</div>
              <div className="font-mono text-[10px] text-brand-purple break-all">{schemaDetail.checksum}</div>
            </div>
          )}
        </div>

        {/* RIGHT: FIELD DEFINITIONS */}
        <div className="lg:col-span-3 min-h-0">
          <Card className="h-full flex flex-col border-slate-800">
            <div className="flex items-center justify-between p-4 border-b border-slate-800 shrink-0 bg-slate-950">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-brand-cyan/10 rounded-lg text-brand-cyan">
                  <Database className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-100">{activeVersion}</h2>
                  <p className="text-xs text-slate-400">
                    Group: <span className="text-brand-cyan uppercase font-mono">{activeGroup}</span> ·{' '}
                    {displayedFields.length} field definitions
                  </p>
                </div>
              </div>
              <Badge variant="success">{schemaDetail?.compatibility_class || 'ADDITIVE'}</Badge>
            </div>

            <div className="p-0 flex-1 overflow-y-auto custom-scrollbar">
              {detailLoading ? (
                <div className="flex items-center justify-center p-12 text-slate-500">
                  <Loader2 className="w-5 h-5 animate-spin mr-2" />
                  Loading field definitions...
                </div>
              ) : (
                <table className="w-full text-left text-sm text-slate-300">
                  <thead className="bg-slate-900 text-slate-400 border-b border-slate-800 sticky top-0">
                    <tr>
                      <th className="px-4 py-3 font-medium">Canonical Field</th>
                      <th className="px-4 py-3 font-medium">Type</th>
                      <th className="px-4 py-3 font-medium">Requirement</th>
                      <th className="px-4 py-3 font-medium">Description</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {displayedFields.map((field, idx) => (
                      <tr key={idx} className="hover:bg-slate-800/30 transition-colors">
                        <td className="px-4 py-3.5 font-mono text-xs text-brand-cyan">{field.name}</td>
                        <td className="px-4 py-3.5">
                          <Badge variant="secondary" className="font-mono text-[10px]">
                            {field.type}
                          </Badge>
                        </td>
                        <td className="px-4 py-3.5">
                          {field.required ? (
                            <span className="px-2 py-0.5 bg-brand-amber/10 text-brand-amber rounded text-xs font-medium">
                              Required
                            </span>
                          ) : (
                            <span className="px-2 py-0.5 bg-slate-800 text-slate-400 rounded text-xs">
                              Optional
                            </span>
                          )}
                        </td>
                        <td className="px-4 py-3.5 text-slate-400 text-xs">{field.description || '—'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
