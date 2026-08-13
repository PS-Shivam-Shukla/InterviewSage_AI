import { createContext } from 'react';
import { ThemeState } from '../types/theme.types';

export const ThemeContext = createContext<ThemeState | undefined>(undefined);
