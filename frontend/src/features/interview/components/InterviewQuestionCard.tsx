import React from 'react';
import { HelpCircle, Target, Layers } from 'lucide-react';
import { AdaptiveDifficultyBadge } from './AdaptiveDifficultyBadge';
import { InterviewDifficulty } from '../types/interview.types';
import { cn } from '../../../lib/utils';

export interface QuestionData {
  id?: string;
  sequence_number?: number;
  round_type?: string;
  competency?: string;
  difficulty?: string;
  text?: string;
}

export interface InterviewQuestionCardProps {
  question?: QuestionData | null;
  sequenceNumber?: number;
  className?: string;
}

export const InterviewQuestionCard: React.FC<InterviewQuestionCardProps> = ({
  question,
  sequenceNumber = 1,
  className,
}) => {
  if (!question || !question.text) {
    return (
      <div className={cn('p-6 rounded-2xl bg-slate-900/80 border border-slate-800 text-center text-slate-400', className)}>
        <HelpCircle className="w-8 h-8 text-slate-600 mx-auto mb-2 animate-pulse" />
        <p className="text-sm font-medium">Preparing next contextual question from backend...</p>
      </div>
    );
  }

  const seq = question.sequence_number || sequenceNumber;
  const roundType = question.round_type || 'TECHNICAL';
  const competency = question.competency || 'System Architecture';
  const difficulty = (question.difficulty || 'MEDIUM') as InterviewDifficulty;

  return (
    <div className={cn('p-6 rounded-2xl bg-gradient-to-b from-slate-900/90 to-slate-950 border border-slate-800/90 shadow-2xl space-y-4', className)}>
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/80 pb-3">
        <div className="flex items-center space-x-2">
          <span className="px-2.5 py-1 rounded-lg bg-indigo-950/80 text-indigo-300 border border-indigo-800/50 text-xs font-bold font-mono">
            QUESTION #{seq}
          </span>
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-lg bg-slate-800 text-slate-300 text-xs font-semibold">
            <Layers className="w-3.5 h-3.5 text-slate-400" />
            <span>{roundType} ROUND</span>
          </span>
        </div>

        <div className="flex items-center space-x-2">
          <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-800/90 border border-slate-700 text-xs text-slate-300 font-medium">
            <Target className="w-3.5 h-3.5 text-indigo-400" />
            <span>{competency}</span>
          </span>
          <AdaptiveDifficultyBadge difficulty={difficulty} />
        </div>
      </div>

      <div className="pt-2">
        <p className="text-lg lg:text-xl font-medium text-slate-100 leading-relaxed">
          "{question.text}"
        </p>
      </div>
    </div>
  );
};
