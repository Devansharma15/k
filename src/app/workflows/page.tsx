"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, CopyPlus, Workflow } from "lucide-react";
import { useRouter } from "next/navigation";

import { createPlatformWorkflow, listPlatformWorkflows, type WorkflowDefinition } from "@/lib/api";

const starterSnapshot: WorkflowDefinition = {
  name: "New Workflow",
  nodes: [],
  edges: [],
};

export default function WorkflowsIndexPage() {
  const router = useRouter();
  const workflowsQuery = useQuery({
    queryKey: ["platform-workflows"],
    queryFn: listPlatformWorkflows,
  });
  const createMutation = useMutation({
    mutationFn: () => createPlatformWorkflow("New Workflow", starterSnapshot),
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
                Run history and draft management
              </h1>
              <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground">
                Open an existing workflow or create a new blank draft. Templates now
                live on a dedicated page.
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
                  {workflow.status} | v{workflow.latest_version ?? 0}
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
            <p className="text-sm font-semibold">Workflow Templates</p>
          </div>
          <p className="mt-4 text-sm leading-7 text-muted-foreground">
            Browse the new preloaded templates and open any template directly in the
            canvas as a draft workflow.
          </p>
          <button
            onClick={() => router.push("/workflow-templates")}
            className="mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground"
          >
            Browse Templates
            <ArrowRight className="h-4 w-4" />
          </button>
        </section>
      </div>
    </div>
  );
}
