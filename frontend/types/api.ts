// These mirror the Pydantic schemas in backend/app/schemas.py
// Keep these in sync manually — if you change a schema, update these too.

export type TaskStatus = "pending" | "running" | "done" | "failed";
export type RunStatus = "running" | "passed" | "failed" | "gave_up";
export type LogLevel = "info" | "error";
export type LogStep =
  | "setup"
  | "inspect"
  | "analyze"
  | "modify"
  | "run_tests"
  | "recovery"
  | "done"
  | "error";

export interface Task {
  id: number;
  repo_url: string;
  task_text: string;
  status: TaskStatus;
  created_at: string;
}

export interface Run {
  id: number;
  task_id: number;
  status: RunStatus;
  attempts: number;
  tokens_used: number;
  duration_s: number | null;
  error_msg: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface RunLog {
  id: number;
  run_id: number;
  step: LogStep;
  level: LogLevel;
  message: string;
  diff: string | null;
  created_at: string;
}

export interface RunTriggerResponse {
  run_id: number;
  status: string;
  message: string;
}

export interface EvalResult {
  id: number;
  eval_name: string;
  total_tasks: number;
  passed: number;
  failed: number;
  pass_rate: number;
  avg_attempts: number;
  avg_tokens: number;
  avg_duration_s: number;
  run_at: string;
}