import React, { useState } from 'react';
import { ShieldAlert, Check, X, Flag, RotateCcw, Loader2, CheckCircle2 } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { ReviewQueueItem, ReviewStatus } from '../types/admin.types';
import { useProcessReviewStatus } from '../hooks/useAdmin';

interface HumanReviewQueueCardProps {
  queue?: ReviewQueueItem[];
}

export const HumanReviewQueueCard: React.FC<HumanReviewQueueCardProps> = ({ queue }) => {
  const processMutation = useProcessReviewStatus();
  const [activeReviewId, setActiveReviewId] = useState<string | null>(null);

  const handleAction = async (reviewId: string, statusVal: ReviewStatus) => {
    setActiveReviewId(reviewId);
    try {
      await processMutation.mutateAsync({ reviewId, statusVal });
    } catch (err) {
      console.error('Failed to process review item:', err);
    } finally {
      setActiveReviewId(null);
    }
  };

  if (!queue || queue.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Human Review Queue</h2>
        </div>
        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 p-4 text-xs text-emerald-300">
          <CheckCircle2 className="w-4 h-4 shrink-0" />
          <span>Review queue is clear! No low-confidence AI evaluation items currently pending human review.</span>
        </div>
      </div>
    );
  }

  const getStatusBadge = (status: string) => {
    const s = (status || '').toUpperCase();
    if (s === 'APPROVED') return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
    if (s === 'REJECTED') return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
    if (s === 'FLAGGED') return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
    if (s === 'OVERRIDDEN') return 'bg-purple-500/10 border-purple-500/30 text-purple-400';
    return 'bg-slate-800 border-slate-700 text-slate-300';
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <ShieldAlert className="h-5 w-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Human Review Queue</h2>
        </div>
        <span className="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-amber-500/10 border border-amber-500/30 text-amber-400">
          {queue.length} Queue Items
        </span>
      </div>

      <div className="space-y-3">
        {queue.map((item) => {
          const isPending = processMutation.isPending && activeReviewId === item.review_id;

          return (
            <div
              key={item.review_id}
              className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/60 space-y-3"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono font-semibold text-slate-300">
                    Review #{item.review_id.substring(0, 8)}
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">
                    Interview: {item.interview_id.substring(0, 8)}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono text-amber-400">
                    Confidence: {(item.confidence * 100).toFixed(0)}%
                  </span>
                  <span className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${getStatusBadge(item.status)}`}>
                    {item.status}
                  </span>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-mono">
                Reason: {item.reason}
              </p>

              <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-slate-800/60">
                <span className="text-[11px] text-slate-500 font-mono">
                  Queued: {new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>

                <div className="flex items-center gap-1.5">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={isPending}
                    onClick={() => handleAction(item.review_id, 'APPROVED')}
                    className="border-emerald-800 text-emerald-400 hover:bg-emerald-950/50 text-[11px] px-2.5 py-1"
                  >
                    {isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3 mr-1" />}
                    Approve
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    disabled={isPending}
                    onClick={() => handleAction(item.review_id, 'FLAGGED')}
                    className="border-amber-800 text-amber-400 hover:bg-amber-950/50 text-[11px] px-2.5 py-1"
                  >
                    {isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <Flag className="w-3 h-3 mr-1" />}
                    Flag
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    disabled={isPending}
                    onClick={() => handleAction(item.review_id, 'REJECTED')}
                    className="border-rose-800 text-rose-400 hover:bg-rose-950/50 text-[11px] px-2.5 py-1"
                  >
                    {isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <X className="w-3 h-3 mr-1" />}
                    Reject
                  </Button>

                  <Button
                    size="sm"
                    variant="outline"
                    disabled={isPending}
                    onClick={() => handleAction(item.review_id, 'OVERRIDDEN')}
                    className="border-purple-800 text-purple-400 hover:bg-purple-950/50 text-[11px] px-2.5 py-1"
                  >
                    {isPending ? <Loader2 className="w-3 h-3 animate-spin" /> : <RotateCcw className="w-3 h-3 mr-1" />}
                    Override
                  </Button>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
