export interface RequestLog {
  id: number;
  timestamp: string;
  path: string;
  method: string;
  baseline_tokens: number;
  compressed_tokens: number;
  savings_pct: number;
  retrieval_id: string;
}

export interface MetricsSummary {
  total_requests: number;
  total_baseline_tokens: number;
  total_compressed_tokens: number;
  total_tokens_saved: number;
  overall_savings_pct: number;
  estimated_usd_saved: number;
  total_retrievals: number;
  active_vault_items?: number;
  recent_requests: RequestLog[];
  discipline_stats?: Record<string, { requests: number; output_tokens: number }>;
}

export interface BenchmarkTask {
  id: number;
  name: string;
  category: string;
  baseline: number;
  compressed: number;
  savings_pct: number;
  correctness: string;
}

export interface CompressionResult {
  compressed_text: string;
  original_tokens: number;
  compressed_tokens: number;
  savings_pct: number;
  retrieval_id: string | null;
}

export interface VaultItem {
  retrieval_id: string;
  created_at: number;
  size_bytes: number;
  preview: string;
  full_content: string;
}

export interface CompressionSettings {
  head_lines: number;
  tail_lines: number;
  max_json_array: number;
  min_tokens_threshold: number;
  discipline_mode?: string;
}
