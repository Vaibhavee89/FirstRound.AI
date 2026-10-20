import { promises as fs } from "fs";
import path from "path";
import type { Application, Job } from "./types";

// jobs.json and applications.json live in the frontend folder (see DEPLOYMENT.md)
const DATA_DIR = process.cwd();

async function readJson<T>(file: string): Promise<T[]> {
  try {
    return JSON.parse(await fs.readFile(path.join(/*turbopackIgnore: true*/ DATA_DIR, file), "utf8"));
  } catch (err) {
    // A missing file means no records yet; anything else should surface so we never overwrite data
    if ((err as NodeJS.ErrnoException).code === "ENOENT") return [];
    throw err;
  }
}

async function writeJson<T>(file: string, data: T[]) {
  await fs.writeFile(path.join(/*turbopackIgnore: true*/ DATA_DIR, file), JSON.stringify(data, null, 2));
}

export const getJobs = () => readJson<Job>("jobs.json");

export async function getJob(id: string) {
  return (await getJobs()).find((job) => job.id === id);
}

export const getApplications = () => readJson<Application>("applications.json");

export async function getApplication(id: string) {
  return (await getApplications()).find((app) => app.id === id);
}

export const saveApplications = (applications: Application[]) =>
  writeJson("applications.json", applications);
