"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { KeyRound, Search, ShieldCheck, X } from "lucide-react";

import {
  connectIntegrationApiKey,
  connectIntegrationOAuth,
  detectIntegrationEnv,
  type IntegrationProvider,
} from "@/lib/api";
import { cn } from "@/lib/utils";

interface IntegrationModalProps {
  provider: IntegrationProvider | null;
  open: boolean;
  onClose: () => void;
}

export function IntegrationModal({
  provider,
  open,
  onClose,
}: IntegrationModalProps) {
  const queryClient = useQueryClient();
  const [apiKey, setApiKey] = useState("");
  const [detectedKeyName, setDetectedKeyName] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setApiKey("");
      setDetectedKeyName(null);
      setMessage(null);
    }
  }, [open, provider]);

  const detectMutation = useMutation({
    mutationFn: async () => {
      if (!provider) {
        throw new Error("No integration selected.");
      }
      return detectIntegrationEnv(provider.slug);
    },
    onSuccess: (result) => {
      if (result.api_key) {
        setApiKey(result.api_key);
        setDetectedKeyName(result.env_key);
        setMessage(`Detected credentials from ${result.env_key}.`);
        return;
      }
      setMessage("No matching key was found in the scanned environment files.");
    },
    onError: (error) => {
      setMessage(error instanceof Error ? error.message : "Detection failed.");
    },
  });

  const apiKeyMutation = useMutation({
    mutationFn: async () => {
      if (!provider) {
        throw new Error("No integration selected.");
      }
      return connectIntegrationApiKey(provider.slug, apiKey);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["integrations"] });
      onClose();
    },
    onError: (error) => {
      setMessage(error instanceof Error ? error.message : "Connection failed.");
    },
  });

  const oauthMutation = useMutation({
    mutationFn: async () => {
      if (!provider) {
        throw new Error("No integration selected.");
      }
      return connectIntegrationOAuth(provider.slug);
    },
    onSuccess: async (result) => {
      await queryClient.invalidateQueries({ queryKey: ["integrations"] });
      window.open(result.auth_url, "_blank", "noopener,noreferrer");
      setMessage("OAuth handoff opened in a new tab.");
    },
    onError: (error) => {
      setMessage(error instanceof Error ? error.message : "OAuth failed.");
    },
  });

  if (!open || !provider) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[90] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl overflow-hidden rounded-[2rem] border border-border bg-background shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-full border border-border bg-background/80 p-2 text-muted-foreground transition-colors hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="border-b border-border bg-[radial-gradient(circle_at_top,_rgba(59,130,246,0.16),_transparent_50%)] p-8">
          <div className="flex items-start gap-4">
            <div
              className="flex h-16 w-16 items-center justify-center rounded-2xl border text-lg font-semibold text-white shadow-lg"
              style={{
                background: `linear-gradient(135deg, ${provider.accent}, rgba(15, 23, 42, 0.92))`,
                borderColor: `${provider.accent}66`,
              }}
            >
              {provider.logo}
            </div>
            <div className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-muted-foreground">
                Integration Setup
              </p>
              <h2 className="text-3xl font-semibold tracking-tight">
                {provider.name}
              </h2>
              <p className="max-w-xl text-sm leading-6 text-muted-foreground">
                Connect this provider once and AuraFlow can later reference the
                saved connection in workflow nodes.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-6 p-8">
          <div className="flex flex-wrap items-center gap-3 text-xs font-semibold uppercase tracking-[0.2em]">
            <span className="rounded-full border border-border bg-accent px-3 py-1 text-muted-foreground">
              {provider.type === "api_key" ? "API Key" : "OAuth"}
            </span>
            <span
              className={cn(
                "rounded-full border px-3 py-1",
                provider.status === "Connected"
                  ? "border-emerald-400/30 bg-emerald-500/10 text-emerald-400"
                  : "border-border bg-secondary text-muted-foreground",
              )}
            >
              {provider.status}
            </span>
          </div>

          {provider.type === "api_key" ? (
            <div className="space-y-6">
              <div className="grid gap-4 md:grid-cols-2">
                <button
                  onClick={() => detectMutation.mutate()}
                  disabled={detectMutation.isPending}
                  className="rounded-[1.5rem] border border-border bg-card p-5 text-left transition-all hover:-translate-y-0.5 hover:border-sky-400/40 hover:bg-accent"
                >
                  <Search className="h-5 w-5 text-sky-400" />
                  <p className="mt-4 text-lg font-semibold">Auto-detect from .env</p>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    Scan local env files and fill the matching key automatically.
                  </p>
                </button>
                <div className="rounded-[1.5rem] border border-border bg-card p-5">
                  <KeyRound className="h-5 w-5 text-amber-400" />
                  <p className="mt-4 text-lg font-semibold">Enter API Key</p>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">
                    Paste the provider secret directly and store it encrypted in
                    AuraFlow.
                  </p>
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                  API Key
                </label>
                <textarea
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                  rows={4}
                  placeholder={`Paste your ${provider.name} key`}
                  className="w-full rounded-[1.5rem] border border-border bg-card px-4 py-4 text-sm outline-none transition-colors focus:border-primary"
                />
                {detectedKeyName ? (
                  <p className="text-xs text-muted-foreground">
                    Auto-filled from <span className="font-semibold">{detectedKeyName}</span>.
                  </p>
                ) : null}
              </div>

              <button
                onClick={() => apiKeyMutation.mutate()}
                disabled={!apiKey.trim() || apiKeyMutation.isPending}
                className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <ShieldCheck className="h-4 w-4" />
                Save encrypted connection
              </button>
            </div>
          ) : (
            <div className="space-y-5 rounded-[1.5rem] border border-border bg-card p-6">
              <p className="text-sm leading-6 text-muted-foreground">
                This provider uses OAuth. AuraFlow will create a pending
                connection reference and hand off to your configured Nango flow.
              </p>
              <button
                onClick={() => oauthMutation.mutate()}
                disabled={oauthMutation.isPending}
                className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-transform hover:-translate-y-0.5 disabled:cursor-not-allowed disabled:opacity-60"
              >
                Continue with OAuth
              </button>
            </div>
          )}

          {message ? (
            <div className="rounded-2xl border border-border bg-accent px-4 py-3 text-sm text-muted-foreground">
              {message}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
