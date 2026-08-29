import Link from "next/link";
import { TaskForm } from "@/components/TaskForm";
import { buttonVariants } from "@/components/ui/button";

export default function NewTaskPage() {
  return (
    <main className="mx-auto min-h-screen max-w-3xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col gap-4 border-b pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-medium text-cyan-300">New run</p>
          <h1 className="text-3xl font-semibold tracking-normal">Create Task</h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Point the agent at a repository and describe the exact behavior to
            fix.
          </p>
        </div>
        <Link href="/" className={buttonVariants({ variant: "ghost" })}>
          Back
        </Link>
      </div>
      <TaskForm />
    </main>
  );
}
