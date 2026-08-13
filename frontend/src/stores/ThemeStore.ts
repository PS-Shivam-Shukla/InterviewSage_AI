import { create } from 'zustand';
import { ENV } from '../config/env.config';
import { Theme, ThemeState } from '../types/theme.types';

const getInitialTheme = (): Theme => {
  const saved = localStorage.getItem(ENV.THEME_KEY) as Theme;
  return saved || 'dark';
};

const resolveTheme = (theme: Theme): 'light' | 'dark' => {
  if (theme === 'system') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  return theme;
};

export const useThemeStore = create<ThemeState>((set) => {
  const initial = getInitialTheme();
  return {
    theme: initial,
    resolvedTheme: resolveTheme(initial),
    setTheme: (theme: Theme) => {
      localStorage.setItem(ENV.THEME_KEY, theme);
      const resolved = resolveTheme(theme);
      if (resolved === 'dark') {
        document.documentElement.classList.add('dark');
      } else {
        document.documentElement.classList.remove('dark');
      }
      set({ theme, resolvedTheme: resolved });
    },
  };
});
