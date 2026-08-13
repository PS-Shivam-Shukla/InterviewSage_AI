import { AIState, InterviewDifficulty } from '../types/interview.types';

export function formatSecondsToTimer(totalSeconds: number): string {
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

export function getAIStateColor(state: AIState): string {
  switch (state) {
    case 'SPEAKING':
      return 'text-indigo-400 border-indigo-500 shadow-indigo-500/50';
    case 'LISTENING':
      return 'text-emerald-400 border-emerald-500 shadow-emerald-500/50';
    case 'THINKING':
      return 'text-amber-400 border-amber-500 shadow-amber-500/50';
    case 'IDLE':
    default:
      return 'text-slate-400 border-slate-700 shadow-none';
  }
}

export function getDifficultyColor(difficulty: InterviewDifficulty | string): string {
  switch (difficulty?.toUpperCase()) {
    case 'HARD':
      return 'bg-rose-950/60 text-rose-300 border-rose-800/50';
    case 'MEDIUM':
    case 'ADAPTIVE':
      return 'bg-amber-950/60 text-amber-300 border-amber-800/50';
    case 'EASY':
    default:
      return 'bg-emerald-950/60 text-emerald-300 border-emerald-800/50';
  }
}
