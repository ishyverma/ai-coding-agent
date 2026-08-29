import axios from "axios";
import type {
  EvalResult,
  Run,
  RunLog,
  RunTriggerResponse,
  Task,
} from "@/types/api";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const client = axios.create({ baseURL: `${BASE}/api/v1` });

export const api = {
  tasks: {
    list: (): Promise<Task[]> =>
      client.get("/tasks").then((r) => r.data),
    get: (id: number): Promise<Task> =>
      client.get(`/tasks/${id}`).then((r) => r.data),
    create: (data: {
      repo_url: string;
      task_text: string;
    }): Promise<Task> => client.post("/tasks", data).then((r) => r.data),
    runs: (id: number): Promise<Run[]> =>
      client.get(`/tasks/${id}/runs`).then((r) => r.data),
    run: (id: number): Promise<RunTriggerResponse> =>
      client.post(`/tasks/${id}/run`).then((r) => r.data),
  },
  runs: {
    get: (id: number): Promise<Run> =>
      client.get(`/runs/${id}`).then((r) => r.data),
    getLogs: (id: number): Promise<RunLog[]> =>
      client.get(`/runs/${id}/logs`).then((r) => r.data),
  },
  evals: {
    list: (): Promise<EvalResult[]> =>
      client.get("/evals").then((r) => r.data),
    trigger: (): Promise<{ message: string }> =>
      client.post("/evals/run").then((r) => r.data),
  },
};