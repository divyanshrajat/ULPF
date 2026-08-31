import { useState } from 'react';
import type { DragEvent } from 'react';
import {
  createSource,
  createOnboardingSession,
  uploadOnboardingFile,
  approveReview,
  processOnboardingSession,
  fetchReviews,
} from '../services/api';
import { Card, CardContent } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Badge } from '../components/ui/Badge';
import {
  UploadCloud, CheckCircle2, Server, ArrowRight, Zap, Network,
  Loader2, AlertTriangle, ShieldCheck,
} from 'lucide-react';
import { useSourceContext } from '../contexts/SourceContext';
import { useSources } from '../hooks/useSources';
import { cn } from '../utils/classnames';

export function Onboarding() {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState('');
  const [loading, setLoading] = useState(false);
  const [sourceName, setSourceName] = useState('Firewall-X');
  const [vendor, setVendor] = useState('Cisco');
  const [product, setProduct] = useState('ASA');
  const [transport, setTransport] = useState('syslog');

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [createdSourceId, setCreatedSourceId] = useState<string | null>(null);
  const [proposals, setProposals] = useState<any[]>([]);
  const [templateId, setTemplateId] = useState('');
  const [pattern, setPattern] = useState('');
  const [detectedFormat, setDetectedFormat] = useState('');
  const [isDragOver, setIsDragOver] = useState(false);
  const [processResult, setProcessResult] = useState<any | null>(null);

  const { setCurrentSource } = useSourceContext();
  const { refetch: refetchSources } = useSources();

  const handleCreateSourceAndSession = async () => {
    setUploadError('');
    setLoading(true);
    try {
      // 1. Create Source
      const src = await createSource({
        name: sourceName.trim(),
        vendor: vendor.trim(),
        product: product.trim(),
        transport: transport.trim(),
      });
      const srcId = src.source_id || src.id;
      setCreatedSourceId(srcId);

      // 2. Create Onboarding Session
      const session = await createOnboardingSession(srcId);
      setSessionId(session.id);

      // Advance to sample upload step
      setStep(2);
      refetchSources();
    } catch (e: any) {
      setUploadError(e?.message || 'Failed to create source identity');
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async () => {
    if (!file) {
      setUploadError('Please select a file to upload.');
      return;
    }
    if (!sessionId) {
      setUploadError('Session not initialized.');
      return;
    }

    setUploadError('');
    setLoading(true);

    // Transition visually through stage indicators
    setStep(3); // DETECT
    try {
      const data = await uploadOnboardingFile(sessionId, file);
      setProposals(data.proposals || []);
      setTemplateId(data.template_id || '');
      setPattern(data.pattern || '');
      setDetectedFormat(data.format || 'unknown');

      // If review is required, go to step 7 (Review Proposals)
      // If already auto-accepted / fast path available, can proceed directly
      setStep(7);
    } catch (e: any) {
      setUploadError(e?.message || 'Analysis failed during discovery.');
      setStep(2);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!createdSourceId || !templateId) return;
    setLoading(true);
    setUploadError('');
    try {
      const field_bindings: Record<string, string> = {};
      const confidence_summary: Record<string, number> = {};

      proposals.forEach((p) => {
        if (p.decision !== 'extension_only') {
          field_bindings[p.source_field] = p.proposed_target;
        }
        confidence_summary[p.source_field] = p.confidence;
      });

      // Find if a review item exists for this source & template
      const reviews = await fetchReviews({ source_id: createdSourceId, status: 'PENDING' });
      const matchingReview = (reviews.items ?? []).find(
        (r: any) => r.template_id === templateId || r.source_id === createdSourceId
      );

      if (matchingReview) {
        await approveReview(matchingReview.review_id, field_bindings);
      }

      // Trigger file processing for the session
      if (sessionId) {
        try {
          const pr = await processOnboardingSession(sessionId);
          setProcessResult(pr);
        } catch (pe) {
          console.warn('Processing session triggered with warning:', pe);
        }
      }

      setStep(10); // READY
      setCurrentSource({
        id: createdSourceId,
        name: sourceName,
        vendor: vendor,
        product: product,
      });
      refetchSources();
    } catch (e: any) {
      setUploadError(e?.message || 'Failed to approve mapping');
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      setFile(e.dataTransfer.files[0]);
      setUploadError('');
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-12">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">ONBOARD NEW SOURCE</h1>
          <p className="text-slate-400">
            Source: {sourceName || 'Unnamed'} {createdSourceId ? `(${createdSourceId})` : ''}
          </p>
        </div>
        <div className="w-1/2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-500 mb-2 px-1">
            <span className={step >= 1 ? 'text-brand-cyan' : ''}>01 IDENTITY</span>
            <span className={step >= 2 ? 'text-brand-cyan' : ''}>02 UPLOAD</span>
            <span className={step >= 3 ? 'text-brand-purple' : ''}>03 DISCOVERY</span>
            <span className={step >= 7 ? 'text-brand-purple' : ''}>07 REVIEW</span>
            <span className={step === 10 ? 'text-brand-green' : ''}>10 READY</span>
          </div>
          <div className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
            <div
              className="h-full bg-brand-cyan transition-all duration-500"
              style={{ width: `${(step / 10) * 100}%` }}
            />
          </div>
        </div>
      </div>

      {uploadError && (
        <div className="p-4 bg-brand-red/10 border border-brand-red/30 rounded-xl text-brand-red text-sm flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 shrink-0" />
          {uploadError}
        </div>
      )}

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
                  onChange={(e) => setSourceName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-md p-2.5 text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan transition-all outline-none"
                  placeholder="e.g. Core-Firewall-Tokyo"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Vendor</label>
                  <input
                    type="text"
                    value={vendor}
                    onChange={(e) => setVendor(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-md p-2.5 text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan outline-none"
                    placeholder="e.g. Cisco, Palo Alto, Linux"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1">Product</label>
                  <input
                    type="text"
                    value={product}
                    onChange={(e) => setProduct(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-md p-2.5 text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan outline-none"
                    placeholder="e.g. ASA, PAN-OS, Syslog"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Transport Protocol</label>
                <select
                  value={transport}
                  onChange={(e) => setTransport(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-md p-2.5 text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan outline-none"
                >
                  <option value="syslog">Syslog (RFC 3164 / RFC 5424)</option>
                  <option value="http">HTTP POST / API</option>
                  <option value="file_upload">Direct File Upload</option>
                  <option value="kafka">Kafka Consumer</option>
                </select>
              </div>

              <div className="p-3 bg-slate-800/50 rounded-md border border-slate-800 flex items-center justify-between">
                <span className="text-sm text-slate-400">Predicted Source ID:</span>
                <span className="font-mono text-sm text-brand-cyan bg-brand-cyan/10 px-2 py-0.5 rounded">
                  SRC-{(vendor || sourceName).replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, 5) || 'UNK'}-001
                </span>
              </div>
            </div>

            <div className="flex justify-end pt-4">
              <Button onClick={handleCreateSourceAndSession} disabled={!sourceName.trim() || loading}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                Create & Continue <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
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
                <p className="text-sm text-slate-400">
                  Upload a sample log file. Raw bytes are preserved in the Vault before transformation.
                </p>
              </div>
            </div>

            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setIsDragOver(false);
              }}
              onDrop={handleDrop}
              className={cn(
                'border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200',
                isDragOver ? 'border-brand-cyan bg-brand-cyan/5 scale-[1.02]' : 'border-slate-700 bg-slate-950',
                file ? 'py-8' : ''
              )}
            >
              {!file ? (
                <div className="space-y-3 flex flex-col items-center">
                  <UploadCloud className="w-10 h-10 text-slate-500 mb-2" />
                  <p className="text-slate-300 font-medium">Drop your log file here</p>
                  <p className="text-slate-500 text-xs">Supports raw syslog, JSON, CEF, KV, or delimited logs up to 50MB</p>
                  <label className="cursor-pointer mt-4">
                    <span className="px-4 py-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-md text-sm text-slate-200 transition-colors">
                      Choose File
                    </span>
                    <input
                      type="file"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files?.length) {
                          setFile(e.target.files[0]);
                          setUploadError('');
                        }
                      }}
                    />
                  </label>
                </div>
              ) : (
                <div className="flex flex-col items-center space-y-3">
                  <CheckCircle2 className="w-10 h-10 text-brand-green mb-2" />
                  <div className="text-slate-100 font-medium text-lg">{file.name}</div>
                  <div className="text-slate-400 text-sm">Size: {(file.size / 1024).toFixed(1)} KB</div>
                  <div className="flex space-x-3 mt-4">
                    <Button variant="outline" size="sm" onClick={() => setFile(null)}>
                      Remove
                    </Button>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-between pt-4">
              <Button variant="ghost" onClick={() => setStep(1)}>
                Back
              </Button>
              <Button onClick={handleAnalyze} disabled={!file || loading}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Zap className="mr-2 w-4 h-4" />}
                Analyze Sample
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {step >= 3 && step < 7 && (
        <div className="max-w-2xl mx-auto space-y-6">
          <Card className="bg-slate-900 border-slate-800 p-8 text-center space-y-6">
            <h2 className="text-xl font-bold text-slate-100 animate-pulse">
              ANALYZING & DISCOVERING PATTERNS...
            </h2>
            <p className="text-sm text-slate-400">
              Preserving in Raw Vault → Classifying Format → Drain3 Template Mining → Type Inference → Semantic Mapping
            </p>
            <div className="flex items-center justify-center gap-4 text-slate-500 py-4">
              <Loader2 className="w-8 h-8 text-brand-cyan animate-spin" />
            </div>
          </Card>
        </div>
      )}

      {step === 7 && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="bg-brand-amber/10 border border-brand-amber/30 rounded-lg p-4 flex gap-4">
            <Network className="w-6 h-6 text-brand-amber shrink-0" />
            <div>
              <h3 className="text-brand-amber font-bold mb-1">
                FORMAT: {detectedFormat.toUpperCase()} → DISCOVERY COMPLETE
              </h3>
              <p className="text-slate-300 text-sm">
                ULPF mined a template from your log sample and generated AI field mapping proposals. Review and approve below.
              </p>
            </div>
          </div>

          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="p-6">
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">Discovered Template</h4>
              <div className="p-4 bg-slate-950 rounded-md border border-slate-800 overflow-x-auto">
                <code className="text-brand-cyan font-mono text-sm whitespace-pre">{pattern || '—'}</code>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-900 border-slate-800">
            <CardContent className="p-6">
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-3">
                Extracted Fields & AI Mappings ({proposals.length} fields)
              </h4>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-800 text-slate-400">
                      <th className="pb-3 font-medium">SOURCE FIELD</th>
                      <th className="pb-3 font-medium">INFERRED TYPE</th>
                      <th className="pb-3 font-medium">PROPOSED TARGET</th>
                      <th className="pb-3 font-medium">CONFIDENCE</th>
                      <th className="pb-3 font-medium">DECISION</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {proposals.map((p, i) => (
                      <tr key={i} className="hover:bg-slate-800/30">
                        <td className="py-3 font-mono text-slate-300">{p.source_field}</td>
                        <td className="py-3">
                          <Badge variant="secondary" className="font-mono text-xs">
                            {p.inferred_type || 'text'}
                          </Badge>
                        </td>
                        <td className="py-3 font-mono text-brand-purple">{p.proposed_target}</td>
                        <td className="py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                              <div className="h-full bg-brand-cyan" style={{ width: `${(p.confidence || 0) * 100}%` }} />
                            </div>
                            <span className="text-slate-400 text-xs">{((p.confidence || 0) * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                        <td className="py-3">
                          <Badge variant={p.confidence >= 0.8 ? 'success' : 'warning'}>
                            {p.decision || (p.confidence >= 0.8 ? 'auto_accepted' : 'review')}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex justify-end pt-6 border-t border-slate-800 mt-6 gap-3">
                <Button variant="outline" onClick={() => setStep(2)}>
                  Upload Different Sample
                </Button>
                <Button onClick={handleApprove} disabled={loading}>
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <ShieldCheck className="w-4 h-4 mr-2" />}
                  Approve & Activate Mapping
                </Button>
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
              <h2 className="text-2xl font-bold text-slate-100 mb-2">SOURCE ONBOARDED & MAPPING ACTIVE</h2>
              <p className="text-slate-400">
                ULPF is now actively processing events from this source on the Fast Path.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto text-left">
              <div className="bg-slate-950 p-3 rounded border border-slate-800">
                <div className="text-xs text-slate-500 mb-1">Source ID</div>
                <div className="font-mono text-sm text-slate-200 truncate">{createdSourceId}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded border border-slate-800">
                <div className="text-xs text-slate-500 mb-1">Status</div>
                <div className="font-mono text-sm text-brand-green">ACTIVE (Fast Path)</div>
              </div>
            </div>
            {processResult?.count && (
              <p className="text-xs text-slate-400">
                Queued {processResult.count} sample events into the pipeline.
              </p>
            )}
            <div className="pt-4 flex gap-4 justify-center">
              <Button variant="outline" onClick={() => (window.location.href = '/trace')}>
                View Traces
              </Button>
              <Button onClick={() => (window.location.href = '/events')}>
                Explore Normalized Events
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
