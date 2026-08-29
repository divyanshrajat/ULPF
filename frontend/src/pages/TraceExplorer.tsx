import { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/Card';
import { Badge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { Search, Activity, GitCommit, Clock, Hash, Lock, Globe } from 'lucide-react';
import { cn } from '../utils/classnames';
import { VisualLineage } from '../components/explainability/VisualLineage';

export function TraceExplorer() {
  const [searchQuery, setSearchQuery] = useState("");
  const activeTraceId = "trace-8f92a1-b4c";
  const [hoveredField, setHoveredField] = useState<string | null>(null);

  // Mock data for demonstration
  const rawLog = `<14>1 2026-08-29T10:15:22.123Z fw-tokyo-01 CEF:0|Security|Firewall|9.0|100|ACCEPT|1|src=192.168.1.100 dst=10.0.0.5 spt=51234 dpt=443 proto=TCP act=permit category=Web msg=Allowed HTTPS traffic`;
  
  const normalizedLog = {
    "@timestamp": "2026-08-29T10:15:22.123Z",
    "event.category": ["network"],
    "event.type": ["connection", "allowed"],
    "observer.hostname": "fw-tokyo-01",
    "observer.vendor": "Security",
    "observer.product": "Firewall",
    "source.ip": "192.168.1.100",
    "source.port": 51234,
    "destination.ip": "10.0.0.5",
    "destination.port": 443,
    "network.protocol": "TCP",
    "rule.name": "100",
    "rule.category": "Web",
    "message": "Allowed HTTPS traffic"
  };

  // Map normalized fields to their start/end indices in the raw string for highlighting
  const fieldMapping: Record<string, { start: number; end: number }> = {
    "@timestamp": { start: 7, end: 31 },
    "observer.hostname": { start: 32, end: 43 },
    "observer.vendor": { start: 50, end: 58 },
    "observer.product": { start: 59, end: 67 },
    "rule.name": { start: 72, end: 75 },
    "source.ip": { start: 88, end: 101 },
    "destination.ip": { start: 106, end: 114 },
    "source.port": { start: 119, end: 124 },
    "destination.port": { start: 129, end: 132 },
    "network.protocol": { start: 139, end: 142 },
    "rule.category": { start: 153, end: 156 },
    "message": { start: 161, end: 182 }
  };

  const renderRawLog = () => {
    if (!hoveredField || !fieldMapping[hoveredField]) {
      return <span>{rawLog}</span>;
    }
    
    const { start, end } = fieldMapping[hoveredField];
    const before = rawLog.substring(0, start);
    const highlight = rawLog.substring(start, end);
    const after = rawLog.substring(end);

    return (
      <>
        <span className="text-slate-500">{before}</span>
        <span className="bg-brand-cyan/20 text-brand-cyan border-b-2 border-brand-cyan relative">
          {highlight}
          <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-brand-cyan text-slate-900 text-[10px] font-bold px-2 py-0.5 rounded whitespace-nowrap">
            {hoveredField}
          </div>
        </span>
        <span className="text-slate-500">{after}</span>
      </>
    );
  };

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-6 max-w-7xl mx-auto">
      {/* TRACE SEARCH & LIST */}
      <div className="w-80 flex flex-col gap-4 border-r border-slate-800 pr-6 shrink-0">
        <h2 className="text-lg font-bold text-slate-100 flex items-center gap-2">
          <GitCommit className="w-5 h-5 text-brand-purple" />
          Trace Explorer
        </h2>
        
        <div className="relative">
          <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input 
            type="text" 
            placeholder="Search by Trace ID or Hash..." 
            className="w-full bg-slate-900 border border-slate-700 rounded-md pl-9 p-2 text-sm text-slate-100 focus:border-brand-purple focus:ring-1 focus:ring-brand-purple outline-none"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>

        <div className="flex-1 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
          {[1,2,3,4,5].map((i) => (
            <div 
              key={i} 
              className={cn(
                "p-3 rounded-lg border cursor-pointer transition-colors",
                i === 1 ? "bg-brand-purple/5 border-brand-purple/30" : "bg-slate-900 border-slate-800 hover:border-slate-600"
              )}
            >
              <div className="flex justify-between items-start mb-1">
                <div className="text-xs font-mono text-brand-purple">trace-8f92a1-b4c</div>
                <div className="text-[10px] text-slate-500">10:15:22</div>
              </div>
              <div className="text-xs text-slate-300 truncate">fw-tokyo-01 (CEF:0)</div>
              <div className="mt-2 flex gap-1">
                <Badge variant="success" className="text-[9px] px-1 py-0">Mapped</Badge>
                <Badge variant="secondary" className="text-[9px] px-1 py-0">Verified</Badge>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* TRACE DETAILS WORKSPACE */}
      <div className="flex-1 flex flex-col gap-6 overflow-y-auto pr-2 custom-scrollbar">
        <div className="flex items-center justify-between bg-slate-900 p-4 rounded-xl border border-slate-800">
           <div className="flex items-center gap-4">
             <div className="w-10 h-10 rounded-full bg-brand-purple/10 flex items-center justify-center">
               <GitCommit className="w-5 h-5 text-brand-purple" />
             </div>
             <div>
               <h2 className="text-slate-100 font-mono font-bold">{activeTraceId}</h2>
               <p className="text-slate-400 text-sm">Processed 2 minutes ago via Deterministic Path</p>
             </div>
           </div>
           <div className="flex gap-2">
              <Button variant="outline"><Activity className="w-4 h-4 mr-2" /> View Metrics</Button>
              <Button><Hash className="w-4 h-4 mr-2" /> Copy Integrity Hash</Button>
           </div>
        </div>

        <div className="grid grid-cols-2 gap-6 h-[400px]">
          {/* RAW VIEW */}
          <Card className="bg-slate-900 border-slate-800 flex flex-col h-full">
            <CardHeader className="border-b border-slate-800 pb-3 flex flex-row items-center justify-between py-3">
              <CardTitle className="text-sm text-slate-300">RAW EVENT</CardTitle>
              <Badge variant="secondary">482 bytes</Badge>
            </CardHeader>
            <CardContent className="p-0 flex-1 overflow-auto bg-slate-950 font-mono text-sm leading-relaxed p-4 text-slate-300 break-all">
               {renderRawLog()}
            </CardContent>
          </Card>

          {/* NORMALIZED VIEW */}
          <Card className="bg-slate-900 border-slate-800 flex flex-col h-full">
            <CardHeader className="border-b border-slate-800 pb-3 flex flex-row items-center justify-between py-3">
              <CardTitle className="text-sm text-brand-cyan">NORMALIZED EVENT (ECS)</CardTitle>
              <Badge variant="success">Validated</Badge>
            </CardHeader>
            <CardContent className="p-0 flex-1 overflow-auto bg-slate-950 p-4">
               <div className="space-y-1">
                 {Object.entries(normalizedLog).map(([key, val]) => (
                   <div 
                     key={key} 
                     className="flex hover:bg-slate-800/50 rounded transition-colors px-2 py-1"
                     onMouseEnter={() => setHoveredField(key)}
                     onMouseLeave={() => setHoveredField(null)}
                   >
                     <div className="w-1/3 text-brand-cyan font-mono text-xs">{key}:</div>
                     <div className="w-2/3 text-slate-300 font-mono text-xs pl-2 truncate" title={JSON.stringify(val)}>
                       {typeof val === 'string' ? `"${val}"` : JSON.stringify(val)}
                     </div>
                   </div>
                 ))}
               </div>
            </CardContent>
          </Card>
        </div>

        {/* PROVENANCE AND EXPLAINABILITY */}
        <div className="grid grid-cols-3 gap-6">
          <Card className="bg-slate-900 border-slate-800 col-span-2">
            <CardHeader>
              <CardTitle className="text-sm text-slate-300">LINEAGE & PROVENANCE</CardTitle>
            </CardHeader>
            <CardContent>
               <div className="flex justify-center py-4">
                 <VisualLineage 
                   raw="fw-tokyo-01 Syslog TCP 482b"
                   extracted="CEF Decoder v1.2"
                   type="Deterministic"
                   mapping="CEF to ECS Security v2"
                   transformation="IP validation, Date normalization"
                   normalized="ECS v8.11 JSON"
                   provenance="sha256:8f92a1b4c3d..."
                 />
               </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800 col-span-1">
             <CardHeader>
               <CardTitle className="text-sm text-slate-300">INTEGRITY</CardTitle>
             </CardHeader>
             <CardContent className="space-y-4">
               <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-md border border-slate-800">
                 <Lock className="w-5 h-5 text-brand-green" />
                 <div>
                   <div className="text-xs text-slate-400">Cryptographic Seal</div>
                   <div className="text-sm text-brand-green font-medium">Valid</div>
                 </div>
               </div>
               
               <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-md border border-slate-800">
                 <Globe className="w-5 h-5 text-brand-cyan" />
                 <div>
                   <div className="text-xs text-slate-400">Schema Validation</div>
                   <div className="text-sm text-slate-200">ECS v8.11 Strict</div>
                 </div>
               </div>

               <div className="flex items-center gap-3 p-3 bg-slate-800/50 rounded-md border border-slate-800">
                 <Clock className="w-5 h-5 text-slate-400" />
                 <div>
                   <div className="text-xs text-slate-400">Processing Latency</div>
                   <div className="text-sm text-slate-200">14ms</div>
                 </div>
               </div>
             </CardContent>
          </Card>
        </div>

      </div>
    </div>
  );
}
