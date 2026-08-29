import { useState } from 'react';
import type { DragEvent } from 'react';
import { API_BASE } from '../services/api';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import { UploadCloud, CheckCircle2, Server, ArrowRight, Zap, Network } from 'lucide-react';
import { useSourceContext } from '../contexts/SourceContext';
import { cn } from '../utils/classnames';

export function Onboarding() {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [sourceName, setSourceName] = useState("Firewall-X");
  const [proposals, setProposals] = useState<any[]>([]);
  const [templateId, setTemplateId] = useState("");
  const [pattern, setPattern] = useState("");
  const [isDragOver, setIsDragOver] = useState(false);
  
  const { setCurrentSource } = useSourceContext();

  const handleAnalyze = async () => {
    setUploadError("");
    setUploading(true);
    
    // Simulate multi-step processing visually
    setStep(3); // Detect
    await new Promise(r => setTimeout(r, 800));
    setStep(4); // Discover
    await new Promise(r => setTimeout(r, 800));
    setStep(5); // Map
    
    try {
      const sourceId = `SRC-${sourceName.replace(/[^a-zA-Z0-9]/g, '').toUpperCase()}-001`;
      let res;
      if (!file) {
        setUploadError("Please select a file to upload.");
        setUploading(false);
        setStep(2);
        return;
      }
      const formData = new FormData();
      formData.append("source_id", sourceId);
      formData.append("file", file);
      
      res = await fetch(`${API_BASE}/onboarding/upload`, {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (res.ok) {
        setProposals(data.proposals);
        setTemplateId(data.template_id);
        setPattern(data.pattern);
        setStep(7); // Review mapping
      } else {
        setUploadError(data.detail || "Analysis failed");
        setStep(2);
      }
    } catch (e) {
      console.error(e);
      setUploadError("Network error occurred.");
      setStep(2);
    } finally {
      setUploading(false);
    }
  };

  const handleApprove = async () => {
    try {
      const sourceId = `SRC-${sourceName.replace(/[^a-zA-Z0-9]/g, '').toUpperCase()}-001`;
      const field_bindings: Record<string, string> = {};
      const confidence_summary: Record<string, number> = {};
      
      proposals.forEach(p => {
        field_bindings[p.source_field] = p.proposed_target;
        confidence_summary[p.source_field] = p.confidence;
      });
      
      const res = await fetch(`${API_BASE}/mappings/${sourceId}/${templateId}/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-ULPF-User': 'admin', 'X-ULPF-Role': 'admin' },
        body: JSON.stringify({ field_bindings, confidence_summary })
      });
      if (res.ok) {
        setStep(10); // Ready
        setCurrentSource({ id: sourceId, name: sourceName, vendor: "Custom", product: sourceName });
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setUploadError("");
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">ONBOARD NEW SOURCE</h1>
          <p className="text-slate-400">Source: {sourceName || 'Unnamed'}</p>
        </div>
        <div className="w-1/2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-500 mb-2 px-1">
            <span>01 SOURCE</span>
            <span className={step >= 3 ? "text-brand-cyan" : ""}>03 DETECT</span>
            <span className={step >= 7 ? "text-brand-purple" : ""}>07 MAP</span>
            <span className={step === 10 ? "text-brand-green" : ""}>10 READY</span>
          </div>
          <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-brand-cyan transition-all duration-500" style={{ width: `${(step / 10) * 100}%` }} />
          </div>
        </div>
      </div>

      {step === 1 && (
        <Card className="bg-slate-900 border-slate-800 max-w-2xl mx-auto">
          <CardContent className="p-8 space-y-6">
            <div className="flex items-center gap-4 border-b border-slate-800 pb-4">
              <div className="w-12 h-12 rounded-lg bg-brand-cyan/10 text-brand-cyan flex items-center justify-center">
                <Server className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-100">Source Identity</h2>
                <p className="text-sm text-slate-400">Define the system generating these logs.</p>
              </div>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Source Name</label>
                <input 
                  type="text" 
                  value={sourceName} 
                  onChange={e => setSourceName(e.target.value)} 
                  className="w-full bg-slate-950 border border-slate-700 rounded-md p-2.5 text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan transition-all outline-none"
                />
              </div>
              <div className="p-3 bg-slate-800/50 rounded-md border border-slate-800 flex items-center justify-between">
                <span className="text-sm text-slate-400">Generated Source ID:</span>
                <span className="font-mono text-sm text-brand-cyan bg-brand-cyan/10 px-2 py-0.5 rounded">
                  SRC-{sourceName.replace(/[^a-zA-Z0-9]/g, '').toUpperCase() || 'XXX'}-001
                </span>
              </div>
            </div>
            <div className="flex justify-end pt-4">
              <Button onClick={() => setStep(2)}>Continue <ArrowRight className="ml-2 w-4 h-4" /></Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step === 2 && (
        <Card className="bg-slate-900 border-slate-800 max-w-2xl mx-auto">
          <CardContent className="p-8 space-y-6">
             <div className="flex items-center gap-4 border-b border-slate-800 pb-4">
              <div className="w-12 h-12 rounded-lg bg-brand-cyan/10 text-brand-cyan flex items-center justify-center">
                <UploadCloud className="w-6 h-6" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-slate-100">Sample Ingestion</h2>
                <p className="text-sm text-slate-400">Provide an unknown log file to discover its structure.</p>
              </div>
            </div>

            <div 
              onDragOver={e => { e.preventDefault(); setIsDragOver(true); }}
              onDragLeave={e => { e.preventDefault(); setIsDragOver(false); }}
              onDrop={handleDrop}
              className={cn(
                "border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200",
                isDragOver ? 'border-brand-cyan bg-brand-cyan/5 scale-[1.02]' : 'border-slate-700 bg-slate-950',
                file ? 'py-8' : ''
              )}
            >
              {!file ? (
                <div className="space-y-3 flex flex-col items-center">
                  <UploadCloud className="w-10 h-10 text-slate-500 mb-2" />
                  <p className="text-slate-300 font-medium">Drop your log file here</p>
                  <label className="cursor-pointer mt-4">
                    <span className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-md text-sm text-slate-200 transition-colors">
                      Choose File
                    </span>
                    <input type="file" className="hidden" onChange={e => {
                      if (e.target.files?.length) {
                        setFile(e.target.files[0]);
                        setUploadError("");
                      }
                    }} />
                  </label>
                </div>
              ) : (
                <div className="flex flex-col items-center space-y-3">
                  <CheckCircle2 className="w-10 h-10 text-brand-green mb-2" />
                  <div className="text-slate-100 font-medium text-lg">{file.name}</div>
                  <div className="text-slate-400 text-sm">Size: {(file.size / 1024).toFixed(1)} KB</div>
                  <div className="flex space-x-3 mt-4">
                    <Button variant="outline" size="sm" onClick={() => setFile(null)}>Remove</Button>
                  </div>
                </div>
              )}
            </div>
            
            {uploadError && <p className="text-brand-red text-sm font-medium">{uploadError}</p>}

            <div className="flex justify-between pt-4">
              <Button variant="ghost" onClick={() => setStep(1)}>Back</Button>
              <Button onClick={handleAnalyze} disabled={!file || uploading}>
                {uploading ? 'Analyzing...' : 'Analyze Sample'} <Zap className="ml-2 w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {(step >= 3 && step < 7) && (
        <div className="max-w-2xl mx-auto space-y-6">
          <Card className="bg-slate-900 border-slate-800 p-8 text-center space-y-6">
            <h2 className="text-xl font-bold text-slate-100 animate-pulse">
              {step === 3 && "DETECTING FORMAT..."}
              {step === 4 && "ADAPTIVE DISCOVERY RUNNING..."}
              {step === 5 && "EXTRACTING FIELDS..."}
              {step === 6 && "INFERRING TYPES..."}
            </h2>
            <div className="h-16 flex items-center justify-center gap-4 text-slate-500">
               <div className={cn("w-3 h-3 rounded-full", step >= 3 ? "bg-brand-cyan animate-ping" : "bg-slate-800")} />
               <div className={cn("w-3 h-3 rounded-full", step >= 4 ? "bg-brand-cyan animate-ping delay-75" : "bg-slate-800")} />
               <div className={cn("w-3 h-3 rounded-full", step >= 5 ? "bg-brand-cyan animate-ping delay-150" : "bg-slate-800")} />
            </div>
          </Card>
        </div>
      )}

      {step === 7 && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="bg-brand-amber/10 border border-brand-amber/30 rounded-lg p-4 flex gap-4">
            <Network className="w-6 h-6 text-brand-amber shrink-0" />
            <div>
              <h3 className="text-brand-amber font-bold mb-1">FORMAT UNKNOWN → SWITCHED TO ADAPTIVE DISCOVERY</h3>
              <p className="text-slate-300 text-sm">No registered deterministic parser matched this event. ULPF mined a new template and extracted candidate fields.</p>
            </div>
          </div>
          
          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="p-6">
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Discovered Template</h4>
              <div className="p-4 bg-slate-950 rounded-md border border-slate-800 overflow-x-auto">
                <code className="text-brand-cyan font-mono text-sm whitespace-pre">{pattern}</code>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="p-6">
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Extracted Fields & AI Mappings</h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="pb-3 font-medium">SOURCE FIELD</th>
                      <th className="pb-3 font-medium">PROPOSED TARGET</th>
                      <th className="pb-3 font-medium">CONFIDENCE</th>
                      <th className="pb-3 font-medium">STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {proposals.map((p, i) => (
                      <tr key={i} className="border-b border-slate-800/50">
                        <td className="py-3 font-mono text-slate-300">{p.source_field}</td>
                        <td className="py-3 font-mono text-brand-purple">{p.proposed_target}</td>
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                              <div className="h-full bg-brand-cyan" style={{ width: `${p.confidence * 100}%` }} />
                            </div>
                            <span className="text-slate-400 text-xs">{(p.confidence * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="py-3">
                          {p.confidence > 0.8 ? (
                            <Badge variant="success">Auto Accept</Badge>
                          ) : (
                            <Badge variant="warning">Review Required</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex justify-end pt-6 border-t border-slate-800 mt-6 gap-3">
                 <Button variant="outline" onClick={() => setStep(1)}>Cancel</Button>
                 <Button onClick={handleApprove}>Approve & Create Mapping</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {step === 10 && (
        <Card className="bg-slate-900 border-brand-green/30 max-w-2xl mx-auto shadow-[0_0_30px_rgba(34,197,94,0.1)]">
          <CardContent className="p-10 text-center space-y-6">
            <div className="w-20 h-20 mx-auto rounded-full bg-brand-green/10 flex items-center justify-center">
              <CheckCircle2 className="w-10 h-10 text-brand-green" />
            </div>
            <div>
              <h2 className="text-2xl font-bold text-slate-100 mb-2">MAPPING APPROVED</h2>
              <p className="text-slate-400">ULPF is now ready to process events from this source on the Fast Path.</p>
            </div>
            <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto text-left">
               <div className="bg-slate-950 p-3 rounded border border-slate-800">
                 <div className="text-xs text-slate-500 mb-1">Source</div>
                 <div className="font-mono text-sm text-slate-200">{sourceName}</div>
               </div>
               <div className="bg-slate-950 p-3 rounded border border-slate-800">
                 <div className="text-xs text-slate-500 mb-1">Mapping Version</div>
                 <div className="font-mono text-sm text-brand-green">v1 (Active)</div>
               </div>
            </div>
            <div className="pt-4 flex gap-4 justify-center">
              <Button variant="outline">Process Event</Button>
              <Button>View Active Mappings</Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
