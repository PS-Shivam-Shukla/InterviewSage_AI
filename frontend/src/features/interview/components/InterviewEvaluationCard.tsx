import React from 'react';
import { Award, ArrowRight, Brain, Sparkles } from 'lucide-react';
import { Button } from '../../../components/ui/Button';
import { cn } from '../../../lib/utils';

export interface EvaluationData {
  score?: number;
  reasoning?: string;
  feedback?: string;
  ideal_answer_summary?: string;
  technical_score?: number;
  technical_coverage?: number;
  communication_score?: number;
  confidence_score?: number;
}

export interface InterviewEvaluationCardProps {
  evaluation: EvaluationData | null;
  onNextQuestion?: () => void;
  hasNextQuestion?: boolean;
  className?: string;
}

export const InterviewEvaluationCard: React.FC<InterviewEvaluationCardProps> = ({
  evaluation,
  onNextQuestion,
  hasNextQuestion = true,
  className,
}) => {
  if (!evaluation) return null;

  const score = evaluation.score ?? 0;
  const reasoning = evaluation.reasoning || evaluation.feedback || 'No feedback provided.';
  const techScore = evaluation.technical_score ?? evaluation.technical_coverage ?? score;
  const commDisplay = evaluation.communication_score != null ? `${evaluation.communication_score}%` : 'N/A';
  const confDisplay = evaluation.confidence_score != null ? `${evaluation.confidence_score}%` : 'N/A';

  const getScoreColor = (val: number) => {
    if (val >= 85) return 'text-emerald-400 bg-emerald-950/60 border-emerald-800/60';
    if (val >= 70) return 'text-amber-400 bg-amber-950/60 border-amber-800/60';
    return 'text-rose-400 bg-rose-950/60 border-rose-800/60';
  };

  return (
    <div className={cn('p-6 rounded-2xl bg-gradient-to-b from-indigo-950/40 via-slate-900 to-slate-950 border border-indigo-900/40 shadow-2xl space-y-5 animate-fadeIn', className)}>
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-indigo-900/30 pb-4">
        <div className="flex items-center space-x-2">
          <Brain className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-bold text-slate-100 uppercase tracking-wide">
            Evaluation Feedback
          </h3>
        </div>

        <div className={cn('px-4 py-1.5 rounded-full border text-sm font-bold font-mono flex items-center space-x-2', getScoreColor(score))}>
          <Award className="w-4 h-4" />
          <span>Overall Score: {score}/100</span>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col items-center justify-center">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Technical</span>
          <span className="text-lg font-bold font-mono text-emerald-400">{techScore}%</span>
        </div>
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col items-center justify-center">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Communication</span>
          <span className="text-lg font-bold font-mono text-indigo-400">{commDisplay}</span>
        </div>
        <div className="p-3 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col items-center justify-center">
          <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider">Confidence</span>
          <span className="text-lg font-bold font-mono text-amber-400">{confDisplay}</span>
        </div>
      </div>

      <div className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2">
        <div className="flex items-center space-x-2 text-xs font-bold text-slate-300 uppercase tracking-wide">
          <Sparkles className="w-4 h-4 text-indigo-400" />
          <span>Evaluation Reasoning</span>
        </div>
        <p className="text-sm text-slate-200 leading-relaxed font-sans">
          {reasoning}
        </p>
      </div>

      {evaluation.ideal_answer_summary && (
        <div className="p-4 rounded-xl bg-indigo-950/40 border border-indigo-800/50 space-y-2">
          <div className="flex items-center space-x-2 text-xs font-bold text-indigo-300 uppercase tracking-wide">
            <Brain className="w-4 h-4 text-emerald-400" />
            <span>Ideal Reference Answer</span>
          </div>
          <p className="text-sm text-indigo-100 leading-relaxed font-sans">
            {evaluation.ideal_answer_summary}
          </p>
        </div>
      )}

      {onNextQuestion && hasNextQuestion && (
        <div className="flex justify-end pt-2">
          <Button
            onClick={onNextQuestion}
            className="bg-emerald-600 hover:bg-emerald-500 text-white font-semibold shadow-lg shadow-emerald-600/30 px-6 py-2.5 rounded-xl transition-all flex items-center space-x-2"
          >
            <span>Proceed to Next Question</span>
            <ArrowRight className="w-4 h-4" />
          </Button>
        </div>
      )}
    </div>
  );
};
