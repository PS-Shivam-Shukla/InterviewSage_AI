import React from 'react';
import { motion } from 'framer-motion';

export interface PageTransitionWrapperProps {
  children: React.ReactNode;
}

export const PageTransitionWrapper: React.FC<PageTransitionWrapperProps> = ({ children }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.22, ease: 'easeOut' }}
      className="w-full h-full flex flex-col flex-1"
    >
      {children}
    </motion.div>
  );
};
