
import { useEffect, useRef, useState } from "react";
import { toPng } from "html-to-image";
import {
  Download,
  FileCode2,
  ArrowRightLeft
} from "lucide-react";

// =====================================
// CONFIGURATION
// =====================================

let mermaidInitialized = false;
let renderCounter = 0;

const COLORS = {
  request: "#2563eb",
  response: "#0d9488",
  lifeline: "#cbd5e1",
  text: "#334155",
  condition: "#a5b4fc"
};

// =====================================
// TEXT VALIDATION
// =====================================

function cleanText(value, field = "Text") {
  if (
    typeof value !== "string" ||
    !value.trim()
  ) {
    throw new Error(
      `${field} must be a nonempty string.`
    );
  }

  return value
    .trim()
    .replace(/[\r\n\t]+/g, " ")
    .replace(/%%/g, "% %")
    .replace(/;/g, ",")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// =====================================
// SAFE FILENAME
// =====================================

function safeFilename(title) {
  return (
    String(title || "sequence-diagram")
      .replace(/[^a-z0-9_-]+/gi, "-")
      .replace(/^-|-$/g, "")
      .slice(0, 100) ||
    "sequence-diagram"
  );
}

// =====================================
// FILE DOWNLOAD
// =====================================

function saveDownload(url, filename, revoke = false) {
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.appendChild(link);
  link.click();
  link.remove();

  if (revoke) {
    setTimeout(() => {
      URL.revokeObjectURL(url);
    }, 2000);
  }
}

// =====================================
// JSON -> MERMAID CONVERTER
// =====================================

function buildMermaid(diagram) {
  if (
    diagram?.type !== "sequence" ||
    !Array.isArray(diagram.participants) ||
    !Array.isArray(diagram.events)
  ) {
    throw new Error(
      "Invalid sequence diagram JSON."
    );
  }

  if (
    diagram.participants.length < 2 ||
    diagram.participants.length > 12
  ) {
    throw new Error(
      "Provide 2–12 participants."
    );
  }

  const ids = new Set();

  // No automatic numbering.
  const lines = ["sequenceDiagram"];

  // =====================================
  // PARTICIPANTS
  // =====================================

  for (const participant of diagram.participants) {
    const id = participant.id;

    if (
      typeof id !== "string" ||
      !/^[A-Za-z][A-Za-z0-9_]*$/.test(id) ||
      ids.has(id)
    ) {
      throw new Error(
        "Participant IDs must be unique letters/numbers."
      );
    }

    ids.add(id);

    const label = cleanText(
      participant.label,
      `Participant ${id}`
    );

    // All participants use matching cards.
    lines.push(
      `participant ${id} as ${label}`
    );
  }

  let totalEvents = 0;

  function validateParticipant(id) {
    if (!ids.has(id)) {
      throw new Error(
        `Unknown participant: ${id}`
      );
    }
  }

  // =====================================
  // EVENTS
  // =====================================

  function addEvents(events, depth = 0) {
    if (!Array.isArray(events)) {
      throw new Error(
        "Events must be an array."
      );
    }

    if (depth > 6) {
      throw new Error(
        "Sequence nesting is too deep."
      );
    }

    for (const event of events) {
      totalEvents++;

      if (totalEvents > 150) {
        throw new Error(
          "Too many sequence events."
        );
      }

      switch (event.kind) {
        // =================================
        // MESSAGE
        // =================================

        case "message": {
          validateParticipant(event.from);
          validateParticipant(event.to);

          // Solid = request/action
          // Dashed = response/result
          const arrow = event.dashed
            ? "-->>"
            : "->>";

          const label = cleanText(
            event.text,
            "Message label"
          );

          lines.push(
            `${event.from}${arrow}${event.to}: ${label}`
          );

          break;
        }

        // =================================
        // NOTE
        // =================================

        case "note": {
          validateParticipant(event.over);

          const note = cleanText(
            event.text,
            "Note"
          );

          lines.push(
            `Note over ${event.over}: ${note}`
          );

          break;
        }

        // =================================
        // LOOP
        // =================================

        case "loop": {
          const label = cleanText(
            event.label,
            "Loop label"
          );

          lines.push(`loop ${label}`);

          addEvents(
            event.events,
            depth + 1
          );

          lines.push("end");
          break;
        }

        // =================================
        // OPTIONAL
        // =================================

        case "optional": {
          const label = cleanText(
            event.label,
            "Option label"
          );

          lines.push(`opt ${label}`);

          addEvents(
            event.events,
            depth + 1
          );

          lines.push("end");
          break;
        }

        // =================================
        // ALTERNATIVE BRANCHES
        // =================================

        case "alternative":
        case "alt": {
          if (
            !Array.isArray(event.branches) ||
            event.branches.length < 2
          ) {
            throw new Error(
              "Alternative requires at least two branches."
            );
          }

          event.branches.forEach(
            (branch, index) => {
              const condition = cleanText(
                branch.condition,
                "Branch condition"
              );

              lines.push(
                `${
                  index === 0 ? "alt" : "else"
                } ${condition}`
              );

              addEvents(
                branch.events,
                depth + 1
              );
            }
          );

          lines.push("end");
          break;
        }

        default:
          throw new Error(
            `Unsupported event kind: ${event.kind}`
          );
      }
    }
  }

  addEvents(diagram.events);

  return lines.join("\n");
}

// =====================================
// MERMAID THEME
// =====================================

function configureMermaid(mermaid) {
  if (mermaidInitialized) return;

  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",

    theme: "base",
    look: "classic",

    // =================================
    // THEME COLORS
    // =================================

    themeVariables: {
      fontFamily:
        "Inter, Segoe UI, Arial, sans-serif",

      fontSize: "14px",

      background: "#ffffff",

      primaryColor: "#eff6ff",
      primaryTextColor: "#0f172a",
      primaryBorderColor: "#93c5fd",

      // Participant cards
      actorBkg: "#eef2ff",
      actorBorder: "#818cf8",
      actorTextColor: "#1e3a8a",

      // Lifelines
      actorLineColor: COLORS.lifeline,

      // Default communication colors
      signalColor: COLORS.request,
      signalTextColor: COLORS.text,

      // Conditional blocks
      labelBoxBkgColor: "#e0e7ff",
      labelBoxBorderColor: COLORS.condition,
      labelTextColor: "#3730a3",
      loopTextColor: "#3730a3",

      // Notes
      noteBkgColor: "#fffbeb",
      noteBorderColor: "#fcd34d",
      noteTextColor: "#92400e",

      lineColor: "#94a3b8"
    },

    // =================================
    // LAYOUT
    // =================================

    sequence: {
      diagramMarginX: 30,
      diagramMarginY: 20,

      actorMargin: 75,
      messageMargin: 36,
      noteMargin: 14,

      actorFontSize: 14,
      actorFontWeight: 600,

      messageFontSize: 14,
      messageFontWeight: 500,

      mirrorActors: false,
      showSequenceNumbers: false,

      wrap: true,
      wrapPadding: 12,
      useMaxWidth: false
    },

    // =================================
    // CUSTOM SVG CSS
    // =================================

    themeCSS: `

      /* PARTICIPANT CARDS */

      rect.actor {
        rx: 10px;
        ry: 10px;
        stroke-width: 1.5px;

        filter: drop-shadow(
          0 3px 4px rgba(15, 23, 42, 0.08)
        );
      }

      text.actor,
      .actor text,
      .actor tspan {
        font-weight: 600;
      }

      /* VERTICAL LIFELINES */

      .actor-line {
        stroke: ${COLORS.lifeline} !important;
        stroke-width: 1.2px !important;
        stroke-dasharray: 4 7 !important;
      }

      /* BLUE SOLID REQUESTS */

      .messageLine0 {
        stroke: ${COLORS.request} !important;
        stroke-width: 2.5px !important;
        stroke-dasharray: none !important;
      }

      /* TEAL DASHED RESPONSES */

      .messageLine1 {
        stroke: ${COLORS.response} !important;
        stroke-width: 2.5px !important;
        stroke-dasharray: 7 5 !important;
      }

      /* MESSAGE LABELS */

      .messageText {
        fill: ${COLORS.text} !important;
        font-weight: 500;
      }

      /* CONDITIONAL BOXES */

      .loopLine {
        stroke: #c7d2fe !important;
        stroke-width: 1.2px !important;
        stroke-dasharray: 5 5 !important;
        fill: #eef2ff;
        fill-opacity: 0.08;
      }

      .labelBox {
        fill: #e0e7ff !important;
        stroke: #a5b4fc !important;
      }

      .labelText,
      .loopText {
        fill: #3730a3 !important;
        font-weight: 600;
      }

      /* NOTES */

      rect.note {
        rx: 8px;
        ry: 8px;
        stroke-width: 1.3px;
      }

      .noteText {
        font-weight: 500;
      }
    `
  });

  mermaidInitialized = true;
}

