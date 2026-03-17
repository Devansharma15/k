"use client";

import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Paperclip, 
  Smile, 
  MoreHorizontal, 
  Settings,
  Database,
  Cpu,
  RefreshCw,
  Copy,
  ThumbsUp,
  ThumbsDown
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import ReactMarkdown from 'react-markdown';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  time: string;
}

export const ChatUI = () => {
  const [messages, setMessages] = useState<Message[]>([
    { role: 'assistant', content: "Hello! I'm AuraFlow. How can I help you today?", time: '10:00 AM' }
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMsg: Message = { 
      role: 'user', 
      content: input, 
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
    };
    
    setMessages(prev => [...prev, userMsg]);
    const currentInput = input;
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput,
          model: 'gpt-4o'
        }),
      });

      if (!response.ok) throw new Error('Failed to connect to backend');

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let assistantMsgContent = '';
      
      const assistantMsg: Message = { 
        role: 'assistant', 
        content: '', 
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) 
      };
      
      setMessages(prev => [...prev, assistantMsg]);
      setIsTyping(false);

      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.token) {
                assistantMsgContent += data.token;
                setMessages(prev => {
                  const last = prev[prev.length - 1];
                  if (last && last.role === 'assistant') {
                    return [...prev.slice(0, -1), { ...last, content: assistantMsgContent }];
                  }
                  return prev;
                });
              }
            } catch (e) {
              console.error('Error parsing SSE chunk', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error in chat:', error);
      setIsTyping(false);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "Error: Could not connect to the AuraFlow backend. Please ensure the FastAPI server is running.",
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-140px)] bg-card/30 rounded-3xl border border-border overflow-hidden relative glass">
      {/* Chat Header */}
      <div className="p-4 border-b border-border flex items-center justify-between bg-background/50 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-500/20 flex items-center justify-center border border-blue-500/20">
            <Cpu size={20} className="text-blue-400" />
          </div>
          <div>
            <h3 className="font-bold text-sm">Customer Support Assistant</h3>
            <div className="flex items-center gap-2 mt-0.5">
              <span className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
              <p className="text-[10px] text-muted-foreground uppercase font-bold tracking-widest">GPT-4o Mini • Knowledge Base Active</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button className="p-2 hover:bg-accent rounded-lg text-muted-foreground transition-all"><Database size={18} /></button>
          <button className="p-2 hover:bg-accent rounded-lg text-muted-foreground transition-all"><Settings size={18} /></button>
          <button className="p-2 hover:bg-accent rounded-lg text-muted-foreground transition-all"><MoreHorizontal size={18} /></button>
        </div>
      </div>

      {/* Messages Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-8 scroll-smooth">
        {messages.map((msg, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className={cn(
              "flex gap-4 max-w-[85%]",
              msg.role === 'user' ? "ml-auto flex-row-reverse" : "mr-auto"
            )}
          >
            <div className={cn(
              "w-8 h-8 rounded-lg shrink-0 flex items-center justify-center border",
              msg.role === 'user' ? "bg-primary text-primary-foreground border-primary/20" : "bg-card border-border"
            )}>
              {msg.role === 'user' ? <User size={16} /> : <BrainCircuit size={16} className="text-primary" />}
            </div>
            <div className="space-y-2">
              <div className={cn(
                "p-4 rounded-2xl text-sm leading-relaxed shadow-sm",
                msg.role === 'user' 
                  ? "bg-primary text-primary-foreground rounded-tr-none" 
                  : "bg-accent/40 text-foreground border border-border rounded-tl-none"
              )}>
                <div className="prose prose-invert max-w-none text-xs sm:text-sm">
                  <ReactMarkdown>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              </div>
              <div className={cn("flex items-center gap-3 text-[10px] text-muted-foreground font-bold uppercase tracking-wider px-1", msg.role === 'user' ? "justify-end" : "")}>
                <span>{msg.time}</span>
                {msg.role === 'assistant' && (
                  <div className="flex items-center gap-2">
                    <button className="hover:text-primary transition-colors"><Copy size={12} /></button>
                    <button className="hover:text-emerald-400 transition-colors"><ThumbsUp size={12} /></button>
                    <button className="hover:text-red-400 transition-colors"><ThumbsDown size={12} /></button>
                  </div>
                )}
              </div>
            </div>
          </motion.div>
        ))}
        {isTyping && (
          <div className="flex gap-4 mr-auto max-w-[85%]">
            <div className="w-8 h-8 rounded-lg bg-card border border-border flex items-center justify-center">
              <BrainCircuit size={16} className="text-primary animate-pulse" />
            </div>
            <div className="bg-accent/40 p-4 rounded-2xl rounded-tl-none border border-border">
              <div className="flex gap-1.5">
                {[0, 1, 2].map(d => (
                  <motion.div 
                    key={d}
                    animate={{ y: [0, -5, 0] }}
                    transition={{ repeat: Infinity, duration: 0.6, delay: d * 0.1 }}
                    className="w-1.5 h-1.5 bg-primary/40 rounded-full"
                  />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-6 bg-gradient-to-t from-background to-transparent">
        <div className="relative group glass shadow-2xl overflow-hidden rounded-2xl border border-white/5 focus-within:border-primary/30 transition-all">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
            placeholder="Type your message or use / for commands..."
            className="w-full bg-transparent border-none py-4 px-6 pr-14 text-sm focus:ring-0 outline-none min-h-[56px] max-h-32 resize-none"
            rows={1}
          />
          <div className="absolute left-4 -top-8 bg-zinc-900 border border-border rounded-lg px-2 py-1 flex items-center gap-2 opacity-0 group-focus-within:opacity-100 transition-opacity pointer-events-none">
            <span className="text-[10px] text-muted-foreground font-bold">SMART COMPOSED</span>
          </div>
          <div className="absolute right-3 bottom-3 flex items-center gap-2">
            <button className="p-2 hover:bg-primary/20 transition-all rounded-lg text-muted-foreground hover:text-primary"><Paperclip size={18} /></button>
            <button 
              onClick={handleSend}
              disabled={!input.trim()}
              className={cn(
                "p-2 rounded-lg transition-all",
                input.trim() ? "bg-primary text-primary-foreground shadow-lg shadow-primary/20" : "text-muted-foreground opacity-50 cursor-not-allowed"
              )}
            >
              <Send size={18} />
            </button>
          </div>
          <div className="absolute left-6 bottom-1 flex items-center gap-4 py-1">
             <div className="flex items-center gap-1.5 text-[9px] font-bold text-muted-foreground opacity-50">
               <span className="px-1 py-px bg-muted/20 border border-border rounded">SHIFT</span> + <span className="px-1 py-px bg-muted/20 border border-border rounded">ENTER</span> to add newline
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Simple icons
const User = ({ size, className }: { size: number, className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
  </svg>
);

const BrainCircuit = ({ size, className }: { size: number, className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M12 2a3 3 0 0 0-3 3v7l-1.3 1.3a2 2 0 0 1-2.1.5l-1.6-.5" /><path d="M9 21a3 3 0 0 0 3-3V5l1.3-1.3a2 2 0 0 1 2.1-.5l1.6.5" /><path d="m22 2-7.7 7.7a2 2 0 1 1-2.8-2.8L19.2 2Z" /><path d="m2 2 7.7 7.7a2 2 0 0 0 2.8-2.8L5.3 2Z" /><path d="M12 11h.01" /><path d="M12 7h.01" /><path d="M12 15h.01" /><path d="M12 19h.01" />
  </svg>
);
