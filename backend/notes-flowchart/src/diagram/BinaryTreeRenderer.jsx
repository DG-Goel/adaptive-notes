
import { useMemo, useRef, useState } from "react";
import { hierarchy, tree } from "d3-hierarchy";
import { toPng } from "html-to-image";
import { Download, FileCode2 } from "lucide-react";

const RADIUS = 25;
const PAD_X = 90;
const PAD_Y = 90;

function makeTree(values) {
  if (
    !Array.isArray(values) ||
    values.length < 1 ||
    values.length > 63 ||
    values[0] == null
  ) {
    throw new Error(
      "Provide 1–63 level-order values with a root."
    );
  }

  values.forEach((value, i) => {
    if (value === null) return;

    const valid =
      (typeof value === "number" && Number.isFinite(value)) ||
      (typeof value === "string" &&
        value.trim().length > 0);

    if (!valid || String(value).length > 8) {
      throw new Error(
        `Invalid or excessively long value at index ${i}.`
      );
    }

    if (
      i > 0 &&
      values[Math.floor((i - 1) / 2)] == null
    ) {
      throw new Error(
        `Node at index ${i} has no parent.`
      );
    }
  });

  // In level-order representation:
  // left child = 2*i + 1
  // right child = 2*i + 2
  function build(index) {
    if (
      index >= values.length ||
      values[index] == null
    ) {
      return null;
    }

    const left = build(2 * index + 1);
    const right = build(2 * index + 2);

    const node = {
      id: String(index),
      value: values[index]
    };

    if (left || right) {
      // Invisible placeholders preserve
      // left/right positioning for sparse trees.
      node.children = [
        left || {
          id: `ghost-left-${index}`,
          ghost: true
        },
        right || {
          id: `ghost-right-${index}`,
          ghost: true
        }
      ];
    }

    return node;
  }

  const root = hierarchy(build(0));

  // D3 calculates every coordinate.
  tree()
    .nodeSize([108, 125])
    .separation((a, b) =>
      a.parent === b.parent ? 1.1 : 1.4
    )(root);

  const nodes = root.descendants().filter(
    node => !node.data.ghost
  );

  const links = root.links().filter(
    link =>
      !link.source.data.ghost &&
      !link.target.data.ghost
  );

  const minX = Math.min(...nodes.map(n => n.x));
  const maxX = Math.max(...nodes.map(n => n.x));
  const maxY = Math.max(...nodes.map(n => n.y));

  return {
    nodes,
    links,
    width: Math.ceil(maxX - minX + 2 * PAD_X),
    height: Math.ceil(maxY + 2 * PAD_Y),
    offsetX: PAD_X - minX,
    offsetY: PAD_Y
  };
}

function safeFilename(title) {
  return String(title || "binary-tree")
    .replace(/[^a-z0-9_-]+/gi, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 100) || "binary-tree";
}

function startDownload(url, filename) {
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
}

