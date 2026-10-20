import { getApplications, getJob, saveApplications } from "@/lib/data";
import { startPhoneInterview, startWebInterview } from "@/lib/agent";
import type { Application, InterviewMode } from "@/lib/types";

type ApplyBody = {
  jobId?: string;
  name?: string;
  email?: string;
  phone?: string;
  resume?: string;
  mode?: InterviewMode;
};

export async function POST(request: Request) {
  const body = (await request.json()) as ApplyBody;
  const { jobId, name, email, phone, resume, mode } = body;

  if (!jobId || !name?.trim() || !email?.includes("@") || !resume?.trim()) {
    return Response.json({ error: "Name, email, and resume are required." }, { status: 400 });
  }
  if (mode !== "web" && mode !== "phone") {
    return Response.json({ error: "Choose a web or phone interview." }, { status: 400 });
  }
  if (mode === "phone" && !phone?.startsWith("+")) {
    return Response.json({ error: "Phone numbers must include a country code, e.g. +14155550123." }, { status: 400 });
  }

  const job = await getJob(jobId);
  if (!job) {
    return Response.json({ error: "Job not found." }, { status: 404 });
  }

  // Start the interview before saving, so a failed agent call never leaves a stuck record
  let roomUrl: string | undefined;
  let callSid: string | undefined;
  try {
    if (mode === "web") {
      ({ room_url: roomUrl } = await startWebInterview(job.description, resume));
    } else {
      ({ call_sid: callSid } = await startPhoneInterview(job.description, resume, phone!));
    }
  } catch (err) {
    console.error("Failed to start interview:", err);
    return Response.json(
      { error: "Could not start the interview. Check that the agent is running." },
      { status: 502 },
    );
  }

  const application: Application = {
    id: crypto.randomUUID(),
    jobId,
    name: name.trim(),
    email: email.trim(),
    phone: mode === "phone" ? phone : undefined,
    resume: resume.trim(),
    mode,
    status: "interviewing",
    roomUrl,
    callSid,
    appliedAt: new Date().toISOString(),
  };

  await saveApplications([...(await getApplications()), application]);
  return Response.json(application, { status: 201 });
}
