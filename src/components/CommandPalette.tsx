"use client";

import React, { useState, useEffect } from 'react';
import { 
  Search, 
  Terminal, 
  Workflow, 
  MessageSquare, 
  Settings,
  X,
  Command
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useRouter } from 'next/navigation';

export const CommandPalette = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState('');
  const router = useRouter();

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setIsOpen((prev) => !prev);
      }
      if (e.key === 'Escape') setIsOpen(false);
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const commands = [
    { name: 'Create New App', icon: MessageSquare, action: () => router.push('/') },
    { name: 'Design Workflow', icon: Workflow, action: () => router.push('/workflows/new') },
    { name: 'View Logs', icon: Terminal, action: () => router.push('/logs') },
    { name: 'Workspace Settings', icon: Settings, action: () => router.push('/settings') },
  ].filter(cmd => cmd.name.toLowerCase().includes(query.toLowerCase()));

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[10vh] px-4 pointer-events-none">
      <motion.div 
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={() => setIsOpen(false)}
        className="fixed inset-0 bg-black/60 backdrop-blur-sm pointer-events-auto"
      />
      
      <motion.div
        initial={{ y: -20, opacity: 0, scale: 0.95 }}
        animate={{ y: 0, opacity: 1, scale: 1 }}
        exit={{ y: -20, opacity: 0, scale: 0.95 }}
        className="w-full max-w-lg glass-card rounded-2xl shadow-2xl relative z-[101] pointer-events-auto border-white/10"
      >
        <div className="flex items-center px-4 py-3 border-b border-white/5">
          <Search className="w-4 h-4 text-muted-foreground mr-3" />
          <input
            autoFocus
            type="text"
            placeholder="Search commands or docs..."
            className="flex-1 bg-transparent border-none outline-none text-sm font-medium"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <button 
            onClick={() => setIsOpen(false)}
            className="p-1 hover:bg-accent rounded-lg text-muted-foreground transition-all"
          >
            <X size={16} />
          </button>
        </div>

        <div className="p-2 max-h-[300px] overflow-y-auto">
          {commands.length > 0 ? (
            <div className="space-y-1">
              <p className="px-3 py-2 text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Suggestions</p>
              {commands.map((cmd) => (
                <button
                  key={cmd.name}
                  onClick={() => {
                    cmd.action();
                    setIsOpen(false);
                  }}
                  className="w-full flex items-center gap-3 px-3 py-2 rounded-xl hover:bg-primary/10 hover:text-primary transition-all text-sm group"
                >
                  <cmd.icon size={16} className="text-muted-foreground group-hover:text-primary transition-colors" />
                  <span className="font-medium">{cmd.name}</span>
                </button>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center">
              <p className="text-xs text-muted-foreground">No commands found for "{query}"</p>
            </div>
          )}
        </div>

        <div className="p-3 bg-background/50 border-t border-white/5 flex items-center justify-between">
           <div className="flex items-center gap-4 text-[10px] font-bold text-muted-foreground uppercase opacity-50">
              <div className="flex items-center gap-1">
                 <span className="px-1 py-px bg-muted/20 border border-border rounded">↑↓</span> to navigate
              </div>
              <div className="flex items-center gap-1">
                 <span className="px-1 py-px bg-muted/20 border border-border rounded">↵</span> to select
              </div>
           </div>
           <div className="flex items-center gap-1 text-[10px] font-bold text-muted-foreground opacity-50 uppercase">
              POWERED BY <span className="text-primary tracking-tighter">AURA</span>
           </div>
        </div>
      </motion.div>
    </div>
  );
};
