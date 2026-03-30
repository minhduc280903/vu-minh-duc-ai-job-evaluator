export interface Job {
  id: string;
  platform: string;
  title: string;
  company: string | null;
  url: string | null;
  salary: string | null;
  location: string | null;
  level: string | null;
  skills: string | null;
  deadline: string | null;
  keyword_score: number;
  llm_score: number;
  final_score: number;
  tier: string | null;
  llm_rationale: string | null;
  llm_pros: string | null;
  llm_cons: string | null;
  scraped_at: string | null;
  summary?: string | null;
  description?: string | null;
  requirements?: string | null;
  benefits?: string | null;
  domain?: string | null;
  views?: number;
  published_at?: string | null;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}

export interface DashboardStats {
  total_jobs: number;
  tier_s: number;
  tier_a: number;
  tier_b: number;
  tier_c: number;
  by_platform: Record<string, number>;
  evaluated: number;
  pending_eval: number;
  avg_score: number;
  new_today: number;
  applications_count: number;
  interviews_count: number;
}

export interface Application {
  id: number;
  job_id: string;
  status: string;
  applied_at: string | null;
  notes: string | null;
  interview_date: string | null;
  interview_notes: string | null;
  salary_offered: string | null;
  created_at: string | null;
  updated_at: string | null;
  job_title: string | null;
  job_company: string | null;
  job_platform: string | null;
  job_tier: string | null;
  job_score: number | null;
  job_url: string | null;
}

export interface ScraperRun {
  id: number;
  platform: string;
  status: string;
  started_at: string | null;
  completed_at: string | null;
  jobs_found: number;
  jobs_new: number;
  jobs_updated: number;
  error_message: string | null;
  triggered_by: string;
}

export type TierType = "S" | "A" | "B" | "C";

