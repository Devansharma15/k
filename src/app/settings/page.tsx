"use client";

import React, { useState } from 'react';
import { 
  User, 
  Key, 
  Users, 
  CreditCard, 
  Bell, 
  Shield, 
  Mail,
  MoreVertical,
  Plus,
  Eye,
  EyeOff,
  Copy,
  Trash2,
  ExternalLink,
  ChevronRight
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

const tabs = [
  { id: 'profile', label: 'Profile', icon: User },
  { id: 'api', label: 'API Keys', icon: Key },
  { id: 'team', label: 'Team', icon: Users },
  { id: 'billing', label: 'Billing', icon: CreditCard },
  { id: 'security', label: 'Security', icon: Shield },
];

const apiKeys = [
  { name: 'Production_Frontend', key: 'af_live_••••••••••••••••3a', created: '2 months ago', lastUsed: '3m ago' },
  { name: 'Dev_Testing', key: 'af_test_••••••••••••••••9c', created: '1 week ago', lastUsed: '6h ago' },
];

const members = [
  { name: 'John Doe', email: 'john@aura.flow', role: 'Owner', status: 'Active' },
  { name: 'Jane Smith', email: 'jane@aura.flow', role: 'Admin', status: 'Active' },
  { name: 'Robert Wilson', email: 'robert@dev.io', role: 'Developer', status: 'Invite Sent' },
];

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('api');
  const [showKey, setShowKey] = useState<string | null>(null);

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-1">Manage your workspace, API keys, and team preferences.</p>
        </div>
      </div>

      <div className="flex flex-col md:flex-row gap-8">
        {/* Sidebar Tabs */}
        <aside className="w-full md:w-64 space-y-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                "w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all",
                activeTab === tab.id 
                  ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" 
                  : "text-muted-foreground hover:bg-accent hover:text-foreground"
              )}
            >
              <tab.icon size={18} />
              {tab.label}
            </button>
          ))}
        </aside>

        {/* Content Area */}
        <div className="flex-1">
          <AnimatePresence mode="wait">
            {activeTab === 'api' && (
              <motion.div
                key="api"
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="space-y-6"
              >
                <div className="glass-card p-6 rounded-2xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold tracking-tight">Workspace API Keys</h3>
                      <p className="text-xs text-muted-foreground mt-1">Used to authenticate requests from your external applications.</p>
                    </div>
                    <button className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground text-xs font-bold rounded-xl hover:bg-primary/90 transition-all">
                      <Plus size={14} />
                      NEW KEY
                    </button>
                  </div>

                  <div className="space-y-3 pt-4">
                    {apiKeys.map((k) => (
                      <div key={k.name} className="flex items-center justify-between p-4 rounded-xl bg-accent/20 border border-white/5 hover:border-white/10 transition-all group">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-lg bg-background flex items-center justify-center border border-border">
                            <Key size={18} className="text-primary" />
                          </div>
                          <div>
                            <p className="text-sm font-bold tracking-tight">{k.name}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <code className="text-[10px] text-muted-foreground font-mono bg-background px-1.5 py-0.5 rounded border border-border">{k.key}</code>
                              <button className="text-muted-foreground hover:text-foreground"><Copy size={12} /></button>
                              <button className="text-muted-foreground hover:text-foreground"><Eye size={12} /></button>
                            </div>
                          </div>
                        </div>
                        <div className="text-right flex items-center gap-6">
                           <div className="hidden sm:block">
                              <p className="text-[10px] font-bold text-muted-foreground uppercase">Last Used</p>
                              <p className="text-[10px] font-bold mt-1">{k.lastUsed}</p>
                           </div>
                           <button className="p-2 hover:bg-red-500/10 rounded-lg text-muted-foreground hover:text-red-400 transition-colors">
                              <Trash2 size={16} />
                           </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="p-4 rounded-xl border border-dashed border-primary/30 bg-primary/5 space-y-2">
                   <div className="flex items-center gap-2 text-[10px] font-bold text-primary uppercase">
                      <Shield size={12} />
                      Security Note
                   </div>
                   <p className="text-[11px] text-muted-foreground leading-relaxed">
                     Treat your API keys as passwords. Never share them or commit them to version control. AuraFlow will never ask for your full secret key.
                   </p>
                </div>
              </motion.div>
            )}

            {activeTab === 'team' && (
              <motion.div
                key="team"
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="space-y-6"
              >
                <div className="glass-card p-6 rounded-2xl space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-lg font-bold tracking-tight">Team Members</h3>
                      <p className="text-xs text-muted-foreground mt-1">Manage who can access and build in this workspace.</p>
                    </div>
                    <button className="flex items-center gap-2 px-4 py-2 bg-secondary text-secondary-foreground text-xs font-bold rounded-xl hover:bg-secondary/80 transition-all">
                      <Mail size={14} />
                      INVITE MEMBER
                    </button>
                  </div>

                  <div className="divide-y divide-white/5 border-t border-white/5 mt-6">
                    {members.map((m) => (
                      <div key={m.email} className="flex items-center justify-between py-4 group">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-full bg-gradient-to-tr from-primary/20 to-blue-500/20 flex items-center justify-center text-primary font-bold text-xs border border-primary/10">
                            {m.name.split(' ').map(n => n[0]).join('')}
                          </div>
                          <div>
                            <p className="text-sm font-bold tracking-tight">{m.name}</p>
                            <p className="text-[11px] text-muted-foreground">{m.email}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-8">
                           <div className="text-right">
                              <p className="text-[10px] font-bold text-muted-foreground uppercase">Role</p>
                              <p className="text-[11px] font-bold mt-1 text-foreground">{m.role}</p>
                           </div>
                           <div className="text-right hidden sm:block">
                              <p className="text-[10px] font-bold text-muted-foreground uppercase">Status</p>
                              <div className="flex items-center gap-1.5 mt-1 justify-end">
                                 <span className={cn("w-1.5 h-1.5 rounded-full", m.status === 'Active' ? 'bg-emerald-500' : 'bg-yellow-500')} />
                                 <span className="text-[11px] font-bold">{m.status}</span>
                              </div>
                           </div>
                           <button className="p-2 hover:bg-accent rounded-lg text-muted-foreground opacity-0 group-hover:opacity-100 transition-all">
                              <MoreVertical size={16} />
                           </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
            
            {/* Other tabs placeholders would go here */}
            {activeTab === 'profile' && <div className="glass-card p-12 rounded-2xl flex flex-col items-center justify-center text-center">
               <div className="w-20 h-20 rounded-full bg-accent mb-4" />
               <h3 className="font-bold">Profile Settings</h3>
               <p className="text-xs text-muted-foreground">General identity and preference management.</p>
            </div>}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
