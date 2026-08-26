import hashlib
from dataclasses import dataclass, field
from typing import Optional

from ..classifier.task_classifier import DecomposedPrompt
from ..semantic.relevance_scorer import ScoredSymbol
from ..store.retrieval_store import get_global_store
from ..utils.token_utils import get_token_count


@dataclass
class AllocationDecision:
    symbol_name: str
    filepath: Optional[str]
    action: str  # "PRESERVE", "SUMMARIZE", "OMIT"
    relevance_score: float
    original_tokens: int
    allocated_tokens: int
    content: str
    vault_id: Optional[str] = None


@dataclass
class OptimizedContextResult:
    compressed_text: str
    original_tokens: int
    compressed_tokens: int
    budget_limit: int
    savings_ratio: float
    decisions: list[AllocationDecision] = field(default_factory=list)
    preserved_count: int = 0
    summarized_count: int = 0
    omitted_count: int = 0


class BudgetOptimizer:
    """
    Solves the knapsack token budget optimization problem:
    Maximize sum(Relevance_i * Action_i) subject to Total_Tokens <= Budget_B.
    Produces a tri-state compressed context (PRESERVE, SUMMARIZE, OMIT).
    """

    def __init__(self, default_budget: int = 8192):
        self.default_budget = default_budget
        self.store = get_global_store()

    def optimize(
        self,
        decomposed: DecomposedPrompt,
        scored_symbols: list[ScoredSymbol],
        budget_limit: Optional[int] = None,
        compressed_logs: Optional[str] = None,
        primary_vault_id: Optional[str] = None,
    ) -> OptimizedContextResult:
        budget = budget_limit or self.default_budget
        decisions: list[AllocationDecision] = []

        # 1. Base cost: User Instructions + Compressed Logs
        user_req_tokens = get_token_count(decomposed.user_request)
        logs_text = compressed_logs or ("\n".join(decomposed.log_blocks) if decomposed.log_blocks else "")
        logs_tokens = get_token_count(logs_text) if logs_text else 0

        reserved_tokens = user_req_tokens + logs_tokens + 100  # 100 tokens header/footer margin
        available_budget = max(200, budget - reserved_tokens)

        # 2. Pre-calculate token sizes for full vs skeleton
        for scored in scored_symbols:
            sym = scored.symbol
            if sym.full_tokens == 0:
                sym.full_tokens = get_token_count(sym.full_code)
            if sym.skeleton_tokens == 0:
                sym.skeleton_tokens = get_token_count(sym.skeleton_code)

        # 3. Knapsack Greedy Optimization
        # Sort candidates by relevance descending
        remaining_budget = available_budget
        preserved_cnt = 0
        summarized_cnt = 0
        omitted_cnt = 0

        for item in scored_symbols:
            sym = item.symbol
            rel = item.total_relevance

            # Decision logic based on relevance threshold and remaining token capacity
            if rel >= 0.70 and remaining_budget >= sym.full_tokens:
                # PRESERVE full implementation
                action = "PRESERVE"
                allocated_tok = sym.full_tokens
                content = sym.full_code
                remaining_budget -= sym.full_tokens
                preserved_cnt += 1
            elif (rel >= 0.25 or item.dependency_score > 0.0) and remaining_budget >= sym.skeleton_tokens:
                # SUMMARIZE to structural signature / skeleton
                action = "SUMMARIZE"
                allocated_tok = sym.skeleton_tokens
                content = sym.skeleton_code
                remaining_budget -= sym.skeleton_tokens
                summarized_cnt += 1
            elif rel >= 0.50 and remaining_budget >= sym.skeleton_tokens:
                # Degrade high-relevance to skeleton if budget is exhausted
                action = "SUMMARIZE"
                allocated_tok = sym.skeleton_tokens
                content = sym.skeleton_code
                remaining_budget -= sym.skeleton_tokens
                summarized_cnt += 1
            else:
                # OMIT completely (referenced via master prompt vault_id)
                action = "OMIT"
                allocated_tok = 0
                content = ""
                omitted_cnt += 1

            # Point to primary actual prompt Vault ID
            vault_id = primary_vault_id

            decisions.append(AllocationDecision(
                symbol_name=sym.name,
                filepath=sym.filepath,
                action=action,
                relevance_score=rel,
                original_tokens=sym.full_tokens,
                allocated_tokens=allocated_tok,
                content=content,
                vault_id=vault_id,
            ))

        # 4. Context Assembly
        assembled_parts: list[str] = []

        # (a) User Request
        if decomposed.user_request:
            assembled_parts.append(f"## Task Request\n{decomposed.user_request}")

        # (b) Cleaned Logs (if any)
        if logs_text.strip():
            assembled_parts.append(f"## Execution / Log Context\n```log\n{logs_text.strip()}\n```")

        # (c) Codebase Context Grouped by File
        files_map: dict[str, list[AllocationDecision]] = {}
        for d in decisions:
            if d.action != "OMIT":
                fp = d.filepath or "code_context"
                files_map.setdefault(fp, []).append(d)

        if files_map:
            assembled_parts.append("## Codebase Context")
            for fp, file_decisions in files_map.items():
                assembled_parts.append(f"### File: `{fp}`")
                
                # Check file actions
                has_preserved = any(d.action == "PRESERVE" for d in file_decisions)
                
                for d in file_decisions:
                    if d.action == "PRESERVE":
                        assembled_parts.append(f"```\n{d.content}\n```")
                    elif d.action == "SUMMARIZE":
                        vault_hint = f" <!-- [Vault ID: {d.vault_id}] -->" if d.vault_id else ""
                        assembled_parts.append(f"```\n// Structural Skeleton: {d.symbol_name}{vault_hint}\n{d.content}\n```")

        # (d) Omitted symbols summary with retrieval vault pointers
        omitted_decisions = [d for d in decisions if d.action == "OMIT" and d.vault_id]
        if omitted_decisions:
            omitted_list = ", ".join(f"`{d.symbol_name}` ({d.vault_id})" for d in omitted_decisions[:10])
            assembled_parts.append(f"> [!NOTE]\n> Omitted background symbols ({len(omitted_decisions)}): {omitted_list}. Retrieve via `retrieve_original(id)` if needed.")

        final_compressed_text = "\n\n".join(assembled_parts)
        compressed_tokens = get_token_count(final_compressed_text)
        original_tokens = get_token_count(decomposed.raw_prompt)

        savings = 1.0 - (compressed_tokens / max(1, original_tokens))

        return OptimizedContextResult(
            compressed_text=final_compressed_text,
            original_tokens=original_tokens,
            compressed_tokens=compressed_tokens,
            budget_limit=budget,
            savings_ratio=round(max(0.0, savings), 4),
            decisions=decisions,
            preserved_count=preserved_cnt,
            summarized_count=summarized_cnt,
            omitted_count=omitted_cnt,
        )
