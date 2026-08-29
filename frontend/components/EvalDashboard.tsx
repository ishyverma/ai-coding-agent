"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { api } from "@/lib/api";

export function EvalDashboard() {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState<string | null>(null);

  const { data: results, isLoading } = useQuery({
    queryKey: ["evals"],
    queryFn: api.evals.list,
    refetchInterval: 5000,
  });

  const trigger = useMutation({
    mutationFn: api.evals.trigger,
    onSuccess: (data) => {
      setMessage(data.message);
      queryClient.invalidateQueries({ queryKey: ["evals"] });
    },
    onError: (err: Error) => {
      setMessage(err.message ?? "Failed to start eval run");
    },
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-5 text-sm text-muted-foreground">
          Loading eval results...
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="space-y-1.5">
          <CardTitle className="text-xl">Eval Results</CardTitle>
          <CardDescription>
            Agent pass rate across the 5 fixture repos
          </CardDescription>
        </div>
        <Button onClick={() => trigger.mutate()} disabled={trigger.isPending}>
          {trigger.isPending ? "Running eval..." : "Run Eval"}
        </Button>
      </CardHeader>
      <CardContent>
        {message && (
          <p className="mb-4 rounded-md border bg-muted/40 p-3 text-sm leading-6 text-muted-foreground">
            {message}
          </p>
        )}

        {!results?.length ? (
          <p className="text-sm text-muted-foreground">
            No eval results yet. Click {"Run Eval"} to benchmark the agent.
          </p>
        ) : (
          <div className="space-y-3">
            {results.map((result) => (
              <div key={result.id} className="rounded-md border p-4">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div>
                    <p className="text-sm font-medium">
                      {result.eval_name} suite
                    </p>
                    <p className="mt-1 text-xs leading-5 text-muted-foreground">
                      {new Date(result.run_at).toLocaleString()}
                    </p>
                  </div>
                  <Badge
                    variant={
                      result.pass_rate === 1
                        ? "success"
                        : result.pass_rate >= 0.6
                          ? "warning"
                          : "destructive"
                    }
                  >
                    {(result.pass_rate * 100).toFixed(0)}%
                  </Badge>
                </div>
                <dl className="mt-4 grid grid-cols-2 gap-3 text-xs sm:grid-cols-5">
                  <div>
                    <dt className="text-muted-foreground">Passed</dt>
                    <dd className="mt-1 font-medium">{result.passed}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Failed</dt>
                    <dd className="mt-1 font-medium">{result.failed}</dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Avg attempts</dt>
                    <dd className="mt-1 font-medium">
                      {result.avg_attempts}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Avg tokens</dt>
                    <dd className="mt-1 font-medium">
                      {result.avg_tokens.toLocaleString()}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-muted-foreground">Avg time</dt>
                    <dd className="mt-1 font-medium">
                      {result.avg_duration_s}s
                    </dd>
                  </div>
                </dl>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