// =====================================
// MATCH ARROWHEAD COLORS TO LINES
// =====================================

function colorArrowheads(svgMarkup) {
  const doc = new DOMParser().parseFromString(
    svgMarkup,
    "image/svg+xml"
  );

  const svg = doc.documentElement;

  if (svg.localName !== "svg") {
    return svgMarkup;
  }

  const namespace =
    "http://www.w3.org/2000/svg";

  let defs = svg.querySelector("defs");

  if (!defs) {
    defs = doc.createElementNS(
      namespace,
      "defs"
    );

    svg.insertBefore(defs, svg.firstChild);
  }

  const prefix =
    `adaptive-arrow-${++renderCounter}`;

  const arrowTypes = [
    {
      selector: ".messageLine0",
      name: "request",
      color: COLORS.request,
      dashed: false
    },
    {
      selector: ".messageLine1",
      name: "response",
      color: COLORS.response,
      dashed: true
    }
  ];

  for (const type of arrowTypes) {
    const markerId =
      `${prefix}-${type.name}`;

    // Create a colored arrowhead.
    const marker = doc.createElementNS(
      namespace,
      "marker"
    );

    marker.setAttribute("id", markerId);
    marker.setAttribute("viewBox", "0 0 10 10");
    marker.setAttribute("refX", "9");
    marker.setAttribute("refY", "5");
    marker.setAttribute("markerWidth", "7");
    marker.setAttribute("markerHeight", "7");
    marker.setAttribute("orient", "auto");

    const path = doc.createElementNS(
      namespace,
      "path"
    );

    path.setAttribute(
      "d",
      "M 0 0 L 10 5 L 0 10 Z"
    );

    path.setAttribute(
      "fill",
      type.color
    );

    marker.appendChild(path);
    defs.appendChild(marker);

    // Apply the marker to message arrows.
    svg.querySelectorAll(
      type.selector
    ).forEach(line => {
      const url = `url(#${markerId})`;

      line.setAttribute(
        "marker-end",
        url
      );

      // Inline styles take precedence over
      // Mermaid's default arrow markers.
      line.style.setProperty(
        "marker-end",
        url,
        "important"
      );
    });
  }

  return new XMLSerializer()
    .serializeToString(svg);
}

