"use client";

import React from "react";
import { Hero } from "./Hero";
import { FeaturesGrid } from "./FeaturesGrid";
import { DashboardPreview } from "./DashboardPreview";
import { CTASection } from "./CTASection";
import { motion, useScroll, useSpring } from "framer-motion";
import { Globe, Github, Twitter, Linkedin } from "lucide-react";
import Link from "next/link";

export default function LandingPage() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 100,
    damping: 30,
    restDelta: 0.001
  });

  return (
    <div className="bg-background text-foreground selection:bg-primary/30">
      {/* Scroll Progress Bar */}
      <motion.div
        className="fixed top-0 left-0 right-0 h-1 bg-primary z-[110] origin-left"
        style={{ scaleX }}
      />

      {/* Navigation */}
      <nav className="fixed top-0 w-full z-[100] bg-background/50 backdrop-blur-xl border-b border-white/5">
        <div className="container mx-auto px-6 h-20 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2 group">
            <div className="w-10 h-10 rounded-xl bg-primary flex items-center justify-center shadow-lg shadow-primary/20 transition-transform group-hover:scale-110">
              <Globe className="text-white" size={24} />
            </div>
            <span className="text-xl font-black tracking-tighter uppercase italic">AuraFlow</span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            <Link href="#features" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">Features</Link>
            <Link href="#demo" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">Demo</Link>
            <Link href="#pricing" className="text-sm font-medium text-muted-foreground hover:text-primary transition-colors">Pricing</Link>
            <Link href="/dashboard" className="px-5 py-2.5 bg-white text-black rounded-xl text-sm font-bold hover:bg-white/90 transition-all">
              Sign In
            </Link>
          </div>
        </div>
      </nav>

      <main>
        <Hero />
        <div id="demo">
           <DashboardPreview />
        </div>
        <div id="features">
           <FeaturesGrid />
        </div>
        <CTASection />
      </main>

      {/* Footer */}
      <footer className="py-20 border-t border-white/5 bg-background">
        <div className="container mx-auto px-6 grid grid-cols-1 md:grid-cols-4 gap-12 lg:gap-24">
          <div className="col-span-2 space-y-6">
            <Link href="/" className="flex items-center gap-2">
              <Globe className="text-primary" size={24} />
              <span className="text-xl font-black tracking-tighter uppercase italic">AuraFlow</span>
            </Link>
            <p className="text-muted-foreground max-w-sm leading-relaxed">
              Empowering developers and businesses to build complex AI applications with ease. The open-source standard for AI orchestration.
            </p>
            <div className="flex gap-4">
              <button className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center hover:bg-primary/20 transition-colors group">
                 <Twitter size={20} className="group-hover:text-primary transition-colors" />
              </button>
              <button className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center hover:bg-primary/20 transition-colors group">
                 <Github size={20} className="group-hover:text-primary transition-colors" />
              </button>
              <button className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center hover:bg-primary/20 transition-colors group">
                 <Linkedin size={20} className="group-hover:text-primary transition-colors" />
              </button>
            </div>
          </div>
          
          <div className="space-y-4">
            <h4 className="font-bold uppercase text-[10px] tracking-widest text-muted-foreground">Product</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="#" className="hover:text-primary transition-colors">Features</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Workflows</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Agents</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">API</Link></li>
            </ul>
          </div>

          <div className="space-y-4">
            <h4 className="font-bold uppercase text-[10px] tracking-widest text-muted-foreground">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="#" className="hover:text-primary transition-colors">Blog</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Docs</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Guides</Link></li>
              <li><Link href="#" className="hover:text-primary transition-colors">Discord</Link></li>
            </ul>
          </div>
        </div>
        <div className="container mx-auto px-6 mt-20 pt-8 border-t border-white/5 flex flex-col md:flex-row justify-between gap-4">
          <p className="text-[10px] uppercase font-bold text-muted-foreground">© 2026 AuraFlow AI. All rights reserved.</p>
          <div className="flex gap-8 text-[10px] uppercase font-bold text-muted-foreground">
             <Link href="#" className="hover:text-white transition-colors">Privacy Policy</Link>
             <Link href="#" className="hover:text-white transition-colors">Terms of Service</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
