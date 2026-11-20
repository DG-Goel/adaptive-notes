
import { useRef, useState } from "react";
import { toPng } from "html-to-image";
import { Download } from "lucide-react";

import BinaryTreeRenderer from "./BinaryTreeRenderer.jsx";

// =====================================
// SHARED COLORS AND STYLES
// =====================================

const colors = {
  array: {
    fill: "#eff6ff",
    stroke: "#60a5fa",
    text: "#1d4ed8"
  },

  stack: {
    fill: "#eef2ff",
    stroke: "#818cf8",
    text: "#4338ca"
  },

  queue: {
    fill: "#f0fdfa",
    stroke: "#2dd4bf",
    text: "#0f766e"
  },

  linked_list: {
    fill: "#ecfdf5",
    stroke: "#34d399",
    text: "#047857"
  }
};

const LABEL_COLOR = "#64748b";
const ARROW_COLOR = "#64748b";

// =====================================
// SHARED VALUE TEXT
// =====================================

function ValueText({ x, y, value, color }) {
  return (
    <text
      x={x}
      y={y}
      fill={color}
      fontSize="17"
      fontWeight="600"
      textAnchor="middle"
      dominantBaseline="middle"
    >
      {String(value)}
    </text>
  );
}

// =====================================
// ARRAY TEMPLATE
// =====================================

function ArrayDiagram({ values }) {
  const color = colors.array;

  return (
    <>
      {values.map((value, index) => {
        const x = 50 + index * 94;

        return (
          <g key={index}>
            {/* Array index */}
            <text
              x={x + 44}
              y="91"
              fill={LABEL_COLOR}
              fontSize="13"
              textAnchor="middle"
            >
              {index}
            </text>

            {/* Array element box */}
            <rect
              x={x}
              y="106"
              width="88"
              height="64"
              rx="8"
              fill={color.fill}
              stroke={color.stroke}
              strokeWidth="2"
            />

            <ValueText
              x={x + 44}
              y={138}
              value={value}
              color={color.text}
            />
          </g>
        );
      })}
    </>
  );
}

// =====================================
// STACK TEMPLATE
// =====================================

function StackDiagram({ values, height }) {
  const color = colors.stack;

  const bottom = height - 82;
  const top = bottom - values.length * 54;

  return (
    <>
      {values.map((value, index) => {
        // Values are ordered bottom to top.
        const y = bottom - (index + 1) * 54;

        return (
          <g key={index}>
            <rect
              x="220"
              y={y}
              width="160"
              height="52"
              rx="7"
              fill={color.fill}
              stroke={color.stroke}
              strokeWidth="2"
            />

            <ValueText
              x={300}
              y={y + 26}
              value={value}
              color={color.text}
            />
          </g>
        );
      })}

      {/* TOP indicator */}
      <text
        x="145"
        y={top + 31}
        fill="#16a34a"
        fontSize="15"
        fontWeight="700"
        textAnchor="end"
      >
        TOP
      </text>

      <path
        d={`M160 ${top + 26} H209`}
        fill="none"
        stroke={ARROW_COLOR}
        strokeWidth="2"
      />

      <path
        d={`
          M202 ${top + 20}
          L211 ${top + 26}
          L202 ${top + 32}
        `}
        fill="none"
        stroke={ARROW_COLOR}
        strokeWidth="2"
      />

      {/* BOTTOM indicator */}
      <text
        x="300"
        y={bottom + 30}
        fill={LABEL_COLOR}
        fontSize="13"
        textAnchor="middle"
      >
        BOTTOM
      </text>
    </>
  );
}

// =====================================
// QUEUE TEMPLATE
// =====================================

