import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getJobs, getJob, createApplication } from "../api/client";
import { TierBadge } from "../components/ui/TierBadge";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { X, ExternalLink, Bookmark, ChevronLeft, ChevronRight } from "lucide-react";

export default function Jobs() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["jobs", page, filters],
    queryFn: () => getJobs({ page, per_page: 50, sort_by: "final_score", sort_order: "desc", ...filters }),
  });

  const { data: detail } = useQuery({
    queryKey: ["job", selectedId],
    queryFn: () => getJob(selectedId!),
    enabled: !!selectedId,
  });

  const saveMutation = useMutation({
    mutationFn: (jobId: string) => createApplication({ job_id: jobId, status: "saved" }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["applications"] }),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="flex gap-0">
      <div className={`flex-1 ${selectedId ? "mr-96" : ""}`}>
        <h1 className="text-2xl font-bold mb-4">Jobs</h1>

        {/* Filters */}
        <div className="flex gap-3 mb-4 flex-wrap">
          <select
            className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm"
            onChange={(e) => setFilters((f) => ({ ...f, tier: e.target.value || undefined }))}
          >
            <option value="">All Tiers</option>
            <option value="S">Tier S</option>
            <option value="A">Tier A</option>
            <option value="B">Tier B</option>
            <option value="C">Tier C</option>
          </select>
          <select
            className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm"
            onChange={(e) => setFilters((f) => ({ ...f, platform: e.target.value || undefined }))}
          >
            <option value="">All Platforms</option>
            {["VietnamWorks", "CareerViet", "ITviec", "Ybox", "TopCV", "Joboko"].map((p) => (
              <option key={p} value={p}>{p}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Search title, company..."
            className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-2 text-sm flex-1 min-w-[200px]"
            onChange={(e) => {
              const v = e.target.value;
              setTimeout(() => setFilters((f) => ({ ...f, search: v || undefined })), 300);
            }}
          />
        </div>

        {/* Table */}
        <div className="bg-dark-800 rounded-xl border border-dark-700 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700">
                {["Tier", "Score", "Title", "Company", "Salary", "Location", "Platform"].map((h) => (
                  <th key={h} className="text-left p-3 text-slate-400 font-medium text-xs">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data?.jobs.map((job) => (
                <tr
                  key={job.id}
                  className={`border-b border-dark-900 cursor-pointer transition-colors ${
                    selectedId === job.id ? "bg-dark-700" : "hover:bg-dark-700/50"
                  }`}
                  onClick={() => setSelectedId(job.id)}
                >
                  <td className="p-3"><TierBadge tier={job.tier} /></td>
                  <td className="p-3 font-semibold">{job.final_score > -1 ? job.final_score : job.keyword_score}</td>
                  <td className="p-3 max-w-xs truncate">{job.title}</td>
                  <td className="p-3 text-slate-400 max-w-[150px] truncate">{job.company}</td>
                  <td className="p-3 text-slate-400 text-xs">{job.salary || "—"}</td>
                  <td className="p-3 text-slate-400 text-xs">{job.location || "—"}</td>
                  <td className="p-3 text-slate-400 text-xs">{job.platform}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {data && data.total_pages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <span className="text-slate-400 text-sm">{data.total} jobs total</span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
                className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-1.5 text-sm disabled:opacity-50"
              >
                <ChevronLeft size={16} />
              </button>
              <span className="text-sm py-1.5">{page} / {data.total_pages}</span>
              <button
                disabled={page >= data.total_pages}
                onClick={() => setPage((p) => p + 1)}
                className="bg-dark-800 border border-dark-700 rounded-lg px-3 py-1.5 text-sm disabled:opacity-50"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Detail Panel */}
      {selectedId && detail && (
        <div className="fixed right-0 top-0 h-full w-96 bg-dark-800 border-l border-dark-700 overflow-y-auto p-5 z-50">
          <div className="flex justify-between items-center mb-4">
            <TierBadge tier={detail.tier} />
            <button onClick={() => setSelectedId(null)} className="text-slate-400 hover:text-slate-50">
              <X size={20} />
            </button>
          </div>
          <h2 className="text-lg font-bold mb-1">{detail.title}</h2>
          <p className="text-slate-400 text-sm mb-4">{detail.company} · {detail.platform}</p>

          <div className="grid grid-cols-3 gap-2 mb-4">
            <div className="bg-dark-900 rounded-lg p-2 text-center">
              <div className="text-xs text-slate-400">KW</div>
              <div className="font-bold">{detail.keyword_score}</div>
            </div>
            <div className="bg-dark-900 rounded-lg p-2 text-center">
              <div className="text-xs text-slate-400">LLM</div>
              <div className="font-bold">{detail.llm_score > -1 ? detail.llm_score : "—"}</div>
            </div>
            <div className="bg-dark-900 rounded-lg p-2 text-center">
              <div className="text-xs text-slate-400">Final</div>
              <div className="font-bold text-tier-s">{detail.final_score > -1 ? detail.final_score : "—"}</div>
            </div>
          </div>

          {detail.salary && <p className="text-sm mb-2"><span className="text-slate-400">Salary:</span> {detail.salary}</p>}
          {detail.location && <p className="text-sm mb-2"><span className="text-slate-400">Location:</span> {detail.location}</p>}
          {detail.level && <p className="text-sm mb-4"><span className="text-slate-400">Level:</span> {detail.level}</p>}

          {detail.llm_rationale && (
            <div className="bg-dark-900 rounded-lg p-3 mb-4">
              <div className="text-xs text-slate-400 mb-1">AI Analysis</div>
              <p className="text-sm">{detail.llm_rationale}</p>
            </div>
          )}

          {detail.description && (
            <div className="mb-4">
              <h4 className="text-xs text-slate-400 mb-1 uppercase">Description</h4>
              <p className="text-sm text-slate-300 whitespace-pre-line max-h-40 overflow-y-auto">{detail.description}</p>
            </div>
          )}

          <div className="flex gap-2 mt-4">
            <button
              onClick={() => saveMutation.mutate(detail.id)}
              className="flex-1 bg-tier-a hover:bg-blue-600 text-white rounded-lg py-2 text-sm font-medium flex items-center justify-center gap-2"
            >
              <Bookmark size={14} /> Save
            </button>
            {detail.url && (
              <a
                href={detail.url}
                target="_blank"
                rel="noopener"
                className="flex-1 bg-dark-700 hover:bg-dark-600 rounded-lg py-2 text-sm font-medium flex items-center justify-center gap-2"
              >
                <ExternalLink size={14} /> Open
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
