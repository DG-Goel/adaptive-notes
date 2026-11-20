
import {
  Handle,
  Position
} from "@xyflow/react";

import {
  Monitor,
  Server,
  Database,
  Cpu,
  MemoryStick,
  HardDrive,
  Cloud,
  Network,
  Boxes
} from "lucide-react";

const componentStyles = {
  client: {
    Icon: Monitor,
    title: "CLIENT",
    bg: "bg-blue-50",
    border: "border-blue-300",
    icon: "text-blue-600"
  },

  service: {
    Icon: Server,
    title: "SERVICE",
    bg: "bg-violet-50",
    border: "border-violet-300",
    icon: "text-violet-600"
  },

  database: {
    Icon: Database,
    title: "DATABASE",
    bg: "bg-emerald-50",
    border: "border-emerald-300",
    icon: "text-emerald-600"
  },

  cpu: {
    Icon: Cpu,
    title: "PROCESSOR",
    bg: "bg-amber-50",
    border: "border-amber-300",
    icon: "text-amber-600"
  },

  memory: {
    Icon: MemoryStick,
    title: "MEMORY",
    bg: "bg-cyan-50",
    border: "border-cyan-300",
    icon: "text-cyan-600"
  },

  storage: {
    Icon: HardDrive,
    title: "STORAGE",
    bg: "bg-teal-50",
    border: "border-teal-300",
    icon: "text-teal-600"
  },

  cloud: {
    Icon: Cloud,
    title: "CLOUD",
    bg: "bg-sky-50",
    border: "border-sky-300",
    icon: "text-sky-600"
  },

  network: {
    Icon: Network,
    title: "NETWORK",
    bg: "bg-pink-50",
    border: "border-pink-300",
    icon: "text-pink-600"
  },

  component: {
    Icon: Boxes,
    title: "COMPONENT",
    bg: "bg-slate-50",
    border: "border-slate-300",
    icon: "text-slate-600"
  }
};

export default function ArchitectureNode({ data }) {
  const config =
    componentStyles[data.kind] ||
    componentStyles.component;

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
        position={
          horizontal ? Position.Left : Position.Top
        }
        isConnectable={false}
        style={{ opacity: 0 }}
      />

      <div className="shrink-0 rounded-xl bg-white p-3 shadow-sm">
        <Icon size={27} className={config.icon} />
      </div>

      <div className="min-w-0 flex-1">
        <div className="text-[11px] font-bold tracking-wide text-slate-500">
          {config.title}
        </div>

        <div className="mt-1 break-words text-sm font-semibold text-slate-800">
          {data.label}
        </div>

        {data.description && (
          <div className="mt-1 line-clamp-2 text-[11px] text-slate-500">
            {data.description}
          </div>
        )}
      </div>

      <Handle
        type="source"
        position={
          horizontal ? Position.Right : Position.Bottom
        }
        isConnectable={false}
        style={{ opacity: 0 }}
      />
    </div>
  );
}
