"use client";

import { useEffect, useState } from "react";

const LANGUAGES = ["python", "typescript", "javascript"] as const;
type Language = (typeof LANGUAGES)[number];

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ExecuteResult {
  success: boolean;
  output: string | null;
  error: string | null;
  exit_code: number;
}

export default function Home() {
  const [task, setTask] = useState("");
  const [language, setLanguage] = useState<Language>("python");
  const [code, setCode] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const [executeResult, setExecuteResult] = useState<ExecuteResult | null>(null);
  const [executeLoading, setExecuteLoading] = useState(false);
  const [executeError, setExecuteError] = useState("");
  const [executionTime, setExecutionTime] = useState<number | null>(null);

  async function generate() {
    if (!task.trim() || loading) return;
    setLoading(true);
    setError("");
    setCode("");
    setExecuteResult(null);
    setExecuteError("");
    setExecutionTime(null);

    try {
      const res = await fetch(`${API_URL}/api/v1/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, language }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Server error ${res.status}`);
      }

      const data = await res.json();
      setCode(data.code);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }

  async function handleExecute() {
    if (!code || executeLoading) return;
    setExecuteLoading(true);
    setExecuteError("");
    setExecuteResult(null);
    setExecutionTime(null);

    const start = Date.now();
    try {
      const res = await fetch(`${API_URL}/api/v1/execute`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code, language: "python" }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? `Server error ${res.status}`);
      }

      const data: ExecuteResult = await res.json();
      setExecuteResult(data);
      setExecutionTime(Date.now() - start);
    } catch (err) {
      setExecuteError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setExecuteLoading(false);
    }
  }

  async function copyCode() {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Enter" && (e.metaKey || e.ctrlKey) && e.shiftKey && code) {
        e.preventDefault();
        handleExecute();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [code, executeLoading]);

  return (
    <main className="max-w-3xl mx-auto px-4 py-16">
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-5xl font-bold tracking-tight mb-3">
          Code<span className="text-blue-400">Agent</span>
        </h1>
        <p className="text-gray-400 text-lg">
          Describe what you want to build — get working code instantly
        </p>
      </div>

      {/* Input area */}
      <div className="space-y-3">
        <textarea
          className="w-full h-40 bg-gray-900 border border-gray-700 rounded-xl p-4 text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500 resize-none transition-colors font-mono text-sm"
          placeholder="e.g. Write a function that reverses a linked list in Python..."
          value={task}
          onChange={(e) => setTask(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) generate();
          }}
        />

        <div className="flex gap-3">
          <select
            className="bg-gray-900 border border-gray-700 rounded-lg px-4 py-2.5 text-gray-200 focus:outline-none focus:border-blue-500 transition-colors cursor-pointer"
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
          >
            {LANGUAGES.map((l) => (
              <option key={l} value={l}>
                {l.charAt(0).toUpperCase() + l.slice(1)}
              </option>
            ))}
          </select>

          <button
            onClick={generate}
            disabled={loading || !task.trim()}
            className="flex-1 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed rounded-lg px-6 py-2.5 font-semibold transition-colors"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <span className="inline-block w-4 h-4 border-2 border-blue-300 border-t-transparent rounded-full animate-spin" />
                Generating...
              </span>
            ) : (
              "Generate  ⌘↵"
            )}
          </button>
        </div>
      </div>

      {/* Generate error */}
      {error && (
        <div className="mt-4 bg-red-950/60 border border-red-800 rounded-xl p-4 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Generated code */}
      {code && (
        <div className="mt-6">
          <div className="flex items-center justify-between mb-2 px-1">
            <span className="text-xs text-gray-500 font-mono">{language}</span>
            <button
              onClick={copyCode}
              className="text-xs text-gray-400 hover:text-gray-200 bg-gray-800 hover:bg-gray-700 px-3 py-1 rounded-md transition-colors"
            >
              {copied ? "Copied!" : "Copy"}
            </button>
          </div>
          <pre className="bg-gray-900 border border-gray-700 rounded-xl p-5 overflow-x-auto text-sm text-gray-100 font-mono leading-relaxed">
            <code>{code}</code>
          </pre>

          {/* Execute button */}
          <div className="mt-3 flex justify-end">
            <button
              onClick={handleExecute}
              disabled={executeLoading || !code}
              className="bg-green-700 hover:bg-green-600 disabled:bg-gray-800 disabled:text-gray-600 disabled:cursor-not-allowed rounded-lg px-6 py-2.5 font-semibold transition-colors text-sm"
            >
              {executeLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="inline-block w-4 h-4 border-2 border-green-300 border-t-transparent rounded-full animate-spin" />
                  Executing...
                </span>
              ) : (
                "Execute Code  ⌘⇧↵"
              )}
            </button>
          </div>
        </div>
      )}

      {/* Execute error */}
      {executeError && (
        <div className="mt-4 bg-red-950/60 border border-red-800 rounded-xl p-4 text-red-300 text-sm">
          {executeError}
        </div>
      )}

      {/* Execution output panel */}
      {executeResult && (
        <div className="mt-4">
          <div className="flex items-center justify-between mb-2 px-1">
            <div className="flex items-center gap-2">
              <span
                className={`inline-block w-2 h-2 rounded-full ${
                  executeResult.success ? "bg-green-400" : "bg-red-400"
                }`}
              />
              <span
                className={`text-xs font-semibold ${
                  executeResult.success ? "text-green-400" : "text-red-400"
                }`}
              >
                {executeResult.success
                  ? "Success"
                  : `Failed (exit ${executeResult.exit_code})`}
              </span>
            </div>
            {executionTime !== null && (
              <span className="text-xs text-gray-500 font-mono">{executionTime}ms</span>
            )}
          </div>
          <div className="bg-gray-900 border border-gray-700 rounded-xl p-5 font-mono text-sm leading-relaxed space-y-3">
            {executeResult.output && (
              <div>
                <span className="text-xs text-gray-500 block mb-1">stdout</span>
                <pre className="text-gray-100 whitespace-pre-wrap">{executeResult.output}</pre>
              </div>
            )}
            {executeResult.error && (
              <div>
                <span className="text-xs text-gray-500 block mb-1">stderr</span>
                <pre className="text-red-300 whitespace-pre-wrap">{executeResult.error}</pre>
              </div>
            )}
            {!executeResult.output && !executeResult.error && (
              <span className="text-gray-500">(no output)</span>
            )}
          </div>
        </div>
      )}
    </main>
  );
}
