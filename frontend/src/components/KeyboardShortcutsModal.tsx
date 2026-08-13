import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Keyboard, X } from 'lucide-react';
import { useFocusTrap } from '../hooks/useFocusTrap';

export const KeyboardShortcutsModal: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);

  const containerRef = useFocusTrap<HTMLDivElement>({
    isOpen,
    onClose: () => setIsOpen(false),
  });

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === '/') {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const shortcuts = [
    { key: 'Ctrl + K', description: 'Open Global Command Palette & Search' },
    { key: 'Ctrl + /', description: 'Toggle Keyboard Shortcuts Guide' },
    { key: 'Escape', description: 'Close active modal, drawer, or dropdown' },
    { key: 'Enter / Space', description: 'Activate focused button or navigation link' },
    { key: 'Tab / Shift + Tab', description: 'Navigate interactive element focus ring' },
  ];

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setIsOpen(false)}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            aria-hidden="true"
          />
          <motion.div
            ref={containerRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-label="Keyboard Shortcuts Guide"
            initial={{ opacity: 0, scale: 0.95, y: 10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 10 }}
            className="relative z-50 w-full max-w-md overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl p-5 space-y-4 focus-visible:outline-none"
          >
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2">
                <Keyboard className="w-5 h-5 text-indigo-400" aria-hidden="true" />
                <h3 className="text-sm font-bold text-slate-100">Keyboard Shortcuts Guide</h3>
              </div>
              <button
                type="button"
                onClick={() => setIsOpen(false)}
                aria-label="Close keyboard shortcuts guide"
                className="p-1 rounded-lg text-slate-400 hover:text-slate-100 hover:bg-slate-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
              >
                <X className="w-4 h-4" aria-hidden="true" />
              </button>
            </div>

            <div className="space-y-2">
              {shortcuts.map((sc) => (
                <div
                  key={sc.key}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs"
                >
                  <span className="text-slate-300 font-medium">{sc.description}</span>
                  <kbd className="rounded-md border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[10px] font-bold text-indigo-300">
                    {sc.key}
                  </kbd>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
