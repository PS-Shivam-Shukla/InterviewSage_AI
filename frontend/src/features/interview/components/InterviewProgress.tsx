import React from 'react';
import { Target, HelpCircle } from 'lucide-react';
import { cn } from '../../../lib/utils';

export interface InterviewProgressProps {
  currentQuestionIndex: number;
  totalQuestions: number;
  currentCompetency?: string;
  className?: string;
}

export const InterviewProgress: React.FC<InterviewProgressProps> = ({
  currentQuestionIndex,
  totalQuestions,
  currentCompetency,
  className,
}) => {
  const safeTotal = totalQuestions > 0 ? totalQuestions : 5;
  const currentNum = Math.min(Math.max(currentQuestionIndex, 1), safeTotal);
  const percentage = Math.min(Math.round((currentNum / safeTotal) * 100), 100);

  return (
    <div className={cn('p-4 rounded-xl bg-slate-900/60 border border-slate-800/80 space-y-3', className)}>
      <div className="flex items-center justify-between text-xs font-semibold">
        <div className="flex items-center space-x-2 text-slate-300">
          <HelpCircle className="w-4 h-4 text-indigo-400" />
          <span>Question <strong className="text-white">{currentNum}</strong> of <strong className="text-slate-400">{safeTotal}</strong></span>
        </div>
        {currentCompetency && (
          <div className="flex items-center space-x-1.5 text-indigo-300 bg-indigo-950/60 border border-indigo-800/40 px-2.5 py-0.5 rounded-md">
            <Target className="w-3.5 h-3.5" />
            <span className="truncate max-w-[200px]">{currentCompetency}</span>
          </div>
        )}
        <span className="font-mono text-slate-400">{percentage}%</span>
      </div>

      <div className="w-full h-2 rounded-full bg-slate-800 overflow-hidden">
        <div
          className="h-full bg-gradient-to-r from-indigo-500 to-emerald-400 transition-all duration-500 ease-out"
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
};
