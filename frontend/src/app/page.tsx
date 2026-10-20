import Link from "next/link";
import { connection } from "next/server";
import { getJobs } from "@/lib/data";

// Reads the JSON store per request, so it must not be prerendered at build time
export const instant = false;

export default async function JobsPage() {
  await connection();
  const jobs = await getJobs();

  return (
    <section className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Open roles</h1>
        <p className="mt-2 text-black/60 dark:text-white/60">
          Apply and complete a short AI-led interview on the web or by phone.
        </p>
      </div>

      <ul className="divide-y divide-black/10 dark:divide-white/10 rounded-lg border border-black/10 dark:border-white/10">
        {jobs.map((job) => (
          <li key={job.id}>
            <Link
              href={`/jobs/${job.id}`}
              className="flex items-center justify-between gap-4 p-4 hover:bg-black/5 dark:hover:bg-white/5"
            >
              <div>
                <p className="font-medium">{job.title}</p>
                <p className="text-sm text-black/60 dark:text-white/60">{job.location}</p>
              </div>
              <span className="text-sm">View →</span>
            </Link>
          </li>
        ))}
        {jobs.length === 0 && (
          <li className="p-4 text-black/60 dark:text-white/60">No open roles right now.</li>
        )}
      </ul>
    </section>
  );
}
