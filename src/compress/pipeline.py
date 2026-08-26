import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Optional

from ..allocator.budget_optimizer import BudgetOptimizer, OptimizedContextResult
from ..classifier.task_classifier import DecomposedPrompt, TaskCategory, TaskClassifier
from ..compress.json_compressor import compress_json
from ..compress.text_compressor import compress_text
from ..graph.dependency_graph import DependencyGraph, ExpandedNeighborhood
from ..parser.ast_parser import ASTParser, CodeSymbol, ParsedCodeFile
from ..semantic.embedder import LightweightEmbedder
from ..semantic.relevance_scorer import RelevanceScorer, ScoredSymbol
from ..store.retrieval_store import get_global_store
from ..utils.token_utils import get_token_count


@dataclass
class StageMetrics:
    stage_name: str
    token_count: int
    reduction_pct: float
    latency_ms: float


@dataclass
class PipelineCompressionResult:
    final_prompt: str
    task_category: TaskCategory
    task_confidence: float
    original_tokens: int
    compressed_tokens: int
    total_savings_pct: float
    total_latency_ms: float
    retrieval_id: str
    stage_metrics: list[StageMetrics] = field(default_factory=list)
    preserved_count: int = 0
    summarized_count: int = 0
    omitted_count: int = 0
    parsed_files: list[str] = field(default_factory=list)
    detected_symbols: list[str] = field(default_factory=list)


