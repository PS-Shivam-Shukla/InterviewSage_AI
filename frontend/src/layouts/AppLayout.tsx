import { ReactNode, useState } from "react";

import Sidebar from "./Sidebar";
import TopNavbar from "./TopNavbar";
import PageContainer from "./PageContainer";

interface Props {
  children: ReactNode;
}

export default function AppLayout({ children }: Props) {
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  return (
    <div className="flex h-screen bg-slate-950 text-white overflow-hidden">
      <Sidebar
        isOpen={isMobileSidebarOpen}
        onClose={() => setIsMobileSidebarOpen(false)}
      />

      <div className="flex flex-col flex-1 overflow-hidden">
        <TopNavbar
          onMobileMenuToggle={() => setIsMobileSidebarOpen((prev) => !prev)}
        />

        <PageContainer>{children}</PageContainer>
      </div>
    </div>
  );
}