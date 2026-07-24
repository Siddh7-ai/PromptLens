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
  recent_requests: RequestLog[];
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
