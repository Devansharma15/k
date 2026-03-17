"use client";

import React, { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { GitBranch, Split } from 'lucide-react';
import { cn } from '@/lib/utils';

export const ConditionNode = memo(({ data, selected }: NodeProps) => {
  return (
    <div className={cn(
      "glass-card p-0 rounded-xl min-w-[240px] shadow-2xl transition-all duration-300",
      selected ? "ring-2 ring-yellow-500 border-yellow-500/50 scale-[1.02]" : "border-white/5"
    )}>
      {/* Node Header */}
      <div className="bg-yellow-500/10 px-4 py-3 rounded-t-xl border-b border-white/5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="p-1.5 bg-yellow-500/20 rounded-lg">
            <Split size={16} className="text-yellow-500" />
          </div>
          <span className="text-xs font-bold tracking-tight uppercase">Logical Split</span>
        </div>
      </div>

      {/* Node Content */}
      <div className="p-4 space-y-3 bg-background/20 backdrop-blur-md">
        <div className="space-y-1.5 text-center">
          <p className="text-[10px] text-muted-foreground italic font-medium">"If variable X contains..."</p>
        </div>
        
        <div className="flex justify-between items-center text-[9px] font-bold uppercase tracking-widest pt-2">
          <div className="text-emerald-500">True</div>
          <div className="text-red-500">False</div>
        </div>
      </div>

      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="w-3 h-3 bg-card border-2 border-yellow-500 ring-4 ring-yellow-500/20"
      />
      <Handle
        id="true"
        type="source"
        position={Position.Right}
        style={{ top: '65%' }}
        className="w-3 h-3 bg-emerald-500 border-2 border-card ring-4 ring-emerald-500/20"
      />
      <Handle
        id="false"
        type="source"
        position={Position.Right}
        style={{ top: '85%' }}
        className="w-3 h-3 bg-red-500 border-2 border-card ring-4 ring-red-500/20"
      />
    </div>
  );
});

ConditionNode.displayName = 'ConditionNode';
