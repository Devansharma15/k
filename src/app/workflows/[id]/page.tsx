"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bot, CheckCheck, Clock3, CopyPlus, GitBranch, History, Play, Plus, RotateCcw, Save, Settings2, ShieldCheck, Sparkles, WandSparkles, XCircle } from "lucide-react";
import { useRouter } from "next/navigation";

import { WorkflowCanvas } from "@/features/workflows/components/WorkflowCanvas";
import {
  decideWorkflowApproval,
  generateWorkflowFromPrompt,
  getPlatformRun,
  getPlatformWorkflow,
  instantiateWorkflowTemplate,
  listPlatformRuns,
  listPlatformVersions,
  listWorkflowApprovals,
  listWorkflowNodeTypes,
  listWorkflowTemplates,
  listWorkflowUsage,
  publishPlatformWorkflow,
  rollbackPlatformWorkflow,
  runPlatformWorkflow,
  updatePlatformWorkflow,
  validatePlatformWorkflow,
  type ApprovalTask,
  type WorkflowDefinition,
  type WorkflowEdgeDefinition,
  type WorkflowNodeDefinition,
  type WorkflowNodeType,
} from "@/lib/api";
import { cn } from "@/lib/utils";

const emptySnapshot: WorkflowDefinition = {
  name: "New Workflow",
  nodes: [{ id: "trigger-1", type: "trigger_webhook", name: "Webhook Trigger", position: { x: 100, y: 180 }, config: { path: "/webhooks/new-flow" }, ai_brain: false, memory: null, retry_policy: { max_retries: 0, backoff: "none", retry_on: [] }, timeout_ms: 5000 }],
  edges: [],
};

type RunMode = "manual" | "trigger" | "test";

