import { create } from "zustand";

interface AppState {
  sidebarCollapsed: boolean;
  selectedJobId: string | null;
  toggleSidebar: () => void;
  setSelectedJob: (id: string | null) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarCollapsed: false,
  selectedJobId: null,
  toggleSidebar: () => set((s) => ({ sidebarCollapsed: !s.sidebarCollapsed })),
  setSelectedJob: (id) => set({ selectedJobId: id }),
}));
