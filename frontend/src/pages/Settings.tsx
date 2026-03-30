import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { getProfile, getNotifications, updateNotification, testTelegram, testEmail, getScheduler, updateScheduler } from "../api/client";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { Send } from "lucide-react";

const TABS = ["Profile", "Notifications", "Scheduler"] as const;

export default function SettingsPage() {
  const [tab, setTab] = useState<typeof TABS[number]>("Profile");

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Settings</h1>
      <div className="flex gap-1 mb-6 bg-dark-800 rounded-lg p-1 w-fit">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${tab === t ? "bg-dark-700 text-slate-50" : "text-slate-400 hover:text-slate-50"}`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "Profile" && <ProfileTab />}
      {tab === "Notifications" && <NotificationsTab />}
      {tab === "Scheduler" && <SchedulerTab />}
    </div>
  );
}

function ProfileTab() {
  const { data, isLoading } = useQuery({ queryKey: ["profile"], queryFn: getProfile });
  if (isLoading) return <LoadingSpinner />;
  if (!data) return <p className="text-slate-400">Failed to load profile</p>;

  const profile = data.data;
  return (
    <div className="bg-dark-800 rounded-xl p-5 border border-dark-700 max-w-2xl">
      <h3 className="font-semibold mb-4">User Profile</h3>
      <div className="space-y-3 text-sm">
        <div><span className="text-slate-400">Name:</span> {profile.profile_name}</div>
        <div><span className="text-slate-400">Background:</span> {profile.background}</div>
        <div><span className="text-slate-400">Location:</span> {profile.location}</div>
        <div><span className="text-slate-400">Experience:</span> {profile.experience_years} years</div>
        <div className="mt-4">
          <span className="text-slate-400">Tier S Keywords:</span>
          <div className="flex flex-wrap gap-1 mt-1">
            {profile.title_keywords?.tier_s?.keywords?.map((kw: string) => (
              <span key={kw} className="bg-dark-700 px-2 py-0.5 rounded text-xs">{kw}</span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function NotificationsTab() {
  const queryClient = useQueryClient();
  const { data: notifs, isLoading } = useQuery({ queryKey: ["notifications"], queryFn: getNotifications });
  const [testResult, setTestResult] = useState<string | null>(null);

  const updateMut = useMutation({
    mutationFn: ({ channel, data }: { channel: string; data: any }) => updateNotification(channel, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["notifications"] }),
  });

  const testTgMut = useMutation({
    mutationFn: testTelegram,
    onSuccess: (d) => setTestResult(d.success ? "Telegram sent!" : "Failed"),
  });

  const testEmailMut = useMutation({
    mutationFn: testEmail,
    onSuccess: (d) => setTestResult(d.success ? "Email sent!" : "Failed"),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="space-y-4 max-w-2xl">
      {notifs?.map((n: any) => (
        <div key={n.channel} className="bg-dark-800 rounded-xl p-5 border border-dark-700">
          <div className="flex justify-between items-center mb-3">
            <h3 className="font-semibold capitalize">{n.channel}</h3>
            <button
              onClick={() => updateMut.mutate({ channel: n.channel, data: { enabled: !n.enabled } })}
              className={`w-10 h-5 rounded-full transition-colors ${n.enabled ? "bg-tier-s" : "bg-dark-700"} relative`}
            >
              <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${n.enabled ? "left-5" : "left-0.5"}`} />
            </button>
          </div>
          <div className="text-sm text-slate-400 mb-3">
            Min Tier: {n.min_tier} | Daily Digest: {n.daily_digest ? "On" : "Off"}
          </div>
          <button
            onClick={() => n.channel === "telegram" ? testTgMut.mutate() : testEmailMut.mutate()}
            className="text-xs text-tier-a hover:text-blue-400 flex items-center gap-1"
          >
            <Send size={12} /> Test {n.channel}
          </button>
        </div>
      ))}
      {testResult && <p className="text-sm text-tier-s">{testResult}</p>}
    </div>
  );
}

function SchedulerTab() {
  const queryClient = useQueryClient();
  const { data: configs, isLoading } = useQuery({ queryKey: ["scheduler"], queryFn: getScheduler });

  const updateMut = useMutation({
    mutationFn: ({ name, data }: { name: string; data: any }) => updateScheduler(name, data),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["scheduler"] }),
  });

  if (isLoading) return <LoadingSpinner />;

  const labels: Record<string, string> = {
    auto_scrape: "Auto Scrape", auto_evaluate: "Auto Evaluate", daily_report: "Daily Report",
  };

  return (
    <div className="space-y-4 max-w-2xl">
      {configs?.map((c: any) => (
        <div key={c.task_name} className="bg-dark-800 rounded-xl p-5 border border-dark-700">
          <div className="flex justify-between items-center mb-2">
            <h3 className="font-semibold">{labels[c.task_name] || c.task_name}</h3>
            <button
              onClick={() => updateMut.mutate({ name: c.task_name, data: { enabled: !c.enabled } })}
              className={`w-10 h-5 rounded-full transition-colors ${c.enabled ? "bg-tier-s" : "bg-dark-700"} relative`}
            >
              <div className={`w-4 h-4 bg-white rounded-full absolute top-0.5 transition-transform ${c.enabled ? "left-5" : "left-0.5"}`} />
            </button>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-400">Cron:</span>
            <input
              defaultValue={c.cron_expression}
              className="bg-dark-900 border border-dark-700 rounded px-2 py-1 text-xs font-mono w-32"
              onBlur={(e) => updateMut.mutate({ name: c.task_name, data: { cron_expression: e.target.value } })}
            />
            {c.last_run && <span className="text-xs text-slate-500">Last: {new Date(c.last_run).toLocaleString()}</span>}
          </div>
        </div>
      ))}
    </div>
  );
}
