// Utility formatters for metrics, units, and timestamps

export function formatWeight(kg: number): string {
  if (kg >= 1000) {
    return `${(kg / 1000).toFixed(1)} T`;
  }
  return `${kg.toLocaleString()} kg`;
}

export function formatDistance(km: number): string {
  return `${km.toFixed(1)} km`;
}

export function formatPercentage(pct: number): string {
  return `${pct.toFixed(1)}%`;
}

export function formatRiskBadge(tier: string): { bg: string; text: string; border: string } {
  switch (tier.toUpperCase()) {
    case 'CRITICAL':
      return { bg: 'bg-[#93000a]/20', text: 'text-[#ffb4ab]', border: 'border-[#ffb4ab]/30' };
    case 'HIGH':
      return { bg: 'bg-[#ff8786]/20', text: 'text-[#ffb3b1]', border: 'border-[#ffb3b1]/30' };
    case 'MODERATE':
      return { bg: 'bg-[#01a0c9]/20', text: 'text-[#61d4ff]', border: 'border-[#61d4ff]/30' };
    default:
      return { bg: 'bg-[#20bfa5]/20', text: 'text-[#4ddcc1]', border: 'border-[#4ddcc1]/30' };
  }
}
