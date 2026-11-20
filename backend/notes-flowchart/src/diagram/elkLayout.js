
import ELK from "elkjs/lib/elk.bundled.js";

const elk = new ELK();

export const NODE_WIDTH = 260;
export const NODE_HEIGHT = 100;

// =====================================
// CENTER SIMPLE TWO-WAY FLOWCHARTS
// =====================================

function centerSimpleBranches(
  layout,
  diagram
) {
  if (
    diagram.type !== "flowchart" ||
    diagram.direction !== "DOWN"
  ) {
    return;
  }

  const positioned = new Map(
    layout.children.map(node => [node.id, node])
  );

  const incoming = new Map(
    diagram.nodes.map(node => [node.id, []])
  );

  const outgoing = new Map(
    diagram.nodes.map(node => [node.id, []])
  );

  for (const edge of diagram.edges) {
    outgoing.get(edge.source).push(edge.target);
    incoming.get(edge.target).push(edge.source);
  }

  const decisions = diagram.nodes.filter(
    node =>
      node.data.kind === "decision" &&
      outgoing.get(node.id).length === 2
  );

  if (decisions.length !== 1) return;

  const decision = decisions[0];
  const targets = outgoing.get(decision.id);

  const simpleFork = targets.every(
    id =>
      outgoing.get(id).length === 0 &&
      incoming.get(id).length === 1
  );

  if (!simpleFork || targets[0] === targets[1]) {
    return;
  }

  const trunk = [decision.id];
  const visited = new Set(trunk);

  let currentId = decision.id;

  while (incoming.get(currentId).length === 1) {
    const parentId = incoming.get(currentId)[0];

    if (
      visited.has(parentId) ||
      outgoing.get(parentId).length !== 1
    ) {
      break;
    }

    trunk.push(parentId);
    visited.add(parentId);
    currentId = parentId;
  }

  // Don't change complex or disconnected graphs.
  if (trunk.length + 2 !== diagram.nodes.length) {
    return;
  }

  const first = positioned.get(targets[0]);
  const second = positioned.get(targets[1]);

  if (!first || !second) return;

  const center =
    (
      first.x + first.width / 2 +
      second.x + second.width / 2
    ) / 2;

  for (const id of trunk) {
    const node = positioned.get(id);

    if (node) {
      node.x = center - node.width / 2;
    }
  }
}

// =====================================
// SHARED AUTOMATIC LAYOUT
// =====================================

export async function layoutDiagram(diagram) {
  const graph = {
    id: "root",

    layoutOptions: {
      "elk.algorithm": "layered",
      "elk.direction": diagram.direction,

      "elk.layered.nodePlacement.strategy":
        "BRANDES_KOEPF",

      "elk.layered.nodePlacement.bk.fixedAlignment":
        "BALANCED",

      "elk.spacing.nodeNode": "70",

      "elk.layered.spacing.nodeNodeBetweenLayers":
        "110"
    },

    children: diagram.nodes.map(node => ({
      id: node.id,
      width: NODE_WIDTH,
      height: NODE_HEIGHT
    })),

    edges: diagram.edges.map(edge => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target]
    }))
  };

  const result = await elk.layout(graph);

  centerSimpleBranches(result, diagram);

  const originalNodes = new Map(
    diagram.nodes.map(node => [node.id, node])
  );

  const nodes = result.children.map(node => {
    const original = originalNodes.get(node.id);

    return {
      ...original,
      position: {
        x: node.x,
        y: node.y
      }
    };
  });

  return {
    nodes,
    edges: diagram.edges
  };
}
