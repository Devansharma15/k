"use client";

import { motion } from "framer-motion";
import { Sparkles, ArrowRight, Play, Cpu, Globe, Zap } from "lucide-react";
import Link from "next/link";

export const Hero = () => {
  return (
    <section className="relative pt-32 pb-20 lg:pt-48 lg:pb-32 overflow-hidden">
      {/* Background Gradients */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full -z-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-primary/10 via-background to-background opacity-50" />
      <div className="absolute -top-[10%] -left-[10%] w-[40%] h-[40%] bg-primary/20 rounded-full blur-[120px] -z-10 animate-pulse" />
      <div className="absolute -bottom-[10%] -right-[10%] w-[40%] h-[40%] bg-blue-500/10 rounded-full blur-[120px] -z-10" />

      <div className="container mx-auto px-6 relative">
        <div className="max-w-4xl mx-auto text-center space-y-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-bold uppercase tracking-wider mb-4"
          >
            <Sparkles size={14} />
            The Future of AI Orchestration
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="text-5xl lg:text-7xl font-extrabold tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-white/50"
          >
            Build AI Apps <br className="hidden md:block" /> Without Limits
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-lg lg:text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed"
          >
            AuraFlow lets you create, deploy, and scale AI workflows with powerful RAG, agents, and real-time streaming. Experience the next generation of AI development.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4"
          >
            <Link
              href="/dashboard"
              className="px-8 py-4 bg-primary text-primary-foreground rounded-2xl font-bold flex items-center gap-2 hover:bg-primary/90 transition-all shadow-lg shadow-primary/20 group"
            >
              Get Started
              <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <button className="px-8 py-4 bg-secondary text-secondary-foreground rounded-2xl font-bold flex items-center gap-2 hover:bg-secondary/80 transition-all border border-border group">
              <Play size={18} className="fill-current" />
              View Demo
            </button>
          </motion.div>

          {/* Social Proof / Stats */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 1, delay: 0.5 }}
            className="pt-16 grid grid-cols-2 md:grid-cols-4 gap-8 border-t border-white/5"
          >
            <div>
              <p className="text-2xl font-bold">10k+</p>
              <p className="text-xs text-muted-foreground uppercase font-bold tracking-widest mt-1">Users</p>
            </div>
            <div>
              <p className="text-2xl font-bold">1M+</p>
              <p className="text-xs text-muted-foreground uppercase font-bold tracking-widest mt-1">Executions</p>
            </div>
            <div>
              <p className="text-2xl font-bold">99.9%</p>
              <p className="text-xs text-muted-foreground uppercase font-bold tracking-widest mt-1">Uptime</p>
            </div>
            <div>
              <p className="text-2xl font-bold">50+</p>
              <p className="text-xs text-muted-foreground uppercase font-bold tracking-widest mt-1">Models</p>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
