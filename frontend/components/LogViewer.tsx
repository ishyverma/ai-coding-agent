"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import { ChevronDown, ChevronRight, ChevronUp, Copy, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { PrismLight as SyntaxHighlighter } from "react-syntax-highlighter";
import javascript from "react-syntax-highlighter/dist/esm/languages/prism/javascript";
import python from "react-syntax-highlighter/dist/esm/languages/prism/python";
import bash from "react-syntax-highlighter/dist/esm/languages/prism/bash";
import go from "react-syntax-highlighter/dist/esm/languages/prism/go";
import rust from "react-syntax-highlighter/dist/esm/languages/prism/rust";
import tsx from "react-syntax-highlighter/dist/esm/languages/prism/tsx";
import { atomDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Badge } from "@/components/ui/badge";
import { useRunStream } from "@/lib/useRunStream";
import type { RunLog } from "@/types/api";

SyntaxHighlighter.registerLanguage("javascript", javascript);
SyntaxHighlighter.registerLanguage("jsx", javascript);
SyntaxHighlighter.registerLanguage("python", python);
SyntaxHighlighter.registerLanguage("py", python);
SyntaxHighlighter.registerLanguage("bash", bash);
SyntaxHighlighter.registerLanguage("sh", bash);
SyntaxHighlighter.registerLanguage("go", go);
SyntaxHighlighter.registerLanguage("rust", rust);
SyntaxHighlighter.registerLanguage("tsx", tsx);
SyntaxHighlighter.registerLanguage("ts", tsx);

const STEP_COLORS: Record<string, string> = {
  setup: "bg-zinc-600",
  inspect: "bg-sky-600",
  analyze: "bg-blue-600",
  modify: "bg-purple-600",
  run_tests: "bg-yellow-600",
  recovery: "bg-orange-600",
  done: "bg-green-600",
  error: "bg-red-600",
};

const LONG_MESSAGE_THRESHOLD = 300;

function CopyButton({ code, inline }: { code: string; inline?: boolean }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      const textarea = document.createElement("textarea");
      textarea.value = code;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [code]);

  return (
    <button
      type="button"
      onClick={handleCopy}
      className={`flex items-center gap-1 rounded-md bg-zinc-800 px-2 py-1 text-xs text-zinc-400 hover:bg-zinc-700 hover:text-zinc-200${inline ? "" : " absolute top-2 right-2"}`}
      title="Copy code"
    >
      {copied ? (
        <>
          <Check className="h-3 w-3" />
          Copied
        </>
      ) : (
        <>
          <Copy className="h-3 w-3" />
          Copy
        </>
      )}
    </button>
  );
}

function CodeBlock({ language, children }: { language?: string; children: string }) {
  const lang = language || "text";
  return (
    <div className="relative my-2 rounded-lg border border-zinc-800">
      <CopyButton code={children} />
      <SyntaxHighlighter
        language={lang}
        style={atomDark}
        customStyle={{
          margin: 0,
          borderRadius: "0.5rem",
          fontSize: "0.8rem",
          lineHeight: "1.5",
          paddingTop: "2rem",
        }}
        showLineNumbers={children.split("\n").length > 5}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  );
}

