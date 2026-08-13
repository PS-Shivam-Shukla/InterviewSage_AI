import React, { useId } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '../lib/utils';
import { useFocusTrap } from '../hooks/useFocusTrap';

export interface DialogProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export const Dialog: React.FC<DialogProps> = ({ isOpen, onClose, title, description, children, className }) => {
  const containerRef = useFocusTrap<HTMLDivElement>({ isOpen, onClose });
  const titleId = useId();
  const descId = useId();

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            aria-hidden="true"
          />
          <motion.div
            ref={containerRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-labelledby={title ? titleId : undefined}
            aria-describedby={description ? descId : undefined}
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className={cn(
              'relative z-50 w-full max-w-lg rounded-xl border border-slate-800 bg-slate-900 p-6 shadow-2xl text-slate-100 focus-visible:outline-none',
              className
            )}
          >
            <div className="flex items-center justify-between pb-3">
              <div>
                {title && (
                  <h3 id={titleId} className="text-lg font-semibold text-slate-100">
                    {title}
                  </h3>
                )}
                {description && (
                  <p id={descId} className="text-xs text-slate-400 mt-1">
                    {description}
                  </p>
                )}
              </div>
              <button
                type="button"
                onClick={onClose}
                aria-label="Close dialog"
                className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-slate-200 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
              >
                <X className="w-5 h-5" aria-hidden="true" />
              </button>
            </div>
            <div className="mt-2">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
