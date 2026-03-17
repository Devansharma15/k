"use client";

import React from 'react';
import { 
  Plus, 
  Search, 
  FileText, 
  Database, 
  Download, 
  MoreVertical,
  Table as TableIcon,
  Globe,
  UploadCloud,
  CheckCircle2,
  Clock,
  AlertCircle,
  Settings
} from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

const datasets = [
  { id: 1, name: 'Customer_Base_Q3', type: 'PDF/TXT', documents: 142, size: '42.5 MB', status: 'Ready', updated: '2 hours ago' },
  { id: 2, name: 'Product_Catalog_2026', type: 'JSON/CSV', documents: 12, size: '156.2 MB', status: 'Indexing', updated: '15m ago' },
  { id: 3, name: 'Legal_Compliance_Docs', type: 'Folder', documents: 89, size: '12.1 GB', status: 'Error', updated: 'Yesterday' },
  { id: 4, name: 'Support_Hallucinations_Log', type: 'API Sync', documents: 1045, size: '2.4 MB', status: 'Ready', updated: '3 days ago' },
];

export default function KnowledgeBasePage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Knowledge Base</h1>
          <p className="text-muted-foreground mt-1">Manage and sync your data sources for RAG-enabled applications.</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-2.5 bg-primary text-primary-foreground rounded-xl font-bold hover:bg-primary/90 transition-all shadow-lg shadow-primary/20">
          <UploadCloud size={18} />
          Create Dataset
        </button>
      </div>

      {/* RAG Stats Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-card p-4 rounded-xl flex items-center gap-4">
           <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center text-blue-500">
              <Database size={20} />
           </div>
           <div>
              <p className="text-[10px] font-bold text-muted-foreground uppercase">Total Storage</p>
              <p className="text-lg font-bold">14.8 GB</p>
           </div>
        </div>
        <div className="glass-card p-4 rounded-xl flex items-center gap-4">
           <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center text-emerald-500">
              <FileText size={20} />
           </div>
           <div>
              <p className="text-[10px] font-bold text-muted-foreground uppercase">Indexed Chunks</p>
              <p className="text-lg font-bold">1.2M</p>
           </div>
        </div>
        <div className="glass-card p-4 rounded-xl flex items-center gap-4">
           <div className="w-10 h-10 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-500">
              <RefreshCw size={20} className="animate-spin-slow" />
           </div>
           <div>
              <p className="text-[10px] font-bold text-muted-foreground uppercase">Active Syncs</p>
              <p className="text-lg font-bold">12 sources</p>
           </div>
        </div>
      </div>

      <div className="glass-card rounded-2xl overflow-hidden border border-white/5">
        <div className="p-4 border-b border-white/5 flex items-center justify-between bg-background/30">
          <div className="relative w-64 group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground w-4 h-4 group-focus-within:text-primary transition-colors" />
            <input 
              type="text" 
              placeholder="Search datasets..." 
              className="w-full bg-accent/50 border-none rounded-lg py-1.5 pl-10 text-xs focus:ring-1 focus:ring-primary/30 outline-none"
            />
          </div>
          <div className="flex gap-2">
            <button className="p-1.5 hover:bg-accent rounded-lg text-muted-foreground"><Download size={16} /></button>
            <button className="p-1.5 hover:bg-accent rounded-lg text-muted-foreground"><Settings size={16} /></button>
          </div>
        </div>
        
        <table className="w-full text-left">
          <thead>
            <tr className="bg-background/20 text-[10px] font-bold text-muted-foreground uppercase tracking-wider border-b border-white/5">
              <th className="px-6 py-4">Dataset Name</th>
              <th className="px-6 py-4">Type</th>
              <th className="px-6 py-4">Documents</th>
              <th className="px-6 py-4">Size</th>
              <th className="px-6 py-4">Status</th>
              <th className="px-6 py-4 text-right">Updated</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {datasets.map((ds, i) => (
              <motion.tr 
                key={ds.id}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: i * 0.05 }}
                className="hover:bg-accent/20 transition-all group cursor-pointer"
              >
                <td className="px-6 py-4">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-accent/50 flex items-center justify-center border border-white/5 group-hover:bg-primary/10 transition-colors">
                      {ds.name.includes('Legal') ? <FileText size={16} className="text-purple-400" /> : 
                       ds.name.includes('API') ? <Globe size={16} className="text-emerald-400" /> :
                       <Database size={16} className="text-blue-400" />}
                    </div>
                    <span className="text-sm font-semibold tracking-tight">{ds.name}</span>
                  </div>
                </td>
                <td className="px-6 py-4 text-xs text-muted-foreground font-medium">{ds.type}</td>
                <td className="px-6 py-4 text-xs font-bold">{ds.documents}</td>
                <td className="px-6 py-4 text-xs text-muted-foreground">{ds.size}</td>
                <td className="px-6 py-4">
                   <div className={cn(
                     "inline-flex items-center gap-1.5 px-2 py-1 rounded-lg text-[9px] font-bold uppercase",
                     ds.status === 'Ready' ? "bg-emerald-500/10 text-emerald-500 border border-emerald-500/20" :
                     ds.status === 'Indexing' ? "bg-blue-500/10 text-blue-500 border border-blue-500/20" :
                     "bg-red-500/10 text-red-500 border border-red-500/20"
                   )}>
                      {ds.status === 'Ready' && <CheckCircle2 size={10} />}
                      {ds.status === 'Indexing' && <Clock size={10} className="animate-pulse" />}
                      {ds.status === 'Error' && <AlertCircle size={10} />}
                      {ds.status}
                   </div>
                </td>
                <td className="px-6 py-4 text-right text-[10px] font-bold text-muted-foreground">{ds.updated}</td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const RefreshCw = ({ size, className }: { size: number, className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" /><path d="M21 3v5h-5" /><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" /><path d="M3 21v-5h5" />
  </svg>
);
