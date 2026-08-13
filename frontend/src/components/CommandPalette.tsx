import React, { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Search, LayoutDashboard, FileText, Brain, Mic, Shield, UserCheck, Upload, Users, Settings, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAppStore } from '../stores/AppStore';
import { useFocusTrap } from '../hooks/useFocusTrap';

export interface CommandItem {
  id: string;
  category: 'Pages' | 'Resumes' | 'Interviews' | 'Analytics' | 'Settings';
  title: string;
  subtitle?: string;
  icon: React.ReactNode;
  href: string;
}

export const CommandPalette: React.FC = () => {
  const { isCommandPaletteOpen, setCommandPaletteOpen } = useAppStore();
  const [query, setQuery] = useState('');
  const navigate = useNavigate();

  const containerRef = useFocusTrap<HTMLDivElement>({
    isOpen: isCommandPaletteOpen,
    onClose: () => setCommandPaletteOpen(false),
  });

  const items: CommandItem[] = [
    { id: '1', category: 'Pages', title: 'Dashboard Overview', subtitle: 'Global metrics hub', icon: <LayoutDashboard className="w-4 h-4 text-indigo-400" aria-hidden="true" />, href: '/dashboard' },
    { id: '2', category: 'Resumes', title: 'Resume Intelligence Vault', subtitle: 'Browse parsed candidate resumes', icon: <UserCheck className="w-4 h-4 text-emerald-400" aria-hidden="true" />, href: '/resumes' },
    { id: '3', category: 'Resumes', title: 'Resume Library', subtitle: 'Filterable candidate resume grid', icon: <FileText className="w-4 h-4 text-emerald-400" aria-hidden="true" />, href: '/resumes/library' },
    { id: '4', category: 'Resumes', title: 'Upload Candidate Resume', subtitle: 'PDF, DOCX, TXT parser', icon: <Upload className="w-4 h-4 text-emerald-400" aria-hidden="true" />, href: '/resumes/upload' },
    { id: '5', category: 'Interviews', title: 'Interview Lobby & Launchpad', subtitle: 'Start voice or text sessions', icon: <Mic className="w-4 h-4 text-indigo-400" aria-hidden="true" />, href: '/interviews' },
    { id: '6', category: 'Interviews', title: 'Configure AI Interview Setup', subtitle: 'Select role, company, difficulty', icon: <Settings className="w-4 h-4 text-indigo-400" aria-hidden="true" />, href: '/interviews/setup' },
    { id: '7', category: 'Analytics', title: 'Candidate Memory Graph', subtitle: 'Multi-interview learning timeline', icon: <Brain className="w-4 h-4 text-amber-400" aria-hidden="true" />, href: '/memory' },
    { id: '8', category: 'Analytics', title: 'Career Intelligence Benchmarks', subtitle: 'Skill gap audit & learning roadmap', icon: <Brain className="w-4 h-4 text-amber-400" aria-hidden="true" />, href: '/career' },
    { id: '9', category: 'Analytics', title: 'Recruiter Governance Dashboard', subtitle: 'Enterprise hiring metrics', icon: <Users className="w-4 h-4 text-emerald-400" aria-hidden="true" />, href: '/recruiter' },
    { id: '10', category: 'Settings', title: 'Admin & System Settings', subtitle: 'Feature flags & API security', icon: <Shield className="w-4 h-4 text-rose-400" aria-hidden="true" />, href: '/admin' },
  ];

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(!isCommandPaletteOpen);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isCommandPaletteOpen, setCommandPaletteOpen]);

  const filtered = items.filter(
    (item) =>
      item.title.toLowerCase().includes(query.toLowerCase()) ||
      (item.subtitle && item.subtitle.toLowerCase().includes(query.toLowerCase()))
  );

  const handleSelect = (href: string) => {
    navigate(href);
    setCommandPaletteOpen(false);
  };

  return (
    <AnimatePresence>
      {isCommandPaletteOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setCommandPaletteOpen(false)}
            className="fixed inset-0 bg-black/70 backdrop-blur-sm"
            aria-hidden="true"
          />
          <motion.div
            ref={containerRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-label="Global Command Palette & Quick Search"
            initial={{ opacity: 0, scale: 0.95, y: -10 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: -10 }}
            className="relative z-50 w-full max-w-2xl overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 shadow-2xl focus-visible:outline-none"
          >
            <div className="flex items-center border-b border-slate-800 px-4 py-3">
              <Search className="w-5 h-5 text-slate-400 mr-3 shrink-0" aria-hidden="true" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search commands, pages, features... (Press Esc to exit)"
                aria-label="Search commands, pages, and features"
                className="w-full bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
                autoFocus
              />
              <div className="flex items-center gap-2">
                <kbd className="hidden sm:inline-block rounded border border-slate-700 bg-slate-800 px-2 py-0.5 font-mono text-[10px] font-bold text-slate-400">
                  ESC
                </kbd>
                <button
                  type="button"
                  onClick={() => setCommandPaletteOpen(false)}
                  aria-label="Close command palette"
                  className="p-1 text-slate-400 hover:text-slate-200"
                >
                  <X className="w-4 h-4" aria-hidden="true" />
                </button>
              </div>
            </div>

            <div className="max-h-96 overflow-y-auto p-2 space-y-1">
              {filtered.length === 0 ? (
                <div className="p-8 text-center text-xs text-slate-500 font-mono">
                  No command or page matched "{query}"
                </div>
              ) : (
                filtered.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => handleSelect(item.href)}
                    className="w-full flex items-center justify-between p-3 rounded-xl hover:bg-slate-800/80 text-left transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500"
                  >
                    <div className="flex items-center space-x-3">
                      <div className="p-2 rounded-lg bg-slate-950 border border-slate-800 shrink-0">
                        {item.icon}
                      </div>
                      <div>
                        <div className="text-xs font-semibold text-slate-200">{item.title}</div>
                        {item.subtitle && <div className="text-[11px] text-slate-400">{item.subtitle}</div>}
                      </div>
                    </div>
                    <span className="text-[10px] font-mono text-slate-500 bg-slate-950 px-2 py-1 rounded border border-slate-800">
                      {item.category}
                    </span>
                  </button>
                ))
              )}
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
