"use client";

import React from 'react';
import { 
  Zap, 
  Users, 
  Cpu, 
  Activity, 
  ArrowUpRight,
  Plus,
  Rocket
} from 'lucide-react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

const stats = [
  { name: 'Total Apps', value: '12', icon: Cpu, trend: '+2 this month', color: 'text-blue-500' },
  { name: 'Active Workflows', value: '8', icon: Zap, trend: '+1 today', color: 'text-yellow-500' },
  { name: 'Total Tokens', value: '1.2M', icon: Activity, trend: '85% of limit', color: 'text-emerald-500' },
  { name: 'Team Size', value: '5', icon: Users, trend: 'Professional Plan', color: 'text-purple-500' },
];

const activities = [
  { id: 1, type: 'app', name: 'Customer Support Bot', action: 'deployed to production', time: '2 hours ago' },
  { id: 2, type: 'workflow', name: 'Lead Gen Pipeline', action: 'updated logic', time: '4 hours ago' },
  { id: 3, type: 'model', name: 'GPT-4o Mini', action: 'selected for testing', time: 'Yesterday' },
];

export default function DashboardPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Welcome back, John!</h1>
          <p className="text-muted-foreground mt-1">Here is what's happening with your AI projects today.</p>
        </div>
        <div className="flex gap-3">
          <button className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground rounded-xl font-medium hover:bg-secondary/80 transition-all">
            <Plus size={18} />
            Quick Action
          </button>
          <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-xl font-medium hover:bg-primary/90 transition-all shadow-lg shadow-primary/20">
            <Rocket size={18} />
            New App
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <motion.div
            key={stat.name}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass-card p-6 rounded-2xl relative overflow-hidden group"
          >
            <div className="flex items-center justify-between">
              <div className={cn("p-2 rounded-lg bg-background/50", stat.color)}>
                <stat.icon size={20} />
              </div>
              <ArrowUpRight size={16} className="text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
            <div className="mt-4">
              <p className="text-sm text-muted-foreground font-medium">{stat.name}</p>
              <h3 className="text-2xl font-bold mt-1">{stat.value}</h3>
              <p className="text-[10px] uppercase tracking-wider font-bold text-muted-foreground mt-2">{stat.trend}</p>
            </div>
            {/* Subtle background glow */}
            <div className={cn("absolute -right-4 -bottom-4 w-24 h-24 blur-3xl opacity-10 group-hover:opacity-20 transition-opacity", stat.color.replace('text', 'bg'))} />
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-6 rounded-2xl h-[400px] flex flex-col">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-bold">Usage Analytics</h2>
              <div className="flex gap-2">
                {['24h', '7d', '30d'].map(t => (
                  <button key={t} className="px-3 py-1 text-xs rounded-lg hover:bg-accent transition-all uppercase font-bold text-muted-foreground hover:text-foreground">
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex-1 flex items-center justify-center border-t border-border mt-auto pt-4">
              <p className="text-muted-foreground text-sm italic">Analytics visualization loading...</p>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="glass-card p-6 rounded-2xl h-full">
            <h2 className="text-xl font-bold mb-6">Recent Activity</h2>
            <div className="space-y-6">
              {activities.map((act) => (
                <div key={act.id} className="flex gap-4 relative">
                  <div className="w-10 h-10 rounded-xl bg-accent/50 flex items-center justify-center shrink-0 border border-white/5">
                    {act.type === 'app' ? <MessageSquare size={16} className="text-blue-400" /> : 
                     act.type === 'workflow' ? <Workflow size={16} className="text-yellow-400" /> :
                     <Cpu size={16} className="text-emerald-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold truncate">{act.name}</p>
                    <p className="text-xs text-muted-foreground mt-0.5">{act.action}</p>
                    <p className="text-[10px] text-muted-foreground font-bold uppercase tracking-tighter mt-2">{act.time}</p>
                  </div>
                </div>
              ))}
            </div>
            <button className="w-full mt-8 py-2 text-xs font-bold text-muted-foreground hover:text-foreground transition-colors border border-dashed border-border rounded-lg hover:bg-accent/50">
              View All Logs
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Simple icons for activity mapping
const MessageSquare = ({ size, className }: { size: number, className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
  </svg>
);

const Workflow = ({ size, className }: { size: number, className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="3" y="3" width="7" height="7" />
    <rect x="14" y="3" width="7" height="7" />
    <rect x="14" y="14" width="7" height="7" />
    <rect x="3" y="14" width="7" height="7" />
  </svg>
);
