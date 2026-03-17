"use client";

import React, { useState } from 'react';
import { 
  Play, 
  Settings, 
  Sliders, 
  Terminal,
  ChevronRight,
  Database,
  Trash2,
  Sparkles,
  Zap,
  MessageSquare,
  Cpu
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

export default function PlaygroundPage() {
  const [prompt, setPrompt] = useState('Write a high-converting landing page headline for a new AI-powered task management app.');
  const [outputs, setOutputs] = useState([
    { id: 1, model: 'Claude 3.5 Sonnet', content: 'Transform Your Productivity: The Only Task Manager Powered by Generative Intelligence.', tokens: 142, latency: '1.2s' },
    { id: 2, model: 'GPT-4o', content: 'Work Smarter, Not Harder. Experience the Future of Task Management with AuraFlow AI.', tokens: 156, latency: '0.8s' },
  ]);
  const [isPrimeLoading, setIsPrimeLoading] = useState(false);

  const handleRun = () => {
    setIsPrimeLoading(true);
    setTimeout(() => {
      setIsPrimeLoading(false);
      // Mock update
    }, 2000);
  };

  return (
    <div className="flex h-screen -m-8 overflow-hidden">
      {/* Left Settings Sidebar */}
      <div className="w-80 border-r border-border bg-card/20 backdrop-blur-md p-6 overflow-y-auto space-y-8 hidden lg:block">
        <div className="space-y-4">
          <div className="flex items-center gap-2 text-sm font-bold tracking-tight">
            <Sliders size={18} className="text-primary" />
            Global Parameters
          </div>
          <div className="space-y-4 pt-2">
             <div className="space-y-2">
                <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Default Context</label>
                <select className="w-full bg-accent/50 border border-border rounded-lg p-2 text-xs outline-none focus:ring-1 focus:ring-primary/40">
                  <option>Customer_Support_v2</option>
                  <option>Product_Docs_Q4</option>
                </select>
             </div>
             <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">Top-P</label>
                  <span className="text-[10px] font-bold">0.9</span>
                </div>
                <input type="range" className="w-full h-1 bg-accent rounded-lg appearance-none cursor-pointer accent-primary" min="0" max="1" step="0.05" defaultValue="0.9" />
             </div>
          </div>
        </div>

        <div className="h-px bg-border" />

        <div className="space-y-4">
           <div className="flex items-center gap-2 text-sm font-bold tracking-tight">
              <Zap size={18} className="text-yellow-500" />
              Dynamic Tools
           </div>
           <div className="space-y-2">
              <div className="flex items-center justify-between p-3 rounded-xl bg-accent/30 border border-white/5 hover:border-primary/20 transition-all cursor-pointer">
                 <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
                    <span className="text-xs font-medium">Web Search</span>
                 </div>
                 <div className="w-8 h-4 bg-primary rounded-full relative"><div className="absolute right-1 top-1 w-2 h-2 bg-white rounded-full" /></div>
              </div>
              <div className="flex items-center justify-between p-3 rounded-xl bg-accent/30 border border-white/5 opacity-50">
                 <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-red-500" />
                    <span className="text-xs font-medium">Interpreter</span>
                 </div>
                 <div className="w-8 h-4 bg-zinc-700 rounded-full relative"><div className="absolute left-1 top-1 w-2 h-2 bg-white rounded-full" /></div>
              </div>
           </div>
        </div>
      </div>

      {/* Main Workspace */}
      <div className="flex-1 flex flex-col min-w-0 bg-background/50">
         {/* Top Bar */}
         <div className="h-14 border-b border-border flex items-center justify-between px-8 bg-background/80 backdrop-blur-sm shrink-0">
            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
              <span>Playground</span>
              <ChevronRight size={12} />
              <span className="text-foreground">Marketing_Copy_Compare</span>
            </div>
            <div className="flex items-center gap-3">
               <button className="p-2 hover:bg-accent rounded-lg text-muted-foreground transition-all"><Trash2 size={16} /></button>
               <button 
                 onClick={handleRun}
                 disabled={isPrimeLoading}
                 className="flex items-center gap-2 px-6 py-1.5 bg-primary text-primary-foreground text-xs font-bold rounded-xl hover:bg-primary/90 transition-all shadow-lg shadow-primary/20"
               >
                 {isPrimeLoading ? <div className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" /> : <Play size={14} />}
                 EXECUTE COMPARISON
               </button>
            </div>
         </div>

         {/* Content Area */}
         <div className="flex-1 overflow-y-auto p-8 space-y-8">
            <section className="space-y-4">
               <div className="flex items-center gap-2 text-sm font-bold tracking-tight">
                  <Terminal size={18} className="text-emerald-500" />
                  Prompt Sandbox
               </div>
               <div className="glass shadow-2xl rounded-3xl border border-white/5 overflow-hidden">
                  <textarea 
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    className="w-full h-40 bg-card/20 p-6 text-sm font-medium outline-none resize-none focus:bg-card/40 transition-all leading-relaxed"
                    placeholder="Enter your experiment prompt here..."
                  />
                  <div className="px-6 py-3 bg-background/50 border-t border-white/5 flex items-center justify-between">
                     <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1 text-[9px] font-bold text-muted-foreground uppercase">
                           <MessageSquare size={12} />
                           Tokens: {prompt.length}
                        </div>
                        <div className="flex items-center gap-1 text-[9px] font-bold text-muted-foreground uppercase">
                           <Database size={12} />
                           Context: Active
                        </div>
                     </div>
                     <span className="text-[9px] font-bold text-primary italic">CTRL + ENTER to run</span>
                  </div>
               </div>
            </section>

            <section className="space-y-4 flex-1 flex flex-col">
               <div className="flex items-center gap-2 text-sm font-bold tracking-tight">
                  <Sparkles size={18} className="text-primary" />
                  Model Comparison
               </div>
               
               <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1">
                  {outputs.map((out) => (
                    <div key={out.id} className="glass-card flex flex-col rounded-3xl overflow-hidden min-h-[300px]">
                       <div className="p-4 border-b border-white/5 flex items-center justify-between bg-background/40">
                          <div className="flex items-center gap-3">
                             <div className="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center border border-primary/20">
                                <Cpu size={16} className="text-primary" />
                             </div>
                             <span className="text-xs font-bold">{out.model}</span>
                          </div>
                          <div className="text-[9px] font-bold text-muted-foreground uppercase tracking-tighter">
                             {out.latency} • {out.tokens} Tokens
                          </div>
                       </div>
                       <div className="p-6 flex-1 text-sm leading-relaxed text-muted-foreground overflow-y-auto scrollbar-hide">
                          <div className="prose prose-invert prose-sm">
                             <ReactMarkdown>
                                {out.content}
                             </ReactMarkdown>
                          </div>
                       </div>
                       <div className="px-6 py-3 bg-background/20 border-t border-white/5 flex gap-4">
                          <button className="text-[9px] font-bold uppercase text-primary hover:underline">Copy Response</button>
                          <button className="text-[9px] font-bold uppercase text-muted-foreground hover:text-foreground">View Trace</button>
                       </div>
                    </div>
                  ))}
               </div>
            </section>
         </div>
      </div>
    </div>
  );
}
