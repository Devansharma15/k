"use client";

import { use, useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, ChevronDown, ChevronRight, ChevronsLeft, ChevronsRight, Plus, Play, Save, Sparkles } from "lucide-react";

import { WorkflowCanvas } from "@/features/workflows/components/WorkflowCanvas";
import {
  generateWorkflowFromPrompt,
  getPlatformWorkflow,
  listWorkflowNodeTypes,
  publishPlatformWorkflow,
  runPlatformWorkflow,
  updatePlatformWorkflow,
  validatePlatformWorkflow,
  type WorkflowDefinition,
  type WorkflowNodeDefinition,
  type WorkflowNodeType,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const emptySnapshot: WorkflowDefinition = {
  name: "New Workflow",
  nodes: [
    {
      id: "trigger-1",
      type: "trigger_webhook",
      name: "Webhook Trigger",
      position: { x: 100, y: 180 },
      config: { path: "/webhooks/new-flow" },
      ai_brain: false,
      memory: null,
      retry_policy: { max_retries: 0, backoff: "none", retry_on: [] },
      timeout_ms: 5000,
    },
  ],
  edges: [],
};

export default function WorkflowPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const qc = useQueryClient();
  const [draft, setDraft] = useState(emptySnapshot);
  const [name, setName] = useState("Workflow Studio");
  const [prompt, setPrompt] = useState(
    "Send Slack message when new Stripe payment is received and store in Notion",
  );
  const [feedback, setFeedback] = useState<string | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [familyOpen, setFamilyOpen] = useState<Record<string, boolean>>({});

  const workflowQuery = useQuery({
    queryKey: ["platform-workflow", id],
    queryFn: () => getPlatformWorkflow(id),
  });
  const nodeTypesQuery = useQuery({
    queryKey: ["workflow-node-types"],
    queryFn: listWorkflowNodeTypes,
  });

  useEffect(() => {
    if (!workflowQuery.data) return;
    setName(workflowQuery.data.name);
    setDraft(workflowQuery.data.draft_snapshot);
  }, [workflowQuery.data]);

  const groupedNodeTypes = useMemo(() => {
    const groups = new Map<string, WorkflowNodeType[]>();
    for (const item of nodeTypesQuery.data ?? []) {
      groups.set(item.family, [...(groups.get(item.family) ?? []), item]);
    }
    return Array.from(groups.entries());
  }, [nodeTypesQuery.data]);

  useEffect(() => {
    if (!groupedNodeTypes.length) return;
    setFamilyOpen((current) => {
      const next = { ...current };
      for (const [family] of groupedNodeTypes) {
        if (next[family] === undefined) next[family] = true;
      }
      return next;
    });
  }, [groupedNodeTypes]);

  const invalidateWorkflow = async () => {
    await qc.invalidateQueries({ queryKey: ["platform-workflow", id] });
  };

  const saveMutation = useMutation({
    mutationFn: () => updatePlatformWorkflow(id, name, draft),
    onSuccess: async () => {
      setFeedback("Draft saved.");
      await invalidateWorkflow();
    },
    onError: (e: Error) => setFeedback(e.message),
  });
  const validateMutation = useMutation({
    mutationFn: () => validatePlatformWorkflow(id, name, draft),
    onSuccess: (r) => setFeedback(`Validation passed: ${r.nodes} nodes, ${r.edges} edges.`),
    onError: (e: Error) => setFeedback(e.message),
  });
  const publishMutation = useMutation({
    mutationFn: () => publishPlatformWorkflow(id),
    onSuccess: async () => {
      setFeedback("Published new version.");
      await invalidateWorkflow();
    },
    onError: (e: Error) => setFeedback(e.message),
  });
  const runMutation = useMutation({
    mutationFn: () =>
      runPlatformWorkflow(id, {
        mode: "test",
        debug: true,
        input: { source: "workflow-studio" },
      }),
    onSuccess: () => setFeedback("Test run triggered."),
    onError: (e: Error) => setFeedback(e.message),
  });
  const generateMutation = useMutation({
    mutationFn: () => generateWorkflowFromPrompt(prompt),
    onSuccess: (generated) => {
      setDraft(generated);
      setName(generated.name);
      setFeedback("Prompt converted into workflow draft.");
    },
    onError: (e: Error) => setFeedback(e.message),
  });

  const addNode = (nodeType: WorkflowNodeType) => {
    const node: WorkflowNodeDefinition = {
      id: `${nodeType.type}-${crypto.randomUUID()}`,
      type: nodeType.type,
      name: nodeType.label,
      position: { x: 140 + draft.nodes.length * 70, y: 120 + (draft.nodes.length % 4) * 110 },
      config: { ...nodeType.default_config },
      ai_brain: nodeType.supports_ai_brain,
      memory: nodeType.supports_memory ? "short_term" : null,
      retry_policy: { max_retries: 1, backoff: "exponential", retry_on: ["api_error"] },
      timeout_ms: nodeType.family === "ai" ? 30000 : 10000,
    };
    setDraft((current) => ({ ...current, nodes: [...current.nodes, node] }));
  };

  return (
    <div className="flex h-full min-h-[calc(100vh-4rem)] flex-col overflow-hidden bg-background">
      <section className="border-b border-border bg-card/70 p-4">
        <div className="rounded-[1.5rem] border border-border bg-background/80 px-4 py-3">
          <div className="flex items-center gap-3">
            <Bot className="h-5 w-5 text-primary" />
            <input
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the workflow you want to build..."
              className="h-12 w-full rounded-full border border-border bg-card px-5 text-sm outline-none"
            />
            <button
              onClick={() => generateMutation.mutate()}
              className="inline-flex h-12 items-center gap-2 rounded-full bg-primary px-5 text-sm font-semibold text-primary-foreground"
            >
              {generateMutation.isPending ? "Generating..." : "Generate"}
            </button>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={() => saveMutation.mutate()}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold"
            >
              <Save className="h-4 w-4" />
              {saveMutation.isPending ? "Saving..." : "Save"}
            </button>
            <button
              onClick={() => validateMutation.mutate()}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold"
            >
              <Sparkles className="h-4 w-4" />
              Validate
            </button>
            <button
              onClick={() => publishMutation.mutate()}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold"
            >
              <Sparkles className="h-4 w-4" />
              Publish
            </button>
            <button
              onClick={() => runMutation.mutate()}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold"
            >
              <Play className="h-4 w-4" />
              Run Test
            </button>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="ml-auto h-10 min-w-[220px] rounded-full border border-border bg-card px-4 text-sm outline-none"
            />
          </div>

          {feedback ? (
            <p className="mt-3 rounded-xl border border-border bg-card px-3 py-2 text-sm text-muted-foreground">
              {feedback}
            </p>
          ) : null}
        </div>
      </section>

      <main className="flex min-h-0 flex-1 overflow-hidden">
        <aside
          className={cn(
            "shrink-0 border-r border-border bg-card/70 p-2 transition-all duration-300",
            paletteOpen ? "w-72" : "w-14",
          )}
        >
          <div className="rounded-2xl border border-border bg-background/80 p-2">
            <button
              onClick={() => setPaletteOpen((current) => !current)}
              className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-border bg-card text-muted-foreground"
            >
              {paletteOpen ? <ChevronsLeft className="h-4 w-4" /> : <ChevronsRight className="h-4 w-4" />}
            </button>

            {paletteOpen ? (
              <div className="mt-3 max-h-[calc(100vh-14rem)] space-y-3 overflow-y-auto">
                {groupedNodeTypes.map(([family, nodes]) => (
                  <div key={family}>
                    <button
                      onClick={() =>
                        setFamilyOpen((current) => ({ ...current, [family]: !current[family] }))
                      }
                      className="flex w-full items-center justify-between rounded-lg border border-border bg-card px-3 py-2 text-left"
                    >
                      <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">
                        {family}
                      </p>
                      {familyOpen[family] ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>
                    {familyOpen[family] ? (
                      <div className="mt-2 grid gap-2">
                        {nodes.map((nodeType) => (
                          <button
                            key={nodeType.type}
                            onClick={() => addNode(nodeType)}
                            className="rounded-xl border border-border bg-card px-3 py-2 text-left transition hover:border-primary/40"
                          >
                            <p className="text-sm font-semibold">{nodeType.label}</p>
                            <p className="mt-1 text-[10px] uppercase tracking-[0.16em] text-muted-foreground">
                              {nodeType.type}
                            </p>
                          </button>
                        ))}
                      </div>
                    ) : null}
                  </div>
                ))}
              </div>
            ) : (
              <div className="mt-3 flex flex-col items-center gap-2">
                <div className="rounded-full border border-border bg-card p-2">
                  <Plus className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
            )}
          </div>
        </aside>

        <section className="min-h-0 flex-1 p-2">
          <div className="h-full w-full">
            <WorkflowCanvas
              snapshot={draft}
              nodeTypesCatalog={nodeTypesQuery.data ?? []}
              onSnapshotChange={setDraft}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
