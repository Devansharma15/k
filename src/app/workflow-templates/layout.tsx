"use client";

import { DashboardLayout } from "@/components/DashboardLayout";

export default function WorkflowTemplatesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <DashboardLayout>{children}</DashboardLayout>;
}
