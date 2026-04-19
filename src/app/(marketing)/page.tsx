"use client";

import React from "react";
import { motion } from "framer-motion";
import { 
  ChevronRight, 
  Play, 
  Terminal, 
  Workflow, 
  Activity, 
  Cpu, 
  Code, 
  ArrowRight,
  ShieldCheck,
  Zap,
  Globe,
  Database
} from "lucide-react";
import Link from "next/link";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6 } }
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1
    }
  }
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#0a0a0c] text-slate-200 selection:bg-indigo-500/30 overflow-hidden font-sans">
      {/* Navigation */}
      <nav className="fixed top-0 inset-x-0 z-50 border-b border-white/5 bg-[#0a0a0c]/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-500 flex items-center justify-center">
              <Workflow className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-semibold text-white tracking-tight">AuraFlow</span>
          </div>
          <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-400">
            <a href="#features" className="hover:text-white transition-colors">Features</a>
            <a href="#developers" className="hover:text-white transition-colors">Developers</a>
            <a href="#use-cases" className="hover:text-white transition-colors">Use Cases</a>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="text-sm font-medium hover:text-white transition-colors hidden sm:block">
              Log In
            </Link>
            <Link 
              href="/dashboard"
              className="text-sm font-medium bg-white text-black px-4 py-2 rounded-full hover:bg-slate-200 transition-colors"
            >
              Start Building
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 md:pt-48 md:pb-32 px-6">
        {/* Background glow effects */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/20 rounded-full blur-[120px] pointer-events-none" />
        
        <div className="max-w-5xl mx-auto text-center relative z-10">
          <motion.div
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="flex flex-col items-center"
          >
            <motion.div variants={fadeIn} className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-xs font-medium text-indigo-300 mb-8 backdrop-blur-sm">
              <Zap className="w-3 h-3" />
              <span>AuraFlow 2.0 is now available</span>
            </motion.div>
            
            <motion.h1 variants={fadeIn} className="text-5xl md:text-7xl font-bold text-white tracking-tight leading-[1.1] mb-6">
              Design, Validate, and Run <br className="hidden md:block"/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-indigo-400 to-cyan-400">
                Powerful Workflows Visually
              </span>
            </motion.h1>
            
            <motion.p variants={fadeIn} className="text-lg md:text-xl text-slate-400 max-w-3xl mb-10 leading-relaxed">
              AuraFlow is the developer-first workflow automation platform. Connect third-party services via secure OAuth, design custom logic on a node-based canvas, and let our FastAPI execution engine handle the rest.
            </motion.p>
            
            <motion.div variants={fadeIn} className="flex flex-col sm:flex-row items-center gap-4">
              <Link
                href="/dashboard"
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-white text-black font-semibold hover:bg-slate-200 transition-all active:scale-95 w-full sm:w-auto"
              >
                Start Building <ChevronRight className="w-4 h-4" />
              </Link>
              <button
                className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full bg-white/5 text-white font-medium hover:bg-white/10 border border-white/10 transition-all active:scale-95 w-full sm:w-auto backdrop-blur-sm"
              >
                <Play className="w-4 h-4" /> View Demo
              </button>
            </motion.div>
          </motion.div>
        </div>
      </section>

      {/* Product Visualization: Code-based decorative visual */}
      <section className="relative px-6 pb-32">
        <div className="max-w-6xl mx-auto relative rounded-2xl border border-white/10 bg-[#0a0a0c] shadow-2xl overflow-hidden">
          {/* Mac-like header */}
          <div className="h-12 border-b border-white/10 bg-white/5 flex items-center px-4 gap-2">
            <div className="w-3 h-3 rounded-full bg-rose-500/80" />
            <div className="w-3 h-3 rounded-full bg-amber-500/80" />
            <div className="w-3 h-3 rounded-full bg-emerald-500/80" />
            <div className="ml-4 text-xs font-mono text-slate-500 flex items-center gap-2">
              <Code className="w-3 h-3" /> AuraFlow Workflow Editor
            </div>
          </div>
          
          <div className="h-[400px] md:h-[600px] relative bg-grid-white/[0.02] overflow-hidden flex items-center justify-center bg-[#050505]">
            <svg className="absolute inset-0 w-full h-full stroke-white/5" style={{ backgroundSize: '40px 40px', backgroundImage: 'linear-gradient(to right, rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(255,255,255,0.05) 1px, transparent 1px)' }} />
            
            {/* Abstract Workflow Presentation */}
            <div className="relative w-full max-w-3xl flex flex-col md:flex-row items-center justify-center gap-8 md:gap-16 z-10 px-4">
              {/* Trigger Node */}
              <motion.div 
                initial={{ opacity: 0, x: -50 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                className="w-full md:w-64 flex flex-col bg-slate-900 border border-indigo-500/30 rounded-xl overflow-hidden shadow-xl shadow-indigo-500/10"
              >
                <div className="bg-indigo-500/10 border-b border-indigo-500/20 px-4 py-2 flex items-center gap-2">
                  <Globe className="w-4 h-4 text-indigo-400" />
                  <span className="text-sm font-medium text-indigo-100">Webhook Trigger</span>
                </div>
                <div className="p-4 bg-slate-900/50">
                  <div className="text-xs text-slate-400 mb-2">POST /api/v1/webhook</div>
                  <div className="h-2 w-3/4 bg-slate-800 rounded mb-2"></div>
                  <div className="h-2 w-1/2 bg-slate-800 rounded"></div>
                </div>
              </motion.div>

              {/* Connecting Line (Desktop) */}
              <div className="hidden md:block absolute top-1/2 left-1/4 right-1/4 h-0.5 bg-indigo-500/30 -z-10 flex items-center">
                <motion.div 
                  initial={{ left: '0%' }}
                  animate={{ left: '100%' }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                  className="absolute w-2 h-2 rounded-full bg-indigo-400 shadow-[0_0_10px_#818cf8]"
                />
              </div>

              {/* Processing Node */}
              <motion.div 
                initial={{ opacity: 0, y: 50 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.2 }}
                className="w-full md:w-64 flex flex-col bg-slate-900 border border-emerald-500/30 rounded-xl overflow-hidden shadow-xl shadow-emerald-500/10"
              >
                <div className="bg-emerald-500/10 border-b border-emerald-500/20 px-4 py-2 flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-emerald-400" />
                  <span className="text-sm font-medium text-emerald-100">Transform Data</span>
                </div>
                <div className="p-4 bg-slate-900/50 border-l-[3px] border-emerald-500 ml-4 mb-2">
                  <div className="text-xs font-mono text-emerald-400">Validation Passed</div>
                </div>
              </motion.div>

              {/* Connecting Line (Desktop) */}
              <div className="hidden md:block absolute top-1/2 left-[60%] right-0 h-0.5 bg-emerald-500/30 -z-10 flex items-center">
                 <motion.div 
                  initial={{ left: '0%' }}
                  animate={{ left: '100%' }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear", delay: 1 }}
                  className="absolute w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_10px_#34d399]"
                />
              </div>

              {/* Action Node */}
              <motion.div 
                initial={{ opacity: 0, x: 50 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: 0.4 }}
                className="w-full md:w-64 flex flex-col bg-slate-900 border border-cyan-500/30 rounded-xl overflow-hidden shadow-xl shadow-cyan-500/10"
              >
                <div className="bg-cyan-500/10 border-b border-cyan-500/20 px-4 py-2 flex items-center gap-2">
                  <Database className="w-4 h-4 text-cyan-400" />
                  <span className="text-sm font-medium text-cyan-100">Update CRM</span>
                </div>
                <div className="p-4 bg-slate-900/50">
                   <div className="flex items-center gap-2 mb-2">
                     <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
                     <span className="text-xs text-slate-400">OAuth Authenticated</span>
                   </div>
                   <div className="h-2 w-full bg-slate-800 rounded"></div>
                </div>
              </motion.div>
            </div>
          </div>
        </div>

        <div className="max-w-3xl mx-auto text-center mt-16">
          <h2 className="text-3xl font-bold text-white mb-4">Complex Automation, Simplified.</h2>
          <p className="text-slate-400 text-lg">
            Drag, drop, and deploy. Our visual editor gives you the freedom to compose workflows with modular nodes without losing the underlying code-level control.
          </p>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-24 bg-white/[0.02] border-y border-white/5 relative" id="how-it-works">
        <div className="max-w-7xl mx-auto px-6">
           <div className="mb-16 text-center">
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">From Idea to Execution in Three Steps</h2>
            <p className="text-slate-400 text-lg">A simple pipeline that masks immense backend power.</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                step: "01",
                icon: ShieldCheck,
                title: "Connect Integrations",
                desc: "Securely manage OAuth connections globally. Authenticate once, use across infinite workflows.",
                color: "text-indigo-400",
                bg: "bg-indigo-500/10"
              },
              {
                step: "02",
                icon: Workflow,
                title: "Build Workflows",
                desc: "Compose logic, conditions, and API chains visually on a canvas. Real-time validation prevents errors.",
                color: "text-emerald-400",
                bg: "bg-emerald-500/10"
              },
              {
                step: "03",
                icon: Activity,
                title: "Execute & Automate",
                desc: "Rely on a robust deterministic FastAPI backend for scale, with built-in retry and monitoring logic.",
                color: "text-cyan-400",
                bg: "bg-cyan-500/10"
              }
            ].map((item, i) => (
              <motion.div 
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="relative p-8 rounded-2xl bg-white/[0.02] border border-white/5 hover:border-white/10 transition-colors"
              >
                <div className="text-5xl font-bold text-white/5 absolute top-6 right-6">{item.step}</div>
                <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-6 ${item.bg}`}>
                  <item.icon className={`w-6 h-6 ${item.color}`} />
                </div>
                <h3 className="text-xl font-semibold text-white mb-3">{item.title}</h3>
                <p className="text-slate-400 leading-relaxed">{item.desc}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Bento } */}
      <section className="py-24 px-6" id="features">
        <div className="max-w-7xl mx-auto">
          <div className="mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-white mb-4 tracking-tight">Built for Scale and Reliability</h2>
            <p className="text-slate-400 text-lg max-w-2xl">Enterprise-ready automation principles, implemented flawlessly. Stop worrying about rate limits, malformed JSON, or broken triggers.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 p-8 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-white/10 relative overflow-hidden group">
               <div className="absolute top-0 right-0 p-8 opacity-20 group-hover:opacity-100 transition-opacity">
                 <Globe className="w-32 h-32 text-indigo-500" />
               </div>
               <h3 className="text-2xl font-semibold text-white mb-3">Integration Management</h3>
               <p className="text-slate-400 max-w-md">Connect with external platforms effortlessly using secure OAuth workflows managed centrally. No more hardcoded tokens.</p>
            </div>
            
            <div className="p-8 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-white/10">
               <ShieldCheck className="w-8 h-8 text-emerald-400 mb-4" />
               <h3 className="text-xl font-semibold text-white mb-3">Real-Time Validation</h3>
               <p className="text-slate-400">Workflows are validated before execution, ensuring required endpoints and configurations are healthy.</p>
            </div>

            <div className="p-8 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-white/10">
               <Terminal className="w-8 h-8 text-cyan-400 mb-4" />
               <h3 className="text-xl font-semibold text-white mb-3">Execution Engine</h3>
               <p className="text-slate-400">A high-performance Python/FastAPI backend driving deterministic, scalable task execution.</p>
            </div>

            <div className="lg:col-span-2 p-8 rounded-2xl bg-gradient-to-br from-slate-900 to-slate-950 border border-white/10">
               <Activity className="w-8 h-8 text-rose-400 mb-4" />
               <h3 className="text-2xl font-semibold text-white mb-3">Debugging and Monitoring</h3>
               <p className="text-slate-400 max-w-xl">Inspect every node execution, trace dependencies, and monitor state in real-time. Full visibility into data transformations means faster resolution times.</p>
            </div>
          </div>
        </div>
      </section>

      {/* Developer Section */}
      <section className="py-24 bg-[#050505] border-y border-white/5 relative" id="developers">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center gap-16">
          <div className="flex-1">
            <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">Developer-Friendly Architecture</h2>
            <p className="text-slate-400 text-lg mb-8 leading-relaxed">
              We didn't abstract away the power. AuraFlow pairs a responsive Next.js frontend with an API-first FastAPI backend. Easily extend endpoints, inject custom code logic into nodes, and seamlessly integrate workflow automation into your existing stack.
            </p>
            <ul className="space-y-4">
              {['API First approach', 'Scalable backend/frontend architecture', 'Extensible custom nodes'].map((item, i) => (
                <li key={i} className="flex items-center gap-3 text-slate-300">
                  <div className="w-5 h-5 rounded-full bg-indigo-500/20 flex items-center justify-center">
                    <div className="w-2 h-2 rounded-full bg-indigo-400" />
                  </div>
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="flex-1 w-full">
            <div className="rounded-xl border border-white/10 bg-[#0a0a0c] overflow-hidden shadow-2xl">
               <div className="border-b border-white/10 bg-white/5 px-4 py-3 flex items-center gap-3">
                 <Terminal className="w-4 h-4 text-slate-400" />
                 <span className="text-sm font-mono text-slate-400">api/v1/trigger</span>
               </div>
               <div className="p-6 font-mono text-sm">
                 <div className="text-indigo-400 mb-2">import requests</div>
                 <div className="text-slate-300 mb-4">
                   <span className="text-cyan-400">response</span> = requests.post(
                 </div>
                 <div className="pl-4 text-emerald-400 mb-2">"https://api.auraflow.com/v1/workflows/trigger"</div>
                 <div className="pl-4 text-slate-300 mb-2">headers={"{"}<span className="text-rose-400">"Authorization"</span>: <span className="text-emerald-400">"Bearer token..."</span>{"}"},</div>
                 <div className="pl-4 text-slate-300 mb-4">json={"{"}<span className="text-rose-400">"workflow_id"</span>: <span className="text-emerald-400">"wkfl_9x8... "</span>{"}"}</div>
                 <div className="text-slate-300">)</div>
               </div>
            </div>
          </div>
        </div>
      </section>

      {/* Use Cases */}
      <section className="py-24 px-6" id="use-cases">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-5xl font-bold text-white mb-4">Automate Anything</h2>
            <p className="text-slate-400 text-lg">Purpose-built for demanding automation requirements.</p>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {[
              { title: "SaaS Automation", desc: "Synchronize user data across your CRMs, billing systems, and support tools automatically.", icon: Globe },
              { title: "Internal Orchestration", desc: "Streamline mundane internal approval pipelines and complex data transformations.", icon: Workflow },
              { title: "API Chaining", desc: "Take output from one API, transform it, and feed it directly into another—all visually mapped.", icon: Zap }
            ].map((uc, i) => (
              <div key={i} className="p-8 rounded-2xl bg-white/[0.01] border hover:bg-white/[0.03] border-white/5 transition-colors cursor-default">
                <uc.icon className="w-8 h-8 text-indigo-400 mb-4" />
                <h3 className="text-xl font-bold text-white mb-2">{uc.title}</h3>
                <p className="text-slate-400">{uc.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-32 px-6 relative overflow-hidden">
        <div className="absolute inset-0 bg-indigo-500/10" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-indigo-500/20 rounded-full blur-[150px] pointer-events-none" />
        
        <div className="max-w-4xl mx-auto text-center relative z-10">
          <h2 className="text-4xl md:text-6xl font-bold text-white mb-6">Ready to supercharge your automation?</h2>
          <p className="text-xl text-slate-300 mb-10 max-w-2xl mx-auto">
            Join builders using AuraFlow to handle their complex integrations seamlessly. Design your first workflow today.
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center gap-2 px-8 py-4 rounded-full bg-white text-black font-bold text-lg hover:bg-slate-200 transition-all active:scale-95 shadow-[0_0_40px_rgba(255,255,255,0.3)]"
          >
            Get Started for Free <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-white/5 bg-[#050505]">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <Workflow className="w-5 h-5 text-indigo-500" />
            <span className="font-semibold text-white">AuraFlow</span>
          </div>
          <p className="text-slate-500 text-sm">© {new Date().getFullYear()} AuraFlow. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
