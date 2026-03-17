"use client";

import React from 'react';
import { ChatUI } from '@/components/ChatUI';
import { 
  Settings, 
  Sliders, 
  Database, 
  History, 
  ChevronRight,
  Info
} from 'lucide-react';
import { cn } from '@/lib/utils';

export default function AppPage({ params }: { params: { id: string } }) {
  return (
    <div className="flex h-screen -m-8 overflow-hidden">
      {/* Main Chat Area */}
      <div className="flex-1 p-8 flex flex-col min-w-0">
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
            <span>Home</span>
            <ChevronRight size={12} />
            <span>Apps</span>
            <ChevronRight size={12} />
            <span className="text-foreground">App {params.id}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="px-2 py-1 bg-emerald-500/10 text-emerald-500 text-[10px] font-bold rounded border border-emerald-500/20">LIVE</div>
            <div className="px-2 py-1 bg-accent text-accent-foreground text-[10px] font-bold rounded border border-border">v1.0.4</div>
          </div>
        </div>
        <ChatUI />
      </div>

      {/* Right Configuration Sidebar */}
      <div className="w-80 border-l border-border bg-card/20 backdrop-blur-md p-6 overflow-y-auto space-y-8 hidden xl:block">
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold tracking-tight">
            <Sliders size={18} className="text-primary" />
            Model Configuration
          </div>
          
          <div className="space-y-4 pt-2">
            <div className="space-y-2">
              <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Model Provider</label>
              <select className="w-full bg-accent/50 border border-border rounded-lg p-2 text-xs outline-none focus:ring-1 focus:ring-primary/40 transition-all">
                <option>Anthropic Claude 3.5 Sonnet</option>
                <option>OpenAI GPT-4o</option>
                <option>Meta Llama 3 (Ollama)</option>
              </select>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Temperature</label>
                <span className="text-[10px] font-bold">0.7</span>
              </div>
              <input type="range" className="w-full h-1 bg-accent rounded-lg appearance-none cursor-pointer accent-primary" min="0" max="1" step="0.1" defaultValue="0.7" />
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Max Tokens</label>
                <span className="text-[10px] font-bold">2,048</span>
              </div>
              <input type="range" className="w-full h-1 bg-accent rounded-lg appearance-none cursor-pointer accent-primary" min="500" max="4000" step="100" defaultValue="2000" />
            </div>
          </div>
        </div>

        <div className="h-px bg-border" />

        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold tracking-tight">
            <Database size={18} className="text-blue-400" />
            Knowledge Base
          </div>
          <div className="p-4 rounded-xl border border-dashed border-border bg-accent/20 flex flex-col items-center justify-center text-center group cursor-pointer hover:bg-accent/40 transition-all">
            <div className="w-8 h-8 rounded-full bg-background flex items-center justify-center mb-2 group-hover:scale-110 transition-transform">
              <span className="text-primary font-bold text-lg">+</span>
            </div>
            <p className="text-[10px] font-bold text-muted-foreground uppercase">Assign Dataset</p>
          </div>
        </div>

        <div className="h-px bg-border" />

        <div className="p-4 rounded-xl bg-primary/10 border border-primary/20 space-y-2">
          <div className="flex items-center gap-2 text-[10px] font-bold text-primary uppercase">
            <Info size={12} />
            Quick Tip
          </div>
          <p className="text-[11px] leading-relaxed text-muted-foreground">
            You can use <code className="text-primary">{"{variable}"}</code> syntax in your system prompt to inject dynamic context.
          </p>
        </div>
      </div>
    </div>
  );
}
