import { type ReactNode } from "react";

interface StatsCardProps {
  label: string;
  value: string | number;
  icon?: ReactNode;
  change?: string;
  color?: string;
}

export function StatsCard({ label, value, icon, change, color = "text-slate-50" }: StatsCardProps) {
  return (
    <div className="bg-dark-800 rounded-xl p-5 border border-dark-700">
      <div className="flex justify-between items-center mb-2">
        <span className="text-slate-400 text-xs">{label}</span>
        {change && <span className="text-tier-s text-xs">{change}</span>}
        {icon && <span className="text-xl">{icon}</span>}
      </div>
      <div className={`text-3xl font-bold ${color}`}>{value}</div>
    </div>
  );
}
