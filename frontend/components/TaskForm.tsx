"use client";

import { useId, useState } from "react";
import { useRouter } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

export function TaskForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const repoInputId = useId();
  const taskInputId = useId();

  const [repoUrl, setRepoUrl] = useState("");
  const [taskText, setTaskText] = useState("");
  const [error, setError] = useState<string | null>(null);

  const mutation = useMutation({
    mutationFn: api.tasks.create,
    onSuccess: (task) => {
      queryClient.invalidateQueries({ queryKey: ["tasks"] });
      router.push(`/tasks/${task.id}`);
    },
    onError: (err: Error) => {
      setError(err.message ?? "Failed to create task");
    },
  });

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (!repoUrl.trim() || !taskText.trim()) {
      setError("Both repository URL and task are required.");
      return;
    }

    mutation.mutate({ repo_url: repoUrl.trim(), task_text: taskText.trim() });
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-xl">Task details</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor={repoInputId} className="text-sm font-medium">
              Repository URL
            </label>
            <input
              id={repoInputId}
              type="url"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
              className="flex min-h-11 w-full rounded-md border border-input bg-background px-3 py-2 text-sm leading-6 placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor={taskInputId} className="text-sm font-medium">
              Task
            </label>
            <textarea
              id={taskInputId}
              value={taskText}
              onChange={(e) => setTaskText(e.target.value)}
              placeholder="Fix the add function so all tests pass..."
              rows={7}
              className="flex w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm leading-6 placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            />
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <div className="flex flex-col-reverse gap-3 sm:flex-row">
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Create Task
                </>
              )}
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => router.push("/")}
            >
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
