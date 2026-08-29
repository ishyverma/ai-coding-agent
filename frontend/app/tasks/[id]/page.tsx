"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Loader2, Play } from "lucide-react";
import { Button, buttonVariants } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LogViewer } from "@/components/LogViewer";
import { RunStatusBadge, TaskStatusBadge } from "@/components/StatusBadge";
import { api } from "@/lib/api";
import { useState } from "react";

export default function TaskDetailPage() {
  const params = useParams<{ id: string }>();
  const taskId = Number(params.id);
  const queryClient = useQueryClient();

  const [error, setError] = useState<string | null>(null);
  const [streamRunId, setStreamRunId] = useState<number | null>(null);

  const { data: task, isLoading: taskLoading } = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => api.tasks.get(taskId),
    refetchInterval: (query) =>
      query.state.data?.status === "running" ? 3000 : false,
  });

  const { data: runs, isLoading: runsLoading } = useQuery({
    queryKey: ["runs", taskId],
    queryFn: () => api.tasks.runs(taskId),
    refetchInterval: (query) =>
      query.state.data?.some((run) => run.status === "running")
        ? 3000
        : false,
  });

  const triggerRun = useMutation({
    mutationFn: () => api.tasks.run(taskId),
    onSuccess: (data) => {
      setError(null);
      setStreamRunId(data.run_id);
      queryClient.invalidateQueries({ queryKey: ["task", taskId] });
      queryClient.invalidateQueries({ queryKey: ["runs", taskId] });
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
    },
    onError: (err: Error) => {
      setError(err.message ?? "Failed to start run");
    },
  });

  if (taskLoading || !task) {
    return (
      <main className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <Card>
          <CardContent className="p-5 text-sm text-muted-foreground">
            Loading task...
          </CardContent>
        </Card>
      </main>
    );
  }

  const latestRun = runs?.[0] ?? null;

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-6 flex flex-col gap-4 border-b pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div className="min-w-0">
          <Link href="/" className={buttonVariants({ variant: "ghost" })}>
            Back
          </Link>
          <h1 className="mt-4 text-2xl font-semibold tracking-normal sm:text-3xl">
            Task #{task.id}
          </h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Created {new Date(task.created_at).toLocaleString()}
          </p>
        </div>
        <div className="self-start sm:self-end">
          <TaskStatusBadge status={task.status} />
        </div>
      </div>

      {/* Task card + Runs row (side by side on desktop, stacked on mobile) */}
      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <Card>
          <CardHeader className="p-4 sm:p-6">
            <CardTitle className="break-words text-lg leading-7 sm:text-xl sm:leading-8">
              {task.task_text}
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 p-4 pt-0 sm:p-6 sm:pt-0">
            <div>
              <p className="text-xs font-medium text-muted-foreground">
                Repository
              </p>
              <p className="mt-1 break-all text-sm leading-6 text-foreground">
                {task.repo_url}
              </p>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <Button
              onClick={() => triggerRun.mutate()}
              disabled={triggerRun.isPending || task.status === "running"}
            >
              {triggerRun.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Starting...
                </>
              ) : task.status === "running" ? (
                "Agent already running"
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Run Agent
                </>
              )}
            </Button>
          </CardContent>
        </Card>

        <aside>
          <h2 className="mb-3 text-base font-semibold">Runs</h2>
          {runsLoading ? (
            <Card>
              <CardContent className="p-5 text-sm text-muted-foreground">
                Loading runs...
              </CardContent>
            </Card>
          ) : !runs?.length ? (
            <Card>
              <CardContent className="p-5 text-sm text-muted-foreground">
                No runs yet for this task.
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {runs.map((run) => (
                <Card key={run.id}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-medium">Run #{run.id}</p>
                        <p className="mt-1 text-xs leading-5 text-muted-foreground">
                          {new Date(run.created_at).toLocaleString()}
                        </p>
                      </div>
                      <RunStatusBadge status={run.status} />
                    </div>
                    <dl className="mt-4 grid grid-cols-2 gap-3 text-xs">
                      <div>
                        <dt className="text-muted-foreground">Attempts</dt>
                        <dd className="mt-1 font-medium">{run.attempts}</dd>
                      </div>
                      <div>
                        <dt className="text-muted-foreground">Tokens</dt>
                        <dd className="mt-1 font-medium">
                          {run.tokens_used.toLocaleString()}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-muted-foreground">Duration</dt>
                        <dd className="mt-1 font-medium">
                          {run.duration_s != null
                            ? `${run.duration_s}s`
                            : "Pending"}
                        </dd>
                      </div>
                      <div>
                        <dt className="text-muted-foreground">Completed</dt>
                        <dd className="mt-1 font-medium">
                          {run.completed_at
                            ? new Date(run.completed_at).toLocaleTimeString()
                            : "Pending"}
                        </dd>
                      </div>
                    </dl>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </aside>
      </div>

      {/* Live Logs — full width */}
      <section className="mt-6">
        <h2 className="mb-3 text-base font-semibold">Live Logs</h2>
        <LogViewer runId={streamRunId ?? (latestRun?.id ?? null)} />
      </section>
    </main>
  );
}
