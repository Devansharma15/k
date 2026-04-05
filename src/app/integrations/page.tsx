"use client";

import type { ReactNode } from "react";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, Link2, ShieldCheck, Sparkles } from "lucide-react";

import { IntegrationModal } from "@/components/IntegrationModal";
import { getIntegrations, type IntegrationProvider } from "@/lib/api";
import { cn } from "@/lib/utils";

export default function IntegrationsPage() {
  const [selectedProvider, setSelectedProvider] =
    useState<IntegrationProvider | null>(null);
  const { data, isLoading, isError } = useQuery({
    queryKey: ["integrations"],
    queryFn: getIntegrations,
  });

  return (
    <>
      <div className="space-y-10">
        <section className="overflow-hidden rounded-[2rem] border border-border bg-[radial-gradient(circle_at_top_left,_rgba(59,130,246,0.16),_transparent_28%),linear-gradient(135deg,rgba(255,255,255,0.04),rgba(255,255,255,0.01))] p-8">
          <div className="flex flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div className="max-w-3xl">
              <p className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                <Sparkles className="h-4 w-4 text-sky-400" />
                Integrations
              </p>
              <h1 className="mt-6 text-4xl font-semibold tracking-tight sm:text-5xl">
                Connect the tools your workflows already rely on.
              </h1>
              <p className="mt-4 text-base leading-7 text-muted-foreground">
                AuraFlow now has a dedicated integration control room with
                encrypted API-key storage, session-based OAuth via Nango, and
                reusable connection references for workflow nodes.
              </p>
            </div>

            <div className="grid gap-4 sm:grid-cols-3">
              <SummaryCard
                label="Providers"
                value={data?.summary.total ?? 110}
                tone="sky"
              />
              <SummaryCard
                label="Connected"
                value={data?.summary.connected ?? 0}
                tone="emerald"
              />
              <SummaryCard
                label="Ready to Configure"
                value={data?.summary.disconnected ?? 110}
                tone="amber"
              />
            </div>
          </div>
        </section>

        {isLoading ? (
          <div className="grid gap-6">
            {Array.from({ length: 3 }).map((_, index) => (
              <div
                key={index}
                className="h-64 animate-pulse rounded-[2rem] border border-border bg-card"
              />
            ))}
          </div>
        ) : null}

        {isError ? (
          <div className="rounded-[2rem] border border-destructive/30 bg-destructive/10 p-6 text-sm text-destructive-foreground">
            The integrations catalog could not be loaded from the backend.
          </div>
        ) : null}

        {data?.categories.map((category) => (
          <section key={category.id} className="space-y-5">
            <div className="flex items-center justify-between gap-4">
              <div>
                <h2 className="text-2xl font-semibold tracking-tight">
                  {category.name}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {category.providers.length} providers ready for connection.
                </p>
              </div>
              <span className="rounded-full border border-border bg-card px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                {category.providers.filter((item) => item.status === "Connected").length} connected
              </span>
            </div>

            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
              {category.providers.map((provider) => (
                <button
                  key={`${category.id}-${provider.slug}`}
                  onClick={() => setSelectedProvider(provider)}
                  className="group rounded-[1.75rem] border border-border bg-card/80 p-5 text-left transition-all duration-300 hover:-translate-y-1 hover:border-primary/40 hover:shadow-2xl hover:shadow-primary/10"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div
                      className="flex h-12 w-12 items-center justify-center rounded-2xl border text-sm font-semibold text-white shadow-lg transition-transform group-hover:scale-105"
                      style={{
                        background: `linear-gradient(135deg, ${provider.accent}, rgba(15, 23, 42, 0.92))`,
                        borderColor: `${provider.accent}66`,
                      }}
                    >
                      {provider.logo}
                    </div>
                    <ArrowUpRight className="h-4 w-4 text-muted-foreground transition-colors group-hover:text-foreground" />
                  </div>

                  <div className="mt-5">
                    <h3 className="text-lg font-semibold leading-6">
                      {provider.name}
                    </h3>
                    <p className="mt-2 text-sm text-muted-foreground">
                      {provider.type === "api_key" ? "API key setup" : "OAuth setup"}
                    </p>
                  </div>

                  <div className="mt-5 flex items-center justify-between gap-3">
                    <span
                      className={cn(
                        "rounded-full border px-3 py-1 text-xs font-semibold",
                        provider.status === "Connected"
                          ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-400"
                          : "border-border bg-secondary text-muted-foreground",
                      )}
                    >
                      {provider.status}
                    </span>
                    <span className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                      {provider.type}
                    </span>
                  </div>
                </button>
              ))}
            </div>
          </section>
        ))}

        <section className="grid gap-4 rounded-[2rem] border border-border bg-card/60 p-6 lg:grid-cols-3">
          <FeatureCard
            icon={<ShieldCheck className="h-5 w-5 text-emerald-400" />}
            title="Encrypted storage"
            body="API keys are saved as encrypted secrets and never returned in provider list responses."
          />
          <FeatureCard
            icon={<Link2 className="h-5 w-5 text-sky-400" />}
            title="Workflow ready"
            body="Each connection stores a reusable reference for future workflow node integration."
          />
          <FeatureCard
            icon={<Sparkles className="h-5 w-5 text-amber-400" />}
            title="Fast setup"
            body="Choose direct API keys or launch a session-based OAuth popup through Nango."
          />
        </section>
      </div>

      <IntegrationModal
        key={selectedProvider?.slug ?? "closed"}
        provider={selectedProvider}
        open={Boolean(selectedProvider)}
        onClose={() => setSelectedProvider(null)}
      />
    </>
  );
}

function SummaryCard({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "sky" | "emerald" | "amber";
}) {
  const toneClasses = {
    sky: "border-sky-400/20 bg-sky-500/10 text-sky-200",
    emerald: "border-emerald-400/20 bg-emerald-500/10 text-emerald-200",
    amber: "border-amber-400/20 bg-amber-500/10 text-amber-100",
  };

  return (
    <div className={cn("rounded-[1.5rem] border p-5", toneClasses[tone])}>
      <p className="text-xs font-semibold uppercase tracking-[0.2em] opacity-80">
        {label}
      </p>
      <p className="mt-3 text-3xl font-semibold text-foreground">{value}</p>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  body,
}: {
  icon: ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div className="rounded-[1.5rem] border border-border bg-background/80 p-5">
      <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-border bg-card">
        {icon}
      </div>
      <h3 className="mt-4 text-lg font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p>
    </div>
  );
}
