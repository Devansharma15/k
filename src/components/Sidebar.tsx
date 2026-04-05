"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  MessageSquare, 
  Workflow, 
  CopyPlus,
  Database, 
  Plug, 
  BarChart3, 
  Settings,
  ChevronLeft,
  ChevronRight,
  BrainCircuit
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useUIStore } from '@/store/uiStore';
import { motion } from 'framer-motion';

const navItems = [
  { name: 'Dashboard', icon: LayoutDashboard, href: '/' },
  { name: 'Apps', icon: MessageSquare, href: '/apps' },
  { name: 'Workflows', icon: Workflow, href: '/workflows' },
  { name: 'Workflow Templates', icon: CopyPlus, href: '/workflow-templates' },
  { name: 'Knowledge Base', icon: Database, href: '/knowledge-base' },
  { name: 'Integrations', icon: Plug, href: '/integrations' },
  { name: 'Logs', icon: BarChart3, href: '/logs' },
  { name: 'Settings', icon: Settings, href: '/settings' },
];

export const Sidebar = () => {
  const pathname = usePathname();
  const { sidebarOpen, toggleSidebar } = useUIStore();

  return (
    <motion.aside
      initial={false}
      animate={{ width: sidebarOpen ? 240 : 80 }}
      className={cn(
        "h-screen bg-card border-r border-border sticky top-0 flex flex-col transition-all duration-300 ease-in-out z-50",
        !sidebarOpen && "items-center"
      )}
    >
      <div className="p-6 flex items-center gap-3 overflow-hidden">
        <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
          <BrainCircuit className="text-primary-foreground w-5 h-5" />
        </div>
        {sidebarOpen && (
          <span className="font-bold text-xl tracking-tight whitespace-nowrap">AuraFlow</span>
        )}
      </div>

      <nav className="flex-1 px-4 space-y-2 mt-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 p-3 rounded-xl transition-all group relative",
                isActive 
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" 
                  : "hover:bg-accent text-muted-foreground hover:text-foreground"
              )}
            >
              <item.icon size={20} className={cn("shrink-0", isActive ? "" : "group-hover:scale-110 transition-transform")} />
              {sidebarOpen && (
                <span className="font-medium whitespace-nowrap">{item.name}</span>
              )}
              {!sidebarOpen && (
                <div className="absolute left-full ml-4 px-2 py-1 bg-popover text-popover-foreground rounded text-xs opacity-0 group-hover:opacity-100 pointer-events-none transition-opacity whitespace-nowrap z-[100] border border-border shadow-md">
                  {item.name}
                </div>
              )}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t border-border">
        <button
          onClick={toggleSidebar}
          className="flex items-center justify-center w-full p-2 hover:bg-accent rounded-lg text-muted-foreground transition-colors"
        >
          {sidebarOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
        </button>
      </div>
    </motion.aside>
  );
};
