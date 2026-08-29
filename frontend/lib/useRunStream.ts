"use client";

import { useEffect, useState } from "react";
import type { RunLog, RunStatus } from "@/types/api";

const WS_BASE = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000")
  .replace("https://", "wss://")
  .replace("http://", "ws://");

interface UseRunStreamResult {
  logs: RunLog[];
  finalStatus: RunStatus | null;
  isConnected: boolean;
  error: string | null;
}

/**
 * Opens a WebSocket to stream live logs for a run.
 * The backend replays all logs from the start, so this works
 * for finished runs too. Closes automatically when the run ends.
 *
 * Usage:
 *   const { logs, finalStatus, isConnected } = useRunStream(runId);
 */
export function useRunStream(runId: number | null): UseRunStreamResult {
  const [logs, setLogs] = useState<RunLog[]>([]);
  const [finalStatus, setFinalStatus] = useState<RunStatus | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!runId) return;

    setLogs([]);
    setFinalStatus(null);
    setError(null);

    const ws = new WebSocket(`${WS_BASE}/api/v1/runs/${runId}/stream`);

    ws.onopen = () => setIsConnected(true);

    ws.onmessage = (event) => {
      let payload: {
        type: string;
        data?: RunLog;
        status?: RunStatus;
        message?: string;
      };

      try {
        payload = JSON.parse(event.data as string) as typeof payload;
      } catch {
        setError("Received an invalid stream message");
        return;
      }

      if (payload.type === "log" && payload.data) {
        setLogs((prev) => [...prev, payload.data!]);
      } else if (payload.type === "done" && payload.status) {
        setFinalStatus(payload.status);
        setIsConnected(false);
      } else if (payload.type === "error") {
        setError(payload.message ?? "Stream error");
      }
    };

    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => {
      setIsConnected(false);
      setError("WebSocket connection failed");
    };

    return () => ws.close();
  }, [runId]);

  return { logs, finalStatus, isConnected, error };
}
