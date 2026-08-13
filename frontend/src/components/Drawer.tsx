import React from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '../lib/utils';

export interface DrawerProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  position?: 'left' | 'right';
  children: React.ReactNode;
  className?: string;
}

export const Drawer: React.FC<DrawerProps> = ({
  isOpen,
  onClose,
  title,
  position = 'right',
  children,
  className,
}) => {
  const isRight = position === 'right';

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex overflow-hidden">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
          />
          <motion.div
            initial={{ x: isRight ? '100%' : '-100%' }}
            animate={{ x: 0 }}
            exit={{ x: isRight ? '100%' : '-100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className={cn(
              'relative z-50 flex w-full max-w-md flex-col bg-slate-900 border-slate-800 p-6 text-slate-100 shadow-2xl',
              isRight ? 'ml-auto border-l' : 'mr-auto border-r',
              className
            )}
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-4 mb-4">
              {title && <h3 className="text-base font-semibold text-slate-100">{title}</h3>}
              <button
                onClick={onClose}
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
