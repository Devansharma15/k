import dagre from "dagre";
import { type Node, type Edge, Position } from "reactflow";

export type LayoutDirection = "TB" | "LR";

interface LayoutOptions {
  direction?: LayoutDirection;
  nodeWidth?: number;
  nodeHeight?: number;
  ranksep?: number;
  nodesep?: number;
}

/**
 * Calculates a deterministic layout for a graph using Dagre.
 * Converts calculated center-points back to top-left bounding box coordinates for React Flow.
 */
export function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  options: LayoutOptions = {}
) {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));

  const {
    direction = "LR",
    nodeWidth = 300,
    nodeHeight = 150,
    ranksep = 180, // Horizontal gap strictly pushed for branch clarity
    nodesep = 100, // Vertical gap explicitly increased to avoid overlap
  } = options;

  dagreGraph.setGraph({ rankdir: direction, ranksep, nodesep });

  nodes.forEach((node) => {
    // dagre requires nodes to have w and h
    dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Execute the layout calculation algorithm
  dagre.layout(dagreGraph);

  // Apply positions back to nodes
  const layoutedNodes = nodes.map((node) => {
    // We get the node's position from dagre
    const nodeWithPosition = dagreGraph.node(node.id);

    // Dagre outputs positioning based on the *center* of the node.
    // React Flow anchors positioning at the *top-left*.
    const x = nodeWithPosition.x - nodeWidth / 2;
    const y = nodeWithPosition.y - nodeHeight / 2;

    return {
      ...node,
      position: { x, y },
      targetPosition: direction === "LR" ? Position.Left : Position.Top,
      sourcePosition: direction === "LR" ? Position.Right : Position.Bottom,
    };
  });

  return { nodes: layoutedNodes, edges };
}
