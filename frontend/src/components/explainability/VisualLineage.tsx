import React from 'react';
import { ArrowDown } from 'lucide-react';
import { cn } from '../../utils/classnames';

interface LineageNodeProps {
  stage: string;
  value: React.ReactNode;
  isActive?: boolean;
}

function LineageNode({ stage, value, isActive = false }: LineageNodeProps) {
  return (
    <div className="flex flex-col items-center">
      <div className="text-[10px] font-bold tracking-widest text-slate-500 uppercase mb-2">
        {stage}
      </div>
      <div 
        className={cn(
          "px-4 py-2 rounded-md font-mono text-sm min-w-[120px] text-center transition-colors",
          isActive 
            ? "bg-brand-cyan/20 border border-brand-cyan/50 text-brand-cyan shadow-[0_0_15px_rgba(34,211,238,0.2)]" 
            : "bg-slate-800 border border-slate-700 text-slate-300"
        )}
      >
        {value}
      </div>
    </div>
  );
}

function LineageArrow() {
  return (
    <div className="flex justify-center my-2">
      <ArrowDown className="w-4 h-4 text-slate-600" />
    </div>
  );
}

interface VisualLineageProps {
  raw: string;
  extracted: string;
  type: string;
  mapping: string;
  transformation: string;
  normalized: string;
  provenance: string;
}

export function VisualLineage(props: VisualLineageProps) {
  return (
    <div className="w-full max-w-sm mx-auto p-6 bg-slate-900/50 rounded-xl border border-slate-800">
      <LineageNode stage="RAW" value={props.raw} />
      <LineageArrow />
      <LineageNode stage="EXTRACT" value={props.extracted} />
      <LineageArrow />
      <LineageNode stage="TYPE" value={props.type} />
      <LineageArrow />
      <LineageNode stage="MAPPING" value={props.mapping} />
      <LineageArrow />
      <LineageNode stage="TRANSFORMATION" value={props.transformation} />
      <LineageArrow />
      <LineageNode stage="NORMALIZED" value={props.normalized} isActive />
      <LineageArrow />
      <div className="flex flex-col items-center">
        <div className="text-[10px] font-bold tracking-widest text-slate-500 uppercase mb-2">
          PROVENANCE
        </div>
        <div className="text-xs text-slate-400 flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-brand-green" />
          {props.provenance}
        </div>
      </div>
    </div>
  );
}
