import { connection } from "next/server";
import { getInterviewLogs } from "@/lib/agent";
import { getApplications, getJobs } from "@/lib/data";

// Reads the JSON store per request, so it must not be prerendered at build time
export const instant = false;

export default async function RecruiterPage() {
  await connection();
  const [applications, jobs, logs] = await Promise.all([
    getApplications(),
    getJobs(),
    getInterviewLogs(),
  ]);
  const jobTitles = new Map(jobs.map((job) => [job.id, job.title]));

  return (
    <div className="space-y-10">
      <section className="space-y-4">
        <h1 className="text-3xl font-semibold">Applications</h1>
        {applications.length === 0 ? (
          <p className="text-black/60 dark:text-white/60">No applications yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-black/10 dark:border-white/10">
            <table className="w-full text-left text-sm">
              <thead className="bg-black/5 dark:bg-white/5">
                <tr>
                  <th className="p-3 font-medium">Candidate</th>
                  <th className="p-3 font-medium">Role</th>
                  <th className="p-3 font-medium">Interview</th>
                  <th className="p-3 font-medium">Status</th>
                  <th className="p-3 font-medium">Score</th>
                </tr>
              </thead>
              <tbody>
                {applications.map((app) => (
                  <tr key={app.id} className="border-t border-black/10 dark:border-white/10">
                    <td className="p-3">
                      <p className="font-medium">{app.name}</p>
                      <p className="text-black/60 dark:text-white/60">{app.email}</p>
                    </td>
                    <td className="p-3">{jobTitles.get(app.jobId) ?? app.jobId}</td>
                    <td className="p-3 capitalize">{app.mode}</td>
                    <td className="p-3 capitalize">{app.status}</td>
                    <td className="p-3">
                      {app.evaluation ? `${app.evaluation.overall_score}/10` : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Agent interview logs</h2>
        {logs.length === 0 ? (
          <p className="text-black/60 dark:text-white/60">
            No logs found. The agent may be offline, or no interviews have run yet.
          </p>
        ) : (
          <ul className="divide-y divide-black/10 dark:divide-white/10 rounded-lg border border-black/10 dark:border-white/10">
            {logs.map((log) => (
              <li key={log.call_sid} className="flex justify-between gap-4 p-3 text-sm">
                <span className="font-mono">{log.call_sid}</span>
                <span className="text-black/60 dark:text-white/60">
                  {log.status} · {log.exchange_count} exchanges · {new Date(log.timestamp).toLocaleString()}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
