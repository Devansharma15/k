"use client";

import { motion } from "framer-motion";
import { Workflow, Database, Cpu, Zap, Share2, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

const features = [
  {
    title: "Visual Workflow Builder",
    description: "Build complex AI pipelines with our intuitive drag-and-drop orchestration canvas. Connect LLMs, APIs, and logic nodes with ease.",
    icon: Workflow,
    color: "text-blue-500",
    bg: "bg-blue-500/10",
  },
  {
    title: "RAG Knowledge Base",
    description: "Turn your data into intelligence. Our advanced RAG system automatically indexes documents for contextual AI responses.",
    icon: Database,
    color: "text-emerald-500",
    bg: "bg-emerald-500/10",
  },
  {
    title: "Multi-Model AI",
    description: "Switch between GPT-4o, Claude 3.5, Gemini, and local models seamlessly. Choose the right brain for every task.",
    icon: Cpu,
    color: "text-purple-500",
    bg: "bg-purple-500/10",
  },
  {
    title: "Real-time Streaming",
    description: "Zero latency experience. Our SSE-based streaming ensures your users get responses instantly, token by token.",
    icon: Zap,
    color: "text-yellow-500",
    bg: "bg-yellow-500/10",
  },
  {
    title: "Global Deployment",
    description: "Publish your apps as public links or embeddable widgets. Version control and rollbacks included out of the box.",
    icon: Share2,
    color: "text-pink-500",
    bg: "bg-pink-500/10",
  },
  {
    title: "Enterprise Security",
    description: "Role-based access, API key management, and data encryption at rest. Built for teams that demand privacy.",
    icon: ShieldCheck,
    color: "text-red-500",
    bg: "bg-red-500/10",
  },
];

export const FeaturesGrid = () => {
  return (
    <section className="py-24 bg-background">
      <div className="container mx-auto px-6">
        <div className="max-w-3xl mx-auto text-center mb-20 space-y-4">
          <h2 className="text-3xl lg:text-5xl font-bold tracking-tight">Everything you need to build <br className="hidden md:block" /> the future of AI</h2>
          <p className="text-muted-foreground text-lg italic">"Powerful tools designed for developers, students, and startups."</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, i) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: i * 0.1 }}
              className="glass-card p-8 rounded-3xl border border-white/5 hover:border-primary/20 transition-all group"
            >
              <div className={cn("w-12 h-12 rounded-2xl flex items-center justify-center mb-6 transition-transform group-hover:scale-110", feature.bg)}>
                <feature.icon className={cn("w-6 h-6", feature.color)} />
              </div>
              <h3 className="text-xl font-bold mb-3">{feature.title}</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                {feature.description}
              </p>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
