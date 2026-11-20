
export function adaptFlowchart(diagram) {
  if (
    !diagram ||
    !Array.isArray(diagram.nodes) ||
    !Array.isArray(diagram.edges)
  ) {
    throw new Error("Invalid flowchart JSON.");
  }

  if (diagram.nodes.length === 0) {
    throw new Error("Flowchart has no nodes.");
  }

  const ids = new Set();

  const nodes = diagram.nodes.map((node) => {
    if (
      !node.id ||
      typeof node.id !== "string" ||
      ids.has(node.id)
    ) {
      throw new Error(
        "Flowchart node IDs must be unique strings."
      );
    }

    if (
      typeof node.label !== "string" ||
      !node.label.trim()
    ) {
      throw new Error(
        `Node ${node.id} has an invalid label.`
      );
    }

    ids.add(node.id);

    return {
      id: node.id,
      type: "flowNode",
      data: {
        label: node.label,
        kind: node.kind || "action",
        direction:
          diagram.direction === "RIGHT"
            ? "RIGHT"
            : "DOWN"
      }
    };
  });

  const edges = diagram.edges.map((edge, index) => {
    if (
      !ids.has(edge.from) ||
      !ids.has(edge.to)
    ) {
      throw new Error(
        `Flowchart edge ${index} references a missing node.`
      );
    }

    return {
      id: `flow-edge-${index}`,
      source: edge.from,
      target: edge.to,
      label: edge.label || "",
      bidirectional: false
    };
  });

  return {
    type: "flowchart",
    title: diagram.title || "Flowchart",
    direction:
      diagram.direction === "RIGHT"
        ? "RIGHT"
        : "DOWN",
    nodes,
    edges
  };
}
