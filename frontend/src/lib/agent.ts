import type { InterviewLog } from "./types";

// Server-side only, so the agent needs no CORS setup. AGENT_URL is used in Docker/Render;
// NEXT_PUBLIC_AGENT_URL matches the variable name in .env.example.
const AGENT_URL =
  process.env.AGENT_URL ??
  process.env.NEXT_PUBLIC_AGENT_URL ??
  "http://localhost:7860";

async function postToAgent<T>(endpoint: string, body: unknown): Promise<T> {
  const res = await fetch(`${AGENT_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Agent ${endpoint} responded with ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function startWebInterview(jd: string, resume: string) {
  return postToAgent<{ room_url: string }>("/start-interview", { jd, resume });
}

export async function startPhoneInterview(
  jd: string,
  resume: string,
  phoneNumber: string,
) {
  return postToAgent<{ call_sid: string; status: string }>(
    "/start-phone-interview",
    { jd, resume, phone_number: phoneNumber },
  );
}

export async function getInterviewLogs(): Promise<InterviewLog[]> {
  try {
    const res = await fetch(`${AGENT_URL}/logs`, { cache: "no-store" });
    return res.ok ? ((await res.json()) as InterviewLog[]) : [];
  } catch {
    // The recruiter view should still load when the agent is offline
    return [];
  }
}