function LogMessage({ log }: { log: RunLog }) {
  const [expanded, setExpanded] = useState(false);
  const isLong = log.message.length > LONG_MESSAGE_THRESHOLD;

  if (log.step === "analyze" || log.step === "modify") {
    return (
      <div className="space-y-2">
        {isLong && !expanded ? (
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300"
          >
            <ChevronDown className="h-3 w-3" />
            Show full message
          </button>
        ) : null}
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: (props) => <h1 className="text-sm font-bold" {...props} />,
            h2: (props) => <h2 className="text-sm font-bold" {...props} />,
            h3: (props) => <h3 className="text-sm font-bold" {...props} />,
            p: (props) => <p className="my-1" {...props} />,
            ul: (props) => (
              <ul className="my-1 list-disc pl-4" {...props} />
            ),
            ol: (props) => (
              <ol className="my-1 list-decimal pl-4" {...props} />
            ),
            li: (props) => <li className="my-0.5" {...props} />,
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            code: (props: { node?: unknown; inline?: boolean; className?: string; children?: React.ReactNode }) => {
                  const { inline, className, children } = props;
                  const match = /language-(\w+)/.exec(className || "");
                  const lang = match?.[1] || "";
                  const text = String(children).replace(/\n$/, "");
                  if (inline) {
                    return (
                      <code className="rounded bg-zinc-800/70 px-1 py-0.5 font-mono text-[0.8em]">
                        {children}
                      </code>
                    );
                  }
                  return <CodeBlock language={lang}>{text}</CodeBlock>;
                },
            pre: () => null,
            a: (props) => (
              <a
                className="text-sky-400 underline"
                target="_blank"
                rel="noreferrer"
                {...props}
              />
            ),
            table: (props) => (
              <table
                className="my-2 w-full border-collapse text-xs"
                {...props}
              />
            ),
            th: (props) => (
              <th className="border border-zinc-700 px-2 py-1" {...props} />
            ),
            td: (props) => (
              <td className="border border-zinc-700 px-2 py-1" {...props} />
            ),
          }}
        >
          {expanded ? log.message : `${log.message.slice(0, LONG_MESSAGE_THRESHOLD)}…`}
        </ReactMarkdown>
        {isLong && expanded && (
          <button
            type="button"
            onClick={() => setExpanded(false)}
            className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-400"
          >
            <ChevronUp className="h-3 w-3" />
            Show less
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {isLong && !expanded ? (
        <>
          <span className="whitespace-pre-wrap text-xs leading-relaxed break-words text-zinc-200">
            {log.message.slice(0, LONG_MESSAGE_THRESHOLD)}…
          </span>
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="flex items-center gap-1 text-xs text-sky-400 hover:text-sky-300"
          >
            <ChevronDown className="h-3 w-3" />
            Show more
          </button>
        </>
      ) : (
        <>
          <span className="whitespace-pre-wrap text-xs leading-relaxed break-words text-zinc-200">
            {log.message}
          </span>
          {isLong && (
            <button
              type="button"
              onClick={() => setExpanded(false)}
              className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-400"
            >
              <ChevronUp className="h-3 w-3" />
              Show less
            </button>
          )}
        </>
      )}
    </div>
  );
}

function parseDiffString(
  diff: string,
): Array<{ type: "file"; path: string; language: string; content: string } | { type: "diff"; content: string }> {
  const results: Array<{
    type: "file";
    path: string;
    language: string;
    content: string;
  } | { type: "diff"; content: string }> = [];

  const fileRegex = /### `([^`]+)`\n\n```(\w+)\n([\s\S]*?)```\n*/g;
  let match;
  while ((match = fileRegex.exec(diff)) !== null) {
    results.push({
      type: "file",
      path: match[1],
      language: match[2],
      content: match[3].replace(/\n+$/, ""),
    });
  }

  const diffRegex = /### Diff\n\n```diff\n([\s\S]*?)```\n*/g;
  while ((match = diffRegex.exec(diff)) !== null) {
    results.push({ type: "diff", content: match[1].replace(/\n+$/, "") });
  }

  if (results.length === 0) {
    results.push({ type: "diff", content: diff.trimEnd() });
  }

  return results;
}

function DiffBlock({ diff }: { diff: string }) {
  const [open, setOpen] = useState(true);
  const sections = parseDiffString(diff);

  return (
    <div className="mt-2 overflow-hidden rounded border border-zinc-800">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between bg-zinc-900 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800"
      >
        <span className="inline-flex items-center gap-1">
          {open ? (
            <ChevronDown className="h-3.5 w-3.5" />
          ) : (
            <ChevronRight className="h-3.5 w-3.5" />
          )}
          {open ? "Hide code changes" : "Show code changes"}
        </span>
      </button>
      {open && (
        <div className="max-h-96 overflow-auto">
          {sections.map((section, i) => (
            <div key={i}>
              <div className="flex items-center justify-between bg-zinc-800/80 px-3 py-1.5">
                <span className="truncate text-xs font-semibold text-zinc-200">
                  {section.type === "file" ? section.path : "Diff"}
                </span>
                <CopyButton inline code={section.content} />
              </div>
              <SyntaxHighlighter
                language={section.type === "file" ? section.language : "diff"}
                style={atomDark}
                customStyle={{
                  margin: 0,
                  fontSize: "0.8rem",
                  lineHeight: "1.5",
                  paddingTop: "0.75rem",
                  borderRadius: i === sections.length - 1 ? "0 0 0.5rem 0.5rem" : undefined,
                }}
                showLineNumbers={section.content.split("\n").length > 5}
              >
                {section.content}
              </SyntaxHighlighter>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export function LogViewer({ runId }: { runId: number | null }) {
  const { logs, finalStatus, isConnected, error } = useRunStream(runId);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  if (!runId) {
    return (
      <p className="text-sm text-muted-foreground">
        No run started yet. Trigger a run to see live logs here.
      </p>
    );
  }

  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-950 p-4 font-mono text-sm">
      <div className="mb-3 flex items-center justify-between border-b border-zinc-800 pb-3">
        <span className="text-xs text-zinc-500">
          {error
            ? "connection error"
            : finalStatus
              ? "finished"
              : isConnected
                ? "● streaming live"
                : "○ connecting..."}
        </span>
        {finalStatus && (
          <Badge
            variant={finalStatus === "passed" ? "success" : "destructive"}
          >
            {finalStatus}
          </Badge>
        )}
      </div>

      <div className="space-y-4 overflow-y-auto pb-2" style={{ maxHeight: "80vh" }}>
        {logs.length === 0 && (
          <p className="text-xs text-zinc-600">
            Waiting for the agent to start...
          </p>
        )}
        {logs.map((log) => (
          <div key={log.id} className="flex items-start gap-3">
            <span className="w-16 shrink-0 pt-0.5 text-xs text-zinc-600">
              {new Date(log.created_at).toLocaleTimeString()}
            </span>
            <div className="min-w-0 flex-1">
              <div className="flex items-start gap-2">
                <span
                  className={`shrink-0 rounded px-1.5 py-0.5 text-xs text-white ${
                    STEP_COLORS[log.step] ?? "bg-zinc-700"
                  }`}
                >
                  {log.step}
                </span>
                <LogMessage log={log} />
              </div>
              {log.diff && <DiffBlock diff={log.diff} />}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}