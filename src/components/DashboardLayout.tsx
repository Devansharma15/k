"use client";

import React from 'react';
import { Sidebar } from './Sidebar';
import { Navbar } from './Navbar';
import { useUIStore } from '@/store/uiStore';
import { cn } from '@/lib/utils';

export const DashboardLayout = ({ children }: { children: React.ReactNode }) => {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="flex min-h-screen bg-background text-foreground selection:bg-primary/20">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        <main className="flex-1 overflow-y-auto p-8 overflow-x-hidden">
          {children}
        </main>
      </div>
    </div>
  );
};