export default function BinaryTreeRenderer({ diagram }) {
  const svgRef = useRef(null);

  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  const { layout, error } = useMemo(() => {
    try {
      return {
        layout: makeTree(diagram?.values),
        error: ""
      };
    } catch (err) {
      return {
        layout: null,
        error: err.message
      };
    }
  }, [diagram?.values]);

  const title = diagram?.title || "Binary Tree";

  async function downloadPNG() {
    if (!svgRef.current || !layout || exporting) return;

    setExporting(true);
    setExportError("");

    try {
      const pixelRatio = Math.min(
        2,
        Math.sqrt(
          16000000 / (layout.width * layout.height)
        )
      );

      const png = await toPng(svgRef.current, {
        backgroundColor: "#ffffff",
        width: layout.width,
        height: layout.height,
        pixelRatio
      });

      startDownload(
        png,
        `${safeFilename(title)}.png`
      );
    } catch (err) {
      console.error(err);
      setExportError(
        err?.message || "PNG export failed."
      );
    } finally {
      setExporting(false);
    }
  }

  function downloadSVG() {
    if (!svgRef.current) return;

    try {
      setExportError("");

      const source = new XMLSerializer()
        .serializeToString(svgRef.current);

      const blob = new Blob([source], {
        type: "image/svg+xml;charset=utf-8"
      });

      const url = URL.createObjectURL(blob);

      startDownload(
        url,
        `${safeFilename(title)}.svg`
      );

      setTimeout(() => {
        URL.revokeObjectURL(url);
      }, 1000);
    } catch (err) {
      setExportError(
        err?.message || "SVG export failed."
      );
    }
  }

  if (error) {
    return (
      <div
        role="alert"
        className="rounded-xl bg-red-50 p-5 text-red-700"
      >
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-800">
            {title}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            {layout.nodes.length} nodes
            {" · "}
            {layout.links.length} connections
            {" · "}
            {Math.max(
              ...layout.nodes.map(n => n.depth)
            ) + 1} levels
          </p>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={downloadSVG}
            className="inline-flex items-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm font-semibold text-blue-700 hover:bg-blue-100"
          >
            <FileCode2 size={17} />
            Download SVG
          </button>

          <button
            type="button"
            onClick={downloadPNG}
            disabled={exporting}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60"
          >
            <Download size={17} />
            {exporting ? "Exporting..." : "Download PNG"}
          </button>
        </div>
      </div>

      {exportError && (
        <p role="alert" className="text-sm text-red-700">
          {exportError}
        </p>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white">
        <svg
          ref={svgRef}
          xmlns="http://www.w3.org/2000/svg"
          width={layout.width}
          height={layout.height}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          role="img"
          aria-label={title}
          style={{
            display: "block",
            maxWidth: "none",
            backgroundColor: "#ffffff",
            fontFamily: "Arial, sans-serif"
          }}
        >
          <rect
            width={layout.width}
            height={layout.height}
            fill="#ffffff"
          />

          {/* Draw connections behind nodes */}
          {layout.links.map(link => {
            const x1 = link.source.x + layout.offsetX;
            const y1 = link.source.y + layout.offsetY;
            const x2 = link.target.x + layout.offsetX;
            const y2 = link.target.y + layout.offsetY;

            const midY = (y1 + y2) / 2;

            return (
              <path
                key={`${link.source.data.id}-${link.target.data.id}`}
                d={`M ${x1} ${y1 + RADIUS}
                    C ${x1} ${midY},
                      ${x2} ${midY},
                      ${x2} ${y2 - RADIUS}`}
                fill="none"
                stroke="#94a3b8"
                strokeWidth="2"
                strokeLinecap="round"
              />
            );
          })}

          {/* Draw all tree nodes */}
          {layout.nodes.map(node => {
            const x = node.x + layout.offsetX;
            const y = node.y + layout.offsetY;

            const rootNode = node.depth === 0;
            const leafNode = !node.children;

            const fill = rootNode
              ? "#2563eb"
              : leafNode
                ? "#d1fae5"
                : "#dbeafe";

            const stroke = rootNode
              ? "#1d4ed8"
              : leafNode
                ? "#34d399"
                : "#60a5fa";

            const textColor = rootNode
              ? "#ffffff"
              : leafNode
                ? "#047857"
                : "#1e40af";

            return (
              <g key={node.data.id}>
                <circle
                  cx={x}
                  cy={y}
                  r={RADIUS}
                  fill={fill}
                  stroke={stroke}
                  strokeWidth="2"
                />

                <text
                  x={x}
                  y={y}
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize={
                    String(node.data.value).length > 5
                      ? 11
                      : 15
                  }
                  fontWeight="700"
                  fill={textColor}
                >
                  {String(node.data.value)}
                </text>

                {rootNode && (
                  <text
                    x={x}
                    y={y - 38}
                    textAnchor="middle"
                    fontSize="13"
                    fontWeight="700"
                    fill="#2563eb"
                  >
                    ROOT
                  </text>
                )}
              </g>
            );
          })}
        </svg>
      </div>

      <p className="text-xs text-slate-500">
        Nodes are positioned automatically.
        Scroll horizontally to inspect wide trees.
      </p>
    </div>
  );
}
