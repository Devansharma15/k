"use client";

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { Cpu, BrainCircuit, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

export const LLMNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div className={cn(
      "glass-card p-0 rounded-xl min-w-[280px] shadow-2xl transition-all duration-300",
      selected ? "ring-2 ring-primary border-primary/50 scale-[1.02]" : "border-white/5"
    )}>
      {/* Node Header */}
      <div className="bg-primary/10 px-4 py-3 rounded-t-xl border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-primary/20 rounded-lg">
            <Sparkles size={16} className="text-primary" />
          </div>
          <span className="text-xs font-bold tracking-tight uppercase">LLM Module</span>
        </div>
        <div className="px-1.5 py-0.5 bg-background/50 rounded text-[9px] font-bold text-muted-foreground border border-white/5">
          GPT-4o
        </div>
      </div>

      {/* Node Content */}
      <div className="p-4 space-y-3 bg-background/20 backdrop-blur-md">
        <div className="space-y-1.5">
          <label className="text-[9px] font-bold text-muted-foreground uppercase">System Prompt</label>
          <div className="bg-accent/40 p-2.5 rounded-lg border border-white/5 text-[10px] leading-relaxed line-clamp-3 text-muted-foreground italic">
            {data.prompt || "You are a helpful assistant..."}
          </div>
        </div>

        <div className="flex items-center justify-between pt-1">
          <div className="flex gap-1.5 items-center">
            <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
            <span className="text-[9px] font-bold text-muted-foreground uppercase">Output: Text</span>
          </div>
          <div className="text-[9px] font-bold text-primary/60">0.7 Temp</div>
        </div>
      </div>

      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-card border-2 border-primary ring-4 ring-primary/20"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="w-3 h-3 bg-primary border-2 border-card ring-4 ring-primary/20"
      />
    </div>
  );
});

LLMNode.displayName = 'LLMNode';
