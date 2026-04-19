"use client";

import { Building2, User2 } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="mt-1 text-muted-foreground">
          Manage the essentials for your AuraFlow profile and workspace.
        </p>
      </div>

      <section className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-[2rem] border border-border bg-card/70 p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-border bg-background">
              <User2 className="h-5 w-5 text-sky-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">Profile</h2>
              <p className="text-sm text-muted-foreground">
                Personal identity and contact preferences.
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-4">
            <SettingField label="Display Name" value="John Doe" />
            <SettingField label="Email" value="john@auraflow.app" />
            <SettingField label="Role" value="Owner" />
          </div>
        </div>

        <div className="rounded-[2rem] border border-border bg-card/70 p-6">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-border bg-background">
              <Building2 className="h-5 w-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold">Workspace</h2>
              <p className="text-sm text-muted-foreground">
                Shared workspace details for workflows and integrations.
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-4">
            <SettingField label="Workspace Name" value="AuraFlow Studio" />
            <SettingField label="Plan" value="Pro" />
            <SettingField label="Default Environment" value="Production" />
          </div>
        </div>
      </section>
    </div>
  );
}

function SettingField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[1.5rem] border border-border bg-background/80 px-4 py-4">
      <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
        {label}
      </p>
      <p className="mt-2 text-sm font-medium text-foreground">{value}</p>
    </div>
  );
}
