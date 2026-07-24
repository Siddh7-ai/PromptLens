import React from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle: string;
  badge?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  badge
}) => {
  return (
    <div className="headroom-card p-6 flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-[#888888] uppercase tracking-wider">{title}</span>
          {badge && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-[#1a1a1a] text-[#aaaaaa] border border-[#2e2e2e]">
              {badge}
            </span>
          )}
        </div>
        <div className="mt-4">
          <span className="text-4xl font-bold text-white tracking-tight font-sans">{value}</span>
        </div>
      </div>
      <p className="text-xs text-[#666666] mt-4">{subtitle}</p>
    </div>
  );
};
