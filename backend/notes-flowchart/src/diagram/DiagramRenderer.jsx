
import { useEffect, useMemo, useRef, useState } from "react";

import {
  ReactFlow,
  Background,
  Controls,
  MarkerType
} from "@xyflow/react";

import {
  Download,
  LoaderCircle,
  AlertCircle
} from "lucide-react";

import { adaptFlowchart } from "./adapters/flowchart.js";
import { adaptArchitecture } from "./adapters/architecture.js";

import { layoutDiagram } from "./elkLayout.js";
import { exportDiagramPNG } from "./exportPNG.js";

import FlowNode from "./nodes/FlowNode.jsx";
import ArchitectureNode from "./nodes/ArchitectureNode.jsx";

import "@xyflow/react/dist/style.css";

// Keep nodeTypes outside the React component
// so React Flow does not recreate them unnecessarily.
const nodeTypes = {
  flowNode: FlowNode,
  architectureNode: ArchitectureNode
};

// =====================================
// SELECT THE CORRECT ADAPTER
// =====================================

function prepareDiagram(diagram) {
  if (!diagram || typeof diagram !== "object") {
    throw new Error("Diagram data is missing.");
  }

  // Accept older flowchart JSON without a type field.
  const type = diagram.type || "flowchart";

  switch (type) {
    case "flowchart":
      return adaptFlowchart(diagram);

    case "architecture":
      return adaptArchitecture(diagram);

    default:
      throw new Error(
        `Unsupported diagram type: ${type}`
      );
  }
}

// =====================================
// STYLE EDGES FOR REACT FLOW
// =====================================

function styleEdges(edges, type) {
  const color =
    type === "architecture"
      ? "#64748b"
      : "#64748b";

  return edges.map(edge => ({
    ...edge,

    type: "smoothstep",

    style: {
      stroke: color,
      strokeWidth: 2
    },

    markerEnd: {
      type: MarkerType.ArrowClosed,
      color
    },

    ...(edge.bidirectional
      ? {
          markerStart: {
            type: MarkerType.ArrowClosed,
            color
          }
        }
      : {}),

    labelStyle: {
      fill: "#334155",
      fontSize: 12,
      fontWeight: 600
    },

    labelBgPadding: [6, 4],
    labelBgBorderRadius: 6,

    labelBgStyle: {
      fill: "#ffffff",
      fillOpacity: 0.95
    }
  }));
}

// =====================================
// SHARED DIAGRAM RENDERER
// =====================================

export default function DiagramRenderer({ diagram }) {
  const [layout, setLayout] = useState(null);
  const [error, setError] = useState("");

  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  const canvasRef = useRef(null);

  // =====================================
  // GENERATE THE LAYOUT
  // =====================================

  useEffect(() => {
    let active = true;

    setLayout(null);
    setError("");
    setExportError("");

    async function generate() {
      try {
        const normalized = prepareDiagram(diagram);

        const result = await layoutDiagram(
          normalized
        );

        if (active) {
          setLayout({
            ...result,
            type: normalized.type,
            title: normalized.title
          });
        }
      } catch (err) {
        if (active) {
          setError(
            err?.message || "Unable to render diagram."
          );
        }
      }
    }

    generate();

    return () => {
      active = false;
    };
  }, [diagram]);

  // =====================================
  // REACT FLOW EDGES
  // =====================================

  const renderedEdges = useMemo(() => {
    if (!layout) return [];

    return styleEdges(
      layout.edges,
      layout.type
    );
  }, [layout]);

  // =====================================
  // DOWNLOAD PNG
  // =====================================

  async function downloadPNG() {
    if (!layout || exporting) return;

    setExporting(true);
    setExportError("");

    try {
      await exportDiagramPNG({
        container: canvasRef.current,
        nodes: layout.nodes,
        title: layout.title
      });
    } catch (err) {
      console.error("Export failed:", err);

      setExportError(
        err?.message || "Failed to download PNG."
      );
    } finally {
      setExporting(false);
    }
  }

  // =====================================
  // ERROR STATE
  // =====================================

  if (error) {
    return (
      <div
        role="alert"
        className="
          flex items-center gap-3
          rounded-xl border border-red-200
          bg-red-50 p-5 text-red-700
        "
      >
        <AlertCircle size={22} />
        <span>{error}</span>
      </div>
    );
  }

  // =====================================
  // LOADING STATE
  // =====================================

  if (!layout) {
    return (
      <div
        className="
          flex items-center gap-3
          rounded-xl bg-white p-6
          text-slate-500
        "
      >
        <LoaderCircle
          size={20}
          className="animate-spin"
        />
        Generating diagram layout...
      </div>
    );
  }

  // =====================================
  // RENDER
  // =====================================

  return (
    <div className="space-y-4">

      {/* Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-800">
            {layout.title}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {layout.nodes.length} components / nodes
            {" · "}
            {layout.edges.length} connections
          </p>
        </div>

        <button
          type="button"
          onClick={downloadPNG}
          disabled={exporting}
          className="
            inline-flex items-center gap-2
            rounded-xl bg-blue-600
            px-5 py-3
            text-sm font-semibold text-white
            shadow-sm transition-colors
            hover:bg-blue-700
            disabled:cursor-wait
            disabled:opacity-60
          "
        >
          <Download size={18} />

          {exporting
            ? "Exporting..."
            : "Download PNG for Word"}
        </button>
      </div>

      {/* Export errors */}
      {exportError && (
        <div
          role="alert"
          className="
            rounded-lg border border-red-200
            bg-red-50 p-3 text-sm text-red-700
          "
        >
          {exportError}
        </div>
      )}

      {/* Shared interactive canvas */}
      <div
        ref={canvasRef}
        className="
          h-[850px] w-full
          overflow-hidden rounded-2xl
          border border-slate-200 bg-white
        "
      >
        <ReactFlow
          nodes={layout.nodes}
          edges={renderedEdges}
          nodeTypes={nodeTypes}
          nodesDraggable={false}
          nodesConnectable={false}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.15}
          maxZoom={2}
          onlyRenderVisibleElements={false}
        >
          <Background
            gap={20}
            color="#e2e8f0"
          />

          <Controls
            showInteractive={false}
          />
        </ReactFlow>
      </div>
    </div>
  );
}
