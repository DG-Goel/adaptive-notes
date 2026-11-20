
export function adaptArchitecture(diagram) {
  if (
    !diagram ||
    !Array.isArray(diagram.components) ||
    !Array.isArray(diagram.connections)
  ) {
    throw new Error("Invalid architecture diagram JSON.");
  }

  if (diagram.components.length === 0) {
    throw new Error("Architecture diagram has no components.");
  }

  const ids = new Set();

  const direction =
    diagram.direction === "DOWN"
      ? "DOWN"
      : "RIGHT";

  const nodes = diagram.components.map((component) => {
    if (
      !component.id ||
      typeof component.id !== "string" ||
      ids.has(component.id)
    ) {
      throw new Error(
        "Architecture component IDs must be unique strings."
      );
    }

    if (
      typeof component.label !== "string" ||
      !component.label.trim()
    ) {
      throw new Error(
        `Component ${component.id} has an invalid label.`
      );
    }

    ids.add(component.id);

    return {
      id: component.id,
      type: "architectureNode",
      data: {
        label: component.label,
        kind: component.kind || "component",
        description: component.description || "",
        direction
      }
    };
  });

  const edges = diagram.connections.map(
    (connection, index) => {
      if (
        !ids.has(connection.from) ||
        !ids.has(connection.to)
      ) {
        throw new Error(
          `Architecture connection ${index} references a missing component.`
        );
      }

      return {
        id: `arch-edge-${index}`,
        source: connection.from,
        target: connection.to,
        label: connection.label || "",
        bidirectional:
          connection.bidirectional === true
      };
    }
  );

  return {
    type: "architecture",
    title: diagram.title || "Architecture Diagram",
    direction,
    nodes,
    edges
  };
}
