"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, CopyPlus, Sparkles, Workflow } from "lucide-react";
import { useRouter } from "next/navigation";

import {
  createPlatformWorkflow,
  instantiateWorkflowTemplate,
  listPlatformWorkflows,
  listWorkflowTemplates,
  type WorkflowDefinition,
} from "@/lib/api";

const starterSnapshot: WorkflowDefinition = {
  name: "Workflow Studio",
  nodes: [
    {
      id: "trigger-1",
      type: "trigger_webhook",
      name: "Webhook Trigger",
      position: { x: 120, y: 180 },
      config: { path: "/webhooks/new-flow" },
      ai_brain: false,
      memory: null,
      retry_policy: { max_retries: 0, backoff: "none", retry_on: [] },
      timeout_ms: 5000,
    },
  ],
  edges: [],
};

export default function WorkflowsIndexPage() {
  const router = useRouter();
  const workflowsQuery = useQuery({
    queryKey: ["platform-workflows"],
    queryFn: listPlatformWorkflows,
  });
  const templatesQuery = useQuery({
    queryKey: ["workflow-templates"],
    queryFn: listWorkflowTemplates,
  });

  const createMutation = useMutation({
    mutationFn: () => createPlatformWorkflow("Workflow Studio", starterSnapshot),
    onSuccess: (workflow) => {
      router.push(`/workflows/${workflow.id}`);
    },
  });
  const instantiateMutation = useMutation({
    mutationFn: (templateId: string) => instantiateWorkflowTemplate(templateId),
    onSuccess: (workflow) => {
      router.push(`/workflows/${workflow.id}`);
    },
  });

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-background px-8 py-8">
      <div className="grid gap-8 xl:grid-cols-[1.4fr_0.8fr]">
        <section className="rounded-[2rem] border border-border bg-card/70 p-8">
          <div className="flex items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
                AuraFlow Workflows
              </p>
              <h1 className="mt-3 text-4xl font-semibold tracking-tight">
                Real workflow engine, versioned drafts, and run history
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground">
                Open an existing workflow, start from a blank graph, or instantiate one
                of the platform templates into a new draft.
              </p>
            </div>
            <button
              onClick={() => createMutation.mutate()}
              className="inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground"
            >
              <Workflow className="h-4 w-4" />
              {createMutation.isPending ? "Creating..." : "New Workflow"}
            </button>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {(workflowsQuery.data ?? []).map((workflow) => (
              <button
                key={workflow.id}
                onClick={() => router.push(`/workflows/${workflow.id}`)}
                className="rounded-[1.5rem] border border-border bg-background/70 p-5 text-left transition hover:-translate-y-0.5 hover:border-primary/40"
              >
                <div className="flex items-center justify-between gap-3">
                  <p className="text-lg font-semibold">{workflow.name}</p>
                  <ArrowRight className="h-4 w-4 text-muted-foreground" />
                </div>
                <p className="mt-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
                  {workflow.status} • v{workflow.latest_version ?? 0}
                </p>
                <p className="mt-3 text-sm text-muted-foreground">
                  {workflow.run_count ?? 0} recorded runs
                </p>
              </button>
            ))}
            {!workflowsQuery.data?.length ? (
              <div className="rounded-[1.5rem] border border-dashed border-border bg-background/40 p-6 text-sm text-muted-foreground">
                No workflows yet. Create one to open the builder.
              </div>
            ) : null}
          </div>
        </section>

        <section className="rounded-[2rem] border border-border bg-card/70 p-8">
          <div className="flex items-center gap-2">
            <CopyPlus className="h-4 w-4 text-emerald-400" />
            <p className="text-sm font-semibold">Starter Templates</p>
          </div>
          <div className="mt-5 space-y-3">
            {(templatesQuery.data ?? []).slice(0, 10).map((template) => (
              <button
                key={template.id}
                onClick={() => instantiateMutation.mutate(template.id)}
                className="w-full rounded-[1.25rem] border border-border bg-background/70 px-4 py-4 text-left transition hover:border-primary/40"
              >
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-semibold">{template.name}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {template.category} • {template.difficulty}
                    </p>
                  </div>
                  <Sparkles className="h-4 w-4 text-muted-foreground" />
                </div>
              </button>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
