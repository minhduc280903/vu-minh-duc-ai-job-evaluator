import { useQuery } from "@tanstack/react-query";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { getStats, getJobs } from "../api/client";
import { StatsCard } from "../components/ui/StatsCard";
import { TierBadge } from "../components/ui/TierBadge";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";

export default function Dashboard() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ["stats"],
    queryFn: getStats,
  });
  const { data: topJobs } = useQuery({
    queryKey: ["topJobs"],
    queryFn: () => getJobs({ page: 1, per_page: 5, sort_by: "final_score", sort_order: "desc" }),
  });

  if (statsLoading) return <LoadingSpinner />;
  if (!stats) return <div className="text-slate-400">Failed to load stats</div>;

  const tierData = [
    { name: "Tier S", count: stats.tier_s, fill: "#10b981" },
    { name: "Tier A", count: stats.tier_a, fill: "#3b82f6" },
    { name: "Tier B", count: stats.tier_b, fill: "#f59e0b" },
    { name: "Tier C", count: stats.tier_c, fill: "#ef4444" },
  ];

  const platformData = Object.entries(stats.by_platform).map(([name, count]) => ({
    name,
    count,
    pct: Math.round(((count as number) / stats.total_jobs) * 100),
  }));

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <p className="text-slate-400 text-sm">
            {stats.new_today > 0 ? (
              <>Có <span className="text-tier-s">{stats.new_today} jobs mới</span> hôm nay.</>
            ) : "Không có jobs mới hôm nay."}
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <StatsCard label="Total Jobs" value={stats.total_jobs.toLocaleString()} />
        <StatsCard label="Tier S Matches" value={stats.tier_s} color="text-tier-s" />
        <StatsCard label="Applied" value={stats.applications_count} color="text-tier-a" />
        <StatsCard label="AI Evaluated" value={stats.evaluated} color="text-violet-400" />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {/* Tier Distribution */}
        <div className="col-span-2 bg-dark-800 rounded-xl p-5 border border-dark-700">
          <h3 className="text-sm font-semibold mb-4">Score Distribution</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={tierData}>
              <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
              <YAxis stroke="#64748b" fontSize={12} />
              <Tooltip
                contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 8 }}
                labelStyle={{ color: "#f8fafc" }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {tierData.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Platform Breakdown */}
        <div className="bg-dark-800 rounded-xl p-5 border border-dark-700">
          <h3 className="text-sm font-semibold mb-4">By Platform</h3>
          <div className="space-y-3">
            {platformData.map((p) => (
              <div key={p.name}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-slate-400">{p.name}</span>
                  <span>{p.count}</span>
                </div>
                <div className="bg-dark-700 rounded h-1.5">
                  <div
                    className="bg-tier-s rounded h-full transition-all"
                    style={{ width: `${p.pct}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Top Matches */}
      <div className="bg-dark-800 rounded-xl p-5 border border-dark-700">
        <h3 className="text-sm font-semibold mb-4">Top Matches</h3>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-dark-700">
              <th className="text-left p-2 text-slate-400 font-medium">Tier</th>
              <th className="text-left p-2 text-slate-400 font-medium">Title</th>
              <th className="text-left p-2 text-slate-400 font-medium">Company</th>
              <th className="text-left p-2 text-slate-400 font-medium">Score</th>
              <th className="text-left p-2 text-slate-400 font-medium">Salary</th>
            </tr>
          </thead>
          <tbody>
            {topJobs?.jobs.map((job) => (
              <tr key={job.id} className="border-b border-dark-900 hover:bg-dark-700/50">
                <td className="p-2"><TierBadge tier={job.tier} /></td>
                <td className="p-2">{job.title}</td>
                <td className="p-2 text-slate-400">{job.company}</td>
                <td className="p-2 font-semibold text-tier-s">{job.final_score > -1 ? job.final_score : job.keyword_score}</td>
                <td className="p-2 text-slate-400">{job.salary || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