export default function WorkflowPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  const qc = useQueryClient();
  const [draft, setDraft] = useState(emptySnapshot);
  const [name, setName] = useState("Workflow Studio");
  const [prompt, setPrompt] = useState("Send Slack message when new Stripe payment is received and store in Notion");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [runMode, setRunMode] = useState<RunMode>("test");
  const [runDebug, setRunDebug] = useState(true);
  const [runInput, setRunInput] = useState('{\n  "source": "workflow-studio"\n}');
  const [configText, setConfigText] = useState("{}");
  const [feedback, setFeedback] = useState<string | null>(null);

  const workflowQuery = useQuery({ queryKey: ["platform-workflow", params.id], queryFn: () => getPlatformWorkflow(params.id) });
  const nodeTypesQuery = useQuery({ queryKey: ["workflow-node-types"], queryFn: listWorkflowNodeTypes });
  const runsQuery = useQuery({ queryKey: ["workflow-runs", params.id], queryFn: () => listPlatformRuns(params.id), refetchInterval: 4000 });
  const versionsQuery = useQuery({ queryKey: ["workflow-versions", params.id], queryFn: () => listPlatformVersions(params.id) });
  const templatesQuery = useQuery({ queryKey: ["workflow-templates"], queryFn: listWorkflowTemplates });
  const approvalsQuery = useQuery({ queryKey: ["workflow-approvals"], queryFn: listWorkflowApprovals, refetchInterval: 4000 });
  const usageQuery = useQuery({ queryKey: ["workflow-usage"], queryFn: listWorkflowUsage });
  const selectedRunQuery = useQuery({
    queryKey: ["workflow-run", params.id, selectedRunId],
    queryFn: () => getPlatformRun(params.id, selectedRunId!),
    enabled: Boolean(selectedRunId),
    refetchInterval: 4000,
  });

  useEffect(() => {
    if (!workflowQuery.data) return;
    setName(workflowQuery.data.name);
    setDraft(workflowQuery.data.draft_snapshot);
  }, [workflowQuery.data]);

  useEffect(() => {
    if (!selectedRunId && runsQuery.data?.length) setSelectedRunId(runsQuery.data[0].id);
  }, [runsQuery.data, selectedRunId]);

  const selectedNode = useMemo(() => draft.nodes.find((node) => node.id === selectedNodeId) ?? null, [draft.nodes, selectedNodeId]);
  const groupedNodeTypes = useMemo(() => {
    const groups = new Map<string, WorkflowNodeType[]>();
    for (const item of nodeTypesQuery.data ?? []) groups.set(item.family, [...(groups.get(item.family) ?? []), item]);
    return Array.from(groups.entries());
  }, [nodeTypesQuery.data]);
  const usageSummary = useMemo(() => (usageQuery.data ?? []).reduce((acc, row) => ({ tokens: acc.tokens + row.tokens_used, cost: acc.cost + row.cost }), { tokens: 0, cost: 0 }), [usageQuery.data]);
  const pendingApprovals = useMemo(() => (approvalsQuery.data ?? []).filter((item) => item.workflow_id === params.id && item.status === "pending"), [approvalsQuery.data, params.id]);

  useEffect(() => setConfigText(selectedNode ? JSON.stringify(selectedNode.config, null, 2) : "{}"), [selectedNode]);

  const invalidateCore = async () => {
    await Promise.all([
      qc.invalidateQueries({ queryKey: ["platform-workflow", params.id] }),
      qc.invalidateQueries({ queryKey: ["workflow-runs", params.id] }),
      qc.invalidateQueries({ queryKey: ["workflow-versions", params.id] }),
      qc.invalidateQueries({ queryKey: ["workflow-approvals"] }),
      qc.invalidateQueries({ queryKey: ["workflow-usage"] }),
    ]);
  };

  const saveMutation = useMutation({ mutationFn: () => updatePlatformWorkflow(params.id, name, draft), onSuccess: async (wf) => { setFeedback("Draft saved."); setDraft(wf.draft_snapshot); await invalidateCore(); }, onError: (e: Error) => setFeedback(e.message) });
  const validateMutation = useMutation({ mutationFn: () => validatePlatformWorkflow(params.id, name, draft), onSuccess: (r) => setFeedback(`Validation passed for ${r.nodes} nodes and ${r.edges} edges.`), onError: (e: Error) => setFeedback(e.message) });
  const publishMutation = useMutation({ mutationFn: () => publishPlatformWorkflow(params.id), onSuccess: async () => { setFeedback("Published a new immutable version."); await invalidateCore(); }, onError: (e: Error) => setFeedback(e.message) });
  const runMutation = useMutation({ mutationFn: () => runPlatformWorkflow(params.id, { mode: runMode, debug: runDebug, input: parseJsonRecord(runInput) }), onSuccess: async (run) => { setSelectedRunId(run.id); setFeedback(`Run started in ${run.mode} mode.`); await invalidateCore(); }, onError: (e: Error) => setFeedback(e.message) });
  const rollbackMutation = useMutation({ mutationFn: (versionId: string) => rollbackPlatformWorkflow(params.id, versionId), onSuccess: async (wf) => { setDraft(wf.draft_snapshot); setFeedback("Rollback copied the selected version into draft."); await invalidateCore(); }, onError: (e: Error) => setFeedback(e.message) });
  const generateMutation = useMutation({ mutationFn: () => generateWorkflowFromPrompt(prompt), onSuccess: (generated) => { setDraft(generated); setName(generated.name); setSelectedNodeId(null); setFeedback("Prompt converted into a draft graph."); }, onError: (e: Error) => setFeedback(e.message) });
  const instantiateMutation = useMutation({ mutationFn: (templateId: string) => instantiateWorkflowTemplate(templateId), onSuccess: (wf) => router.push(`/workflows/${wf.id}`), onError: (e: Error) => setFeedback(e.message) });
  const approvalMutation = useMutation({ mutationFn: ({ approvalId, decision }: { approvalId: string; decision: "approve" | "reject" }) => decideWorkflowApproval(approvalId, decision), onSuccess: async () => { setFeedback("Approval updated."); await invalidateCore(); }, onError: (e: Error) => setFeedback(e.message) });

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
    setSelectedNodeId(node.id);
  };

  const updateNode = (patch: Partial<WorkflowNodeDefinition>) => {
    if (!selectedNode) return;
    setDraft((current) => ({ ...current, nodes: current.nodes.map((node) => (node.id === selectedNode.id ? { ...node, ...patch } : node)) }));
  };

  const removeNode = () => {
    if (!selectedNode) return;
    setDraft((current) => ({
      ...current,
      nodes: current.nodes.filter((node) => node.id !== selectedNode.id),
      edges: current.edges.filter((edge) => edge.source !== selectedNode.id && edge.target !== selectedNode.id),
    }));
    setSelectedNodeId(null);
  };

  return (
    <div className="flex h-full min-h-[calc(100vh-4rem)] overflow-hidden bg-background">
      <aside className="flex w-[340px] flex-col border-r border-border bg-card/80 p-5 backdrop-blur-md">
        <Panel>
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">Agent Builder</p>
          <input value={name} onChange={(e) => setName(e.target.value)} className="mt-3 w-full bg-transparent text-2xl font-semibold tracking-tight outline-none" />
          <p className="mt-2 text-sm leading-6 text-muted-foreground">Draft, validate, test, publish, and roll back workflow versions with a stateful graph runtime.</p>
          <div className="mt-4 flex flex-wrap gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground"><span>{workflowQuery.data?.status ?? "draft"}</span><span>•</span><span>{draft.nodes.length} nodes</span><span>•</span><span>{draft.edges.length} edges</span></div>
        </Panel>
        <Panel className="mt-5">
          <div className="flex items-center gap-2"><WandSparkles className="h-4 w-4 text-violet-400" /><p className="text-sm font-semibold">Prompt to Workflow</p></div>
          <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} className="mt-4 h-32 w-full rounded-[1.25rem] border border-border bg-card px-4 py-4 text-sm outline-none" />
          <button onClick={() => generateMutation.mutate()} className="mt-4 inline-flex w-full items-center justify-center gap-2 rounded-full bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground"><Bot className="h-4 w-4" />{generateMutation.isPending ? "Generating..." : "Generate Draft"}</button>
        </Panel>
        <Panel className="mt-5">
          <div className="flex items-center gap-2"><Play className="h-4 w-4 text-emerald-400" /><p className="text-sm font-semibold">Execution Mode</p></div>
          <div className="mt-4 grid grid-cols-3 gap-2">{(["manual", "trigger", "test"] as RunMode[]).map((mode) => <button key={mode} onClick={() => setRunMode(mode)} className={cn("rounded-full border px-3 py-2 text-xs font-semibold uppercase tracking-[0.16em]", runMode === mode ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card text-muted-foreground")}>{mode}</button>)}</div>
          <label className="mt-4 flex items-center gap-2 text-sm text-muted-foreground"><input type="checkbox" checked={runDebug} onChange={(e) => setRunDebug(e.target.checked)} className="h-4 w-4 rounded border-border" />Capture debug trace</label>
          <textarea value={runInput} onChange={(e) => setRunInput(e.target.value)} className="mt-4 h-28 w-full rounded-[1.25rem] border border-border bg-card px-4 py-4 font-mono text-xs outline-none" />
          <div className="mt-4 grid gap-3">
            <ActionButton icon={<Save className="h-4 w-4" />} label={saveMutation.isPending ? "Saving..." : "Save Draft"} onClick={() => saveMutation.mutate()} />
            <ActionButton icon={<CheckCheck className="h-4 w-4" />} label={validateMutation.isPending ? "Validating..." : "Validate Graph"} onClick={() => validateMutation.mutate()} />
            <ActionButton icon={<Sparkles className="h-4 w-4" />} label={publishMutation.isPending ? "Publishing..." : "Publish Version"} onClick={() => publishMutation.mutate()} />
            <ActionButton icon={<Play className="h-4 w-4" />} label={runMutation.isPending ? "Running..." : "Run Workflow"} onClick={() => runMutation.mutate()} />
          </div>
          {feedback ? <p className="mt-4 rounded-2xl border border-border bg-card px-4 py-3 text-sm text-muted-foreground">{feedback}</p> : null}
        </Panel>
        <Panel className="mt-5">
          <div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-sky-400" /><p className="text-sm font-semibold">Cost Tracking</p></div>
          <div className="mt-4 grid grid-cols-2 gap-3"><MetricCard label="Tokens" value={String(usageSummary.tokens)} /><MetricCard label="Cost" value={`$${usageSummary.cost.toFixed(4)}`} /></div>
        </Panel>
      </aside>

      <main className="grid min-w-0 flex-1 gap-0 xl:grid-cols-[220px_minmax(0,1fr)_400px]">
        <aside className="border-r border-border bg-card/70 p-4">
          <div className="grid h-full gap-4 overflow-y-auto">
            <Panel className="p-4">
              <div className="flex items-center gap-2"><Plus className="h-4 w-4 text-emerald-400" /><p className="text-sm font-semibold">Node Palette</p></div>
              <div className="mt-4 space-y-4">
                {groupedNodeTypes.map(([family, nodes]) => (
                  <div key={family}>
                    <p className="text-[11px] font-semibold uppercase tracking-[0.18em] text-muted-foreground">{family}</p>
                    <div className="mt-2 grid gap-2">{nodes.map((nodeType) => <button key={nodeType.type} onClick={() => addNode(nodeType)} className="rounded-2xl border border-border bg-card px-3 py-3 text-left transition hover:-translate-y-0.5 hover:border-primary/40"><p className="text-sm font-semibold">{nodeType.label}</p><p className="mt-1 text-[11px] uppercase tracking-[0.16em] text-muted-foreground">{nodeType.type}</p></button>)}</div>
                  </div>
                ))}
              </div>
            </Panel>
          </div>
        </aside>

        <div className="min-h-0 p-6">
          <WorkflowCanvas snapshot={draft} nodeTypesCatalog={nodeTypesQuery.data ?? []} onSnapshotChange={setDraft} onSelectNode={setSelectedNodeId} />
        </div>

        <aside className="border-l border-border bg-card/70 p-5">
          <div className="grid h-full gap-5 overflow-y-auto">
            <Panel>
              <div className="flex items-center gap-2"><Settings2 className="h-4 w-4 text-sky-400" /><p className="text-sm font-semibold">Node Settings</p></div>
              {selectedNode ? (
                <div className="mt-4 space-y-4">
                  <input value={selectedNode.name} onChange={(e) => updateNode({ name: e.target.value })} className="w-full rounded-2xl border border-border bg-card px-4 py-3 text-sm outline-none" />
                  <div className="grid grid-cols-2 gap-3">
                    <NumberField label="Timeout (ms)" value={selectedNode.timeout_ms} onChange={(value) => updateNode({ timeout_ms: value })} />
                    <label className="text-xs text-muted-foreground">Memory<select value={selectedNode.memory ?? ""} onChange={(e) => updateNode({ memory: e.target.value === "" ? null : (e.target.value as WorkflowNodeDefinition["memory"]) })} className="mt-2 w-full rounded-2xl border border-border bg-card px-4 py-3 text-sm outline-none"><option value="">None</option><option value="short_term">short_term</option><option value="long_term">long_term</option><option value="dataset_ref">dataset_ref</option></select></label>
                  </div>
                  <label className="flex items-center gap-2 text-sm text-muted-foreground"><input type="checkbox" checked={selectedNode.ai_brain} onChange={(e) => updateNode({ ai_brain: e.target.checked })} className="h-4 w-4 rounded border-border" />Enable AI brain pre-check</label>
                  <div className="grid grid-cols-2 gap-3">
                    <NumberField label="Max retries" value={selectedNode.retry_policy.max_retries} onChange={(value) => updateNode({ retry_policy: { ...selectedNode.retry_policy, max_retries: value } })} />
                    <label className="text-xs text-muted-foreground">Backoff<select value={selectedNode.retry_policy.backoff} onChange={(e) => updateNode({ retry_policy: { ...selectedNode.retry_policy, backoff: e.target.value } })} className="mt-2 w-full rounded-2xl border border-border bg-card px-4 py-3 text-sm outline-none"><option value="none">none</option><option value="exponential">exponential</option></select></label>
                  </div>
                  <label className="text-xs text-muted-foreground">Retry on<input value={selectedNode.retry_policy.retry_on.join(", ")} onChange={(e) => updateNode({ retry_policy: { ...selectedNode.retry_policy, retry_on: e.target.value.split(",").map((item) => item.trim()).filter(Boolean) } })} className="mt-2 w-full rounded-2xl border border-border bg-card px-4 py-3 text-sm outline-none" /></label>
                  <label className="text-xs text-muted-foreground">Config JSON<textarea value={configText} onChange={(e) => setConfigText(e.target.value)} className="mt-2 h-36 w-full rounded-[1.25rem] border border-border bg-card px-4 py-4 font-mono text-xs outline-none" /></label>
                  <div className="grid grid-cols-2 gap-3">
                    <ActionButton icon={<Save className="h-4 w-4" />} label="Apply Config" onClick={() => { try { updateNode({ config: parseJsonRecord(configText) }); setFeedback("Node configuration updated."); } catch (error) { setFeedback(error instanceof Error ? error.message : "Invalid node configuration."); } }} />
                    <ActionButton icon={<XCircle className="h-4 w-4" />} label="Remove Node" onClick={removeNode} />
                  </div>
                </div>
              ) : <p className="mt-4 text-sm text-muted-foreground">Select a node on the canvas to edit config, memory, timeout, and retry strategy.</p>}
            </Panel>

            <Panel>
              <div className="flex items-center gap-2"><GitBranch className="h-4 w-4 text-violet-400" /><p className="text-sm font-semibold">Edge Conditions</p></div>
              <div className="mt-4 space-y-3">
                {draft.edges.length ? draft.edges.map((edge) => <EdgeConditionEditor key={edge.id} edge={edge} onChange={(edgeId, value) => setDraft((current) => ({ ...current, edges: current.edges.map((item) => item.id === edgeId ? { ...item, condition: value } : item) }))} />) : <p className="text-sm text-muted-foreground">Connect nodes on the canvas to define branch conditions here.</p>}
              </div>
            </Panel>

            <Panel>
              <div className="flex items-center gap-2"><History className="h-4 w-4 text-amber-400" /><p className="text-sm font-semibold">Versions</p></div>
              <div className="mt-4 space-y-2">{versionsQuery.data?.map((version) => <div key={version.id} className="flex items-center justify-between gap-3 rounded-2xl border border-border bg-card px-4 py-3"><div><p className="font-semibold">v{version.version_number}</p><p className="text-xs text-muted-foreground">{version.created_at}</p></div><button onClick={() => rollbackMutation.mutate(version.id)} className="rounded-full border border-border p-2 text-muted-foreground transition hover:border-primary/40 hover:text-foreground"><RotateCcw className="h-4 w-4" /></button></div>)}</div>
            </Panel>

            <Panel>
              <div className="flex items-center gap-2"><CopyPlus className="h-4 w-4 text-emerald-400" /><p className="text-sm font-semibold">Templates</p></div>
              <div className="mt-4 space-y-2">{templatesQuery.data?.slice(0, 8).map((template) => <button key={template.id} onClick={() => instantiateMutation.mutate(template.id)} className="w-full rounded-2xl border border-border bg-card px-4 py-3 text-left transition hover:-translate-y-0.5 hover:border-primary/40"><p className="font-semibold">{template.name}</p><p className="mt-1 text-xs text-muted-foreground">{template.category} • {template.difficulty}</p></button>)}</div>
            </Panel>

            <Panel>
              <div className="flex items-center gap-2"><Clock3 className="h-4 w-4 text-sky-400" /><p className="text-sm font-semibold">Run Timeline</p></div>
              <div className="mt-4 space-y-2">{runsQuery.data?.map((run) => <button key={run.id} onClick={() => setSelectedRunId(run.id)} className={cn("w-full rounded-2xl border px-4 py-3 text-left transition", selectedRunId === run.id ? "border-primary bg-primary/5" : "border-border bg-card hover:border-primary/40")}><div className="flex items-center justify-between gap-3"><p className="font-semibold">{run.mode}</p><span className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{run.status}</span></div><p className="mt-1 text-xs text-muted-foreground">{run.created_at}</p></button>)}</div>
              <div className="mt-4 space-y-2">{selectedRunQuery.data?.steps?.map((step) => <div key={step.id} className={cn("rounded-2xl border px-4 py-3", step.status === "failed" ? "border-destructive/40 bg-destructive/5" : "border-border bg-card")}><div className="flex items-center justify-between gap-3"><p className="font-semibold">{step.node_type}</p><span className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{step.status}</span></div><p className="mt-1 text-xs text-muted-foreground">Attempt {step.attempt}</p>{step.error_message ? <p className="mt-2 text-xs text-destructive">{step.error_message}</p> : null}</div>)}</div>
            </Panel>

            <Panel>
              <div className="flex items-center gap-2"><ShieldCheck className="h-4 w-4 text-rose-400" /><p className="text-sm font-semibold">Approvals</p></div>
              <div className="mt-4 space-y-3">{pendingApprovals.length ? pendingApprovals.map((approval) => <ApprovalCard key={approval.id} approval={approval} onDecision={(decision) => approvalMutation.mutate({ approvalId: approval.id, decision })} />) : <p className="text-sm text-muted-foreground">Human approval nodes will surface here when a run pauses.</p>}</div>
            </Panel>
          </div>
        </aside>
      </main>
    </div>
  );
}

function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={cn("rounded-[1.5rem] border border-border bg-background/70 p-5", className)}>{children}</section>;
}

function ActionButton({ icon, label, onClick }: { icon: ReactNode; label: string; onClick: () => void }) {
  return <button onClick={onClick} className="inline-flex items-center justify-center gap-2 rounded-full border border-border bg-card px-4 py-3 text-sm font-semibold transition hover:-translate-y-0.5 hover:border-primary/40">{icon}{label}</button>;
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return <div className="rounded-2xl border border-border bg-card px-4 py-3"><p className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{label}</p><p className="mt-2 text-xl font-semibold">{value}</p></div>;
}

function NumberField({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return <label className="text-xs text-muted-foreground">{label}<input type="number" value={value} onChange={(e) => onChange(Number(e.target.value) || 0)} className="mt-2 w-full rounded-2xl border border-border bg-card px-4 py-3 text-sm outline-none" /></label>;
}

function EdgeConditionEditor({ edge, onChange }: { edge: WorkflowEdgeDefinition; onChange: (edgeId: string, value: string) => void }) {
  return <div className="rounded-2xl border border-border bg-card px-4 py-3"><p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">{edge.source} → {edge.target}</p><input value={edge.condition} onChange={(e) => onChange(edge.id, e.target.value)} className="mt-2 w-full rounded-xl border border-border bg-background px-3 py-2 text-sm outline-none" /></div>;
}

function ApprovalCard({ approval, onDecision }: { approval: ApprovalTask; onDecision: (decision: "approve" | "reject") => void }) {
  return <div className="rounded-2xl border border-border bg-card px-4 py-3"><p className="font-semibold">{approval.message}</p><p className="mt-1 text-xs text-muted-foreground">{approval.created_at}</p><div className="mt-3 grid grid-cols-2 gap-3"><ActionButton icon={<CheckCheck className="h-4 w-4" />} label="Approve" onClick={() => onDecision("approve")} /><ActionButton icon={<XCircle className="h-4 w-4" />} label="Reject" onClick={() => onDecision("reject")} /></div></div>;
}

function parseJsonRecord(value: string): Record<string, unknown> {
  const parsed = JSON.parse(value) as unknown;
  if (!parsed || typeof parsed !== "object" || Array.isArray(parsed)) throw new Error("Input must be a JSON object.");
  return parsed as Record<string, unknown>;
}
