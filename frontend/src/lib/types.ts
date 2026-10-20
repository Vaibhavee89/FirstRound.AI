export type Job = {
  id: string;
  title: string;
  location: string;
  description: string;
};

export type InterviewMode = "web" | "phone";

export type ApplicationStatus = "interviewing" | "accepted" | "rejected";

export type Evaluation = {
  technical_fit: number;
  experience_relevance: number;
  communication: number;
  problem_solving: number;
  culture_fit: number;
  overall_score: number;
  decision: string;
  summary: string;
  strengths: string[];
  areas_of_concern: string[];
};

export type Application = {
  id: string;
  jobId: string;
  name: string;
  email: string;
  phone?: string;
  resume: string;
  mode: InterviewMode;
  status: ApplicationStatus;
  roomUrl?: string;
  callSid?: string;
  evaluation?: Evaluation;
  appliedAt: string;
  interviewedAt?: string;
};

export type InterviewLog = {
  call_sid: string;
  timestamp: string;
  status: string;
  exchange_count: number;
};
