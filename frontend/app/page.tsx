"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Briefing, createBriefing, listBriefings } from "@/lib/api";

export default function Home() {
  const [condition, setCondition] = useState("");
  const [briefings, setBriefings] = useState<Briefing[]>([]);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  useEffect(() => {
    listBriefings().then(setBriefings).catch(console.error);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!condition.trim()) return;
    setLoading(true);
    try {
      const briefing = await createBriefing(condition.trim());
      router.push(`/briefings/${briefing.id}`);
    } catch (err) {
      console.error(err);
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
              onChange={(e) => setCondition(e.target.value)}
              placeholder="Enter a medical condition (e.g., Type 2 Diabetes)"
              className="flex-1 rounded-lg border border-zinc-300 bg-white px-4 py-3 text-zinc-900 placeholder-zinc-400 focus:border-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500/20 dark:border-zinc-700 dark:bg-zinc-900 dark:text-zinc-100 dark:placeholder-zinc-500"
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
