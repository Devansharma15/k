"use client";

import { DashboardLayout } from "@/components/DashboardLayout";

export default function Layout({ children }: { children: React.ReactNode }) {
  // If we want dashboard specific providers or logic, we add them here
  return (
    <DashboardLayout>
      {children}
    </DashboardLayout>
  );
}
