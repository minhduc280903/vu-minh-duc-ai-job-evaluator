import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { startScraping, stopScraping, getScraperStatus, getScraperHistory } from "../api/client";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { wsClient } from "../api/websocket";
import { Play, Square, RefreshCw } from "lucide-react";

const PLATFORMS = ["Ybox", "VietnamWorks", "TopCV", "ITviec", "CareerViet", "Joboko"];

export default function Scrapers() {
  const queryClient = useQueryClient();
  const [logs, setLogs] = useState<{ platform: string; level: string; message: string; timestamp: number }[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const { data: status } = useQuery({ queryKey: ["scraperStatus"], queryFn: getScraperStatus, refetchInterval: 3000 });
  const { data: history, isLoading } = useQuery({ queryKey: ["scraperHistory"], queryFn: getScraperHistory });

  const startMut = useMutation({
    mutationFn: (platforms: string[]) => startScraping(platforms),
    onSuccess: () => { setIsRunning(true); queryClient.invalidateQueries({ queryKey: ["scraperStatus"] }); },
  });

  const stopMut = useMutation({
    mutationFn: stopScraping,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scraperStatus"] }),
  });

  useEffect(() => {
    const unsub1 = wsClient.on("scraper_log", (data) => {
      setLogs((prev) => [...prev.slice(-100), data]);
    });
    const unsub2 = wsClient.on("scraper_complete", () => {
      queryClient.invalidateQueries({ queryKey: ["scraperHistory"] });
      queryClient.invalidateQueries({ queryKey: ["scraperStatus"] });
    });
    return () => { unsub1(); unsub2(); };
  }, [queryClient]);

  useEffect(() => {
    if (status) setIsRunning(status.is_running);
  }, [status]);

  if (isLoading) return <LoadingSpinner />;

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Scrapers</h1>
        <div className="flex gap-2">
          {isRunning ? (
            <button onClick={() => stopMut.mutate()} className="bg-tier-c hover:bg-red-600 text-white rounded-lg px-4 py-2 text-sm font-medium flex items-center gap-2">
              <Square size={14} /> Stop
            </button>
          ) : (
            <button onClick={() => startMut.mutate(["all"])} className="bg-tier-s hover:bg-emerald-600 text-white rounded-lg px-4 py-2 text-sm font-medium flex items-center gap-2">
              <Play size={14} /> Run All
            </button>
          )}
        </div>
      </div>

      {/* Platform Cards */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        {PLATFORMS.map((p) => {
          const lastRun = history?.find((h) => h.platform === p);
          const running = status?.current_platforms?.includes(p.toLowerCase());
          return (
            <div key={p} className="bg-dark-800 rounded-xl p-4 border border-dark-700">
              <div className="flex justify-between items-center mb-2">
                <span className="font-semibold text-sm">{p}</span>
                <div className={`w-2.5 h-2.5 rounded-full ${running ? "bg-tier-s animate-pulse" : lastRun?.status === "completed" ? "bg-tier-s" : "bg-slate-500"}`} />
              </div>
              <p className="text-xs text-slate-400">
                {lastRun ? `Last: ${new Date(lastRun.started_at!).toLocaleDateString()} — ${lastRun.jobs_found} jobs` : "Never run"}
              </p>
              {!isRunning && (
                <button
                  onClick={() => startMut.mutate([p.toLowerCase()])}
                  className="mt-2 text-xs text-tier-a hover:text-blue-400 flex items-center gap-1"
                >
                  <RefreshCw size={10} /> Run
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Live Logs */}
      {logs.length > 0 && (
        <div className="bg-dark-800 rounded-xl p-4 border border-dark-700 mb-6">
          <h3 className="text-sm font-semibold mb-2">Live Logs</h3>
          <div className="bg-dark-900 rounded-lg p-3 max-h-48 overflow-y-auto font-mono text-xs space-y-1">
            {logs.map((log, i) => (
              <div key={i} className={log.level === "error" ? "text-tier-c" : "text-slate-300"}>
                [{log.platform}] {log.message}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History Table */}
      <div className="bg-dark-800 rounded-xl p-4 border border-dark-700">
        <h3 className="text-sm font-semibold mb-3">Run History</h3>
        {(!history || history.length === 0) ? (
          <p className="text-slate-400 text-sm">No scraper runs yet.</p>
        ) : (
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-dark-700">
                {["Platform", "Status", "Jobs Found", "Started", "Duration", "Triggered By"].map((h) => (
                  <th key={h} className="text-left p-2 text-slate-400 font-medium text-xs">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {history.map((run) => (
                <tr key={run.id} className="border-b border-dark-900">
                  <td className="p-2">{run.platform}</td>
                  <td className="p-2">
                    <span className={`text-xs ${run.status === "completed" ? "text-tier-s" : run.status === "failed" ? "text-tier-c" : "text-tier-b"}`}>
                      {run.status}
                    </span>
                  </td>
                  <td className="p-2">{run.jobs_found}</td>
                  <td className="p-2 text-slate-400 text-xs">{run.started_at ? new Date(run.started_at).toLocaleString() : "—"}</td>
                  <td className="p-2 text-slate-400 text-xs">
                    {run.started_at && run.completed_at
                      ? `${Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)}s`
                      : "—"}
                  </td>
                  <td className="p-2 text-slate-400 text-xs">{run.triggered_by}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
