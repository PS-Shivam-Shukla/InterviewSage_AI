import React from 'react';
import { Target, BookOpen, Calendar } from 'lucide-react';
import { LearningRecommendation } from '../types/memory.types';

interface LearningRecommendationsCardProps {
  recommendations?: LearningRecommendation[];
}

export const LearningRecommendationsCard: React.FC<LearningRecommendationsCardProps> = ({ recommendations }) => {
  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-emerald-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">Personalized Learning Roadmap</h2>
        </div>
        <p className="text-xs text-slate-400">
          No learning recommendations generated yet. Complete evaluation turns to receive tailored skill roadmap actions.
        </p>
      </div>
    );
  }

  const getPriorityBadge = (priority: string) => {
    const p = (priority || '').toUpperCase();
    if (p === 'HIGH') {
      return 'bg-rose-500/10 border-rose-500/30 text-rose-400';
    }
    if (p === 'MEDIUM') {
      return 'bg-amber-500/10 border-amber-500/30 text-amber-400';
    }
    return 'bg-indigo-500/10 border-indigo-500/30 text-indigo-400';
  };

  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900/80 p-6 shadow-xl backdrop-blur-md space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookOpen className="h-5 w-5 text-emerald-400" />
          <h2 className="text-base font-bold text-slate-100 font-display">
            Personalized Learning Roadmap
          </h2>
        </div>
        <span className="text-xs font-mono text-slate-400">{recommendations.length} Action Items</span>
      </div>

      <div className="space-y-3">
        {recommendations.map((item, idx) => (
          <div
            key={item.id || idx}
            className="p-4 rounded-xl border border-slate-800/80 bg-slate-950/60 space-y-2"
          >
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="font-semibold text-slate-100 text-sm">{item.target_topic}</span>
              </div>

              <div className="flex items-center gap-2">
                {item.week_number != null && (
                  <span className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded-md border border-slate-800">
                    <Calendar className="w-3 h-3 text-slate-500" /> Week {item.week_number}
                  </span>
                )}
                <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold border ${getPriorityBadge(item.priority)}`}>
                  {item.priority}
                </span>
              </div>
            </div>

            <p className="text-xs text-slate-300 leading-relaxed pl-6 font-mono">
              {item.suggested_action}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};
