import { describe, it, expect } from 'vitest';

describe('Accessibility Primitives & Attributes Unit Tests', () => {
  it('useFocusTrap module should export valid hook function', async () => {
    const { useFocusTrap } = await import('../hooks/useFocusTrap');
    expect(typeof useFocusTrap).toBe('function');
  });

  it('LiveRegion component module should export valid React component', async () => {
    const { LiveRegion } = await import('../components/ui/LiveRegion');
    expect(typeof LiveRegion).toBe('function');
  });

  it('AccessibleDataTable component module should export valid React component', async () => {
    const { AccessibleDataTable } = await import('../components/ui/AccessibleDataTable');
    expect(typeof AccessibleDataTable).toBe('function');
  });

  it('Dialog component module should export valid React component', async () => {
    const { Dialog } = await import('../components/Dialog');
    expect(typeof Dialog).toBe('function');
  });

  it('CommandPalette component module should export valid React component', async () => {
    const { CommandPalette } = await import('../components/CommandPalette');
    expect(typeof CommandPalette).toBe('function');
  });

  it('Sidebar component module should export valid React component', async () => {
    const Sidebar = (await import('../layouts/Sidebar')).default;
    expect(typeof Sidebar).toBe('function');
  });
});
