import React from 'react';
import { Briefcase, Building2, Pause, Play, CheckCircle2, Clock, Square } from 'lucide-react';
import { Interview } from '../types/interview.types';
import { Button } from '../../../components/ui/Button';
import { cn } from '../../../lib/utils';

export interface InterviewHeaderProps {
  interview: Interview | null;
  isPaused: boolean;
  onTogglePause?: () => void;
  onEndSession?: () => void;
  className?: string;
}

export const InterviewHeader: React.FC<InterviewHeaderProps> = ({
  interview,
  isPaused,
  onTogglePause,
  onEndSession,
  className,
}) => {
  if (!interview) return null;

  const getStatusBadge = () => {
    const status = isPaused ? 'PAUSED' : interview.status;
    switch (status) {
      case 'IN_PROGRESS':
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-950/60 text-emerald-400 border border-emerald-800/50 text-xs font-semibold">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Live Session</span>
          </span>
        );
      case 'PAUSED':
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-amber-950/60 text-amber-400 border border-amber-800/50 text-xs font-semibold">
            <Clock className="w-3.5 h-3.5" />
            <span>Paused</span>
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-indigo-950/60 text-indigo-400 border border-indigo-800/50 text-xs font-semibold">
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>Completed</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-slate-800 text-slate-300 border border-slate-700 text-xs font-semibold">
            <span>{interview.status}</span>
          </span>
        );
    }
  };

  const roleTitle = interview.target_role?.trim() || '';
  const displayTitle = roleTitle ? `${roleTitle} Interview` : 'Interview';

  return (
    <div className={cn('flex flex-col md:flex-row md:items-center justify-between gap-4 p-4 lg:p-6 rounded-2xl bg-slate-900/80 border border-slate-800 backdrop-blur-md shadow-xl', className)}>
      <div className="flex flex-col space-y-2">
        <div className="flex items-center space-x-3">
          {getStatusBadge()}
          <span className="text-xs font-mono font-medium text-slate-400 uppercase tracking-wider">
            ID: {interview.id.substring(0, 8)}...
          </span>
        </div>
        <h1 className="text-xl lg:text-2xl font-bold text-slate-100 flex items-center gap-2">
          <Briefcase className="w-5 h-5 text-indigo-400" />
          {displayTitle}
        </h1>
        {interview.target_company && (
          <p className="text-sm text-slate-400 flex items-center gap-1.5">
            <Building2 className="w-4 h-4 text-slate-500" />
            <span>Target Company: <strong className="text-slate-200">{interview.target_company}</strong></span>
          </p>
        )}
      </div>

      {interview.status !== 'COMPLETED' && (
        <div className="flex items-center space-x-3 self-start md:self-auto">
          {onTogglePause && (
            <Button
              variant="outline"
              size="sm"
              onClick={onTogglePause}
              className="border-slate-700 text-slate-300 hover:text-white hover:border-slate-600"
            >
              {isPaused ? (
                <>
                  <Play className="w-4 h-4 mr-2 text-emerald-400" />
                  Resume
                </>
              ) : (
                <>
                  <Pause className="w-4 h-4 mr-2 text-amber-400" />
                  Pause
                </>
              )}
            </Button>
          )}
          {onEndSession && (
            <Button
              variant="outline"
              size="sm"
              onClick={onEndSession}
              className="border-rose-900/60 bg-rose-950/40 text-rose-300 hover:bg-rose-900/60 hover:text-white hover:border-rose-700"
            >
              <Square className="w-4 h-4 mr-2 text-rose-400" />
              Cancel Interview
            </Button>
          )}
        </div>
      )}
    </div>
  );
};
