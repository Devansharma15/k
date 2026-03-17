"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import Link from "next/link";

export const CTASection = () => {
  return (
    <section className="py-24 relative overflow-hidden">
      {/* Background decoration */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[80%] h-[80%] bg-primary/5 rounded-full blur-[120px] -z-10" />
      
      <div className="container mx-auto px-6">
        <div className="glass-card max-w-5xl mx-auto rounded-[40px] p-12 lg:p-24 text-center space-y-8 border border-white/10 relative overflow-hidden">
          <div className="absolute top-0 right-0 p-8 opacity-20">
             <Sparkles size={120} className="text-primary" />
          </div>
          
          <motion.h2 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            className="text-4xl lg:text-6xl font-bold tracking-tight"
          >
            Start Building with <br className="hidden md:block" /> AuraFlow Today
          </motion.h2>
          
          <motion.p 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="text-lg lg:text-xl text-muted-foreground max-w-2xl mx-auto"
          >
            Join thousands of developers and teams building the next generation of AI-native applications. No credit card required.
          </motion.p>
          
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-8"
          >
            <Link
              href="/dashboard"
              className="px-10 py-5 bg-primary text-primary-foreground rounded-2xl font-bold text-lg flex items-center gap-2 hover:bg-primary/90 transition-all shadow-xl shadow-primary/30 group w-full sm:w-auto"
            >
              Get Started for Free
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <button className="px-10 py-5 bg-background border border-border text-foreground rounded-2xl font-bold text-lg hover:bg-accent transition-all w-full sm:w-auto">
              Contact Sales
            </button>
          </motion.div>
          
          <p className="text-xs text-muted-foreground font-bold uppercase tracking-widest pt-8">
            Free forever for individuals • Enterprise plans available
          </p>
        </div>
      </div>
    </section>
  );
};
