import React from 'react';
import { RequestLog } from '../types';

interface RequestStreamProps {
  logs: RequestLog[];
}

export const RequestStream: React.FC<RequestStreamProps> = ({ logs }) => {
  return (
    <div className="headroom-card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white tracking-tight">Recent Proxied Requests Stream</h2>
          <p className="text-xs text-[#888888]">Live request audit trail passing through the local proxy.</p>
        </div>
        <span className="text-xs font-mono text-[#666666]">Auto-updates live</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[#1f1f1f] bg-[#0f0f0f] text-[#888888] font-medium">
              <th className="py-3 px-4">Time</th>
              <th className="py-3 px-4">Method & Path</th>
              <th className="py-3 px-4 text-right">Baseline Tokens</th>
              <th className="py-3 px-4 text-right">Compressed Tokens</th>
              <th className="py-3 px-4 text-right">Savings</th>
              <th className="py-3 px-4 text-center">Vault Hash ID</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[#181818] font-mono text-[#cccccc]">
            {logs.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-6 text-center text-[#555555] font-sans">
                  No requests proxied yet. Run an agent or test request to view live stream.
                </td>
              </tr>
            ) : (
              logs.slice(0, 20).map((req) => (
                <tr key={req.id} className="hover:bg-[#121212] transition">
                  <td className="py-3 px-4 font-sans text-[#888888]">{req.timestamp}</td>
                  <td className="py-3 px-4 font-sans font-semibold text-white">
                    <span className="px-1.5 py-0.5 rounded bg-[#1c1c1c] text-[#888888] text-[10px] mr-1.5 font-mono">
                      {req.method}
                    </span>
                    {req.path}
                  </td>
                  <td className="py-3 px-4 text-right text-[#888888]">{req.baseline_tokens.toLocaleString()}</td>
                  <td className="py-3 px-4 text-right text-white font-semibold">
                    {req.compressed_tokens.toLocaleString()}
                  </td>
                  <td className="py-3 px-4 text-right text-white font-semibold">{req.savings_pct}%</td>
                  <td className="py-3 px-4 text-center font-mono text-xs text-[#888888]">
                    {req.retrieval_id}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
