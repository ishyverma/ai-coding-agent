"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import { TaskStatusBadge } from "@/components/StatusBadge";
import type { Task } from "@/types/api";

export function TaskList() {
  const { data: tasks, isLoading } = useQuery({
    queryKey: ["tasks"],
    queryFn: api.tasks.list,
    refetchInterval: 5000,
  });

  if (isLoading) {
    return (
      <Card>
        <CardContent className="p-5 text-sm text-muted-foreground">
          Loading tasks...
        </CardContent>
      </Card>
    );
  }

  if (!tasks?.length) {
    return (
      <Card>
        <CardContent className="p-5">
          <p className="text-sm font-medium">No tasks yet</p>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">
            Create a task to start the first agent run.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-3">
      {tasks.map((task: Task) => (
        <Link key={task.id} href={`/tasks/${task.id}`} className="block">
          <Card className="transition-colors hover:border-cyan-500/70 hover:bg-cyan-950/10">
            <CardContent className="p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <p className="break-words text-sm font-medium leading-6">
                    {task.task_text}
                  </p>
                  <p className="mt-2 break-all text-xs leading-5 text-muted-foreground">
                    {task.repo_url}
                  </p>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-2">
                  <TaskStatusBadge status={task.status} />
                  <ArrowUpRight className="h-4 w-4 text-muted-foreground" />
                </div>
              </div>
              <p className="mt-3 text-xs text-muted-foreground">
                Created {new Date(task.created_at).toLocaleString()}
              </p>
            </CardContent>
          </Card>
        </Link>
      ))}
    </div>
  );
}
