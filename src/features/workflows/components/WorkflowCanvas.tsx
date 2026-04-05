"use client";

import { useCallback, useEffect, useMemo } from "react";
import ReactFlow, {
  addEdge,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  type Connection,
  type Edge,
  type Node,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";

import type { WorkflowDefinition, WorkflowNodeType } from "@/lib/api";
import { cn } from "@/lib/utils";

import { PlatformNode } from "./nodes/PlatformNode";

interface WorkflowCanvasProps {
  snapshot: WorkflowDefinition;
  nodeTypesCatalog: WorkflowNodeType[];
  onSnapshotChange: (snapshot: WorkflowDefinition) => void;
  onSelectNode?: (nodeId: string | null) => void;
}

export function WorkflowCanvas({
  snapshot,
  nodeTypesCatalog,
  onSnapshotChange,
  onSelectNode,
}: WorkflowCanvasProps) {
  const initialNodes = useMemo<Node[]>(
    () =>
      snapshot.nodes.map((node) => {
        const catalog = nodeTypesCatalog.find((item) => item.type === node.type);
        return {
          id: node.id,
          type: "platform",
          position: node.position,
          data: {
            ...node,
            label: catalog?.label ?? node.name,
            family: catalog?.family ?? "core",
            summary:
              typeof node.config.prompt === "string"
                ? node.config.prompt
                : typeof node.config.expression === "string"
                  ? node.config.expression
                  : `${node.name} configuration`,
          },
        };
      }),
    [snapshot.nodes, nodeTypesCatalog],
  );

  const initialEdges = useMemo<Edge[]>(
    () =>
      snapshot.edges.map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.condition,
        animated: edge.condition === "true",
        style: { strokeWidth: 2 },
      })),
    [snapshot.edges],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => setNodes(initialNodes), [initialNodes, setNodes]);
  useEffect(() => setEdges(initialEdges), [initialEdges, setEdges]);

  useEffect(() => {
    onSnapshotChange({
      ...snapshot,
      nodes: nodes.map((node) => {
        const original = snapshot.nodes.find((item) => item.id === node.id);
        return {
          ...(original ?? {
            id: node.id,
            type: "transform",
            name: String(node.data?.label ?? "Node"),
            config: {},
            ai_brain: false,
            memory: null,
            retry_policy: { max_retries: 0, backoff: "none", retry_on: [] },
            timeout_ms: 10000,
          }),
          position: node.position,
        };
      }),
      edges: edges.map((edge) => {
        const original = snapshot.edges.find((item) => item.id === edge.id);
        return {
          id: edge.id,
          source: edge.source,
          target: edge.target,
          condition: String(original?.condition ?? edge.label ?? "true"),
        };
      }),
    });
  }, [edges, nodes, onSnapshotChange, snapshot]);

  const onConnect = useCallback(
    (params: Connection) => {
      setEdges((current) =>
        addEdge(
          {
            ...params,
            id: `edge-${crypto.randomUUID()}`,
            label: "true",
            animated: true,
            style: { strokeWidth: 2 },
          },
          current,
        ),
      );
    },
    [setEdges],
  );

  return (
    <div className="relative h-full w-full overflow-hidden rounded-[2rem] border border-border bg-background">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onPaneClick={() => onSelectNode?.(null)}
        onNodeClick={(_, node) => onSelectNode?.(node.id)}
        nodeTypes={{ platform: PlatformNode }}
        fitView
        className="bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.04),_transparent_40%),linear-gradient(180deg,rgba(2,6,23,0.55),rgba(2,6,23,0.9))]"
      >
        <Background color="#334155" gap={24} variant={BackgroundVariant.Dots} />
        <Controls className="border border-border bg-card fill-foreground" />
        <MiniMap
          className="overflow-hidden rounded-xl border border-border bg-card"
          maskColor="rgba(2, 6, 23, 0.55)"
          nodeColor={(node) => {
            const family = node.data?.family;
            if (family === "trigger") return "#10b981";
            if (family === "ai") return "#8b5cf6";
            if (family === "human") return "#f59e0b";
            if (family === "integration") return "#f43f5e";
            return "#38bdf8";
          }}
        />
      </ReactFlow>

      <div className="pointer-events-none absolute left-5 top-5 z-10">
        <div className="glass rounded-2xl px-4 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Live canvas editor
        </div>
      </div>

      <div className="pointer-events-none absolute bottom-5 right-5 z-10">
        <div className="glass rounded-2xl px-4 py-3 text-xs text-muted-foreground">
          <span className={cn("font-semibold text-foreground")}>{nodes.length}</span> nodes
          <span className="mx-2">•</span>
          <span className={cn("font-semibold text-foreground")}>{edges.length}</span> edges
        </div>
      </div>
    </div>
  );
}
