"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import ReactFlow, {
  addEdge,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
  type EdgeChange,
  type ReactFlowInstance,
  useEdgesState,
  useNodesState,
} from "reactflow";
import "reactflow/dist/style.css";

import type { WorkflowDefinition, WorkflowNodeType } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Wand2 } from "lucide-react";
import { getLayoutedElements } from "@/lib/layoutUtils";

import { PlatformNode } from "./nodes/PlatformNode";

interface WorkflowCanvasProps {
  snapshot: WorkflowDefinition;
  nodeTypesCatalog: WorkflowNodeType[];
  onSnapshotChange: (snapshot: WorkflowDefinition) => void;
  onSelectNode?: (nodeId: string | null) => void;
  isEditable?: boolean;
  nodeStatuses?: Record<string, string>;
  nodeWarnings?: Record<string, string[]>;
}

type CanvasNodeData = {
  id: string;
  type: string;
  name: string;
  config: Record<string, unknown>;
  input_mapping?: Record<string, string>;
  output_mapping?: Record<string, string>;
  ai_brain: boolean;
  memory: "short_term" | "long_term" | "dataset_ref" | null;
  retry_policy: {
    max_retries: number;
    backoff: string;
    retry_on: string[];
  };
  timeout_ms: number;
  label?: string;
  family?: string;
  summary?: string;
  status?: string;
  warnings?: string[];
};

