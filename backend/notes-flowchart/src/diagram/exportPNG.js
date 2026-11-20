
import { toPng } from "html-to-image";

import {
  getViewportForBounds
} from "@xyflow/react";

import {
  NODE_WIDTH,
  NODE_HEIGHT
} from "./elkLayout.js";

const PADDING = 100;
const MAX_PIXELS = 20000000;

// =====================================
// CALCULATE FULL DIAGRAM BOUNDS
// =====================================

function calculateBounds(nodes) {
  if (!nodes.length) {
    throw new Error("Nothing to export.");
  }

  const minX = Math.min(
    ...nodes.map(node => node.position.x)
  );

  const minY = Math.min(
    ...nodes.map(node => node.position.y)
  );

  const maxX = Math.max(
    ...nodes.map(
      node => node.position.x + NODE_WIDTH
    )
  );

  const maxY = Math.max(
    ...nodes.map(
      node => node.position.y + NODE_HEIGHT
    )
  );

  return {
    x: minX,
    y: minY,
    width: maxX - minX,
    height: maxY - minY
  };
}

// =====================================
// EXPORT DIAGRAM TO PNG
// =====================================

export async function exportDiagramPNG({
  container,
  nodes,
  title
}) {
  if (!container) {
    throw new Error("Diagram container not found.");
  }

  const viewport = container.querySelector(
    ".react-flow__viewport"
  );

  if (!viewport) {
    throw new Error("React Flow viewport not found.");
  }

  const bounds = calculateBounds(nodes);

  const imageWidth = Math.ceil(
    bounds.width + PADDING * 2
  );

  const imageHeight = Math.ceil(
    bounds.height + PADDING * 2
  );

  if (
    imageWidth > 12000 ||
    imageHeight > 12000 ||
    imageWidth * imageHeight > MAX_PIXELS
  ) {
    throw new Error(
      "Diagram is too large for one PNG. " +
      "Split it into smaller diagrams."
    );
  }

  // Scale up for sharper images where possible.
  const pixelRatio = Math.min(
    2,
    Math.sqrt(
      MAX_PIXELS / (imageWidth * imageHeight)
    )
  );

  // Fit the entire diagram, regardless of
  // current interactive zoom.
  const { x, y, zoom } = getViewportForBounds(
    bounds,
    imageWidth,
    imageHeight,
    1,
    1,
    0
  );

  // Wait for fonts before taking the image.
  if (document.fonts?.ready) {
    await document.fonts.ready;
  }

  const dataUrl = await toPng(viewport, {
    backgroundColor: "#ffffff",
    width: imageWidth,
    height: imageHeight,
    pixelRatio,

    style: {
      width: `${imageWidth}px`,
      height: `${imageHeight}px`,

      transform:
        `translate(${x}px, ${y}px) scale(${zoom})`,

      transformOrigin: "top left"
    }
  });

  const filename = String(
    title || "adaptive-notes-diagram"
  )
    .replace(/[^a-z0-9_-]+/gi, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 100);

  const link = document.createElement("a");

  link.href = dataUrl;
  link.download =
    `${filename || "diagram"}.png`;

  document.body.appendChild(link);
  link.click();
  link.remove();
}
