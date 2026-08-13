import React, { useState } from 'react';
import { ChevronDown, ChevronUp, MessageSquare, Award } from 'lucide-react';
import { TranscriptSnapshotItem } from '../../../services/report.service';

interface TranscriptSnapshotAccordionProps {
  transcript: TranscriptSnapshotItem[];
}

export const TranscriptSnapshotAccordion: React.FC<TranscriptSnapshotAccordionProps> = ({ transcript }) => {
  const [openItems, setOpenItems] = useState<Record<number, boolean>>({ 0: true });

  if (!transcript || transcript.length === 0) {
    return null;
  }

  const toggleItem = (idx: number) => {
    setOpenItems((prev) => ({
      ...prev,
      [idx]: !prev[idx],
    }));
  };

  const getScoreBadge = (score: number) => {
    const rounded = Math.round(score);
    if (rounded >= 80) return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
    if (rounded >= 70) return 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400';
    if (rounded >= 60) return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
    return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center gap-2">
        <MessageSquare className="w-5 h-5 text-indigo-400" />
        <h2 className="text-base font-bold text-slate-100 font-display">Question-by-Question Evaluation Breakdown</h2>
      </div>

      <div className="space-y-3">
        {transcript.map((item, idx) => {
          const isOpen = !!openItems[idx];
          const scoreVal = Math.round(item.score);

          return (
            <div
              key={idx}
              className="rounded-xl border border-slate-800 bg-slate-950/60 overflow-hidden transition-colors"
            >
              <button
                type="button"
                onClick={() => toggleItem(idx)}
                className="w-full p-4 flex items-center justify-between gap-4 text-left hover:bg-slate-900/60 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                aria-expanded={isOpen}
              >
                <div className="flex items-center gap-3 min-w-0">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-indigo-950/80 border border-indigo-800/50 text-xs font-bold text-indigo-300 font-mono">
                    Q{idx + 1}
                  </span>
                  <span className="font-semibold text-slate-200 text-sm truncate">
                    {item.question}
                  </span>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${getScoreBadge(scoreVal)}`}>
                    Score: {scoreVal}/100
                  </span>
                  {isOpen ? (
                    <ChevronUp className="w-4 h-4 text-slate-400" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-slate-400" />
                  )}
                </div>
              </button>

              {isOpen && (
                <div className="p-4 pt-2 border-t border-slate-800/60 space-y-4 bg-slate-900/30">
                  <div className="space-y-1">
                    <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">
                      Candidate Response
                    </span>
                    <div className="p-3 rounded-lg bg-slate-900 border border-slate-800 text-xs text-slate-300 font-mono leading-relaxed whitespace-pre-wrap">
                      {item.answer || 'No response provided.'}
                    </div>
                  </div>

                  {item.reasoning && (
                    <div className="space-y-1">
                      <div className="flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-indigo-400">
                        <Award className="w-3.5 h-3.5" />
                        <span>AI Agent Feedback & Evaluation</span>
                      </div>
                      <p className="text-xs text-slate-300 leading-relaxed bg-indigo-950/20 border border-indigo-900/40 p-3 rounded-lg">
                        {item.reasoning}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
