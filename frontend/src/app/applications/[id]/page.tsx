import { notFound } from "next/navigation";
import { connection } from "next/server";
import { getApplication, getJob } from "@/lib/data";
import type { ApplicationStatus } from "@/lib/types";

const statusCopy: Record<ApplicationStatus, string> = {
  interviewing: "Interview in progress",
  accepted: "Moving forward",
  rejected: "Not moving forward",
};

// Reads the JSON store per request, so it must not be prerendered at build time
export const instant = false;

export default async function ApplicationPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  await connection();
  const { id } = await params;
  const application = await getApplication(id);
  if (!application) notFound();

  const job = await getJob(application.jobId);
  const evaluation = application.evaluation;

  return (
    <div className="space-y-8">
      <div>
        <p className="text-sm text-black/60 dark:text-white/60">{job?.title}</p>
        <h1 className="text-3xl font-semibold">Thanks, {application.name}</h1>
        <p className="mt-2">
          Status: <span className="font-medium">{statusCopy[application.status]}</span>
        </p>
      </div>

      {application.mode === "web" && application.roomUrl && application.status === "interviewing" && (
        <iframe
          src={application.roomUrl}
          title="Video interview"
          allow="camera; microphone; fullscreen; display-capture; autoplay"
          className="h-[70vh] w-full rounded-lg border border-black/10 dark:border-white/10"
        />
      )}

      {application.mode === "phone" && application.status === "interviewing" && (
        <p className="text-black/70 dark:text-white/70">
          We are calling {application.phone}. Answer the call to begin your interview.
        </p>
      )}

      {evaluation && (
        <section className="space-y-3 rounded-lg border border-black/10 p-4 dark:border-white/10">
          <h2 className="text-xl font-semibold">Interview summary</h2>
          <p>{evaluation.summary}</p>
          <p className="text-sm">
            Overall score: <span className="font-medium">{evaluation.overall_score}/10</span>
          </p>
        </section>
      )}
    </div>
  );
}
