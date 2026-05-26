"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Briefing, ConfidenceEntry, GroundingEntry, getBriefing } from "@/lib/api";

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
      {/* Confidence Overview */}
      {result.confidence_scores && result.confidence_scores.length > 0 && (
        <ConfidenceOverview scores={result.confidence_scores} />
      )}

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
        <SectionHeader
          title="Standard of Care"
          confidence={result.confidence_scores?.find(
            (s) =>
              s.section.toLowerCase().includes("standard") ||
              s.section.toLowerCase().includes("diagnosis") ||
              s.section.toLowerCase().includes("first-line")
          )}
        />
        <div className="space-y-4">
          {result.standard_of_care.map((section, i) => (
            <div
              key={i}
              className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900"
            >
              <div className="flex items-start justify-between">
                <h3 className="mb-2 text-lg font-medium text-zinc-900 dark:text-zinc-100">
                  {section.title}
                </h3>
                <SectionConfidenceBadge
                  confidence={result.confidence_scores?.find(
                    (s) =>
                      s.section.toLowerCase() ===
                      section.title.toLowerCase()
                  )}
                />
              </div>
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
        <SectionHeader
          title="Emerging Treatments"
          confidence={result.confidence_scores?.find(
            (s) => s.section.toLowerCase().includes("emerging")
          )}
        />
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
        <SectionHeader
          title="Key Players"
          confidence={result.confidence_scores?.find(
            (s) => s.section.toLowerCase().includes("player")
          )}
        />
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

      {/* Grounding / Source Verification */}
      {result.grounding && result.grounding.length > 0 && (
        <GroundingPanel entries={result.grounding} />
      )}

      {/* Disclaimer */}
      <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-950">
        <p className="text-xs text-amber-800 dark:text-amber-200">
          This briefing is generated for strategic planning purposes only. It
          does not constitute medical advice, treatment recommendations, or
          prescribing guidance. All information should be independently verified
          before use in clinical or business decisions.
        </p>
      </div>
    </div>
  );
}

function ConfidenceOverview({ scores }: { scores: ConfidenceEntry[] }) {
  const total = scores.length;
  const strong = scores.filter((s) => s.level === "strong").length;
  const moderate = scores.filter((s) => s.level === "moderate").length;
  const limited = scores.filter((s) => s.level === "limited").length;

  return (
    <section>
      <h2 className="mb-3 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
        Evidence Confidence
      </h2>
      <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mb-4 flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-green-500" />
            <span className="text-sm text-zinc-600 dark:text-zinc-400">
              Strong ({strong}/{total})
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-yellow-500" />
            <span className="text-sm text-zinc-600 dark:text-zinc-400">
              Moderate ({moderate}/{total})
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="h-3 w-3 rounded-full bg-red-400" />
            <span className="text-sm text-zinc-600 dark:text-zinc-400">
              Limited ({limited}/{total})
            </span>
          </div>
        </div>
        <div className="space-y-2">
          {scores.map((score, i) => (
            <div
              key={i}
              className="flex items-center justify-between rounded border border-zinc-100 px-4 py-2 dark:border-zinc-800"
            >
              <div className="flex items-center gap-3">
                <ConfidenceDot level={score.level} />
                <span className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
                  {score.section}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <span className="text-xs text-zinc-500">
                  {score.source_count} sources
                </span>
                {score.newest_year !== "N/A" && (
                  <span className="text-xs text-zinc-500">
                    {score.oldest_year}–{score.newest_year}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function ConfidenceDot({ level }: { level: string }) {
  const color =
    level === "strong"
      ? "bg-green-500"
      : level === "moderate"
        ? "bg-yellow-500"
        : "bg-red-400";
  return <div className={`h-2.5 w-2.5 rounded-full ${color}`} />;
}

function SectionHeader({
  title,
  confidence,
}: {
  title: string;
  confidence?: ConfidenceEntry;
}) {
  return (
    <div className="mb-3 flex items-center justify-between">
      <h2 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
        {title}
      </h2>
      {confidence && (
        <span className="text-xs text-zinc-500" title={confidence.rationale}>
          {confidence.source_count} sources &middot; {confidence.level}{" "}
          confidence
        </span>
      )}
    </div>
  );
}

function SectionConfidenceBadge({
  confidence,
}: {
  confidence?: ConfidenceEntry;
}) {
  if (!confidence) return null;
  const colors = {
    strong: "bg-green-100 text-green-800",
    moderate: "bg-yellow-100 text-yellow-800",
    limited: "bg-red-100 text-red-800",
  };
  return (
    <span
      className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[confidence.level] || ""}`}
      title={confidence.rationale}
    >
      {confidence.level}
    </span>
  );
}

function GroundingPanel({ entries }: { entries: GroundingEntry[] }) {
  const supported = entries.filter((e) => e.supported).length;
  const total = entries.length;
  const percentage = total > 0 ? Math.round((supported / total) * 100) : 0;

  return (
    <section>
      <h2 className="mb-3 text-2xl font-semibold text-zinc-900 dark:text-zinc-100">
        Source Verification
      </h2>
      <div className="rounded-lg border border-zinc-200 bg-white p-6 dark:border-zinc-800 dark:bg-zinc-900">
        <div className="mb-4 flex items-center gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800">
            <span className="text-lg font-bold text-zinc-800 dark:text-zinc-200">
              {percentage}%
            </span>
          </div>
          <div>
            <p className="text-sm font-medium text-zinc-800 dark:text-zinc-200">
              {supported} of {total} claims verified against sources
            </p>
            <p className="text-xs text-zinc-500">
              Claims traced back to PubMed articles and clinical trial records
            </p>
          </div>
        </div>
        <div className="space-y-2">
          {entries.map((entry, i) => (
            <div
              key={i}
              className="flex items-start gap-3 rounded border border-zinc-100 px-4 py-3 dark:border-zinc-800"
            >
              <div className="mt-0.5 shrink-0">
                {entry.supported ? (
                  <svg
                    className="h-4 w-4 text-green-600"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                ) : (
                  <svg
                    className="h-4 w-4 text-amber-500"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm text-zinc-700 dark:text-zinc-300">
                  {entry.claim}
                </p>
                <div className="mt-1 flex items-center gap-2">
                  <span className="text-xs text-zinc-500">{entry.section}</span>
                  {entry.source_ids.length > 0 && (
                    <span className="text-xs text-blue-600 dark:text-blue-400">
                      {entry.source_ids.join(", ")}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