export function WorkflowCanvas({
  snapshot,
  nodeTypesCatalog,
  onSnapshotChange,
  onSelectNode,
  isEditable = true,
  nodeStatuses = {},
  nodeWarnings = {},
}: WorkflowCanvasProps) {
  const flowWrapperRef = useRef<HTMLDivElement | null>(null);
  const rfInstanceRef = useRef<ReactFlowInstance | null>(null);

  const initialNodes = useMemo<Node[]>(
    () =>
      (snapshot?.nodes || []).map((node) => {
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
              typeof node.config?.prompt === "string"
                ? node.config.prompt
                : typeof node.config?.expression === "string"
                  ? node.config.expression
                  : `${node.name} configuration`,
            status: nodeStatuses[node.id] ?? "idle",
            warnings: nodeWarnings[node.id] ?? [],
          },
        };
      }),
    [snapshot?.nodes, nodeTypesCatalog, nodeStatuses, nodeWarnings],
  );

  const initialEdges = useMemo<Edge[]>(
    () =>
      (snapshot?.edges || []).map((edge) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.condition,
        animated: edge.condition === "true",
        style: { strokeWidth: 2 },
      })),
    [snapshot?.edges],
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const lastSyncedSnapshotRef = useRef<string>("");

  // Sync prop changes -> local state (only if changed from outside)
  useEffect(() => {
    const safeNodes = snapshot?.nodes || [];
    const safeEdges = snapshot?.edges || [];
    const snapshotStr = JSON.stringify({ nodes: safeNodes, edges: safeEdges });
    if (snapshotStr !== lastSyncedSnapshotRef.current) {
      setNodes(initialNodes);
      setEdges(initialEdges);
      lastSyncedSnapshotRef.current = snapshotStr;
    }
  }, [initialNodes, initialEdges, snapshot?.nodes, snapshot?.edges, setNodes, setEdges]);

  // Sync internal changes -> parent state
  useEffect(() => {
    const updatedNodes = nodes.map((node) => {
      const nodeData = node.data as CanvasNodeData;
      return {
        id: nodeData.id ?? node.id,
        type: nodeData.type,
        name: nodeData.name ?? nodeData.label ?? "Node",
        position: node.position,
        config: nodeData.config ?? {},
        input_mapping: nodeData.input_mapping ?? {},
        output_mapping: nodeData.output_mapping ?? {},
        ai_brain: Boolean(nodeData.ai_brain),
        memory: nodeData.memory ?? null,
        retry_policy:
          nodeData.retry_policy ?? { max_retries: 0, backoff: "none", retry_on: [] },
        timeout_ms: Number(nodeData.timeout_ms ?? 10000),
      };
    });

    const updatedEdges = edges.map((edge) => {
      return {
        id: edge.id,
        source: edge.source,
        target: edge.target,
        condition: String(edge.label ?? "true"),
      };
    });

    const newSnapshot: WorkflowDefinition = {
      ...snapshot,
      nodes: updatedNodes,
      edges: updatedEdges,
    };

    const newSnapshotStr = JSON.stringify({ nodes: newSnapshot.nodes, edges: newSnapshot.edges });
    
    if (newSnapshotStr !== lastSyncedSnapshotRef.current) {
      lastSyncedSnapshotRef.current = newSnapshotStr;
      onSnapshotChange(newSnapshot);
    }
  }, [nodes, edges, onSnapshotChange, snapshot]);

  const applyLayout = useCallback((currentNodes: Node[], currentEdges: Edge[]) => {
    const { nodes: layoutedNodes, edges: layoutedEdges } = getLayoutedElements(currentNodes, currentEdges);
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
    window.requestAnimationFrame(() => {
      rfInstanceRef.current?.fitView({ duration: 500, padding: 0.15 });
    });
  }, [setNodes, setEdges]);

  const onConnect = useCallback(
    (params: Connection) => {
      if (!isEditable) return;
      
      let label = "true";
      let strokeColor = "inherit";
      
      if (params.sourceHandle === "true") {
        label = "Yes";
        strokeColor = "#10b981"; // Emerald
      } else if (params.sourceHandle === "false") {
        label = "No";
        strokeColor = "#f43f5e"; // Rose
      }

      if (!params.source || !params.target) return;

      const newEdge: Edge = {
        ...params,
        source: params.source,
        target: params.target,
        id: `edge-${crypto.randomUUID()}`,
        label,
        animated: true,
        style: { strokeWidth: 2, stroke: strokeColor },
        labelStyle: { fill: strokeColor, fontWeight: 700, fontSize: 13 },
        labelBgStyle: { fill: "rgba(2, 6, 23, 0.8)", rx: 4, ry: 4 },
        labelBgPadding: [4, 4],
      };
      
      setEdges((currentEdges) => {
        const nextEdges = addEdge(newEdge, currentEdges);
        // Delay to allow state closure correctly via refs
        setTimeout(() => applyLayout(nodes, nextEdges), 0);
        return nextEdges;
      });
    },
    [isEditable, nodes, applyLayout, setEdges],
  );

  const handleNodesChange = useCallback(
    (changes: NodeChange[]) => {
      if (!isEditable) return;
      onNodesChange(changes);
    },
    [isEditable, onNodesChange],
  );

  const handleEdgesChange = useCallback(
    (changes: EdgeChange[]) => {
      if (!isEditable) return;
      onEdgesChange(changes);
    },
    [isEditable, onEdgesChange],
  );

  const onDragOver = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      if (!isEditable) return;
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
    },
    [isEditable],
  );

  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      if (!isEditable) return;
      event.preventDefault();
      const nodeType = event.dataTransfer.getData("application/auraflow-node-type");
      if (!nodeType) return;
      const catalog = nodeTypesCatalog.find((item) => item.type === nodeType);
      if (!catalog) return;
      const wrapperRect = flowWrapperRef.current?.getBoundingClientRect();
      const rawPosition = {
        x: event.clientX - (wrapperRect?.left ?? 0),
        y: event.clientY - (wrapperRect?.top ?? 0),
      };
      const flowPosition = rfInstanceRef.current?.screenToFlowPosition
        ? rfInstanceRef.current.screenToFlowPosition({
            x: event.clientX,
            y: event.clientY,
          })
        : rawPosition;
      const newNodeId = `${catalog.type}-${crypto.randomUUID()}`;
      const newNode: Node = {
        id: newNodeId,
        type: "platform",
        position: flowPosition,
        data: {
          id: newNodeId,
          type: catalog.type,
          name: catalog.label,
          label: catalog.label,
          family: catalog.family,
          config: { ...(catalog.default_config ?? {}) },
          input_mapping: {},
          output_mapping: {},
          ai_brain: catalog.supports_ai_brain,
          memory: catalog.supports_memory ? "short_term" : null,
          retry_policy: { max_retries: 1, backoff: "exponential", retry_on: ["api_error"] },
          timeout_ms: catalog.family === "ai" ? 30000 : 10000,
          summary: `${catalog.label} configuration`,
          status: "idle",
          warnings: [],
        },
      };

      setNodes((currentNodes) => {
        const nextNodes = [...currentNodes, newNode];
        setTimeout(() => applyLayout(nextNodes, edges), 0);
        return nextNodes;
      });
    },
    [isEditable, nodeTypesCatalog, edges, applyLayout, setNodes, flowWrapperRef],
  );

  return (
    <div
      ref={flowWrapperRef}
      className="relative h-full w-full overflow-hidden rounded-[2rem] border border-border bg-background"
      onDragOver={onDragOver}
      onDrop={onDrop}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={handleNodesChange}
        onEdgesChange={handleEdgesChange}
        onConnect={onConnect}
        onPaneClick={() => onSelectNode?.(null)}
        onNodeClick={(_, node) => onSelectNode?.(node.id)}
        nodeTypes={{ platform: PlatformNode }}
        fitView
        onInit={(instance) => {
          rfInstanceRef.current = instance;
        }}
        nodesDraggable={isEditable}
        nodesConnectable={isEditable}
        elementsSelectable
        className="bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.04),_transparent_40%),linear-gradient(180deg,rgba(2,6,23,0.55),rgba(2,6,23,0.9))]"
      >
        <Background color="#334155" gap={24} variant={BackgroundVariant.Dots} />
        <Controls 
          className="overflow-hidden rounded-xl border border-border bg-card shadow-lg [&_button]:!border-b-border [&_button]:!bg-card [&_button]:!fill-muted-foreground hover:[&_button]:!bg-accent hover:[&_button]:!fill-foreground" 
        />
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

      {nodes.length === 0 ? (
        <div className="pointer-events-none absolute inset-0 z-10 grid place-items-center">
          <div className="glass max-w-md rounded-2xl border border-border px-6 py-5 text-center">
            <p className="text-base font-semibold text-foreground">
              Add your first node
            </p>
            <p className="mt-2 text-sm text-muted-foreground">
              Open the palette on the left and drop nodes onto the canvas to start building your workflow.
            </p>
          </div>
        </div>
      ) : null}

      <div className="pointer-events-none absolute left-5 top-5 z-10">
        <div className="glass rounded-2xl px-4 py-3 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          {isEditable ? "Live canvas editor" : "Workflow locked while run is active"}
        </div>
      </div>

      <div className="pointer-events-none absolute bottom-5 right-5 z-10 flex flex-col items-end gap-3">
        {isEditable && nodes.length > 0 && (
          <button
            onClick={() => applyLayout(nodes, edges)}
            className="pointer-events-auto flex items-center justify-center gap-2 rounded-full border border-primary/30 bg-primary px-4 py-2 text-xs font-semibold text-primary-foreground shadow-lg transition-transform hover:scale-105 active:scale-95"
            title="Auto-arrange workflow structure"
          >
            <Wand2 className="h-4 w-4" />
            Magic Align
          </button>
        )}
        <div className="glass rounded-2xl px-4 py-3 text-xs text-muted-foreground shadow-md">
          <span className={cn("font-semibold text-foreground")}>{nodes.length}</span> nodes
          <span className="mx-2">•</span>
          <span className={cn("font-semibold text-foreground")}>{edges.length}</span> edges
        </div>
      </div>
    </div>
  );
}
