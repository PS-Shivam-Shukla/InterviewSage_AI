import React, { useEffect } from 'react';
import { ThemeContext } from '../contexts/ThemeContext';
import { useThemeStore } from '../stores/ThemeStore';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { theme, resolvedTheme, setTheme } = useThemeStore();

  useEffect(() => {
    if (resolvedTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [resolvedTheme]);

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
};
