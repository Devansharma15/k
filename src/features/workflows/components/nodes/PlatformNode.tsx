"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import { Bot, GitBranch, Hand, Layers3, Plug, TimerReset, Zap } from "lucide-react";

import { cn } from "@/lib/utils";

const familyStyles: Record<string, string> = {
  trigger: "from-emerald-500/20 to-emerald-500/5 border-emerald-400/30",
  core: "from-sky-500/20 to-sky-500/5 border-sky-400/30",
  ai: "from-violet-500/20 to-violet-500/5 border-violet-400/30",
  human: "from-amber-500/20 to-amber-500/5 border-amber-400/30",
  integration: "from-rose-500/20 to-rose-500/5 border-rose-400/30",
};

const statusStyles: Record<string, string> = {
  idle: "text-slate-300 border-slate-400/30",
  running: "text-amber-300 border-amber-400/40",
  completed: "text-emerald-300 border-emerald-400/40",
  success: "text-emerald-300 border-emerald-400/40",
  failed: "text-rose-300 border-rose-400/40",
  waiting_approval: "text-orange-300 border-orange-400/40",
  skipped: "text-slate-400 border-slate-500/40",
};

function FamilyIcon({ family }: { family: string }) {
  if (family === "trigger") return <Zap className="h-4 w-4 text-emerald-300" />;
  if (family === "ai") return <Bot className="h-4 w-4 text-violet-300" />;
  if (family === "human") return <Hand className="h-4 w-4 text-amber-300" />;
  if (family === "integration") return <Plug className="h-4 w-4 text-rose-300" />;
  if (family === "core") return <GitBranch className="h-4 w-4 text-sky-300" />;
  return <Layers3 className="h-4 w-4 text-slate-300" />;
}

export const PlatformNode = memo(({ data, selected }: NodeProps) => {
  const family = data.family ?? "core";
  const status = data.status ?? "idle";
  const warnings = Array.isArray(data.warnings) ? (data.warnings as string[]) : [];
  return (
    <div
      className={cn(
        "min-w-[240px] rounded-2xl border bg-gradient-to-br p-0 shadow-2xl backdrop-blur-md transition-all duration-300",
        familyStyles[family] ?? familyStyles.core,
        selected && "ring-2 ring-primary/70",
      )}
    >
      <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
        <div className="flex items-center gap-2">
          <div className="rounded-xl bg-black/20 p-2">
            <FamilyIcon family={family} />
          </div>
          <div>
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-muted-foreground">
              {family}
            </p>
            <p className="text-sm font-semibold">{data.label ?? data.name ?? "Node"}</p>
          </div>
        </div>
        {data.memory ? (
          <div className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            {data.memory}
          </div>
        ) : null}
      </div>

      <div className="space-y-3 px-4 py-4 text-xs text-muted-foreground">
        <p className="line-clamp-3 leading-5">
          {data.summary ?? "Configure this node to participate in the workflow graph."}
        </p>
        <div className="flex items-center justify-between pt-1">
          <span className="rounded-full border border-white/10 bg-black/20 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.16em]">
            {data.type}
          </span>
          <div className="flex items-center gap-1 text-[10px] uppercase tracking-[0.16em]">
            <TimerReset className="h-3 w-3" />
            {data.timeout_ms ?? 0}ms
          </div>
        </div>
        <div className="flex items-center justify-between gap-2">
          <span
            className={cn(
              "rounded-full border px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em]",
              statusStyles[status] ?? statusStyles.idle,
            )}
          >
            {status}
          </span>
          {warnings.length ? (
            <span className="rounded-full border border-amber-400/40 bg-amber-500/10 px-2 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-amber-300">
              {warnings.length} warning{warnings.length > 1 ? "s" : ""}
            </span>
          ) : null}
        </div>
      </div>

      <Handle
        type="target"
        position={Position.Left}
        className="h-3 w-3 border-2 border-background bg-card"
      />
      <Handle
        type="source"
        position={Position.Right}
        className="h-3 w-3 border-2 border-background bg-primary"
      />
    </div>
  );
});

PlatformNode.displayName = "PlatformNode";
