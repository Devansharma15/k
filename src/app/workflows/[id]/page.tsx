"use client";

import React from 'react';
import { WorkflowCanvas } from '@/features/workflows/components/WorkflowCanvas';
import { 
  History, 
  Settings, 
  Play, 
  ChevronRight,
  Database,
  Cloud
} from 'lucide-react';

export default function WorkflowPage({ params }: { params: { id: string } }) {
  return (
    <div className="flex h-screen -m-8 overflow-hidden flex-col">
      {/* Workflow Header Panel */}
      <div className="bg-background/80 backdrop-blur-md border-b border-border p-4 px-8 flex items-center justify-between z-20">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground mr-4">
            <span>Workflows</span>
            <ChevronRight size={12} />
            <span className="text-foreground">Lead Generation Pipeline</span>
          </div>
          <div className="h-4 w-px bg-border mx-2" />
          <div className="flex items-center gap-3">
            <div className="px-2 py-0.5 bg-blue-500/10 text-blue-500 text-[10px] font-bold rounded border border-blue-500/20">DRAFT</div>
            <p className="text-[10px] text-muted-foreground font-bold">Last edited 5m ago by John</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button className="flex items-center gap-2 px-3 py-1.5 bg-secondary text-secondary-foreground text-xs font-bold rounded-xl hover:bg-secondary/80 transition-all">
            <History size={14} />
            HISTORY
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 bg-secondary text-secondary-foreground text-xs font-bold rounded-xl hover:bg-secondary/80 transition-all">
            <Settings size={14} />
            SETTINGS
          </button>
          <button className="flex items-center gap-2 px-4 py-1.5 bg-primary text-primary-foreground text-xs font-bold rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/20">
            <Play size={14} />
            RUN FLOW
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="flex-1 relative">
         <WorkflowCanvas />
      </div>

      {/* Footer Info Bar */}
      <div className="bg-background border-t border-border px-8 py-2 flex items-center justify-between text-[10px] font-bold text-muted-foreground uppercase tracking-widest z-20 shadow-2xl">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <Database size={12} className="text-blue-400" />
            Active Knowledge: Customer_Base_Q3
          </div>
          <div className="flex items-center gap-2">
            <Cloud size={12} className="text-emerald-400" />
            Cloud Environment: Production-US-East
          </div>
        </div>
        <div className="flex items-center gap-4">
           <span>Total Nodes: 14</span>
           <span>Latency: 142ms</span>
        </div>
      </div>
    </div>
  );
}
