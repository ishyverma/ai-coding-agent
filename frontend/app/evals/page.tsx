import Link from "next/link";
import { EvalDashboard } from "@/components/EvalDashboard";
import { buttonVariants } from "@/components/ui/button";

export default function EvalsPage() {
  return (
    <main className="mx-auto min-h-screen max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col gap-4 border-b pb-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="mb-2 text-sm font-medium text-cyan-300">Benchmark</p>
          <h1 className="text-3xl font-semibold tracking-normal">Evals</h1>
          <p className="mt-2 text-sm leading-6 text-muted-foreground">
            Track pass rate, attempts, tokens, and runtime across the fixture
            repositories.
          </p>
        </div>
        <Link href="/" className={buttonVariants({ variant: "ghost" })}>
          Back
        </Link>
      </div>
      <EvalDashboard />
    </main>
  );
}
