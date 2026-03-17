"use client";

import { motion } from "framer-motion";
import { Cpu, MessageSquare, Workflow, Database } from "lucide-react";

export const DashboardPreview = () => {
  return (
    <section className="py-24 bg-background overflow-hidden">
      <div className="container mx-auto px-6">
        <div className="max-w-3xl mx-auto text-center mb-16 space-y-4">
          <h2 className="text-3xl lg:text-5xl font-bold tracking-tight">Built for Performance</h2>
          <p className="text-muted-foreground text-lg">A production-grade interface that keeps you in the flow.</p>
        </div>

        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.7 }}
          className="relative max-w-6xl mx-auto glass-card rounded-[32px] border border-white/10 shadow-[0_0_80px_rgba(59,130,246,0.15)] overflow-hidden aspect-[16/10]"
        >
          {/* Mock Dashboard UI */}
          <div className="absolute inset-0 bg-background/50 flex flex-col">
            {/* Header */}
            <div className="h-14 border-b border-white/5 flex items-center justify-between px-6 shrink-0 bg-background/80">
              <div className="flex gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500/50" />
                <div className="w-3 h-3 rounded-full bg-yellow-500/50" />
                <div className="w-3 h-3 rounded-full bg-emerald-500/50" />
              </div>
              <div className="w-1/3 h-5 bg-accent/50 rounded-lg" />
              <div className="w-10 h-10 bg-accent rounded-full" />
            </div>
            
            <div className="flex-1 flex overflow-hidden">
              {/* Sidebar */}
              <div className="w-20 lg:w-48 border-r border-white/5 flex flex-col p-4 space-y-4 bg-background/30">
                 {[MessageSquare, Workflow, Database, Cpu].map((Icon, i) => (
                   <div key={i} className={`h-10 rounded-xl ${i === 0 ? 'bg-primary/20 border-primary/20 border' : 'bg-transparent'} flex items-center px-4 gap-3`}>
                      <Icon className={i === 0 ? "text-primary" : "text-muted-foreground"} size={18} />
                      <div className={`hidden lg:block h-3 rounded bg-current opacity-20 w-full`} />
                   </div>
                 ))}
              </div>
              
              {/* Main Content */}
              <div className="flex-1 p-8 grid grid-cols-3 gap-6">
                <div className="col-span-2 space-y-6">
                   <div className="h-48 rounded-3xl bg-accent/20 border border-white/5 relative overflow-hidden p-6">
                      <div className="w-1/4 h-6 bg-primary/20 rounded-lg mb-4" />
                      <div className="space-y-2">
                        <div className="w-full h-3 bg-white/5 rounded" />
                        <div className="w-5/6 h-3 bg-white/5 rounded" />
                        <div className="w-4/6 h-3 bg-white/5 rounded" />
                      </div>
                      {/* Animated Line Graph */}
                      <div className="absolute bottom-0 left-0 w-full h-1/2 flex items-end">
                         <motion.div 
                           animate={{ height: ['40%', '60%', '45%', '80%', '55%'] }}
                           transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
                           className="w-full bg-gradient-to-t from-primary/20 to-transparent border-t-2 border-primary/50" 
                         />
                      </div>
                   </div>
                   <div className="grid grid-cols-2 gap-6">
                      <div className="h-32 rounded-2xl bg-accent/10 border border-white/5 p-4">
                         <div className="w-1/2 h-4 bg-emerald-500/20 rounded" />
                         <div className="h-10 mt-4 flex items-end gap-1">
                            {[4, 7, 2, 9, 5].map((h, i) => <div key={i} style={{ height: `${h * 10}%` }} className="w-full bg-emerald-500/20 rounded-t-sm" />)}
                         </div>
                      </div>
                      <div className="h-32 rounded-2xl bg-accent/10 border border-white/5 p-4">
                         <div className="w-1/2 h-4 bg-purple-500/20 rounded" />
                         <div className="h-10 mt-4 flex items-end gap-1">
                            {[6, 3, 8, 4, 7].map((h, i) => <div key={i} style={{ height: `${h * 10}%` }} className="w-full bg-purple-500/20 rounded-t-sm" />)}
                         </div>
                      </div>
                   </div>
                </div>
                <div className="col-span-1 rounded-3xl bg-accent/5 border border-white/5 p-6 flex flex-col space-y-4">
                   <div className="w-full h-4 bg-white/10 rounded" />
                   <div className="flex-1 space-y-4 pt-4">
                      {[1, 2, 3, 4].map(i => (
                        <div key={i} className="flex gap-3">
                           <div className="w-8 h-8 rounded bg-white/5" />
                           <div className="flex-1 space-y-2">
                              <div className="w-full h-2 bg-white/5 rounded" />
                              <div className="w-1/2 h-2 bg-white/5 rounded" />
                           </div>
                        </div>
                      ))}
                   </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