class PromptLensPipeline:
    """
    Unified 5-Stage Multi-Level Coding Prompt Compression Engine:
    - Stage 1: Deterministic Noise & Log Compression (v1)
    - Stage 2: AST Multi-Language Structural Parsing (v2)
    - Stage 3: Semantic Relevance Indexing (v3)
    - Stage 4: Task-Aware + AST Dependency Graph Expansion (v4)
    - Stage 5: Adaptive Token Budget Knapsack Optimization (v5)
    """

    def __init__(self, default_budget: int = 8192):
        self.classifier = TaskClassifier()
        self.parser = ASTParser()
        self.graph = DependencyGraph()
        self.embedder = LightweightEmbedder()
        self.scorer = RelevanceScorer(embedder=self.embedder)
        self.optimizer = BudgetOptimizer(default_budget=default_budget)
        self.store = get_global_store()

    def compress(
        self,
        prompt: str,
        mode: str = "v5",
        budget: Optional[int] = None,
        max_hops: int = 2
    ) -> PipelineCompressionResult:
        t_start = time.perf_counter()
        orig_tokens = get_token_count(prompt)
        stage_metrics: list[StageMetrics] = []

        # Vault the entire raw prompt first
        raw_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        self.store.save(prompt, retrieval_id=raw_hash[:16])

        # Fast path for raw JSON or large JSON tool outputs
        stripped_prompt = prompt.strip()
        if (stripped_prompt.startswith("{") and stripped_prompt.endswith("}")) or (stripped_prompt.startswith("[") and stripped_prompt.endswith("]")):
            try:
                json_obj = json.loads(stripped_prompt)
                if isinstance(json_obj, (dict, list)):
                    json_res = compress_json(stripped_prompt)
                    if json_res.is_compressed:
                        t_end = time.perf_counter()
                        latency = round((t_end - t_start) * 1000, 2)
                        item_count = len(json_obj) if isinstance(json_obj, list) else 1
                        return PipelineCompressionResult(
                            final_prompt=json_res.compressed_str,
                            task_category=TaskCategory.GENERAL,
                            task_confidence=0.99,
                            original_tokens=orig_tokens,
                            compressed_tokens=json_res.compressed_tokens,
                            total_savings_pct=round(json_res.compression_ratio * 100, 2),
                            total_latency_ms=latency,
                            retrieval_id=json_res.retrieval_id,
                            stage_metrics=[
                                StageMetrics("Stage 1 (JSON Array Skimming)", json_res.compressed_tokens, round(json_res.compression_ratio * 100, 2), latency),
                                StageMetrics("Stage 2 (AST Skeletons)", json_res.compressed_tokens, 0.0, 0.1),
                                StageMetrics("Stage 3 (Semantic Match)", json_res.compressed_tokens, 0.0, 0.1),
                                StageMetrics("Stage 4 (Dep Graph)", json_res.compressed_tokens, 0.0, 0.1),
                                StageMetrics("Stage 5 (Budget Optimized)", json_res.compressed_tokens, round(json_res.compression_ratio * 100, 2), latency),
                            ],
                            preserved_count=min(10, item_count),
                            summarized_count=1,
                            omitted_count=max(0, item_count - 10),
                        )
            except Exception:
                pass

        # Step 0: Decompose Prompt and Classify Task
        decomposed = self.classifier.decompose(prompt)

        # -------------------------------------------------------------
        # STAGE 1: Deterministic Compression (Logs, Whitespace, Diffs)
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        compressed_log_str = ""
        if decomposed.log_blocks:
            combined_logs = "\n".join(decomposed.log_blocks)
            s1_log_res = compress_text(combined_logs)
            compressed_log_str = s1_log_res.compressed_str

        # If running purely in v1_rule_based mode:
        if mode == "v1":
            v1_res = compress_text(prompt)
            t_end = time.perf_counter()
            return PipelineCompressionResult(
                final_prompt=v1_res.compressed_str,
                task_category=decomposed.task_category,
                task_confidence=decomposed.confidence,
                original_tokens=orig_tokens,
                compressed_tokens=v1_res.compressed_tokens,
                total_savings_pct=round(v1_res.compression_ratio * 100, 2),
                total_latency_ms=round((t_end - t_start) * 1000, 2),
                retrieval_id=v1_res.retrieval_id,
                stage_metrics=[StageMetrics("Stage 1 (Deterministic)", v1_res.compressed_tokens, v1_res.compression_ratio * 100, (t_end - t_start) * 1000)],
            )

        t1 = time.perf_counter()
        s1_approx_tokens = get_token_count(decomposed.user_request) + get_token_count(compressed_log_str) + sum(get_token_count(cb["content"]) for cb in decomposed.code_blocks)
        s1_reduction = max(0.0, (1.0 - (s1_approx_tokens / max(1, orig_tokens))) * 100)
        stage_metrics.append(StageMetrics("Stage 1 (Deterministic)", s1_approx_tokens, round(s1_reduction, 2), round((t1 - t0) * 1000, 2)))

        # -------------------------------------------------------------
        # STAGE 2: Structural AST Parsing
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        parsed_files: list[ParsedCodeFile] = []
        all_symbols: list[CodeSymbol] = []

        if decomposed.code_blocks:
            for idx, cb in enumerate(decomposed.code_blocks):
                fp = cb.get("filepath") or f"block_{idx}.{cb.get('language', 'py')}"
                pf = self.parser.parse(cb["content"], language=cb.get("language", "python"), filepath=fp)
                parsed_files.append(pf)
                all_symbols.extend(pf.symbols)
        else:
            # If code was inline without markdown fences, try parsing raw text
            if len(prompt.splitlines()) > 5:
                pf = self.parser.parse(prompt, language="python", filepath="main.py")
                if pf.symbols:
                    parsed_files.append(pf)
                    all_symbols.extend(pf.symbols)

        t2 = time.perf_counter()
        s2_skeleton_tokens = sum(get_token_count(pf.full_skeleton) for pf in parsed_files) + get_token_count(decomposed.user_request)
        s2_reduction = max(0.0, (1.0 - (s2_skeleton_tokens / max(1, orig_tokens))) * 100)
        stage_metrics.append(StageMetrics("Stage 2 (AST Structural)", s2_skeleton_tokens, round(s2_reduction, 2), round((t2 - t0) * 1000, 2)))

        if mode == "v2":
            final_skel_text = f"## Task Request\n{decomposed.user_request}\n\n" + "\n\n".join(pf.full_skeleton for pf in parsed_files)
            c_toks = get_token_count(final_skel_text)
            t_end = time.perf_counter()
            return PipelineCompressionResult(
                final_prompt=final_skel_text,
                task_category=decomposed.task_category,
                task_confidence=decomposed.confidence,
                original_tokens=orig_tokens,
                compressed_tokens=c_toks,
                total_savings_pct=round((1.0 - (c_toks / max(1, orig_tokens))) * 100, 2),
                total_latency_ms=round((t_end - t_start) * 1000, 2),
                retrieval_id=raw_hash[:16],
                stage_metrics=stage_metrics,
                parsed_files=[pf.filepath for pf in parsed_files],
            )

        # -------------------------------------------------------------
        # STAGE 3 & 4: Semantic Relevance & AST Dependency Graph Expansion
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        self.graph.build_from_files(parsed_files)

        # Determine seed symbols from prompt mentions + top semantic matches
        seed_symbols = list(decomposed.detected_symbols)
        if not seed_symbols and all_symbols:
            # Pick top semantic symbol as seed
            ranked = self.embedder.rank_chunks(decomposed.user_request, [s.full_code for s in all_symbols])
            if ranked:
                seed_symbols.append(all_symbols[ranked[0][0]].name)

        neighborhood: Optional[ExpandedNeighborhood] = None
        if mode in ("v4", "v5") and seed_symbols:
            neighborhood = self.graph.expand_neighborhood(seed_symbols, max_hops=max_hops)

        scored_symbols: list[ScoredSymbol] = self.scorer.score_symbols(
            symbols=all_symbols,
            decomposed=decomposed,
            neighborhood=neighborhood if mode != "v3" else None,
        )

        t3 = time.perf_counter()
        top_sem_tokens = sum(s.symbol.full_tokens or get_token_count(s.symbol.full_code) for s in scored_symbols if s.semantic_score > 0.3)
        s3_reduction = max(0.0, (1.0 - (top_sem_tokens / max(1, orig_tokens))) * 100)
        stage_metrics.append(StageMetrics("Stage 3 (Semantic Relevance)", top_sem_tokens, round(s3_reduction, 2), round((t3 - t0) * 1000, 2)))

        if mode == "v3":
            # Semantic only: keep chunks with semantic relevance > 0.25
            sem_chunks = [s.symbol.full_code for s in scored_symbols if s.semantic_score >= 0.25]
            if not sem_chunks and scored_symbols:
                sem_chunks = [scored_symbols[0].symbol.full_code]
            final_sem_text = f"## Task Request\n{decomposed.user_request}\n\n## Semantic Relevant Code\n" + "\n\n".join(f"```\n{c}\n```" for c in sem_chunks)
            c_toks = get_token_count(final_sem_text)
            t_end = time.perf_counter()
            return PipelineCompressionResult(
                final_prompt=final_sem_text,
                task_category=decomposed.task_category,
                task_confidence=decomposed.confidence,
                original_tokens=orig_tokens,
                compressed_tokens=c_toks,
                total_savings_pct=round((1.0 - (c_toks / max(1, orig_tokens))) * 100, 2),
                total_latency_ms=round((t_end - t_start) * 1000, 2),
                retrieval_id=raw_hash[:16],
                stage_metrics=stage_metrics,
                parsed_files=[pf.filepath for pf in parsed_files],
            )

        dep_tokens = sum(s.symbol.full_tokens or get_token_count(s.symbol.full_code) for s in scored_symbols if s.dependency_score > 0.0)
        s4_reduction = max(0.0, (1.0 - (dep_tokens / max(1, orig_tokens))) * 100)
        stage_metrics.append(StageMetrics("Stage 4 (Dependency Expansion)", dep_tokens, round(s4_reduction, 2), round((t3 - t0) * 1000, 2)))

        # -------------------------------------------------------------
        # STAGE 5: Adaptive Token Budget Optimization (Knapsack Solver)
        # -------------------------------------------------------------
        t0 = time.perf_counter()
        opt_res: OptimizedContextResult = self.optimizer.optimize(
            decomposed=decomposed,
            scored_symbols=scored_symbols,
            budget_limit=budget,
            compressed_logs=compressed_log_str,
            primary_vault_id=raw_hash[:16],
        )
        t5 = time.perf_counter()
        s5_reduction = opt_res.savings_ratio * 100
        stage_metrics.append(StageMetrics("Stage 5 (Budget Optimization)", opt_res.compressed_tokens, round(s5_reduction, 2), round((t5 - t0) * 1000, 2)))

        t_total_end = time.perf_counter()

        return PipelineCompressionResult(
            final_prompt=opt_res.compressed_text,
            task_category=decomposed.task_category,
            task_confidence=decomposed.confidence,
            original_tokens=orig_tokens,
            compressed_tokens=opt_res.compressed_tokens,
            total_savings_pct=round(s5_reduction, 2),
            total_latency_ms=round((t_total_end - t_start) * 1000, 2),
            retrieval_id=raw_hash[:16],
            stage_metrics=stage_metrics,
            preserved_count=opt_res.preserved_count,
            summarized_count=opt_res.summarized_count,
            omitted_count=opt_res.omitted_count,
            parsed_files=[pf.filepath for pf in parsed_files],
            detected_symbols=[s.name for s in all_symbols],
        )
