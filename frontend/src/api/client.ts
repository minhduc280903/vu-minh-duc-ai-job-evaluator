import axios from "axios";
import type {
  Job,
  JobListResponse,
  DashboardStats,
  Application,
  ScraperRun,
} from "../types";

const api = axios.create({ baseURL: "/api" });

// Jobs
export const getJobs = (params: Record<string, any>) =>
  api.get<JobListResponse>("/jobs", { params }).then((r) => r.data);

export const getJob = (id: string) =>
  api.get<Job>(`/jobs/${id}`).then((r) => r.data);

export const getStats = () =>
  api.get<DashboardStats>("/jobs/stats").then((r) => r.data);

// Scrapers
export const startScraping = (platforms: string[] = ["all"]) =>
  api.post("/scrapers/run", { platforms }).then((r) => r.data);

export const getScraperStatus = () =>
  api.get("/scrapers/status").then((r) => r.data);

export const getScraperHistory = () =>
  api.get<ScraperRun[]>("/scrapers/history").then((r) => r.data);

export const stopScraping = () =>
  api.post("/scrapers/stop").then((r) => r.data);

// Evaluator
export const runKeywordScoring = () =>
  api.post("/evaluator/keyword").then((r) => r.data);

export const runLlmEvaluation = () =>
  api.post("/evaluator/llm").then((r) => r.data);

export const getEvalStatus = () =>
  api.get("/evaluator/status").then((r) => r.data);

export const resetScores = () =>
  api.post("/evaluator/reset").then((r) => r.data);

// Applications
export const getApplications = (status?: string) =>
  api.get<Application[]>("/applications", { params: status ? { status } : {} }).then((r) => r.data);

export const createApplication = (data: { job_id: string; status?: string; notes?: string }) =>
  api.post<Application>("/applications", data).then((r) => r.data);

export const updateApplication = (id: number, data: Record<string, any>) =>
  api.patch<Application>(`/applications/${id}`, data).then((r) => r.data);

export const deleteApplication = (id: number) =>
  api.delete(`/applications/${id}`).then((r) => r.data);

// Settings
export const getProfile = () =>
  api.get("/settings/profile").then((r) => r.data);

export const updateProfile = (data: any) =>
  api.put("/settings/profile", { data }).then((r) => r.data);

export const getNotifications = () =>
  api.get("/settings/notifications").then((r) => r.data);

export const updateNotification = (channel: string, data: any) =>
  api.put(`/settings/notifications/${channel}`, data).then((r) => r.data);

export const testTelegram = () =>
  api.post("/settings/test-telegram").then((r) => r.data);

export const testEmail = () =>
  api.post("/settings/test-email").then((r) => r.data);

export const getScheduler = () =>
  api.get("/settings/scheduler").then((r) => r.data);

export const updateScheduler = (taskName: string, data: any) =>
  api.put(`/settings/scheduler/${taskName}`, data).then((r) => r.data);
