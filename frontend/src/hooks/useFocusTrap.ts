import { useEffect, useRef } from 'react';

export interface UseFocusTrapOptions {
  isOpen: boolean;
  onClose?: () => void;
}

const FOCUSABLE_SELECTOR =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function useFocusTrap<T extends HTMLElement = HTMLDivElement>({ isOpen, onClose }: UseFocusTrapOptions) {
  const containerRef = useRef<T | null>(null);
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!isOpen) return;

    // Save active element prior to trap opening
    previousFocusRef.current = document.activeElement as HTMLElement | null;

    const container = containerRef.current;
    if (!container) return;

    // Focus first focusable element inside container
    const focusables = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));
    if (focusables.length > 0) {
      setTimeout(() => focusables[0].focus(), 10);
    } else {
      container.focus();
    }

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && onClose) {
        e.preventDefault();
        onClose();
        return;
      }

      if (e.key !== 'Tab') return;

      const currentFocusables = Array.from(container.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR));
      if (currentFocusables.length === 0) {
        e.preventDefault();
        return;
      }

      const firstElement = currentFocusables[0];
      const lastElement = currentFocusables[currentFocusables.length - 1];

      if (e.shiftKey) {
        if (document.activeElement === firstElement || document.activeElement === container) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      // Restore focus to original element on close
      if (previousFocusRef.current && typeof previousFocusRef.current.focus === 'function') {
        previousFocusRef.current.focus();
      }
    };
  }, [isOpen, onClose]);

  return containerRef;
}
