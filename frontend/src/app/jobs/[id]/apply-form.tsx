"use client";

import { useRouter } from "next/navigation";
import { useState, type FormEvent } from "react";
import type { InterviewMode } from "@/lib/types";

const inputClass =
  "w-full rounded-md border border-black/15 bg-transparent px-3 py-2 text-sm dark:border-white/20";

export function ApplyForm({ jobId }: { jobId: string }) {
  const router = useRouter();
  const [mode, setMode] = useState<InterviewMode>("web");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);

    const form = new FormData(event.currentTarget);
    const payload = {
      jobId,
      mode,
      name: form.get("name"),
      email: form.get("email"),
      phone: form.get("phone"),
      resume: form.get("resume"),
    };

    try {
      const res = await fetch("/api/applications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Something went wrong. Please try again.");
        return;
      }
      router.push(`/applications/${data.id}`);
    } catch {
      setError("Network error. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="space-y-1 text-sm">
          Full name
          <input name="name" required className={inputClass} />
        </label>
        <label className="space-y-1 text-sm">
          Email
          <input name="email" type="email" required className={inputClass} />
        </label>
      </div>

      <fieldset className="space-y-2 text-sm">
        <legend className="mb-1">Interview type</legend>
        <label className="mr-6 inline-flex items-center gap-2">
          <input
            type="radio"
            name="mode"
            checked={mode === "web"}
            onChange={() => setMode("web")}
          />
          Web (video in browser)
        </label>
        <label className="inline-flex items-center gap-2">
          <input
            type="radio"
            name="mode"
            checked={mode === "phone"}
            onChange={() => setMode("phone")}
          />
          Phone call
        </label>
      </fieldset>

      {mode === "phone" && (
        <label className="block space-y-1 text-sm">
          Phone number
          <input
            name="phone"
            type="tel"
            required
            placeholder="+14155550123"
            className={inputClass}
          />
        </label>
      )}

      <label className="block space-y-1 text-sm">
        Resume (paste as text)
        <textarea name="resume" required rows={10} className={inputClass} />
      </label>

      {error && <p className="text-sm text-red-600">{error}</p>}

      <button
        type="submit"
        disabled={submitting}
        className="rounded-md bg-foreground px-4 py-2 text-sm font-medium text-background disabled:opacity-50"
      >
        {submitting ? "Starting interview…" : "Start interview"}
      </button>
    </form>
  );
}
