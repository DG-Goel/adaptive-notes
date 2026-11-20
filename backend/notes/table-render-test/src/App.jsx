
import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

// Sample structured table data
const sampleData = {
  title: "Java Collections Comparison",
  headers: ["Feature", "ArrayList", "LinkedList"],
  rows: [
    ["Structure", "Resizable array", "Doubly linked list"],
    ["Random Access", "O(1)", "O(n)"],
    ["Insertion", "May require shifting", "O(1) at known node"],
    ["Memory Overhead", "Lower", "Higher"],
    ["Thread Safety", "Not synchronized", "Not synchronized"]
  ]
};

// Convert JSON into Markdown
function jsonToMarkdown(data) {
  if (
    !Array.isArray(data.headers) ||
    data.headers.length === 0
  ) {
    throw new Error("Headers must be a non-empty array.");
  }

  if (!Array.isArray(data.rows)) {
    throw new Error("Rows must be an array.");
  }

  const escapeCell = (value) =>
    String(value ?? "")
      .replace(/\|/g, "\\|")
      .replace(/\r?\n/g, " ");

  const columns = data.headers.length;

  for (const row of data.rows) {
    if (
      !Array.isArray(row) ||
      row.length !== columns
    ) {
      throw new Error(
        "Every row must match the number of headers."
      );
    }
  }

  const header =
    "| " + data.headers.map(escapeCell).join(" | ") + " |";

  const separator =
    "| " + data.headers.map(() => "---").join(" | ") + " |";

  const rows = data.rows.map(
    (row) =>
      "| " + row.map(escapeCell).join(" | ") + " |"
  );

  return [
    "# " + (data.title || "Comparison Table"),
    "",
    header,
    separator,
    ...rows
  ].join("\n");
}

export { jsonToMarkdown };

export function TablePreview({ data }) {
  return (
    <div className="preview">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
        table: ({ children }) => (
          <div className="table-scroll">
            <table className="modern-table" style={{ minWidth: data.headers.length * 190, width: "100%" }}>
              {children}
            </table>
          </div>
        )
      }}>
        {jsonToMarkdown(data)}
      </ReactMarkdown>
    </div>
  );
}

export default function App() {
  const [jsonInput, setJsonInput] = useState(
    JSON.stringify(sampleData, null, 2)
  );

  let markdown = "";
  let error = "";
  let columnCount = 3;

  try {
    const data = JSON.parse(jsonInput);

    markdown = jsonToMarkdown(data);

    // Detect the number of columns automatically
    columnCount = data.headers.length;

  } catch (err) {
    error = err.message;
  }

  // Automatically calculate table width
  const tableMinWidth = columnCount * 190;

  return (
    <main className="app">
      <header>
        <h1>Adaptive Notes — JSON Table Generator</h1>
        <p>JSON to Markdown to Beautiful Table</p>
      </header>

      <div className="workspace">

        {/* JSON Input */}
        <section className="panel">
          <h2>JSON Input</h2>

          <textarea
            value={jsonInput}
            onChange={(e) => setJsonInput(e.target.value)}
            spellCheck={false}
            placeholder="Paste table JSON here..."
          />
        </section>

        {/* Generated Table */}
        <section className="panel">
          <h2>Generated Table</h2>

          <div className="preview">
            {error ? (
              <p style={{ color: "red" }}>
                {error}
              </p>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  table: ({ children }) => (
                    <div className="table-scroll">
                      <table
                        className="modern-table"
                        style={{
                          minWidth: `${tableMinWidth}px`,
                          width: "100%",
                          tableLayout: "auto"
                        }}
                      >
                        {children}
                      </table>
                    </div>
                  )
                }}
              >
                {markdown}
              </ReactMarkdown>
            )}
          </div>
        </section>

      </div>
    </main>
  );
}
