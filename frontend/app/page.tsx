import Link from "next/link";
import { Dashboard } from "@/components/Dashboard";
import { TaskList } from "@/components/TaskList";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export default function Home() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_left,hsl(199_89%_22%/.24),transparent_36rem)]">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8 flex flex-col gap-5 border-b pb-6 sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <p className="mb-2 text-sm font-medium text-cyan-300">
              Agent operations
            </p>
            <h1 className="text-3xl font-semibold tracking-normal text-foreground sm:text-4xl">
              Coding Agent
            </h1>
            <p className="mt-3 max-w-xl text-sm leading-6 text-muted-foreground">
              Submit a repository task, watch the agent work through fixes, and
              compare runs from one dashboard.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href="/evals"
              className={cn(buttonVariants({ variant: "outline" }), "min-w-24")}
            >
              Evals
            </Link>
            <Link href="/tasks/new" className={buttonVariants()}>
              New Task
            </Link>
          </div>
        </header>

        <div className="grid gap-8 lg:grid-cols-[minmax(0,1.15fr)_minmax(20rem,.85fr)]">
          <section>
            <h2 className="mb-4 text-base font-semibold">Tasks</h2>
            <TaskList />
          </section>

          <section>
            <h2 className="mb-4 text-base font-semibold">Run Overview</h2>
            <Dashboard />
          </section>
        </div>
      </div>
    </main>
  );
}
