"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Briefing, getBriefing } from "@/lib/api";

export default function BriefingDetail() {
  const params = useParams();
  const id = params.id as string;
  const [briefing, setBriefing] = useState<Briefing | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    let active = true;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const data = await getBriefing(id);
        if (!active) return;
        setBriefing(data);
        if (data.status === "pending" || data.status === "processing") {
          timer = setTimeout(poll, 3000);
        }
      } catch (err) {
        if (!active) return;
        setError(err instanceof Error ? err.message : "Failed to load");
      }
    }

    poll();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [id]);

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-red-600">{error}</p>
      </div>
    );
  }

  if (!briefing) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-zinc-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col flex-1 items-center bg-zinc-50 dark:bg-zinc-950 font-sans">
      <main className="w-full max-w-4xl px-6 py-12">
        <a
          href="/"
          className="mb-6 inline-block text-sm text-blue-600 hover:underline"
        >
          &larr; Back to all briefings
        </a>

        <div className="mb-8">
          <h1 className="text-3xl font-bold text-zinc-900 dark:text-zinc-50">
            {briefing.condition}
          </h1>
          <div className="mt-2 flex items-center gap-3">
            <StatusBadge status={briefing.status} />
            <span className="text-sm text-zinc-500">
              Created {new Date(briefing.created_at).toLocaleString()}
            </span>
          </div>
        </div>

        {briefing.status === "pending" || briefing.status === "processing" ? (
          <ProcessingState status={briefing.status} />
        ) : briefing.status === "failed" ? (
          <div className="rounded-lg border border-red-200 bg-red-50 p-6 dark:border-red-800 dark:bg-red-950">
            <p className="font-medium text-red-800 dark:text-red-200">
              Generation failed
            </p>
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">
              {briefing.error}
            </p>
          </div>
        ) : briefing.result ? (
          <BriefingResults result={briefing.result} />
        ) : null}
      </main>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    pending: "bg-yellow-100 text-yellow-800",
    processing: "bg-blue-100 text-blue-800",
    completed: "bg-green-100 text-green-800",
    failed: "bg-red-100 text-red-800",
  };
  return (
    <span
      className={`rounded-full px-3 py-1 text-xs font-medium ${colors[status] || ""}`}
    >
      {status}
    </span>
  );
}

function ProcessingState({ status }: { status: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div className="mb-4 h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
      <p className="text-lg font-medium text-zinc-700 dark:text-zinc-300">
        {status === "pending"
          ? "Queued for processing..."
          : "Researching and analyzing..."}
      </p>
      <p className="mt-1 text-sm text-zinc-500">
        This typically takes 30-60 seconds
      </p>
    </div>
  );
}

function BriefingResults({
  result,
}: {
  result: NonNullable<Briefing["result"]>;
}) {
  return (
    <div className="space-y-10">
      {/* Executive Summary */}
      <section>
        <h2 className="mb-3 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Executive Summary
        </h2>
        <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
          <p className="whitespace-pre-wrap leading-relaxed text-zinc-700 dark:text-zinc-300">
            {result.summary}
          </p>
        </div>
      </section>

      {/* Standard of Care */}
      <section>
        <h2 className="mb-3 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Standard of Care
        </h2>
        <div className="space-y-4">
          {result.standard_of_care.map((section, i) => (
            <div
              key={i}
              className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
            >
              <h3 className="mb-2 text-lg font-medium text-zinc-900 dark:text-zinc-100">
                {section.title}
              </h3>
              <p className="whitespace-pre-wrap leading-relaxed text-zinc-700 dark:text-zinc-300">
                {section.content}
              </p>
              {section.references.length > 0 && (
                <div className="mt-4 border-t border-zinc-100 pt-3 dark:border-zinc-800">
                  <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                    References
                  </p>
                  <ul className="mt-1 space-y-1">
                    {section.references.map((ref, j) => (
                      <li
                        key={j}
                        className="text-sm text-zinc-500 dark:text-zinc-400"
                      >
                        {ref}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Emerging Treatments */}
      <section>
        <h2 className="mb-3 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Emerging Treatments
        </h2>
        <div className="space-y-4">
          {result.emerging_treatments.map((treatment, i) => (
            <div
              key={i}
              className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
            >
              <div className="flex items-start justify-between">
                <h3 className="text-lg font-medium text-zinc-900 dark:text-zinc-100">
                  {treatment.name}
                </h3>
                <span className="rounded-full bg-purple-100 px-3 py-1 text-xs font-medium text-purple-800">
                  {treatment.phase}
                </span>
              </div>
              <p className="mt-1 text-sm font-medium text-zinc-500">
                {treatment.company}
              </p>
              <p className="mt-2 text-sm text-zinc-600 dark:text-zinc-400">
                <span className="font-medium">Mechanism:</span>{" "}
                {treatment.mechanism}
              </p>
              <p className="mt-2 leading-relaxed text-zinc-700 dark:text-zinc-300">
                {treatment.description}
              </p>
              {treatment.trial_id && (
                <p className="mt-2 text-sm text-zinc-500">
                  Trial: {treatment.trial_id}
                </p>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Key Players */}
      <section>
        <h2 className="mb-3 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
          Key Players
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          {result.key_players.map((player, i) => (
            <div
              key={i}
              className="rounded-lg border border-zinc-200 bg-white p-5 dark:border-zinc-800 dark:bg-zinc-900"
            >
              <div className="flex items-center gap-2">
                <h3 className="font-medium text-zinc-900 dark:text-zinc-100">
                  {player.name}
                </h3>
                <span className="rounded bg-zinc-100 px-2 py-0.5 text-xs text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400">
                  {player.type}
                </span>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-zinc-600 dark:text-zinc-400">
                {player.role}
              </p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
