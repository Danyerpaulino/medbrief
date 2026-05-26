const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface Section {
  title: string;
  content: string;
  references: string[];
}

export interface Treatment {
  name: string;
  phase: string;
  company: string;
  mechanism: string;
  description: string;
  trial_id: string | null;
}

export interface Player {
  name: string;
  type: string;
  role: string;
}

export interface GroundingEntry {
  section: string;
  claim: string;
  supported: boolean;
  source_ids: string[];
}

export interface ConfidenceEntry {
  section: string;
  level: "strong" | "moderate" | "limited";
  source_count: number;
  newest_year: string;
  oldest_year: string;
  rationale: string;
}

export interface BriefingResult {
  standard_of_care: Section[];
  emerging_treatments: Treatment[];
  key_players: Player[];
  summary: string;
  grounding: GroundingEntry[];
  confidence_scores: ConfidenceEntry[];
}

export interface Briefing {
  id: string;
  condition: string;
  status: "pending" | "processing" | "completed" | "failed";
  result: BriefingResult | null;
  error: string | null;
  created_at: string;
  completed_at: string | null;
}

export async function createBriefing(condition: string): Promise<Briefing> {
  const res = await fetch(`${API_URL}/api/briefings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ condition }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    const detail = body?.detail || "Failed to create briefing";
    throw new Error(detail);
  }
  return res.json();
}

export async function getBriefing(id: string): Promise<Briefing> {
  const res = await fetch(`${API_URL}/api/briefings/${id}`);
  if (!res.ok) throw new Error("Failed to fetch briefing");
  return res.json();
}

export async function listBriefings(): Promise<Briefing[]> {
  const res = await fetch(`${API_URL}/api/briefings`);
  if (!res.ok) throw new Error("Failed to fetch briefings");
  return res.json();
}

export async function deleteBriefing(id: string): Promise<void> {
  const res = await fetch(`${API_URL}/api/briefings/${id}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete briefing");
}
