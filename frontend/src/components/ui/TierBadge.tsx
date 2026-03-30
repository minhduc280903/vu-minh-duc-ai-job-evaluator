import type { TierType } from "../../types";

const tierColors: Record<TierType, string> = {
  S: "bg-tier-s text-white",
  A: "bg-tier-a text-white",
  B: "bg-tier-b text-white",
  C: "bg-tier-c text-white",
};

export function TierBadge({ tier }: { tier: TierType | string | null }) {
  if (!tier) return null;
  const t = tier as TierType;
  return (
    <span className={`px-2 py-0.5 rounded-md text-xs font-bold ${tierColors[t] || "bg-dark-700 text-slate-400"}`}>
      {tier}
    </span>
  );
}
