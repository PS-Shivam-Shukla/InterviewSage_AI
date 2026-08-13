import { Variants } from 'framer-motion';

/**
 * Reusable Framer Motion animation variants
 */
export const fadeIn: Variants = {
  initial: { opacity: 0 },
  animate: { opacity: 1, transition: { duration: 0.25 } },
  exit: { opacity: 0, transition: { duration: 0.2 } },
};

export const slideUp: Variants = {
  initial: { opacity: 0, y: 15 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, y: 10, transition: { duration: 0.2 } },
};

export const slideDown: Variants = {
  initial: { opacity: 0, y: -15 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.3, ease: 'easeOut' } },
  exit: { opacity: 0, y: -10, transition: { duration: 0.2 } },
};

export const scaleIn: Variants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { opacity: 1, scale: 1, transition: { duration: 0.2, ease: 'easeOut' } },
  exit: { opacity: 0, scale: 0.95, transition: { duration: 0.15 } },
};

export const sidebarSlide: Variants = {
  closed: { x: '-100%', transition: { type: 'spring', stiffness: 300, damping: 30 } },
  open: { x: 0, transition: { type: 'spring', stiffness: 300, damping: 30 } },
};
