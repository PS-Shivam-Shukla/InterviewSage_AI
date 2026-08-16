import { describe, it, expect } from 'vitest';
import { useDashboard } from './useDashboard';

describe('useDashboard Cache Key Unit Tests', () => {
  it('should export useDashboard hook function', () => {
    expect(typeof useDashboard).toBe('function');
  });
});
