import { create } from 'zustand';

interface AppState {
  globalLoading: boolean;
  globalLoadingText: string;
  isCommandPaletteOpen: boolean;
  setGlobalLoading: (loading: boolean, text?: string) => void;
  setCommandPaletteOpen: (open: boolean) => void;
}

export const useAppStore = create<AppState>((set) => ({
  globalLoading: false,
  globalLoadingText: 'Loading InterviewSage AI...',
  isCommandPaletteOpen: false,

  setGlobalLoading: (globalLoading, text = 'Loading InterviewSage AI...') =>
    set({ globalLoading, globalLoadingText: text }),

  setCommandPaletteOpen: (isCommandPaletteOpen) => set({ isCommandPaletteOpen }),
}));
