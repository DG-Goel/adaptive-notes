
import { useState } from "react";

import {
  GitBranch,
  Network,
  Layers3,
  FileImage,
  Binary,
  ChevronRight,
  MessagesSquare
} from "lucide-react";

// =====================================
// DIAGRAM RENDERERS
// =====================================

import DiagramRenderer from "./diagram/DiagramRenderer.jsx";
import DataStructureRenderer from "./diagram/DataStructureRenderer.jsx";
import SequenceRenderer from "./diagram/SequenceRenderer.jsx";

// =====================================
// EXAMPLE JSON FILES
// =====================================

import flowchartExample from "./examples/flowchart.json";
import architectureExample from "./examples/architecture.json";
import dataStructureExample from "./examples/dataStructure.json";
import complexTreeExample from "./examples/complexTree.json";
import sequenceExample from "./examples/sequence.json";

// =====================================
// DIAGRAM EXAMPLES
// =====================================

const diagrams = {
  flowchart: flowchartExample,
  architecture: architectureExample,
  sequence: sequenceExample
};

// =====================================
// DATA STRUCTURE TYPES
// =====================================

const structureNames = {
  array: "Array",
  stack: "Stack",
  queue: "Queue",
  linked_list: "Singly Linked List",
  binary_tree: "Binary Tree"
};

// =====================================
// MAIN APPLICATION
// =====================================

export default function App() {
  const [selectedType, setSelectedType] =
    useState("flowchart");

  const [selectedStructure, setSelectedStructure] =
    useState("linked_list");

  // =====================================
  // SELECT THE CORRECT DIAGRAM DATA
  // =====================================

  const diagram =
    selectedType === "data_structure"
      ? selectedStructure === "binary_tree"
        ? complexTreeExample
        : {
            ...dataStructureExample,
            type: "data_structure",
            subtype: selectedStructure,
            title: structureNames[selectedStructure]
          }
      : diagrams[selectedType];

  // =====================================
  // BUTTON STYLING
  // =====================================

  const mainButtonClass = (type) =>
    `flex items-center gap-2 rounded-xl px-5 py-3
     text-sm font-semibold transition-all duration-200
     ${
       selectedType === type
         ? "bg-blue-600 text-white shadow-md"
         : "bg-slate-100 text-slate-700 hover:bg-slate-200"
     }`;

  const structureButtonClass = (type) =>
    `rounded-lg px-4 py-2 text-sm font-medium
     transition-all duration-200
     ${
       selectedStructure === type
         ? "bg-indigo-100 text-indigo-700 ring-1 ring-indigo-300"
         : "bg-slate-100 text-slate-600 hover:bg-slate-200"
     }`;

  // =====================================
  // RENDER
  // =====================================

  return (
    <main className="mx-auto max-w-[1800px] px-5 py-10">

      {/* ==============================
          HEADER
      ============================== */}

      <header className="mb-8">

        <div className="flex items-center gap-3">

          <div className="rounded-2xl bg-blue-600 p-3 text-white shadow-md">
            <Network size={27} />
          </div>

          <div>
            <h1 className="text-3xl font-bold text-slate-900">
              Adaptive Notes
            </h1>

            <p className="mt-1 text-sm text-slate-500">
              Unified Diagram Engine
            </p>
          </div>

        </div>

        <p className="mt-4 text-slate-600">
          Create professional flowcharts,
          architecture diagrams, data structure
          visualizations, and sequence diagrams
          using structured JSON.
        </p>

      </header>

      {/* ==============================
          MAIN DIAGRAM SELECTOR
      ============================== */}

      <section className="mb-6 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">

        <h2 className="mb-4 text-sm font-semibold text-slate-700">
          Select Diagram Type
        </h2>

        <div className="flex flex-wrap gap-3">

          {/* FLOWCHART */}
          <button
            type="button"
            onClick={() => setSelectedType("flowchart")}
            className={mainButtonClass("flowchart")}
            aria-pressed={selectedType === "flowchart"}
          >
            <GitBranch size={18} />
            Flowchart
          </button>

          {/* ARCHITECTURE */}
          <button
            type="button"
            onClick={() => setSelectedType("architecture")}
            className={mainButtonClass("architecture")}
            aria-pressed={selectedType === "architecture"}
          >
            <Network size={18} />
            Architecture
          </button>

          {/* DATA STRUCTURES */}
          <button
            type="button"
            onClick={() => setSelectedType("data_structure")}
            className={mainButtonClass("data_structure")}
            aria-pressed={selectedType === "data_structure"}
          >
            <Layers3 size={18} />
            Data Structures
          </button>

          {/* SEQUENCE DIAGRAM */}
          <button
            type="button"
            onClick={() => setSelectedType("sequence")}
            className={mainButtonClass("sequence")}
            aria-pressed={selectedType === "sequence"}
          >
            <MessagesSquare size={18} />
            Sequence Diagram
          </button>

        </div>

        {/* ==============================
            DATA STRUCTURE SELECTOR
        ============================== */}

        {selectedType === "data_structure" && (
          <div className="mt-5 border-t border-slate-200 pt-5">

            <div className="mb-3 flex items-center gap-2">

              <Binary
                size={18}
                className="text-indigo-600"
              />

              <p className="text-sm font-semibold text-slate-600">
                Select Data Structure
              </p>

            </div>

            <div className="flex flex-wrap gap-2">

              {Object.entries(structureNames).map(
                ([id, label]) => (
                  <button
                    key={id}
                    type="button"
                    onClick={() => setSelectedStructure(id)}
                    className={structureButtonClass(id)}
                    aria-pressed={selectedStructure === id}
                  >
                    {label}
                  </button>
                )
              )}

            </div>

            {/* Selected structure information */}
            <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">

              <ChevronRight size={15} />

              <span>
                {selectedStructure === "binary_tree"
                  ? "Complex 31-node binary search tree with automatic D3 layout."
                  : `SVG-based ${structureNames[selectedStructure]} visualization.`}
              </span>

            </div>

          </div>
        )}

        {/* ==============================
            SEQUENCE DIAGRAM INFORMATION
        ============================== */}

        {selectedType === "sequence" && (
          <div className="mt-5 border-t border-slate-200 pt-5">

            <div className="flex items-center gap-2 text-sm text-slate-600">

              <MessagesSquare
                size={18}
                className="text-indigo-600"
              />

              <span>
                Automatically generates sequence diagrams
                showing participants, messages, conditions,
                and interactions using Mermaid.js.
              </span>

            </div>

          </div>
        )}

      </section>

      {/* ==============================
          DIAGRAM RENDERER
      ============================== */}

      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-lg">

        {selectedType === "sequence" ? (

          <SequenceRenderer diagram={diagram} />

        ) : selectedType === "data_structure" ? (

          <DataStructureRenderer diagram={diagram} />

        ) : (

          <DiagramRenderer diagram={diagram} />

        )}

      </section>

      {/* ==============================
          FOOTER
      ============================== */}

      <footer className="mt-6 flex flex-wrap items-center gap-2 text-sm text-slate-500">

        <FileImage size={17} />

        <span>
          Generate diagrams locally without AI rendering.
          Export supported diagrams as PNG or SVG
          for Microsoft Word.
        </span>

      </footer>

    </main>
  );
}
