"use client";

import React from 'react';
import { Search, Bell, User, Command } from 'lucide-react';
import { cn } from '@/lib/utils';

export const Navbar = () => {
  return (
    <header className="h-16 border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-40 px-8 flex items-center justify-between">
      <div className="flex items-center gap-4 flex-1 max-w-xl">
        <div className="relative group w-full">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4 group-focus-within:text-primary transition-colors" />
          <input 
            type="text" 
            placeholder="Search apps, workflows, logs..." 
            className="w-full bg-accent/50 border-none rounded-xl py-2 pl-10 pr-4 text-sm focus:ring-2 focus:ring-primary/20 focus:bg-accent transition-all outline-none"
          />
          <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 text-[10px] font-bold text-muted-foreground bg-background border border-border px-1.5 py-0.5 rounded">
            <Command size={10} /> K
          </div>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 hover:bg-accent rounded-full text-muted-foreground hover:text-foreground transition-all">
          <Bell size={20} />
          <span className="absolute top-2 right-2 w-2 h-2 bg-red-500 rounded-full border-2 border-background" />
        </button>
        
        <div className="h-8 w-px bg-border mx-2" />

        <button className="flex items-center gap-3 p-1 hover:bg-accent rounded-full transition-all pl-1 pr-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-primary to-blue-500 flex items-center justify-center text-white text-xs font-bold border border-primary/20">
            JD
          </div>
          <div className="text-left hidden md:block">
            <p className="text-xs font-semibold leading-none">John Doe</p>
            <p className="text-[10px] text-muted-foreground leading-tight">Pro Plan</p>
          </div>
        </button>
      </div>
    </header>
  );
};
