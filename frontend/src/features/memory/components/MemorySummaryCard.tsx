import React, { useState } from 'react';
import { Sparkles, Loader2, Award, AlertCircle, RefreshCw } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { useCompressMemories } from '../hooks/useMemory';

interface MemorySummaryCardProps {
  candidateId: string;
}

export const MemorySummaryCard: React.FC<MemorySummaryCardProps> = ({ candidateId }) => {
  const compressMutation = useCompressMemories();
  const [compressResult, setCompressResult] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleCompress = async () => {
    setErrorMsg(null);
    try {
      const res = await compressMutation.mutateAsync({ candidateId });
      setCompressResult(res);
    } catch (err: any) {
      setErrorMsg(err?.message || 'Failed to compress interview memories.');
    }
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">
            AI Memory Compression & Synthesis
          </h2>
        </div>

        <Button
          onClick={handleCompress}
          disabled={compressMutation.isPending}
          className="bg-indigo-600 hover:bg-indigo-500 text-white font-medium px-4 py-2 rounded-xl transition-all shadow-md shadow-indigo-600/20 flex items-center justify-center gap-2 text-xs"
        >
          {compressMutation.isPending ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              <span>Compressing Memories...</span>
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4" />
              <span>Synthesize & Compress Memories</span>
            </>
          )}
        </Button>
      </div>

      {errorMsg && (
        <div className="p-3 rounded-lg border border-rose-500/30 bg-rose-500/10 text-xs text-rose-400">
          {errorMsg}
        </div>
      )}

      {compressResult ? (
        <div className="p-4 rounded-xl border border-indigo-900/60 bg-indigo-950/30 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-indigo-300">
              Covering {compressResult.interview_count_covered} Interview Sessions
            </span>
            <span className="text-[11px] font-mono text-slate-400">
              Compressed Just Now
            </span>
          </div>

          <p className="text-xs text-slate-200 leading-relaxed font-mono">
            {compressResult.compressed_summary}
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-indigo-900/40">
            {compressResult.key_strengths && compressResult.key_strengths.length > 0 && (
              <div className="space-y-1">
                <span className="text-[11px] font-semibold text-emerald-400 flex items-center gap-1">
                  <Award className="w-3 h-3" /> Key Strengths Synthesized
                </span>
                <div className="flex flex-wrap gap-1">
                  {compressResult.key_strengths.map((str: string) => (
                    <span key={str} className="px-2 py-0.5 rounded text-[11px] bg-emerald-500/10 text-emerald-300 border border-emerald-500/20">
                      {str}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {compressResult.key_weaknesses && compressResult.key_weaknesses.length > 0 && (
              <div className="space-y-1">
                <span className="text-[11px] font-semibold text-amber-400 flex items-center gap-1">
                  <AlertCircle className="w-3 h-3" /> Focus Areas Synthesized
                </span>
                <div className="flex flex-wrap gap-1">
                  {compressResult.key_weaknesses.map((weak: string) => (
                    <span key={weak} className="px-2 py-0.5 rounded text-[11px] bg-amber-500/10 text-amber-300 border border-amber-500/20">
                      {weak}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <p className="text-xs text-slate-400 leading-relaxed">
          Trigger memory synthesis to compress longitudinal interview experiences into high-density profile summaries via LLM reasoning.
        </p>
      )}
    </div>
  );
};
