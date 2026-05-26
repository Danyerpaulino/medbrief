"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Briefing, createBriefing, listBriefings } from "@/lib/api";

export default function Home() {
  const [condition, setCondition] = useState("");
  const [briefings, setBriefings] = useState<Briefing[]>([]);
  const [loading, setLoading] = useState(false);
  const [validationError, setValidationError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    listBriefings().then(setBriefings).catch(console.error);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!condition.trim()) return;
    setLoading(true);
    setValidationError(null);
    try {
      const briefing = await createBriefing(condition.trim());
      router.push(`/briefings/${briefing.id}`);
    } catch (err) {
      setValidationError(
        err instanceof Error ? err.message : "Failed to create briefing"
      );
      setLoading(false);
    }
  }

  const statusColor: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    processing: "bg-blue-100 text-blue-800",
    completed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
  };

  return (
    <div className="flex flex-col flex-1 items-center bg-zinc-50 dark:bg-zinc-950 font-sans">
      <main className="w-full max-w-4xl px-6 py-16">
        <div className="mb-12">
          <h1 className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50">
            MedBrief
          </h1>
          <p className="mt-2 text-lg text-zinc-600 dark:text-zinc-400">
            Generate structured medical condition briefings for strategic
            decision-making.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mb-12">
          <div className="flex gap-3">
            <input
              type="text"
              value={condition}
              onChange={(e) => {
                setCondition(e.target.value);
                if (validationError) setValidationError(null);
              }}
              placeholder="Enter a medical condition (e.g., Type 2 Diabetes)"
              className={`flex-1 rounded-lg border bg-white px-4 py-3 text-zinc-900 placeholder-zinc-400 focus:outline-none focus:ring-2 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder-zinc-500 ${
                validationError
                  ? "border-red-400 focus:border-red-500 focus:ring-red-500/20"
                  : "border-zinc-300 focus:border-blue-500 focus:ring-blue-500/20 dark:border-zinc-700"
              }`}
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !condition.trim()}
              className="rounded-lg bg-blue-600 px-6 py-3 font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Creating..." : "Generate Briefing"}
            </button>
          </div>
          {validationError && (
            <div className="mt-3 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-800 dark:bg-red-950">
              <svg
                className="mt-0.5 h-4 w-4 shrink-0 text-red-600 dark:text-red-400"
                fill="currentColor"
                viewBox="0 0 20 20"
              >
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="text-sm text-red-700 dark:text-red-300">
                {validationError}
              </p>
            </div>
          )}
        </form>

        {briefings.length > 0 && (
          <section>
            <h2 className="mb-4 text-xl font-semibold text-zinc-900 dark:text-zinc-100">
              Recent Briefings
            </h2>
            <div className="space-y-3">
              {briefings.map((b) => (
                <a
                  key={b.id}
                  href={`/briefings/${b.id}`}
                  className="flex items-center justify-between rounded-lg border border-zinc-200 bg-white p-4 transition-shadow hover:shadow-md dark:border-zinc-800 dark:bg-zinc-900"
                >
                  <div>
                    <p className="font-medium text-zinc-900 dark:text-zinc-100">
                      {b.condition}
                    </p>
                    <p className="text-sm text-zinc-500">
                      {new Date(b.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-medium ${statusColor[b.status] || ""}`}
                  >
                    {b.status}
                  </span>
                </a>
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}
