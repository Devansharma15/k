"use client";

import { use, useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  Bot,
  ChevronDown,
  ChevronRight,
  ChevronsLeft,
  ChevronsRight,
  Clock,
  Download,
  GitBranch,
  History,
  Play,
  RotateCcw,
  Save,
  Shield,
  Sparkles,
} from "lucide-react";

import { WorkflowCanvas } from "@/features/workflows/components/WorkflowCanvas";
import {
  autosaveWorkflowDraft,
  generateWorkflowFromPrompt,
  getWorkflowLimits,
  getPlatformRunLogs,
  getPlatformWorkflow,
  listPlatformVersions,
  listWorkflowNodeTypes,
  publishPlatformWorkflow,
  rollbackPlatformWorkflow,
  runPlatformWorkflow,
  updatePlatformWorkflow,
  validatePlatformWorkflow,
  type GeneratedWorkflowResponse,
  type WorkflowDefinition,
  type WorkflowNodeDefinition,
  type WorkflowNodeType,
  type WorkflowRunLogsResponse,
  type WorkflowVersionRecord,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const emptySnapshot: WorkflowDefinition = {
  name: "New Workflow",
  nodes: [],
  edges: [],
};

const VARIABLE_EXAMPLES = [
  "{{trigger.amount}}",
  "{{stripe.customer_email}}",
  "{{global_vars.mode}}",
];

function collectNodeValidation(
  snapshot: WorkflowDefinition,
  nodeTypes: WorkflowNodeType[],
): {
  map: Record<string, string[]>;
  critical: Array<{ nodeId: string; message: string }>;
} {
  const metadata = new Map(nodeTypes.map((nodeType) => [nodeType.type, nodeType]));
  const map: Record<string, string[]> = {};
  const critical: Array<{ nodeId: string; message: string }> = [];

  for (const node of snapshot.nodes) {
    const typeMeta = metadata.get(node.type);
    if (!typeMeta) {
      map[node.id] = ["Unsupported node type"];
      critical.push({ nodeId: node.id, message: "Unsupported node type" });
      continue;
    }
    const warnings: string[] = [];
    const requiredFields = typeMeta.required_fields ?? [];
    const requiredSecrets = typeMeta.secrets_required ?? [];
    for (const field of requiredFields) {
      const value = node.config?.[field];
      if (value === undefined || value === null || value === "") {
        warnings.push(`Missing required field: ${field}`);
      }
    }
    for (const secret of requiredSecrets) {
      const value = node.config?.[secret];
      if (value === undefined || value === null || value === "") {
        warnings.push(`Missing API key/secret: ${secret}`);
      }
    }
    if (warnings.length) {
      map[node.id] = warnings;
      for (const message of warnings) {
        critical.push({ nodeId: node.id, message });
      }
    }
  }

  return { map, critical };
}

export default function WorkflowPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const qc = useQueryClient();
  const [draft, setDraft] = useState(emptySnapshot);
  const [name, setName] = useState("");
  const [prompt, setPrompt] = useState("");
  const [feedback, setFeedback] = useState<string | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [familyOpen, setFamilyOpen] = useState<Record<string, boolean>>({});
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [activeFieldKey, setActiveFieldKey] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [generationConfidence, setGenerationConfidence] = useState<number | null>(null);
  const [generationExplanation, setGenerationExplanation] = useState<string | null>(null);
  const [autosaveStatus, setAutosaveStatus] = useState<"idle" | "saving" | "saved">("idle");
  const [showVersions, setShowVersions] = useState(false);
  const autosaveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const workflowQuery = useQuery({
    queryKey: ["platform-workflow", id],
    queryFn: () => getPlatformWorkflow(id),
    refetchInterval: (query) =>
      query.state.data?.is_locked ? 2000 : false,
  });
  const nodeTypesQuery = useQuery({
    queryKey: ["workflow-node-types"],
    queryFn: listWorkflowNodeTypes,
  });
  const runLogsQuery = useQuery<WorkflowRunLogsResponse | null>({
    queryKey: ["workflow-run-logs", id, activeRunId],
    queryFn: () => getPlatformRunLogs(id, activeRunId as string),
    enabled: Boolean(activeRunId),
    retry: false,
    refetchInterval: (query) => {
      if (query.state.error) return false;
      if (query.state.data === null) return false;
      const status = query.state.data?.status;
      if (status && ["completed", "failed", "cancelled"].includes(status)) return false;
      return 1500;
    },
  });

  const versionsQuery = useQuery({
    queryKey: ["workflow-versions", id],
    queryFn: () => listPlatformVersions(id),
    enabled: showVersions,
  });

  const limitsQuery = useQuery({
    queryKey: ["workflow-limits"],
    queryFn: getWorkflowLimits,
  });

  useEffect(() => {
    if (!runLogsQuery.data) return;
    if (["completed", "failed", "cancelled"].includes(runLogsQuery.data.status)) {
      qc.invalidateQueries({ queryKey: ["platform-workflow", id] });
    }
  }, [id, qc, runLogsQuery.data]);

  const groupedNodeTypes = useMemo(() => {
    const groups = new Map<string, WorkflowNodeType[]>();
    for (const item of nodeTypesQuery.data ?? []) {
      groups.set(item.family, [...(groups.get(item.family) ?? []), item]);
    }
    return Array.from(groups.entries());
  }, [nodeTypesQuery.data]);

  const isLocked = workflowQuery.data?.is_locked ?? false;
  const effectiveName = name || workflowQuery.data?.name || "Workflow Studio";
  const effectiveDraft =
    draft.nodes.length === 0 && draft.edges.length === 0 && workflowQuery.data
      ? workflowQuery.data.draft_snapshot
      : draft;
  const lockSummary = workflowQuery.data?.active_run_id
    ? `Run ${workflowQuery.data.active_run_id} is ${workflowQuery.data.active_run_status}.`
    : "Workflow is locked while an active run is executing.";

  const validation = useMemo(
    () => collectNodeValidation(effectiveDraft, nodeTypesQuery.data ?? []),
    [effectiveDraft, nodeTypesQuery.data],
  );
  const nodeStatuses = useMemo(() => {
    const map: Record<string, string> = {};
    for (const step of runLogsQuery.data?.logs ?? []) {
      map[step.node_id] = step.status;
    }
    return map;
  }, [runLogsQuery.data]);

  const selectedNode = useMemo(
    () => effectiveDraft.nodes.find((node) => node.id === selectedNodeId) ?? null,
    [effectiveDraft.nodes, selectedNodeId],
  );
  const selectedNodeType = useMemo(
    () =>
      (nodeTypesQuery.data ?? []).find((item) => item.type === selectedNode?.type) ?? null,
    [nodeTypesQuery.data, selectedNode?.type],
  );
  const selectableVariables = useMemo(() => {
    const tokens = new Set<string>(VARIABLE_EXAMPLES);
    tokens.add("{{input}}");
    tokens.add("{{global_vars.mode}}");
    for (const node of effectiveDraft.nodes) {
      tokens.add(`{{${node.id}}}`);
      tokens.add(`{{${node.id}.output}}`);
    }
    return Array.from(tokens);
  }, [effectiveDraft.nodes]);

  const invalidateWorkflow = async () => {
    await qc.invalidateQueries({ queryKey: ["platform-workflow", id] });
  };

  const saveMutation = useMutation({
    mutationFn: () => updatePlatformWorkflow(id, effectiveName, effectiveDraft),
    onSuccess: async () => {
      setFeedback("Draft saved.");
      await invalidateWorkflow();
    },
    onError: (e: Error) => setFeedback(e.message),
  });
  const validateMutation = useMutation({
    mutationFn: () => validatePlatformWorkflow(id, effectiveName, effectiveDraft),
    onSuccess: (result) => {
      if (Array.isArray(result.errors) && result.errors.length) {
        setFeedback(`Validation found ${result.errors.length} issue(s).`);
        return;
      }
      setFeedback(`Validation passed: ${result.nodes} nodes, ${result.edges} edges.`);
    },
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
    onSuccess: (run) => {
      setActiveRunId(run.id);
      setFeedback("Test run started. Debug logs are live.");
    },
    onError: (e: Error) => setFeedback(e.message),
  });
  const generateMutation = useMutation({
    mutationFn: () => generateWorkflowFromPrompt(prompt),
    onMutate: () => {
      setActiveRunId(null);
    },
    onSuccess: (generated: GeneratedWorkflowResponse) => {
      setDraft(generated);
      setName(generated.name);
      setGenerationConfidence(generated.confidence ?? null);
      setGenerationExplanation(generated.explanation ?? null);
      const confLabel = generated.confidence != null ? ` (confidence: ${Math.round(generated.confidence * 100)}%)` : "";
      setFeedback(`Prompt converted into workflow draft.${confLabel}`);
      if (generated.needs_confirmation) {
        setFeedback(`Low confidence generation${confLabel}. Please review carefully before running.`);
      }
    },
    onError: (e: Error) => setFeedback(e.message),
  });

  const rollbackMutation = useMutation({
    mutationFn: (versionId: string) => rollbackPlatformWorkflow(id, versionId),
    onSuccess: async () => {
      setFeedback("Rolled back to selected version.");
      await invalidateWorkflow();
    },
    onError: (e: Error) => setFeedback(e.message),
  });

  // ── Autosave ───────────────────────────────────────────────────
  const performAutosave = useCallback(async () => {
    if (isLocked || effectiveDraft.nodes.length === 0) return;
    setAutosaveStatus("saving");
    try {
      await autosaveWorkflowDraft("workflow", id, effectiveDraft);
      setAutosaveStatus("saved");
    } catch {
      setAutosaveStatus("idle");
    }
  }, [id, isLocked, effectiveDraft]);

  useEffect(() => {
    if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);
    if (effectiveDraft.nodes.length === 0) return;
    setAutosaveStatus("idle");
    autosaveTimerRef.current = setTimeout(() => {
      void performAutosave();
    }, 5000);
    return () => {
      if (autosaveTimerRef.current) clearTimeout(autosaveTimerRef.current);
    };
  }, [effectiveDraft, performAutosave]);

  const addNode = (nodeType: WorkflowNodeType) => {
    if (isLocked) return;
    const node: WorkflowNodeDefinition = {
      id: `${nodeType.type}-${crypto.randomUUID()}`,
      type: nodeType.type,
      name: nodeType.label,
      position: {
        x: 140 + effectiveDraft.nodes.length * 70,
        y: 120 + (effectiveDraft.nodes.length % 4) * 110,
      },
      config: { ...(nodeType.default_config ?? {}) },
      input_mapping: {},
      output_mapping: {},
      ai_brain: nodeType.supports_ai_brain,
      memory: nodeType.supports_memory ? "short_term" : null,
      retry_policy: { max_retries: 1, backoff: "exponential", retry_on: ["api_error"] },
      timeout_ms: nodeType.family === "ai" ? 30000 : 10000,
    };
    setDraft((current) => ({ ...current, nodes: [...current.nodes, node] }));
  };

  const updateSelectedNode = (update: (node: WorkflowNodeDefinition) => WorkflowNodeDefinition) => {
    if (!selectedNodeId || isLocked) return;
    setDraft((current) => ({
      ...current,
      nodes: current.nodes.map((node) => (node.id === selectedNodeId ? update(node) : node)),
    }));
  };

  const insertVariableToken = (token: string) => {
    if (!activeFieldKey || !selectedNode) return;
    const [bucket, key] = activeFieldKey.split("::");
    if (!bucket || !key) return;
    updateSelectedNode((node) => {
      if (bucket === "config") {
        const current = String(node.config[key] ?? "");
        return { ...node, config: { ...node.config, [key]: `${current}${token}` } };
      }
      if (bucket === "input_mapping") {
        return {
          ...node,
          input_mapping: {
            ...(node.input_mapping ?? {}),
            [key]: `${node.input_mapping?.[key] ?? ""}${token}`,
          },
        };
      }
      if (bucket === "output_mapping") {
        return {
          ...node,
          output_mapping: {
            ...(node.output_mapping ?? {}),
            [key]: `${node.output_mapping?.[key] ?? ""}${token}`,
          },
        };
      }
      return node;
    });
  };

  const canRun =
    !isLocked && validation.critical.length === 0 && effectiveDraft.nodes.length > 0;

  const downloadWorkflow = () => {
    const payload = {
      name: effectiveName,
      nodes: effectiveDraft.nodes,
      edges: effectiveDraft.edges,
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${effectiveName.toLowerCase().replace(/[^a-z0-9]+/g, "-") || "workflow"}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
    setFeedback("Workflow JSON downloaded.");
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
              disabled={generateMutation.isPending || isLocked}
              className="inline-flex h-12 items-center gap-2 rounded-full bg-primary px-5 text-sm font-semibold text-primary-foreground disabled:cursor-not-allowed disabled:opacity-50"
            >
              {generateMutation.isPending ? "Generating..." : "Generate"}
            </button>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <button
              onClick={() => saveMutation.mutate()}
              disabled={saveMutation.isPending || isLocked}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-50"
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
              disabled={publishMutation.isPending || isLocked}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Sparkles className="h-4 w-4" />
              Publish
            </button>
            <button
              onClick={downloadWorkflow}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold"
            >
              <Download className="h-4 w-4" />
              Download JSON
            </button>
            <button
              onClick={() => {
                if (!canRun) {
                  setFeedback("Fix validation warnings before running this workflow.");
                  return;
                }
                runMutation.mutate();
              }}
              disabled={runMutation.isPending || !canRun}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Play className="h-4 w-4" />
              Run Test
            </button>
            <input
              value={effectiveName}
              onChange={(e) => setName(e.target.value)}
              disabled={isLocked}
              className="ml-auto h-10 min-w-[220px] rounded-full border border-border bg-card px-4 text-sm outline-none disabled:cursor-not-allowed disabled:opacity-60"
            />
            <button
              onClick={() => setShowVersions((v) => !v)}
              className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-4 py-2 text-xs font-semibold"
            >
              <History className="h-4 w-4" />
              Versions
            </button>
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-3">
            {autosaveStatus !== "idle" ? (
              <span className={cn(
                "rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.14em]",
                autosaveStatus === "saving" ? "border border-amber-400/30 bg-amber-500/10 text-amber-300" : "border border-emerald-400/30 bg-emerald-500/10 text-emerald-300",
              )}>
                {autosaveStatus === "saving" ? "Autosaving..." : "Autosaved"}
              </span>
            ) : null}
            {generationConfidence != null ? (
              <span className={cn(
                "inline-flex items-center gap-1 rounded-full px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.14em]",
                generationConfidence >= 0.7 ? "border border-emerald-400/30 bg-emerald-500/10 text-emerald-300" :
                generationConfidence >= 0.4 ? "border border-amber-400/30 bg-amber-500/10 text-amber-300" :
                "border border-rose-400/30 bg-rose-500/10 text-rose-300",
              )}>
                <Shield className="h-3 w-3" />
                Confidence: {Math.round(generationConfidence * 100)}%
              </span>
            ) : null}
            {limitsQuery.data ? (
              <span className={cn(
                "inline-flex items-center gap-1 rounded-full border border-border bg-card px-3 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] text-muted-foreground",
                effectiveDraft.nodes.length > (limitsQuery.data.max_nodes * 0.8) && "border-amber-400/40 text-amber-300",
              )}>
                <GitBranch className="h-3 w-3" />
                {effectiveDraft.nodes.length}/{limitsQuery.data.max_nodes} nodes
              </span>
            ) : null}
          </div>

          {isLocked ? (
            <p className="mt-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
              Workflow locked. {lockSummary}
            </p>
          ) : null}
          {feedback ? (
            <p className="mt-3 rounded-xl border border-border bg-card px-3 py-2 text-sm text-muted-foreground">
              {feedback}
            </p>
          ) : null}
          {generationExplanation ? (
            <p className="mt-2 rounded-xl border border-violet-500/20 bg-violet-500/5 px-3 py-2 text-xs text-violet-300">
              <Sparkles className="mr-1 inline h-3 w-3" />
              {generationExplanation}
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
              {paletteOpen ? (
                <ChevronsLeft className="h-4 w-4" />
              ) : (
                <ChevronsRight className="h-4 w-4" />
              )}
            </button>

            {paletteOpen ? (
              <div className="mt-3 max-h-[calc(100vh-14rem)] space-y-3 overflow-y-auto">
                {groupedNodeTypes.map(([family, nodes]) => {
                  const isOpen = familyOpen[family] ?? true;
                  return (
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
                      {isOpen ? (
                        <ChevronDown className="h-4 w-4 text-muted-foreground" />
                      ) : (
                        <ChevronRight className="h-4 w-4 text-muted-foreground" />
                      )}
                    </button>
                    {isOpen ? (
                      <div className="mt-2 grid gap-2">
                        {nodes.map((nodeType) => (
                          <button
                            key={nodeType.type}
                            draggable={!isLocked}
                            onDragStart={(event) => {
                              event.dataTransfer.setData(
                                "application/auraflow-node-type",
                                nodeType.type,
                              );
                              event.dataTransfer.effectAllowed = "move";
                            }}
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
                  );
                })}
              </div>
            ) : null}
          </div>
        </aside>

        <section className="min-h-0 flex-1 p-2">
          <div className="h-full w-full">
            <WorkflowCanvas
              snapshot={effectiveDraft}
              nodeTypesCatalog={nodeTypesQuery.data ?? []}
              onSnapshotChange={setDraft}
              onSelectNode={setSelectedNodeId}
              isEditable={!isLocked}
              nodeStatuses={nodeStatuses}
              nodeWarnings={validation.map}
            />
          </div>
        </section>

        <aside className="w-[26rem] shrink-0 border-l border-border bg-card/70 p-2">
          <div className="flex h-full flex-col gap-2">
            <div className="rounded-2xl border border-border bg-background/80 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                Node Config
              </p>
              {selectedNode ? (
                <div className="mt-3 space-y-3">
                  <p className="text-sm font-semibold text-foreground">{selectedNode.name}</p>
                  {(Array.from(
                    new Set([
                      ...Object.keys(selectedNode.config ?? {}),
                      ...Object.keys(selectedNodeType?.config_schema ?? {}),
                    ]),
                  ) as string[]).map((field) => (
                    <label key={field} className="block space-y-1">
                      <span className="text-xs uppercase tracking-[0.14em] text-muted-foreground">
                        {field}
                      </span>
                      <input
                        value={String(selectedNode.config?.[field] ?? "")}
                        onFocus={() => setActiveFieldKey(`config::${field}`)}
                        onChange={(event) =>
                          updateSelectedNode((node) => ({
                            ...node,
                            config: { ...node.config, [field]: event.target.value },
                          }))
                        }
                        disabled={isLocked}
                        className="h-10 w-full rounded-xl border border-border bg-card px-3 text-sm outline-none disabled:cursor-not-allowed disabled:opacity-60"
                      />
                    </label>
                  ))}
                  <div className="grid gap-2">
                    <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">
                      Input Mapping
                    </p>
                    {Object.entries(selectedNode.input_mapping ?? {}).map(([key, value]) => (
                      <input
                        key={key}
                        value={value}
                        onFocus={() => setActiveFieldKey(`input_mapping::${key}`)}
                        onChange={(event) =>
                          updateSelectedNode((node) => ({
                            ...node,
                            input_mapping: {
                              ...(node.input_mapping ?? {}),
                              [key]: event.target.value,
                            },
                          }))
                        }
                        disabled={isLocked}
                        className="h-10 w-full rounded-xl border border-border bg-card px-3 text-sm outline-none disabled:cursor-not-allowed disabled:opacity-60"
                      />
                    ))}
                  </div>
                  <div className="grid gap-2">
                    <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">
                      Output Mapping
                    </p>
                    {Object.entries(selectedNode.output_mapping ?? {}).map(([key, value]) => (
                      <input
                        key={key}
                        value={value}
                        onFocus={() => setActiveFieldKey(`output_mapping::${key}`)}
                        onChange={(event) =>
                          updateSelectedNode((node) => ({
                            ...node,
                            output_mapping: {
                              ...(node.output_mapping ?? {}),
                              [key]: event.target.value,
                            },
                          }))
                        }
                        disabled={isLocked}
                        className="h-10 w-full rounded-xl border border-border bg-card px-3 text-sm outline-none disabled:cursor-not-allowed disabled:opacity-60"
                      />
                    ))}
                  </div>
                  <div className="rounded-xl border border-border bg-card p-3">
                    <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">
                      Variables
                    </p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      {selectableVariables.map((token) => (
                        <button
                          key={token}
                          onClick={() => insertVariableToken(token)}
                          className="rounded-full border border-border px-2 py-1 text-[10px] font-semibold text-muted-foreground"
                        >
                          {token}
                        </button>
                      ))}
                    </div>
                    {runLogsQuery.data && activeFieldKey ? (
                      <p className="mt-2 text-xs text-muted-foreground">
                        Preview available during run: resolved values are shown in debug logs.
                      </p>
                    ) : null}
                  </div>
                  {validation.map[selectedNode.id]?.length ? (
                    <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
                      {validation.map[selectedNode.id].map((message) => (
                        <p key={message}>Warning: {message}</p>
                      ))}
                    </div>
                  ) : null}
                  {/* Error Handling Config */}
                  <div className="rounded-xl border border-border bg-card p-3">
                    <p className="text-xs uppercase tracking-[0.14em] text-muted-foreground">
                      <AlertTriangle className="mr-1 inline h-3 w-3" />
                      Error Handling
                    </p>
                    <select
                      value={String((selectedNode.config as Record<string, unknown>)?.on_error_strategy ?? "fail")}
                      onChange={(e) =>
                        updateSelectedNode((node) => ({
                          ...node,
                          config: { ...node.config, on_error_strategy: e.target.value },
                        }))
                      }
                      disabled={isLocked}
                      className="mt-2 h-9 w-full rounded-lg border border-border bg-card px-3 text-xs outline-none"
                    >
                      <option value="fail">Fail (default)</option>
                      <option value="retry">Retry</option>
                      <option value="skip">Skip</option>
                      <option value="fallback">Fallback to node</option>
                      <option value="retry_then_fallback">Retry then fallback</option>
                    </select>
                  </div>
                </div>
              ) : (
                <p className="mt-2 text-sm text-muted-foreground">Select a node to edit settings.</p>
              )}
            </div>

            <div className="min-h-0 flex-1 rounded-2xl border border-border bg-background/80 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                Run Debug
              </p>
              {validation.critical.length ? (
                <div className="mt-3 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-200">
                  {validation.critical.map((item, index) => (
                    <p key={`${item.nodeId}-${index}`}>
                      {item.nodeId}: {item.message}
                    </p>
                  ))}
                </div>
              ) : null}
              <div className="mt-3 max-h-[28vh] space-y-2 overflow-y-auto rounded-xl border border-border bg-card p-3">
                {(runLogsQuery.data?.logs ?? []).length ? (
                  (runLogsQuery.data?.logs ?? []).map((log, index) => (
                    <div key={`${log.node_id}-${log.timestamp}-${index}`} className="rounded-lg border border-border p-2 text-xs">
                      <p className="font-semibold text-foreground">
                        [{log.node_type}] {log.node_id} - {log.status}
                      </p>
                      <p className="mt-1 text-muted-foreground">{log.message}</p>
                      <p className="mt-1 text-[10px] uppercase tracking-[0.14em] text-muted-foreground">
                        Attempt {log.attempt} • {new Date(log.timestamp).toLocaleTimeString()}
                      </p>
                    </div>
                  ))
                ) : (
                  <p className="text-xs text-muted-foreground">Run logs will appear here once a test run starts.</p>
                )}
              </div>
            </div>

            {/* Version History Panel */}
            {showVersions ? (
              <div className="rounded-2xl border border-border bg-background/80 p-3">
                <div className="flex items-center gap-2">
                  <History className="h-4 w-4 text-muted-foreground" />
                  <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
                    Version History
                  </p>
                </div>
                <div className="mt-3 max-h-[20vh] space-y-2 overflow-y-auto">
                  {(versionsQuery.data ?? []).length ? (
                    (versionsQuery.data ?? []).map((version) => (
                      <div
                        key={version.id}
                        className="flex items-center justify-between rounded-lg border border-border p-2 text-xs"
                      >
                        <div>
                          <p className="font-semibold text-foreground">v{version.version_number}</p>
                          <p className="text-[10px] text-muted-foreground">
                            {new Date(version.created_at).toLocaleString()}
                          </p>
                        </div>
                        <button
                          onClick={() => rollbackMutation.mutate(version.id)}
                          disabled={rollbackMutation.isPending}
                          className="inline-flex items-center gap-1 rounded-full border border-border px-2 py-1 text-[10px] font-semibold text-muted-foreground hover:border-primary/40 hover:text-foreground"
                        >
                          <RotateCcw className="h-3 w-3" />
                          Rollback
                        </button>
                      </div>
                    ))
                  ) : (
                    <p className="text-xs text-muted-foreground">No versions published yet.</p>
                  )}
                </div>
              </div>
            ) : null}
          </div>
        </aside>
      </main>
    </div>
  );
}
