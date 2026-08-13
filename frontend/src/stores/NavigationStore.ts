import { create } from 'zustand';

interface NavigationState {
  sidebarOpen: boolean;
  mobileMenuOpen: boolean;
  activeItem: string;
  setSidebarOpen: (open: boolean) => void;
  setMobileMenuOpen: (open: boolean) => void;
  toggleSidebar: () => void;
  setActiveItem: (item: string) => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
  sidebarOpen: true,
  mobileMenuOpen: false,
  activeItem: '/dashboard',

  setSidebarOpen: (sidebarOpen) => set({ sidebarOpen }),
  setMobileMenuOpen: (mobileMenuOpen) => set({ mobileMenuOpen }),
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setActiveItem: (activeItem) => set({ activeItem }),
}));
