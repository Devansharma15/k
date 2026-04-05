"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  ArrowRight,
  Bot,
  Cpu,
  Gauge,
  Layers3,
  Sparkles,
  Workflow,
  Zap,
} from "lucide-react";
import { motion } from "framer-motion";

import { getOverview, type OverviewData } from "@/lib/api";
import { cn } from "@/lib/utils";

const iconMap = {
  Activity,
  Bot,
  Cpu,
  Gauge,
  Workflow,
  Zap,
};

const toneMap = {
  sky: "from-sky-500/20 border-sky-400/20 text-sky-200",
  amber: "from-amber-500/20 border-amber-400/20 text-amber-200",
  emerald: "from-emerald-500/20 border-emerald-400/20 text-emerald-200",
  rose: "from-rose-500/20 border-rose-400/20 text-rose-200",
};

export function AppOverview() {
  const { data, isLoading, isError } = useQuery<OverviewData>({
    queryKey: ["overview"],
    queryFn: getOverview,
  });

  if (isLoading) {
    return (
      <div className="grid gap-6">
        <div className="rounded-[2rem] border border-white/10 bg-white/5 p-8">
          <div className="h-8 w-56 animate-pulse rounded-full bg-white/10" />
          <div className="mt-4 h-4 w-80 animate-pulse rounded-full bg-white/10" />
        </div>
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {Array.from({ length: 4 }).map((_, index) => (
            <div
              key={index}
              className="h-36 animate-pulse rounded-[1.75rem] border border-white/10 bg-white/5"
            />
          ))}
        </div>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <div className="rounded-[2rem] border border-rose-400/20 bg-rose-500/10 p-8 text-rose-100">
        <p className="text-lg font-semibold">Backend connection needed</p>
        <p className="mt-2 text-sm text-rose-100/80">
          Start the FastAPI server on `http://localhost:8000` or set
          `NEXT_PUBLIC_API_BASE_URL` to your backend URL.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <section className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-[radial-gradient(circle_at_top_left,_rgba(56,189,248,0.25),_transparent_28%),linear-gradient(135deg,rgba(10,14,26,0.96),rgba(17,24,39,0.86)_45%,rgba(6,95,70,0.82))] p-8 shadow-2xl shadow-black/30">
        <div className="absolute inset-y-0 right-0 hidden w-1/2 bg-[radial-gradient(circle_at_center,_rgba(255,255,255,0.14),_transparent_58%)] lg:block" />
        <div className="relative grid gap-8 lg:grid-cols-[1.5fr_0.9fr]">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-sky-100">
              <Sparkles className="h-4 w-4" />
              Control Room
            </div>
            <h1 className="mt-6 max-w-3xl text-4xl font-semibold tracking-tight text-white sm:text-5xl">
              {data.product.name} is now centered on the product, not a landing page.
            </h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-slate-200">
              {data.product.tagline}
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/apps/1"
                className="inline-flex items-center gap-2 rounded-full bg-white px-5 py-3 text-sm font-semibold text-slate-950 transition-transform hover:-translate-y-0.5"
              >
                Open live app
                <ArrowRight className="h-4 w-4" />
              </Link>
              <Link
                href="/workflows/1"
                className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-white/10"
              >
                Review workflow
                <Layers3 className="h-4 w-4" />
              </Link>
            </div>
          </div>

          <div className="grid gap-4 rounded-[1.75rem] border border-white/10 bg-slate-950/40 p-5 backdrop-blur-sm">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-400">
                Platform Snapshot
              </p>
              <p className="mt-2 text-2xl font-semibold text-white">
                {data.apps.length} apps and {data.workflows.length} workflow tracks
              </p>
            </div>
            <div className="grid gap-3">
              {data.activities.slice(0, 3).map((activity) => (
                <div
                  key={activity.id}
                  className="rounded-2xl border border-white/8 bg-white/[0.03] p-4"
                >
                  <p className="text-sm font-medium text-white">{activity.name}</p>
                  <p className="mt-1 text-sm text-slate-300">{activity.action}</p>
                  <p className="mt-2 text-xs uppercase tracking-[0.2em] text-slate-500">
                    {activity.time}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {data.stats.map((stat, index) => {
          const Icon =
            iconMap[stat.icon as keyof typeof iconMap] ?? Activity;

          return (
            <motion.article
              key={stat.name}
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.06 }}
              className={cn(
                "rounded-[1.75rem] border bg-gradient-to-br p-5",
                toneMap[stat.tone as keyof typeof toneMap] ?? toneMap.sky,
              )}
            >
              <div className="flex items-center justify-between">
                <div className="rounded-2xl bg-black/20 p-3">
                  <Icon className="h-5 w-5" />
                </div>
                <ArrowRight className="h-4 w-4 opacity-60" />
              </div>
              <p className="mt-6 text-sm font-medium text-white/80">{stat.name}</p>
              <p className="mt-2 text-3xl font-semibold text-white">{stat.value}</p>
              <p className="mt-2 text-sm text-white/70">{stat.trend}</p>
            </motion.article>
          );
        })}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <div className="rounded-[2rem] border border-white/10 bg-slate-950/60 p-6">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
                Applications
              </p>
              <h2 className="mt-2 text-2xl font-semibold text-white">
                Active AI surfaces
              </h2>
            </div>
            <Link href="/integrations" className="text-sm font-medium text-sky-300">
              Open integrations
            </Link>
          </div>
          <div className="mt-6 grid gap-4">
            {data.apps.map((app) => (
              <div
                key={app.id}
                className="rounded-[1.5rem] border border-white/8 bg-white/[0.03] p-5"
              >
                <div className="flex items-center justify-between gap-4">
                  <div>
                    <p className="text-lg font-semibold text-white">{app.name}</p>
                    <p className="mt-2 text-sm leading-6 text-slate-300">
                      {app.description}
                    </p>
                  </div>
                  <span className="rounded-full border border-emerald-400/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold text-emerald-200">
                    {app.status}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[2rem] border border-white/10 bg-slate-950/60 p-6">
          <p className="text-xs font-semibold uppercase tracking-[0.2em] text-slate-500">
            Workflow Health
          </p>
          <h2 className="mt-2 text-2xl font-semibold text-white">
            Operational pipelines
          </h2>
          <div className="mt-6 space-y-4">
            {data.workflows.map((workflow) => (
              <div
                key={workflow.id}
                className="rounded-[1.5rem] border border-white/8 bg-white/[0.03] p-5"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="text-lg font-semibold text-white">{workflow.name}</p>
                    <p className="mt-2 text-sm text-slate-300">
                      {workflow.runs_today} runs today
                    </p>
                  </div>
                  <span className="rounded-full border border-amber-300/20 bg-amber-400/10 px-3 py-1 text-xs font-semibold text-amber-100">
                    {workflow.status}
                  </span>
                </div>
                <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/8">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-sky-400 to-emerald-400"
                    style={{ width: `${Math.min(100, workflow.runs_today * 3)}%` }}
                  />
                </div>
                <p className="mt-3 text-xs uppercase tracking-[0.2em] text-slate-500">
                  Median latency {workflow.latency_ms}ms
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