function QueueDiagram({ values }) {
  const color = colors.queue;

  return (
    <>
      {values.map((value, index) => {
        const x = 50 + index * 98;

        return (
          <g key={index}>
            <rect
              x={x}
              y="108"
              width="92"
              height="64"
              rx="7"
              fill={color.fill}
              stroke={color.stroke}
              strokeWidth="2"
            />

            <ValueText
              x={x + 46}
              y={140}
              value={value}
              color={color.text}
            />
          </g>
        );
      })}

      {/* FRONT indicator */}
      <text
        x="96"
        y="64"
        fontSize="14"
        fontWeight="700"
        textAnchor="middle"
        fill="#047857"
      >
        FRONT
      </text>

      <path
        d="M96 70 V101 M90 94 L96 103 L102 94"
        fill="none"
        stroke={ARROW_COLOR}
        strokeWidth="2"
      />

      {/* REAR indicator */}
      {values.length > 1 && (
        <>
          <text
            x={96 + (values.length - 1) * 98}
            y="64"
            fontSize="14"
            fontWeight="700"
            textAnchor="middle"
            fill="#0f766e"
          >
            REAR
          </text>

          <path
            d={`
              M${96 + (values.length - 1) * 98} 70
              V101

              M${90 + (values.length - 1) * 98} 94
              L${96 + (values.length - 1) * 98} 103
              L${102 + (values.length - 1) * 98} 94
            `}
            fill="none"
            stroke={ARROW_COLOR}
            strokeWidth="2"
          />
        </>
      )}

      {values.length === 1 && (
        <text
          x="96"
          y="205"
          fontSize="12"
          textAnchor="middle"
          fill={LABEL_COLOR}
        >
          REAR = FRONT
        </text>
      )}
    </>
  );
}

// =====================================
// SINGLY LINKED LIST TEMPLATE
// =====================================

function LinkedListDiagram({ values }) {
  const color = colors.linked_list;
  const nodeY = 90;

  return (
    <>
      {/* HEAD indicator */}
      <text
        x="40"
        y="64"
        fill="#047857"
        fontSize="14"
        fontWeight="700"
      >
        HEAD
      </text>

      {values.map((value, index) => {
        const x = 40 + index * 180;
        const arrowEnd = x + 169;

        return (
          <g key={index}>
            {/* Node container */}
            <rect
              x={x}
              y={nodeY}
              width="128"
              height="72"
              rx="9"
              fill={color.fill}
              stroke={color.stroke}
              strokeWidth="2"
            />

            {/* Value / pointer divider */}
            <line
              x1={x + 90}
              y1={nodeY}
              x2={x + 90}
              y2={nodeY + 72}
              stroke={color.stroke}
              strokeWidth="2"
            />

            {/* Node value */}
            <ValueText
              x={x + 45}
              y={nodeY + 36}
              value={value}
              color={color.text}
            />

            {/* Pointer indicator */}
            <circle
              cx={x + 109}
              cy={nodeY + 36}
              r="4"
              fill={color.text}
            />

            {/* Connection arrow */}
            <line
              x1={x + 128}
              y1={nodeY + 36}
              x2={arrowEnd}
              y2={nodeY + 36}
              stroke={ARROW_COLOR}
              strokeWidth="2"
            />

            <path
              d={`
                M${arrowEnd - 8} ${nodeY + 30}
                L${arrowEnd} ${nodeY + 36}
                L${arrowEnd - 8} ${nodeY + 42}
              `}
              fill="none"
              stroke={ARROW_COLOR}
              strokeWidth="2"
            />

            {/* Last node points to NULL */}
            {index === values.length - 1 && (
              <text
                x={x + 190}
                y={nodeY + 41}
                fill={LABEL_COLOR}
                fontSize="14"
                fontWeight="700"
              >
                NULL
              </text>
            )}
          </g>
        );
      })}
    </>
  );
}

// =====================================
// CANVAS SIZE CALCULATION
// =====================================

function getCanvasSize(subtype, count) {
  switch (subtype) {
    case "stack":
      return {
        width: 600,
        height: Math.max(
          350,
          count * 54 + 165
        )
      };

    case "linked_list":
      return {
        width: Math.max(
          650,
          count * 180 + 110
        ),
        height: 240
      };

    case "queue":
      return {
        width: Math.max(
          560,
          count * 98 + 100
        ),
        height: 240
      };

    case "array":
      return {
        width: Math.max(
          560,
          count * 94 + 100
        ),
        height: 240
      };

    default:
      return {
        width: 600,
        height: 350
      };
  }
}

// =====================================
// MAIN DATA STRUCTURE RENDERER
// =====================================

