import React from 'react';
import { motion } from 'framer-motion';
import { Sparkles, Mic, Volume2, Brain } from 'lucide-react';
import { AIState } from '../types/interview.types';
import { cn } from '../../../lib/utils';

export interface AIAvatarProps {
  state: AIState;
  className?: string;
}

export const AIAvatar: React.FC<AIAvatarProps> = ({ state, className }) => {
  const getIcon = () => {
    switch (state) {
      case 'SPEAKING':
        return <Volume2 className="w-14 h-14 text-indigo-300 animate-pulse" />;
      case 'LISTENING':
        return <Mic className="w-14 h-14 text-emerald-300 animate-bounce" />;
      case 'THINKING':
        return <Brain className="w-14 h-14 text-amber-300 animate-spin" />;
      case 'IDLE':
      default:
        return <Sparkles className="w-14 h-14 text-indigo-300" />;
    }
  };

  const getLabel = () => {
    switch (state) {
      case 'SPEAKING':
        return 'InterviewSage AI Speaking...';
      case 'LISTENING':
        return 'Listening to Candidate Voice...';
      case 'THINKING':
        return 'Supervisor Agent Evaluating Answer...';
      case 'IDLE':
      default:
        return 'Multi-Agent Voice Engine Ready';
    }
  };

  return (
    <div className={cn('flex flex-col items-center justify-center space-y-6 select-none', className)}>
      <div className="relative flex items-center justify-center">
        {/* Layer 1: Outer Breathing Glow */}
        <motion.div
          animate={{
            scale: state === 'SPEAKING' ? [1, 1.3, 1] : state === 'LISTENING' ? [1, 1.2, 1] : [1, 1.08, 1],
            rotate: [0, 180, 360],
            opacity: state === 'IDLE' ? 0.25 : 0.6,
          }}
          transition={{ repeat: Infinity, duration: state === 'THINKING' ? 2 : 4, ease: 'linear' }}
          className={cn(
            'absolute h-52 w-52 rounded-full border-2 border-dashed',
            state === 'SPEAKING' && 'border-indigo-400 bg-indigo-500/10 shadow-indigo-500/50 shadow-2xl',
            state === 'LISTENING' && 'border-emerald-400 bg-emerald-500/10 shadow-emerald-500/50 shadow-2xl',
            state === 'THINKING' && 'border-amber-400 bg-amber-500/10 shadow-amber-500/50 shadow-2xl',
            state === 'IDLE' && 'border-slate-700 bg-slate-800/20'
          )}
        />

        {/* Layer 2: Middle Ripple Ring */}
        <motion.div
          animate={{
            scale: state === 'SPEAKING' ? [1.1, 1.45, 1.1] : [1, 1.15, 1],
            opacity: state === 'IDLE' ? 0.2 : 0.45,
          }}
          transition={{ repeat: Infinity, duration: 2 }}
          className={cn(
            'absolute h-64 w-64 rounded-full border',
            state === 'SPEAKING' && 'border-indigo-500/30',
            state === 'LISTENING' && 'border-emerald-500/30',
            state === 'THINKING' && 'border-amber-500/30',
            state === 'IDLE' && 'border-slate-800'
          )}
        />

        {/* Layer 3: Central ChatGPT-Voice Orb Canvas Container */}
        <motion.div
          whileHover={{ scale: 1.06 }}
          animate={{
            scale: state === 'SPEAKING' ? [1, 1.04, 1] : [1, 1.02, 1],
          }}
          transition={{ repeat: Infinity, duration: 1.2 }}
          className={cn(
            'relative z-10 flex h-36 w-36 items-center justify-center rounded-full bg-gradient-to-b from-slate-900 via-slate-900 to-indigo-950/80 border-4 shadow-2xl backdrop-blur-md transition-colors duration-300',
            state === 'SPEAKING' && 'border-indigo-500 shadow-indigo-500/60 ring-4 ring-indigo-500/20',
            state === 'LISTENING' && 'border-emerald-500 shadow-emerald-500/60 ring-4 ring-emerald-500/20',
            state === 'THINKING' && 'border-amber-500 shadow-amber-500/60 ring-4 ring-amber-500/20',
            state === 'IDLE' && 'border-slate-700 shadow-slate-950'
          )}
        >
          {getIcon()}
        </motion.div>
      </div>

      <motion.div
        key={state}
        initial={{ opacity: 0, y: 5 }}
        animate={{ opacity: 1, y: 0 }}
        aria-live="polite"
        className="flex items-center space-x-2 text-xs font-bold tracking-wide uppercase"
      >
        <span
          className={cn(
            'h-2.5 w-2.5 rounded-full animate-pulse',
            state === 'SPEAKING' && 'bg-indigo-400 shadow-indigo-400 shadow-sm',
            state === 'LISTENING' && 'bg-emerald-400 shadow-emerald-400 shadow-sm',
            state === 'THINKING' && 'bg-amber-400 shadow-amber-400 shadow-sm',
            state === 'IDLE' && 'bg-slate-500'
          )}
        />
        <span className="text-slate-100">{getLabel()}</span>
      </motion.div>
    </div>
  );
};
