"use client";

import type { ReactNode } from "react";

import { Header, MobileSidebarOverlay, useMobileSidebar } from "@/layouts/Header";
import { MainContent } from "@/layouts/MainContent";
import { Sidebar } from "@/layouts/Sidebar";

export default function AppShell({ children }: { children: ReactNode }) {
  const { open, openSidebar, closeSidebar } = useMobileSidebar();

  return (
    <div className="flex min-h-screen bg-background">
      <div className="hidden md:flex">
        <Sidebar />
      </div>

      <MobileSidebarOverlay open={open} onClose={closeSidebar}>
        <Sidebar onNavigate={closeSidebar} />
      </MobileSidebarOverlay>

      <div className="flex min-w-0 flex-1 flex-col">
        <Header onMenuToggle={openSidebar} />
        <MainContent>{children}</MainContent>
      </div>
    </div>
  );
}