export default function DataStructureRenderer({ diagram }) {
  const svgRef = useRef(null);

  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  const subtype = diagram?.subtype;
  const values = diagram?.values;

  // =====================================
  // BINARY TREE ROUTING
  // =====================================

  // Binary trees use D3 hierarchy for automatic
  // positioning instead of basic SVG templates.

  if (
    diagram?.type === "data_structure" &&
    subtype === "binary_tree"
  ) {
    return (
      <BinaryTreeRenderer
        diagram={diagram}
      />
    );
  }

  // =====================================
  // SUPPORTED BASIC DATA STRUCTURES
  // =====================================

  const allowedTypes = [
    "array",
    "stack",
    "queue",
    "linked_list"
  ];

  if (
    diagram?.type !== "data_structure" ||
    !allowedTypes.includes(subtype)
  ) {
    return (
      <div
        role="alert"
        className="rounded-xl bg-red-50 p-5 text-red-700"
      >
        Unsupported data structure type.
      </div>
    );
  }

  // =====================================
  // DATA VALIDATION
  // =====================================

  if (
    !Array.isArray(values) ||
    values.length === 0 ||
    values.length > 30 ||
    values.some(
      value =>
        !["string", "number"].includes(typeof value) ||
        String(value).length > 12
    )
  ) {
    return (
      <div
        role="alert"
        className="rounded-xl bg-red-50 p-5 text-red-700"
      >
        Provide 1–30 values, each with at most 12 characters.
      </div>
    );
  }

  const { width, height } = getCanvasSize(
    subtype,
    values.length
  );

  const title =
    diagram.title || "Data Structure Diagram";

  // =====================================
  // PNG EXPORT FUNCTION
  // =====================================

  async function downloadPNG() {
    if (!svgRef.current || exporting) return;

    setExporting(true);
    setExportError("");

    try {
      // High-resolution export with pixel limit.
      const pixelRatio = Math.min(
        2,
        Math.sqrt(
          16000000 / (width * height)
        )
      );

      const png = await toPng(
        svgRef.current,
        {
          backgroundColor: "#ffffff",
          width,
          height,
          pixelRatio
        }
      );

      // Safe filename
      const filename = title
        .replace(/[^a-z0-9_-]+/gi, "-")
        .replace(/^-|-$/g, "");

      // Download image
      const link = document.createElement("a");

      link.href = png;

      link.download =
        `${filename || "data-structure"}.png`;

      document.body.appendChild(link);
      link.click();
      link.remove();

    } catch (err) {
      console.error(
        "PNG export failed:",
        err
      );

      setExportError(
        err?.message ||
        "Could not export diagram."
      );
    } finally {
      setExporting(false);
    }
  }

  // =====================================
  // RENDER BASIC DATA STRUCTURE
  // =====================================

  return (
    <div className="space-y-5">

      {/* Header and toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3">

        <div>
          <h2 className="text-xl font-bold text-slate-800">
            {title}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {subtype.replaceAll("_", " ")}
            {" · "}
            {values.length} elements
          </p>
        </div>

        {/* PNG export button */}
        <button
          type="button"
          onClick={downloadPNG}
          disabled={exporting}
          className="
            inline-flex items-center gap-2
            rounded-xl
            bg-blue-600 px-5 py-3
            text-sm font-semibold text-white
            shadow-sm
            hover:bg-blue-700
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
        <p
          role="alert"
          className="text-sm text-red-600"
        >
          {exportError}
        </p>
      )}

      {/* SVG diagram canvas */}
      <div
        className="
          overflow-x-auto
          rounded-2xl
          border border-slate-200
          bg-white
        "
      >
        <svg
          ref={svgRef}
          width={width}
          height={height}
          viewBox={`0 0 ${width} ${height}`}
          xmlns="http://www.w3.org/2000/svg"
          role="img"
          aria-label={title}
          style={{
            display: "block",
            backgroundColor: "#ffffff",
            fontFamily: "Arial, sans-serif"
          }}
        >
          {/* Background */}
          <rect
            width={width}
            height={height}
            fill="#ffffff"
          />

          {/* ARRAY */}
          {subtype === "array" && (
            <ArrayDiagram
              values={values}
            />
          )}

          {/* STACK */}
          {subtype === "stack" && (
            <StackDiagram
              values={values}
              height={height}
            />
          )}

          {/* QUEUE */}
          {subtype === "queue" && (
            <QueueDiagram
              values={values}
            />
          )}

          {/* LINKED LIST */}
          {subtype === "linked_list" && (
            <LinkedListDiagram
              values={values}
            />
          )}
        </svg>
      </div>

      {/* Footer description */}
      <p className="text-xs text-slate-500">
        Diagram generated automatically using
        structured data and SVG templates.
        No AI rendering required.
      </p>
    </div>
  );
}
