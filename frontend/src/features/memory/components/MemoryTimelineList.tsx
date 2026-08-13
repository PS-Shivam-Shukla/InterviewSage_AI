import React from 'react';
import { Clock, Calendar, Hash, FileText } from 'lucide-react';
import { CandidateTimelineItem } from '../types/memory.types';

interface MemoryTimelineListProps {
  timeline?: CandidateTimelineItem[];
}

export const MemoryTimelineList: React.FC<MemoryTimelineListProps> = ({ timeline }) => {
  if (!timeline || timeline.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Interview Memory Timeline</h2>
        </div>
        <div className="py-8 text-center space-y-2">
          <FileText className="w-8 h-8 text-slate-600 mx-auto" />
          <p className="text-xs text-slate-400">
            No interview memories recorded in timeline yet. Complete sessions to build your chronological memory history.
          </p>
        </div>
      </div>
    );
  }

  const getScoreBadge = (score?: number | null) => {
    if (score == null) return null;
    const rounded = Math.round(score);
    if (rounded >= 85) return 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400';
    if (rounded >= 75) return 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400';
    if (rounded >= 60) return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
    return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="h-5 w-5 text-indigo-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Cross-Interview Memory Timeline</h2>
        </div>
        <span className="text-xs font-mono text-slate-400">{timeline.length} Memory Events</span>
      </div>

      <div className="space-y-3">
        {timeline.map((item, idx) => {
          const scoreBadgeClass = getScoreBadge(item.overall_score);

          return (
            <div
              key={item.interview_id || idx}
              className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/60 space-y-2"
            >
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 text-xs font-mono text-slate-400">
                  <Calendar className="w-3.5 h-3.5 text-slate-500" />
                  <span>{item.date}</span>
                </div>

                {item.overall_score != null && scoreBadgeClass && (
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${scoreBadgeClass}`}>
                    Score: {Math.round(item.overall_score)}%
                  </span>
                )}
              </div>

              <p className="text-xs text-slate-200 leading-relaxed font-mono">
                {item.summary}
              </p>

              {item.key_topics && item.key_topics.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {item.key_topics.map((topic) => (
                    <span
                      key={topic}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-semibold bg-indigo-950/60 border border-indigo-900/50 text-indigo-300"
                    >
                      <Hash className="w-3 h-3 text-indigo-400" />
                      {topic}
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
