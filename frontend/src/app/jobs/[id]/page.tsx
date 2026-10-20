import { notFound } from "next/navigation";
import { connection } from "next/server";
import { getJob } from "@/lib/data";
import { ApplyForm } from "./apply-form";

// Reads the JSON store per request, so it must not be prerendered at build time
export const instant = false;

export default async function JobPage({ params }: { params: Promise<{ id: string }> }) {
  await connection();
  const { id } = await params;
  const job = await getJob(id);
  if (!job) notFound();

  return (
    <div className="grid gap-10 md:grid-cols-[1fr_1fr]">
      <section className="space-y-4">
        <div>
          <p className="text-sm text-black/60 dark:text-white/60">{job.location}</p>
          <h1 className="text-3xl font-semibold">{job.title}</h1>
        </div>
        <p className="leading-relaxed">{job.description}</p>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Apply</h2>
        <ApplyForm jobId={job.id} />
      </section>
    </div>
  );
}
