"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { ArrowRight, CopyPlus, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";

import { instantiateWorkflowTemplate, listWorkflowTemplates } from "@/lib/api";

export default function WorkflowTemplatesPage() {
  const router = useRouter();
  const templatesQuery = useQuery({
    queryKey: ["workflow-templates"],
    queryFn: listWorkflowTemplates,
  });
  const instantiateMutation = useMutation({
    mutationFn: (templateId: string) => instantiateWorkflowTemplate(templateId),
    onSuccess: (workflow) => {
      router.push(`/workflows/${workflow.id}`);
    },
  });

  return (
    <div className="min-h-[calc(100vh-4rem)] bg-background px-8 py-8">
      <section className="rounded-[2rem] border border-border bg-card/70 p-8">
        <div className="flex items-start justify-between gap-6">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
              Workflow Templates
            </p>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight">
              Preloaded automation blueprints inspired by production patterns
            </h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-muted-foreground">
              These templates are preloaded for AuraFlow and designed to open directly
              in canvas as editable drafts.
            </p>
          </div>
          <div className="inline-flex items-center gap-2 rounded-full border border-border bg-background/70 px-4 py-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">
            <CopyPlus className="h-4 w-4" />
            {templatesQuery.data?.length ?? 0} templates
          </div>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {(templatesQuery.data ?? []).map((template) => (
            <article
              key={template.id}
              className="rounded-[1.5rem] border border-border bg-background/70 p-5 transition hover:-translate-y-0.5 hover:border-primary/40"
            >
              <div className="flex items-center justify-between gap-3">
                <p className="text-lg font-semibold leading-6">{template.name}</p>
                <Sparkles className="h-4 w-4 text-muted-foreground" />
              </div>
              <p className="mt-3 text-sm leading-6 text-muted-foreground">
                {template.description}
              </p>
              <p className="mt-4 text-xs uppercase tracking-[0.16em] text-muted-foreground">
                {template.category} | {template.difficulty}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                {template.integrations_required.map((integration) => (
                  <span
                    key={integration}
                    className="rounded-full border border-border bg-card px-3 py-1 text-xs text-muted-foreground"
                  >
                    {integration}
                  </span>
                ))}
              </div>
              <button
                onClick={() => instantiateMutation.mutate(template.id)}
                className="mt-5 inline-flex items-center gap-2 rounded-full bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground"
              >
                Open on Canvas
                <ArrowRight className="h-4 w-4" />
              </button>
            </article>
          ))}
        </div>
      </section>
    </div>
  );
}
