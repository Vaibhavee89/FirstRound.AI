import { getApplications, saveApplications } from "@/lib/data";
import type { Evaluation } from "@/lib/types";

// Called by the agent (bot.py update_application_status) once a phone interview is evaluated
type StatusUpdate = {
  status: "accepted" | "rejected";
  evaluation: Evaluation;
  interviewedAt: string;
};

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ callSid: string }> },
) {
  const { callSid } = await params;
  const update = (await request.json()) as StatusUpdate;

  const applications = await getApplications();
  const index = applications.findIndex((app) => app.callSid === callSid);
  if (index === -1) {
    return Response.json({ error: "Application not found." }, { status: 404 });
  }

  applications[index] = {
    ...applications[index],
    status: update.status,
    evaluation: update.evaluation,
    interviewedAt: update.interviewedAt,
  };
  await saveApplications(applications);
  return Response.json(applications[index]);
}
