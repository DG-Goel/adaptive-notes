
import { Handle, Position } from "@xyflow/react";

import {
  PlayCircle,
  Keyboard,
  GitBranch,
  CheckCircle2,
  AlertCircle
} from "lucide-react";

const nodeStyles = {
  start: {
    Icon: PlayCircle,
    title: "START",
    bg: "bg-indigo-50",
    border: "border-indigo-300",
    icon: "text-indigo-600"
  },

  action: {
    Icon: Keyboard,
    title: "ACTION",
    bg: "bg-sky-50",
    border: "border-sky-300",
    icon: "text-sky-600"
  },

  decision: {
    Icon: GitBranch,
    title: "DECISION",
    bg: "bg-amber-50",
    border: "border-amber-300",
    icon: "text-amber-600"
  },

  success: {
    Icon: CheckCircle2,
    title: "SUCCESS",
    bg: "bg-green-50",
    border: "border-green-300",
    icon: "text-green-600"
  },

  error: {
    Icon: AlertCircle,
    title: "ERROR",
    bg: "bg-red-50",
    border: "border-red-300",
    icon: "text-red-600"
  }
};

export default function FlowNode({ data }) {
  const config = nodeStyles[data.kind] || nodeStyles.action;
  const Icon = config.Icon;

  const horizontal = data.direction === "RIGHT";

  return (
    <div
      className={`
        flex h-[100px] w-[260px]
        items-center gap-3 rounded-2xl
        border-2 px-4 shadow-md
        ${config.bg} ${config.border}
      `}
    >
      <Handle
        type="target"
        position={horizontal ? Position.Left : Position.Top}
        isConnectable={false}
        style={{ opacity: 0 }}
      />

      <div className="shrink-0 rounded-xl bg-white p-3 shadow-sm">
        <Icon size={26} className={config.icon} />
      </div>

      <div className="min-w-0">
        <div className="text-xs font-bold text-slate-500">
          {config.title}
        </div>

        <div className="mt-1 break-words text-sm font-semibold text-slate-800">
          {data.label}
        </div>
      </div>

      <Handle
        type="source"
        position={horizontal ? Position.Right : Position.Bottom}
        isConnectable={false}
        style={{ opacity: 0 }}
      />
    </div>
  );
}
