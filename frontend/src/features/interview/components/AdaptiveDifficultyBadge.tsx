import React from 'react';
import { motion } from 'framer-motion';
import { Zap } from 'lucide-react';
import { InterviewDifficulty } from '../types/interview.types';
import { getDifficultyColor } from '../utils/interviewHelpers';

export interface AdaptiveDifficultyBadgeProps {
  difficulty: InterviewDifficulty;
}

export const AdaptiveDifficultyBadge: React.FC<AdaptiveDifficultyBadgeProps> = ({ difficulty }) => {
  const colorClass = getDifficultyColor(difficulty);

  return (
    <motion.div
      key={difficulty}
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full border text-xs font-bold shadow-sm ${colorClass}`}
    >
      <Zap className="w-3.5 h-3.5 animate-pulse" />
      <span>{difficulty} DIFFICULTY</span>
    </motion.div>
  );
};
