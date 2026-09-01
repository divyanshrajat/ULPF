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

function detectLogSourceMetadata(fileName: string, sampleText: string) {
  let detectedVendor = '';
  let detectedProduct = '';
  let detectedTransport = 'syslog';
  let detectedName = '';

  const text = sampleText.slice(0, 4096);

  // 1. CEF Format: CEF:0|Vendor|Product|Version|...
  const cefMatch = text.match(/CEF:\s*\d+\|([^\|]+)\|([^\|]+)/i);
  if (cefMatch) {
    detectedVendor = cefMatch[1].trim();
    detectedProduct = cefMatch[2].trim();
    detectedTransport = 'syslog';
    detectedName = `${detectedVendor}-${detectedProduct}`;
  }
  // 2. LEEF Format: LEEF:1.0|Vendor|Product|...
  else if (text.includes('LEEF:')) {
    const leefMatch = text.match(/LEEF:\s*[^\|]+\|([^\|]+)\|([^\|]+)/i);
    if (leefMatch) {
      detectedVendor = leefMatch[1].trim();
      detectedProduct = leefMatch[2].trim();
      detectedTransport = 'syslog';
      detectedName = `${detectedVendor}-${detectedProduct}`;
    }
  }
  // 3. Cisco ASA / IOS
  else if (/%ASA-|\bciscoasa\b|fw-tokyo|Cisco/i.test(text)) {
    detectedVendor = 'Cisco';
    detectedProduct = 'ASA';
    detectedTransport = 'syslog';
    detectedName = 'Cisco-ASA-Firewall';
  }
  // 4. Palo Alto Networks
  else if (/PAN-OS|TRAFFIC,\s*drop|TRAFFIC,\s*allow/i.test(text)) {
    detectedVendor = 'Palo Alto';
    detectedProduct = 'PAN-OS';
    detectedTransport = 'syslog';
    detectedName = 'PaloAlto-NGFW';
  }
  // 5. Windows Event Log / XML / EVTX
  else if (/<Provider Name="Microsoft-Windows-|EventID|EventData/i.test(text)) {
    detectedVendor = 'Microsoft';
    detectedProduct = 'Windows-Security';
    detectedTransport = 'syslog';
    detectedName = 'Windows-Security-Log';
  }
  // 6. Linux Syslog / Auth / Auditd
  else if (/sshd\[\d+\]|auditd|kernel:|systemd/i.test(text)) {
    detectedVendor = 'Linux';
    detectedProduct = 'Syslog-Auth';
    detectedTransport = 'syslog';
    detectedName = 'Linux-Host-Syslog';
  }
  // 7. AWS CloudWatch / VPC Flow
  else if (/vpc-[0-9a-f]+|aws:events|fl-\w+/i.test(text)) {
    detectedVendor = 'AWS';
    detectedProduct = 'VPC-Flow-Logs';
    detectedTransport = 'http';
    detectedName = 'AWS-VPC-Flow';
  }
  // 8. Web Server (Nginx / Apache)
  else if (/HTTP\/\d\.\d" \d{3}|"GET |"POST |"PUT /i.test(text)) {
    detectedVendor = 'Nginx';
    detectedProduct = 'Access-Log';
    detectedTransport = 'http';
    detectedName = 'Web-Server-Access';
  }
  // 9. JSON Log
  else if (text.trim().startsWith('{')) {
    try {
      const parsed = JSON.parse(text.split('\n')[0]);
      detectedVendor = parsed.vendor || parsed.host || 'Custom';
      detectedProduct = parsed.product || parsed.app || 'AppLogs';
      detectedTransport = 'http';
      detectedName = `${detectedVendor}-${detectedProduct}`;
    } catch {
      detectedVendor = 'Custom';
      detectedProduct = 'JSON-App';
      detectedTransport = 'http';
      detectedName = 'JSON-Service-Log';
    }
  }

  // Fallback to filename if not detected
  if (!detectedVendor) {
    const cleanBase = fileName.replace(/\.[^/.]+$/, '').replace(/[^a-zA-Z0-9_-]/g, '-');
    detectedVendor = 'Generic';
    detectedProduct = cleanBase || 'LogFile';
    detectedTransport = 'file_upload';
    detectedName = cleanBase ? `${cleanBase}-Source` : 'Log-File-Source';
  }

  return {
    vendor: detectedVendor,
    product: detectedProduct,
    transport: detectedTransport,
    sourceName: detectedName,
  };
}

