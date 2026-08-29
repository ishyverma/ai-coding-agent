import { Badge } from "@/components/ui/badge";
import type { RunStatus, TaskStatus } from "@/types/api";

const TASK_VARIANTS: Record<
  TaskStatus,
  "default" | "secondary" | "destructive" | "warning" | "success"
> = {
  pending: "secondary",
  running: "warning",
  done: "success",
  failed: "destructive",
};

const RUN_VARIANTS: Record<
  RunStatus,
  "default" | "secondary" | "destructive" | "warning" | "success"
> = {
  running: "warning",
  passed: "success",
  failed: "destructive",
  gave_up: "secondary",
};

export function TaskStatusBadge({ status }: { status: TaskStatus }) {
  return (
    <Badge variant={TASK_VARIANTS[status] ?? "secondary"}>{status}</Badge>
  );
}

export function RunStatusBadge({ status }: { status: RunStatus }) {
  return (
    <Badge variant={RUN_VARIANTS[status] ?? "secondary"}>{status}</Badge>
  );
}