// =====================================
// MAIN SEQUENCE RENDERER
// =====================================

export default function SequenceRenderer({ diagram }) {
  const diagramRef = useRef(null);

  const [svgMarkup, setSvgMarkup] =
    useState("");

  const [error, setError] =
    useState("");

  const [exporting, setExporting] =
    useState(false);

  const [exportError, setExportError] =
    useState("");

  const title =
    diagram?.title || "Sequence Diagram";

  // =====================================
  // GENERATE DIAGRAM
  // =====================================

  useEffect(() => {
    let active = true;

    setSvgMarkup("");
    setError("");
    setExportError("");

    async function renderSequence() {
      try {
        const source = buildMermaid(diagram);

        const { default: mermaid } =
          await import("mermaid");

        if (!active) return;

        configureMermaid(mermaid);

        const renderId =
          `adaptive-sequence-${++renderCounter}`;

        const result = await mermaid.render(
          renderId,
          source
        );

        // Add request/response arrowheads.
        const styledSVG = colorArrowheads(
          result.svg
        );

        if (active) {
          setSvgMarkup(styledSVG);
        }

      } catch (err) {
        console.error(
          "Sequence rendering failed:",
          err
        );

        if (active) {
          setError(
            err?.message ||
            "Unable to render sequence diagram."
          );
        }
      }
    }

    renderSequence();

    return () => {
      active = false;
    };
  }, [diagram]);

  // =====================================
  // FIND SVG ELEMENT
  // =====================================

  function getSVGElement() {
    const element =
      diagramRef.current?.querySelector("svg");

    if (!element) {
      throw new Error(
        "Rendered SVG not found."
      );
    }

    return element;
  }

  // =====================================
  // EXPORT SVG
  // =====================================

  function downloadSVG() {
    try {
      setExportError("");

      const original = getSVGElement();
      const copy = original.cloneNode(true);

      copy.setAttribute(
        "xmlns",
        "http://www.w3.org/2000/svg"
      );

      const serialized =
        new XMLSerializer()
          .serializeToString(copy);

      const blob = new Blob(
        [serialized],
        {
          type: "image/svg+xml;charset=utf-8"
        }
      );

      const url =
        URL.createObjectURL(blob);

      saveDownload(
        url,
        `${safeFilename(title)}.svg`,
        true
      );

    } catch (err) {
      console.error(
        "SVG export failed:",
        err
      );

      setExportError(
        err?.message ||
        "SVG export failed."
      );
    }
  }

  // =====================================
  // EXPORT PNG
  // =====================================

  async function downloadPNG() {
    if (exporting) return;

    setExporting(true);
    setExportError("");

    try {
      const element = getSVGElement();
      const viewBox = element.viewBox.baseVal;

      const width = Math.ceil(
        viewBox.width
      );

      const height = Math.ceil(
        viewBox.height
      );

      if (
        !width ||
        !height ||
        width * height > 16000000
      ) {
        throw new Error(
          "Diagram is too large for PNG export."
        );
      }

      const pixelRatio = Math.min(
        2,
        Math.sqrt(
          16000000 / (width * height)
        )
      );

      if (document.fonts?.ready) {
        await document.fonts.ready;
      }

      const png = await toPng(
        element,
        {
          backgroundColor: "#ffffff",
          width,
          height,
          pixelRatio,

          style: {
            width: `${width}px`,
            height: `${height}px`,
            maxWidth: "none"
          }
        }
      );

      saveDownload(
        png,
        `${safeFilename(title)}.png`
      );

    } catch (err) {
      console.error(
        "PNG export failed:",
        err
      );

      setExportError(
        err?.message ||
        "PNG export failed."
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
        className="rounded-xl border border-red-200 bg-red-50 p-5 text-red-700"
      >
        {error}
      </div>
    );
  }

  // =====================================
  // MAIN UI
  // =====================================

  return (
    <div className="space-y-5">

      {/* HEADER */}

      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-800">
            {title}
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Sequence Diagram
            {" · "}
            {diagram?.participants?.length || 0}
            {" "}participants
          </p>
        </div>

        {/* EXPORT BUTTONS */}

        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={downloadSVG}
            disabled={!svgMarkup}
            className="inline-flex items-center gap-2 rounded-xl border border-blue-200 bg-blue-50 px-4 py-3 text-sm font-semibold text-blue-700 hover:bg-blue-100 disabled:opacity-50"
          >
            <FileCode2 size={18} />
            Download SVG
          </button>

          <button
            type="button"
            onClick={downloadPNG}
            disabled={!svgMarkup || exporting}
            className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-50"
          >
            <Download size={18} />
            {exporting
              ? "Exporting..."
              : "Download PNG"}
          </button>
        </div>
      </div>

      {/* ARROW LEGEND */}

      <div className="flex flex-wrap items-center gap-x-7 gap-y-3 rounded-xl border border-slate-200 bg-slate-50 px-5 py-3 text-xs font-medium text-slate-600">

        <div className="flex items-center gap-2">
          <svg
            width="42"
            height="16"
            viewBox="0 0 42 16"
          >
            <path
              d="M2 8 H35"
              stroke={COLORS.request}
              strokeWidth="2.5"
              fill="none"
            />
            <path
              d="M32 3 L40 8 L32 13 Z"
              fill={COLORS.request}
            />
          </svg>
          Request / Action
        </div>

        <div className="flex items-center gap-2">
          <svg
            width="42"
            height="16"
            viewBox="0 0 42 16"
          >
            <path
              d="M40 8 H7"
              stroke={COLORS.response}
              strokeWidth="2.5"
              strokeDasharray="7 5"
              fill="none"
            />
            <path
              d="M10 3 L2 8 L10 13 Z"
              fill={COLORS.response}
            />
          </svg>
          Response / Result
        </div>

        <div className="flex items-center gap-2">
          <svg
            width="16"
            height="20"
            viewBox="0 0 16 20"
          >
            <path
              d="M8 1 V19"
              stroke={COLORS.lifeline}
              strokeWidth="1.5"
              strokeDasharray="4 5"
            />
          </svg>
          Participant Lifeline
        </div>

        <ArrowRightLeft
          size={15}
          className="ml-auto text-slate-400"
        />
      </div>

      {/* EXPORT ERROR */}

      {exportError && (
        <div
          role="alert"
          className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700"
        >
          {exportError}
        </div>
      )}

      {/* DIAGRAM */}

      {!svgMarkup ? (
        <div className="rounded-xl bg-slate-50 p-8 text-slate-500">
          Generating sequence diagram...
        </div>
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-gradient-to-b from-slate-50 to-white p-6 md:p-8">
          <div
            ref={diagramRef}
            className="w-max min-w-full [&_svg]:h-auto [&_svg]:max-w-none"
            dangerouslySetInnerHTML={{
              __html: svgMarkup
            }}
          />
        </div>
      )}

      {/* FOOTER */}

      <p className="text-xs text-slate-500">
        Requests use solid blue arrows.
        Responses use dashed teal arrows.
        Vertical lifelines indicate participants.
        Diagrams are generated from structured JSON
        without AI rendering.
      </p>

    </div>
  );
}
