"use client";

import React from 'react';
import { 
  Search, 
  Filter, 
  ArrowUpDown, 
  ExternalLink,
  CheckCircle2,
  AlertCircle,
  Clock,
  ChevronRight,
  Database,
  Cpu,
  MoreHorizontal
} from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

const logs = [
  { id: 'tr_4a29', app: 'Support Bot', model: 'GPT-4o', status: 'Success', tokens: 842, latency: '1.4s', time: '2m ago' },
  { id: 'tr_91b2', app: 'Lead Gen Flow', model: 'Claude 3.5', status: 'Success', tokens: 1250, latency: '2.8s', time: '12m ago' },
  { id: 'tr_cc88', app: 'Support Bot', model: 'GPT-4o Mini', status: 'Error', tokens: 0, latency: '0.2s', time: '1h ago' },
  { id: 'tr_d441', app: 'Data Extractor', model: 'Llama 3', status: 'Success', tokens: 412, latency: '0.9s', time: '2h ago' },
  { id: 'tr_bb20', app: 'Support Bot', model: 'GPT-4o', status: 'Success', tokens: 2104, latency: '3.1s', time: '4h ago' },
];

export default function LogsPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Execution Logs</h1>
          <p className="text-muted-foreground mt-1">Real-time trace monitoring and observability for your AI applications.</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-accent text-accent-foreground rounded-xl text-xs font-bold border border-border hover:bg-accent/80 transition-all">
             <Filter size={14} />
             FILTER
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-xl text-xs font-bold border border-border hover:bg-secondary/80 transition-all">
             EXPORT JSON
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
         {[
           { label: 'Total Requests', value: '42,910', color: 'text-foreground' },
           { label: 'Avg Latency', value: '1.24s', color: 'text-blue-400' },
           { label: 'Success Rate', value: '99.8%', color: 'text-emerald-400' },
           { label: 'Cost (MTD)', value: '$142.50', color: 'text-purple-400' },
         ].map(stat => (
           <div key={stat.label} className="glass-card p-4 rounded-xl text-center">
              <p className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">{stat.label}</p>
              <p className={cn("text-xl font-bold mt-1", stat.color)}>{stat.value}</p>
           </div>
         ))}
      </div>

      <div className="glass-card rounded-2xl overflow-hidden shadow-2xl border border-white/5">
        <div className="p-4 bg-background/30 border-b border-white/5 flex items-center justify-between">
          <div className="flex items-center gap-4">
             <div className="relative group w-64">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4 group-focus-within:text-primary" />
                <input 
                  type="text" 
                  placeholder="Search Trace ID or App Name..." 
                  className="w-full bg-accent/50 border-none rounded-lg py-1.5 pl-10 text-xs focus:ring-1 focus:ring-primary/20 outline-none"
                />
             </div>
             <div className="h-4 w-px bg-border" />
             <div className="flex gap-2">
                {['LAST 24H', 'SUCCESS', 'ERRORS'].map(t => (
                  <button key={t} className="px-3 py-1 bg-accent/30 hover:bg-accent text-[9px] font-bold rounded-lg border border-white/5 transition-all">
                    {t}
                  </button>
                ))}
             </div>
          </div>
          <p className="text-[10px] font-bold text-muted-foreground uppercase">Showing 5 of 4,291 traces</p>
        </div>

        <table className="w-full text-left">
          <thead>
            <tr className="bg-background/20 text-[10px] font-bold text-muted-foreground uppercase tracking-wider border-b border-white/5">
              <th className="px-6 py-4">Trace ID</th>
              <th className="px-6 py-4">Application</th>
              <th className="px-6 py-4">Model</th>
              <th className="px-6 py-4">Tokens</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Time</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {logs.map((log, i) => (
              <motion.tr 
                key={log.id}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="hover:bg-accent/20 transition-all group cursor-pointer"
              >
                <td className="px-6 py-4">
                  <span className="text-xs font-mono text-primary font-bold">{log.id}</span>
                </td>
                <td className="px-6 py-4">
                  <div className="flex items-center gap-2">
                    <div className="w-6 h-6 rounded bg-accent flex items-center justify-center border border-white/5">
                      <Cpu size={12} className="text-muted-foreground group-hover:text-primary transition-colors" />
                    </div>
                    <span className="text-xs font-semibold">{log.app}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-xs font-medium text-muted-foreground">{log.model}</td>
                <td className="px-6 py-4">
                   <div className="flex flex-col">
                      <span className="text-xs font-bold">{log.tokens}</span>
                      <span className="text-[9px] text-muted-foreground font-bold uppercase">{log.latency}</span>
                   </div>
                </td>
                <td className="px-6 py-4">
                  <div className={cn(
                    "inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[9px] font-bold uppercase border",
                    log.status === 'Success' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-red-500/10 text-red-500 border-red-500/20"
                  )}>
                    {log.status === 'Success' ? <CheckCircle2 size={10} /> : <AlertCircle size={10} />}
                    {log.status}
                  </div>
                </td>
                <td className="px-6 py-4 text-right">
                   <div className="flex items-center justify-end gap-3 text-muted-foreground">
                      <span className="text-[10px] font-bold uppercase tracking-widest">{log.time}</span>
                      <button className="hover:text-primary transition-colors"><ExternalLink size={14} /></button>
                   </div>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
        
        <div className="p-4 bg-background/20 text-center border-t border-white/5">
           <button className="text-[10px] font-bold text-muted-foreground uppercase hover:text-primary transition-colors">Load More Traces</button>
        </div>
      </div>
    </div>
  );
}
