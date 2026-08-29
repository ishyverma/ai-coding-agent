"use client";

import { useQuery } from "@tanstack/react-query";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { RunStatusBadge } from "@/components/StatusBadge";
import { buttonVariants } from "@/components/ui/button";
import Link from "next/link";
import { useMemo, useState } from "react";
import { cn } from "@/lib/utils";
import { ChevronLeft, ChevronRight } from "lucide-react";

const RUNS_PER_PAGE = 6;

function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: string;
  hint?: string;
}) {
  return (
    <Card>
      <CardContent className="p-4">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <p className="mt-1 break-words text-2xl font-semibold tracking-normal">
          {value}
        </p>
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}

export function Dashboard() {
  const [runsPage, setRunsPage] = useState(0);

  const { data: tasks } = useQuery({
    queryKey: ["tasks"],
    queryFn: api.tasks.list,
    refetchInterval: 5000,
  });

  const { data: evals } = useQuery({
    queryKey: ["evals"],
    queryFn: api.evals.list,
    refetchInterval: 15000,
  });

  const { data: runs } = useQuery({
    queryKey: ["recent-runs"],
    queryFn: async () => {
      const tasks = await api.tasks.list();
      const all = await Promise.all(
        tasks.map((task) => api.tasks.runs(task.id))
      );
      return all.flat().sort((a, b) => b.created_at.localeCompare(a.created_at));
    },
    refetchInterval: 5000,
  });

  const stats = useMemo(() => {
    const totalTasks = tasks?.length ?? 0;
    const doneTasks = tasks?.filter((t) => t.status === "done").length ?? 0;
    const totalRuns = runs?.length ?? 0;
    const passedRuns = runs?.filter((r) => r.status === "passed").length ?? 0;
    const totalTokens =
      runs?.reduce((sum, r) => sum + (r.tokens_used ?? 0), 0) ?? 0;
    const latestEval = evals?.[0];

    return {
      totalTasks,
      doneTasks,
      successRate: totalTasks ? Math.round((doneTasks / totalTasks) * 100) : 0,
      totalRuns,
      passRate: totalRuns ? Math.round((passedRuns / totalRuns) * 100) : 0,
      totalTokens: totalTokens.toLocaleString(),
      avgTokens: totalRuns ? Math.round(totalTokens / totalRuns) : 0,
      latestEvalRate: latestEval
        ? `${(latestEval.pass_rate * 100).toFixed(0)}%`
        : "—",
      latestEvalName: latestEval ? latestEval.eval_name : "—",
    };
  }, [tasks, runs, evals]);

  const totalRunPages = Math.ceil((runs?.length ?? 0) / RUNS_PER_PAGE);
  const paginatedRuns = runs?.slice(
    runsPage * RUNS_PER_PAGE,
    (runsPage + 1) * RUNS_PER_PAGE
  );

  return (
    <div className="space-y-6">
      {/* Stat cards — 2 cols mobile, 3 cols tablet, 5 cols desktop */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
        <StatCard label="Tasks" value={String(stats.totalTasks)} />
        <StatCard
          label="Task success"
          value={`${stats.successRate}%`}
          hint={`${stats.doneTasks}/${stats.totalTasks} done`}
        />
        <StatCard label="Runs" value={String(stats.totalRuns)} />
        <StatCard label="Run pass rate" value={`${stats.passRate}%`} />
        <StatCard
          label="Tokens"
          value={stats.totalTokens}
          hint={`${stats.avgTokens.toLocaleString()} avg / run`}
        />
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs uppercase tracking-wide text-muted-foreground">
                Latest eval
              </p>
              <p className="mt-1 text-lg font-semibold">
                {stats.latestEvalRate} pass rate
              </p>
              <p className="text-xs text-muted-foreground">
                {stats.latestEvalName} suite
              </p>
            </div>
            <Link
              href="/evals"
              className={cn(
                buttonVariants({ variant: "outline", size: "sm" })
              )}
            >
              View evals
            </Link>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-4 sm:p-5">
          <div className="mb-4 flex items-center justify-between">
            <p className="text-xs uppercase tracking-wide text-muted-foreground">
              Recent runs
            </p>
            <Link href="/">
              <span
                className={cn(
                  buttonVariants({ variant: "ghost", size: "sm" }),
                  "pointer-events-none"
                )}
              >
                All tasks
              </span>
            </Link>
          </div>
          {!runs?.length ? (
            <p className="text-sm text-muted-foreground">
              No runs yet. Create a task to get started.
            </p>
          ) : (
            <>
              <div className="space-y-3">
                {paginatedRuns?.map((run) => (
                  <Link
                    key={run.id}
                    href={`/tasks/${run.task_id}`}
                    className="block"
                  >
                    <div className="flex items-center justify-between rounded-md border border-transparent px-3 py-2.5 hover:border-border hover:bg-muted/50">
                      <div className="min-w-0">
                        <p className="break-words text-sm leading-6">
                          Run #{run.id}
                          <span className="text-muted-foreground">
                            {" "}
                            for task #{run.task_id}
                          </span>
                        </p>
                        <p className="mt-0.5 text-xs leading-5 text-muted-foreground">
                          {run.tokens_used.toLocaleString()} tokens,{" "}
                          {run.duration_s != null
                            ? `${run.duration_s}s`
                            : "duration pending"}
                          ,{" "}
                          {new Date(run.created_at).toLocaleString()}
                        </p>
                      </div>
                      <RunStatusBadge status={run.status} />
                    </div>
                  </Link>
                ))}
              </div>

              {/* Pagination controls */}
              {totalRunPages > 1 && (
                <div className="mt-4 flex items-center justify-between border-t border-border pt-3">
                  <p className="text-xs text-muted-foreground">
                    Page {runsPage + 1} of {totalRunPages}{" "}
                    <span className="hidden sm:inline">
                      ({runs.length} runs)
                    </span>
                  </p>
                  <div className="flex gap-1">
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={runsPage === 0}
                      onClick={() => setRunsPage((p) => p - 1)}
                    >
                      <ChevronLeft className="h-4 w-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      disabled={runsPage >= totalRunPages - 1}
                      onClick={() => setRunsPage((p) => p + 1)}
                    >
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