export function Onboarding() {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [autoDetectedInfo, setAutoDetectedInfo] = useState<string | null>(null);
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

  const handleInspectAndAutoFill = async (selectedFile: File) => {
    try {
      setFile(selectedFile);
      setUploadError('');
      const sampleText = await selectedFile.slice(0, 8192).text();
      const meta = detectLogSourceMetadata(selectedFile.name, sampleText);
      setSourceName(meta.sourceName);
      setVendor(meta.vendor);
      setProduct(meta.product);
      setTransport(meta.transport);
      setAutoDetectedInfo(`✨ Auto-detected from "${selectedFile.name}": ${meta.vendor} ${meta.product} (${meta.transport.toUpperCase()})`);
    } catch (e: any) {
      console.warn('Failed to auto-inspect log file:', e);
    }
  };

  const applyPreset = (presetName: string, presetVendor: string, presetProduct: string, presetTransport: string) => {
    setSourceName(presetName);
    setVendor(presetVendor);
    setProduct(presetProduct);
    setTransport(presetTransport);
    setAutoDetectedInfo(`⚡ Applied preset: ${presetVendor} ${presetProduct}`);
  };

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

      refetchSources();

      // If file was already loaded in Step 1, auto-trigger analysis directly!
      if (file) {
        setStep(3);
        try {
          const data = await uploadOnboardingFile(session.id, file);
          setProposals(data.proposals || []);
          setTemplateId(data.template_id || '');
          setPattern(data.pattern || '');
          setDetectedFormat(data.format || 'unknown');
          setStep(7);
        } catch (uploadErr: any) {
          setUploadError(uploadErr?.message || 'Discovery failed during upload.');
          setStep(2);
        }
      } else {
        // Advance to sample upload step
        setStep(2);
      }
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
    setLoading(true);
    setUploadError('');
    try {
      const field_bindings: Record<string, string> = {};
      const confidence_summary: Record<string, number> = {};

      proposals.forEach((p) => {
        if (p.decision !== 'extension_only' && p.proposed_target) {
          field_bindings[p.source_field] = p.proposed_target;
        }
        confidence_summary[p.source_field] = p.confidence;
      });

      // Find if a review item exists for this source & template
      if (createdSourceId) {
        try {
          const reviews = await fetchReviews({ source_id: createdSourceId, status: 'PENDING' });
          const matchingReview = (reviews.items ?? []).find(
            (r: any) => r.template_id === templateId || r.source_id === createdSourceId
          );

          if (matchingReview) {
            await approveReview(matchingReview.review_id, field_bindings);
          }
        } catch (revErr) {
          console.warn('Review approval note:', revErr);
        }
      }

      // Trigger file processing for the session
      if (sessionId) {
        try {
          const pr = await processOnboardingSession(sessionId);
          setProcessResult(pr);
        } catch (pe) {
          console.warn('Processing session triggered with note:', pe);
        }
      }

      setStep(10); // READY
      if (createdSourceId) {
        setCurrentSource({
          id: createdSourceId,
          name: sourceName,
          vendor: vendor,
          product: product,
        });
      }
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
        <Card className="bg-slate-900 border-slate-800 max-w-2xl mx-auto shadow-xl">
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-brand-cyan/10 text-brand-cyan flex items-center justify-center">
                  <Server className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-100">Source Identity & Log Setup</h2>
                  <p className="text-xs text-slate-400">Configure manually or auto-detect instantly from a log file.</p>
                </div>
              </div>
              {file && (
                <Button
                  size="sm"
                  onClick={handleCreateSourceAndSession}
                  disabled={!sourceName.trim() || loading}
                  className="bg-white text-slate-950 hover:bg-slate-100 font-bold shadow-md shadow-white/10"
                >
                  {loading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Zap className="w-4 h-4 mr-1" />}
                  Proceed with File <ArrowRight className="ml-1 w-3.5 h-3.5" />
                </Button>
              )}
            </div>

            {/* QUICK PRESET CHIPS */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-300">⚡ Quick Presets</span>
              <div className="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  onClick={() => applyPreset('Cisco-ASA-Firewall', 'Cisco', 'ASA', 'syslog')}
                  className="text-xs px-3 py-1.5 rounded-md bg-white hover:bg-slate-100 text-slate-950 border border-slate-200 font-semibold shadow-sm transition-all"
                >
                  Cisco ASA
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('PaloAlto-NGFW', 'Palo Alto', 'PAN-OS', 'syslog')}
                  className="text-xs px-3 py-1.5 rounded-md bg-white hover:bg-slate-100 text-slate-950 border border-slate-200 font-semibold shadow-sm transition-all"
                >
                  Palo Alto NGFW
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('Windows-Security-Log', 'Microsoft', 'Windows-Security', 'syslog')}
                  className="text-xs px-3 py-1.5 rounded-md bg-white hover:bg-slate-100 text-slate-950 border border-slate-200 font-semibold shadow-sm transition-all"
                >
                  Windows Security
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('Linux-Host-Syslog', 'Linux', 'Syslog-Auth', 'syslog')}
                  className="text-xs px-3 py-1.5 rounded-md bg-white hover:bg-slate-100 text-slate-950 border border-slate-200 font-semibold shadow-sm transition-all"
                >
                  Linux Syslog
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('AWS-VPC-Flow', 'AWS', 'VPC-Flow-Logs', 'http')}
                  className="text-xs px-3 py-1.5 rounded-md bg-white hover:bg-slate-100 text-slate-950 border border-slate-200 font-semibold shadow-sm transition-all"
                >
                  AWS VPC Flow
                </button>
                <button
                  type="button"
                  onClick={() => applyPreset('Web-Server-Access', 'Nginx', 'Access-Log', 'http')}
                  className="text-xs px-3 py-1.5 rounded-md bg-white hover:bg-slate-100 text-slate-950 border border-slate-200 font-semibold shadow-sm transition-all"
                >
                  Nginx Web
                </button>
              </div>
            </div>

            {/* AUTO-DETECT DROPZONE */}
            <div
              onDragOver={(e) => {
                e.preventDefault();
                setIsDragOver(true);
              }}
              onDragLeave={(e) => {
                e.preventDefault();
                setIsDragOver(false);
              }}
              onDrop={(e) => {
                e.preventDefault();
                setIsDragOver(false);
                if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                  handleInspectAndAutoFill(e.dataTransfer.files[0]);
                }
              }}
              className={cn(
                'border border-dashed rounded-lg p-3 text-center transition-all',
                isDragOver ? 'border-brand-cyan bg-brand-cyan/10' : 'border-slate-700 bg-slate-950/60'
              )}
            >
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2.5 text-left">
                  <div className="w-7 h-7 rounded bg-slate-800 flex items-center justify-center text-slate-400 shrink-0">
                    <UploadCloud className="w-3.5 h-3.5" />
                  </div>
                  <div>
                    <div className="text-xs font-medium text-slate-200">
                      {file ? `File loaded: ${file.name}` : 'Drop log sample here to auto-fill fields'}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      Auto-detects Vendor, Product & Protocol from log headers
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <label className="cursor-pointer">
                    <span className="px-3 py-1.5 bg-white hover:bg-slate-100 border border-slate-300 rounded-md text-xs font-bold text-slate-950 shadow-sm transition-all inline-block">
                      {file ? 'Change File' : 'Browse File'}
                    </span>
                    <input
                      type="file"
                      className="hidden"
                      onChange={(e) => {
                        if (e.target.files && e.target.files.length > 0) {
                          handleInspectAndAutoFill(e.target.files[0]);
                        }
                      }}
                    />
                  </label>
                  {file && (
                    <button
                      type="button"
                      onClick={() => {
                        setFile(null);
                        setAutoDetectedInfo(null);
                      }}
                      className="text-xs text-slate-300 hover:text-white underline font-medium"
                    >
                      Clear
                    </button>
                  )}
                </div>
              </div>
            </div>

            {autoDetectedInfo && (
              <div className="p-2.5 bg-brand-cyan/10 border border-brand-cyan/30 rounded-md text-brand-cyan text-xs flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 shrink-0" />
                <span>{autoDetectedInfo}</span>
              </div>
            )}

            {/* READY BANNER WHEN FILE IS ATTACHED */}
            {file && (
              <div className="p-3 bg-gradient-to-r from-brand-cyan/15 via-brand-purple/15 to-slate-900 border border-brand-cyan/30 rounded-lg flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-brand-green shrink-0" />
                  <div>
                    <div className="text-xs font-semibold text-slate-100">Ready to Process: {file.name}</div>
                    <div className="text-[11px] text-slate-400">Click button to create source and run discovery</div>
                  </div>
                </div>
                <Button
                  onClick={handleCreateSourceAndSession}
                  disabled={!sourceName.trim() || loading}
                  className="bg-white text-slate-950 font-bold hover:bg-slate-100 text-xs px-3.5 py-1.5 h-auto shadow-md"
                >
                  {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Zap className="w-3.5 h-3.5 mr-1" />}
                  Start Processing Now <ArrowRight className="ml-1 w-3.5 h-3.5" />
                </Button>
              </div>
            )}

            <div className="space-y-3 pt-1">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Source Name</label>
                <input
                  type="text"
                  value={sourceName}
                  onChange={(e) => setSourceName(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-md p-2 text-sm text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan transition-all outline-none"
                  placeholder="e.g. Core-Firewall-Tokyo"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Vendor</label>
                  <input
                    type="text"
                    value={vendor}
                    onChange={(e) => setVendor(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-md p-2 text-sm text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan outline-none"
                    placeholder="e.g. Cisco, Palo Alto, Linux"
                  />
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Product</label>
                  <input
                    type="text"
                    value={product}
                    onChange={(e) => setProduct(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-md p-2 text-sm text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan outline-none"
                    placeholder="e.g. ASA, PAN-OS, Syslog"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Transport Protocol</label>
                <select
                  value={transport}
                  onChange={(e) => setTransport(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-md p-2 text-sm text-slate-100 focus:border-brand-cyan focus:ring-1 focus:ring-brand-cyan outline-none"
                >
                  <option value="syslog">Syslog (RFC 3164 / RFC 5424)</option>
                  <option value="http">HTTP POST / API</option>
                  <option value="file_upload">Direct File Upload</option>
                  <option value="kafka">Kafka Consumer</option>
                </select>
              </div>

              <div className="p-2.5 bg-slate-800/50 rounded-md border border-slate-800 flex items-center justify-between text-xs">
                <span className="text-slate-400">Predicted Source ID:</span>
                <span className="font-mono text-brand-cyan bg-brand-cyan/10 px-2 py-0.5 rounded">
                  SRC-{(vendor || sourceName).replace(/[^a-zA-Z0-9]/g, '').toUpperCase().slice(0, 5) || 'UNK'}-001
                </span>
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-slate-800/60">
              <Button
                onClick={handleCreateSourceAndSession}
                disabled={!sourceName.trim() || loading}
                className="w-full sm:w-auto bg-white text-slate-950 font-bold hover:bg-slate-100 shadow-md"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {file ? (
                  <>⚡ Create Source & Start Discovery <ArrowRight className="ml-2 w-4 h-4" /></>
                ) : (
                  <>Create Source & Continue <ArrowRight className="ml-2 w-4 h-4" /></>
                )}
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
                    <span className="px-4 py-2 bg-white hover:bg-slate-100 border border-slate-300 rounded-md text-sm font-bold text-slate-950 shadow-sm transition-all">
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
              <Button onClick={handleAnalyze} disabled={!file || loading} className="bg-white text-slate-950 font-bold hover:bg-slate-100 shadow-md">
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
