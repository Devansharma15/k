"use client";

import React, { useCallback, useMemo } from 'react';
import ReactFlow, { 
  addEdge, 
  Background, 
  Controls, 
  MiniMap, 
  useNodesState, 
  useEdgesState,
  Connection,
  Edge,
  Node,
  BackgroundVariant
} from 'reactflow';
import 'reactflow/dist/style.css';
import { LLMNode } from './nodes/LLMNode';
import { ConditionNode } from './nodes/ConditionNode';
import { cn } from '@/lib/utils';

const initialNodes: Node[] = [
  { 
    id: '1', 
    type: 'llm', 
    position: { x: 100, y: 100 }, 
    data: { prompt: 'You are a professional copywriter...' } 
  },
  { 
    id: '2', 
    type: 'condition', 
    position: { x: 500, y: 150 }, 
    data: {} 
  },
];

const initialEdges: Edge[] = [
  { id: 'e1-2', source: '1', target: '2', animated: true },
];

export const WorkflowCanvas = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const nodeTypes = useMemo(() => ({
    llm: LLMNode,
    condition: ConditionNode,
  }), []);

  const onConnect = useCallback((params: Connection) => {
    setEdges((eds) => addEdge({ ...params, animated: true, style: { stroke: '#3b82f6', strokeWidth: 2 } }, eds));
  }, [setEdges]);

  return (
    <div className="w-full h-full bg-background rounded-3xl overflow-hidden border border-border relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        className="bg-zinc-950/50"
      >
        <Background color="#333" gap={20} variant={BackgroundVariant.Dots} />
        <Controls className="bg-card border-border fill-foreground" />
        <MiniMap 
          className="bg-card border-border border rounded-xl overflow-hidden" 
          maskColor="rgba(0,0,0,0.5)"
          nodeColor={(node) => {
            if (node.type === 'llm') return '#3b82f6';
            if (node.type === 'condition') return '#eab308';
            return '#333';
          }}
        />
      </ReactFlow>
      
      {/* Top Toolbar */}
      <div className="absolute top-6 left-6 flex items-center gap-3 z-10">
        <div className="glass px-4 py-2 rounded-xl flex items-center gap-4 shadow-2xl">
          <div className="flex items-center gap-2 pr-4 border-r border-white/10">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-[10px] font-bold uppercase text-muted-foreground whitespace-nowrap">Auto-save: ON</span>
          </div>
          <div className="flex items-center gap-2">
             <button className="p-1 px-3 bg-primary text-primary-foreground text-[10px] font-bold rounded-lg hover:bg-primary/90 transition-all">PUBLISH</button>
             <button className="p-1 px-3 bg-secondary text-secondary-foreground text-[10px] font-bold rounded-lg hover:bg-secondary/80 transition-all">DEBUG</button>
          </div>
        </div>
      </div>

      {/* Node Catalog Sidebar (Overlay) */}
      <div className="absolute top-1/2 -translate-y-1/2 right-6 w-48 space-y-4 z-10 pointer-events-none">
         <div className="glass p-4 rounded-3xl space-y-4 pointer-events-auto border-white/5 shadow-2xl">
            <h4 className="text-[10px] font-bold text-muted-foreground uppercase text-center border-b border-white/5 pb-2">Node Catalog</h4>
            <div className="space-y-2">
               {['LLM', 'Condition', 'HTTP', 'Tool', 'Loop'].map(type => (
                 <div key={type} className="p-3 bg-background/50 rounded-xl border border-white/5 flex items-center gap-3 cursor-grab active:cursor-grabbing hover:bg-accent transition-all group">
                    <div className={cn("w-2 h-2 rounded-full", 
                      type === 'LLM' ? 'bg-primary' : type === 'Condition' ? 'bg-yellow-500' : 'bg-muted-foreground'
                    )} />
                    <span className="text-[10px] font-bold">{type}</span>
                 </div>
               ))}
            </div>
         </div>
      </div>
    </div>
  );
};
