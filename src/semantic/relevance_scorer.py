import re
from dataclasses import dataclass
from typing import Optional

from ..classifier.task_classifier import DecomposedPrompt, TaskCategory
from ..graph.dependency_graph import ExpandedNeighborhood
from ..parser.ast_parser import CodeSymbol, SymbolKind
from .embedder import LightweightEmbedder


@dataclass
class ScoredSymbol:
    symbol: CodeSymbol
    semantic_score: float
    dependency_score: float
    task_prior_score: float
    total_relevance: float
    recommended_action: str  # "PRESERVE", "SUMMARIZE", or "OMIT"


class RelevanceScorer:
    """
    Computes composite task-aware relevance for code symbols by combining:
    1. Semantic similarity against the user query (Embeddings)
    2. Static Call/Import Dependency Proximity (Dependency Graph)
    3. Task-specific priors and heuristics (Task Classifier)
    """

    def __init__(self, embedder: Optional[LightweightEmbedder] = None):
        self.embedder = embedder or LightweightEmbedder()

    def score_symbols(
        self,
        symbols: list[CodeSymbol],
        decomposed: DecomposedPrompt,
        neighborhood: Optional[ExpandedNeighborhood] = None,
    ) -> list[ScoredSymbol]:
        results: list[ScoredSymbol] = []
        user_req = decomposed.user_request
        category = decomposed.task_category
        detected_symbols_lower = [s.lower() for s in decomposed.detected_symbols]
        detected_files_lower = [f.lower() for f in decomposed.detected_files]

        dep_scores = neighborhood.expanded_symbols if neighborhood else {}

        # Set task-specific weights
        w_sem = 0.45
        w_dep = 0.35
        w_prior = 0.20

        if category == TaskCategory.DEBUGGING:
            w_sem = 0.50
            w_dep = 0.30
            w_prior = 0.20
        elif category == TaskCategory.REFACTORING or category == TaskCategory.CODE_EXPLANATION:
            w_sem = 0.30
            w_dep = 0.50
            w_prior = 0.20
        elif category == TaskCategory.CODE_REVIEW:
            w_sem = 0.40
            w_dep = 0.20
            w_prior = 0.40

        for sym in symbols:
            # 1. Semantic Similarity
            # Embed signature + docstring + body preview
            sym_text = f"{sym.name} {sym.signature} {sym.docstring or ''} {sym.full_code[:200]}"
            sem_score = self.embedder.compute_similarity(user_req, sym_text)

            # 2. Dependency Graph Score
            dep_score = dep_scores.get(sym.name, 0.0)
            short_name = sym.name.split(".")[-1]
            if dep_score == 0.0 and short_name in dep_scores:
                dep_score = dep_scores[short_name]

            # 3. Task Prior & Mention Bonus
            prior_score = 0.0

            # Explicit symbol name mention bonus
            if short_name.lower() in detected_symbols_lower or sym.name.lower() in detected_symbols_lower:
                prior_score += 0.8

            # File path match bonus
            if sym.filepath and any(df in sym.filepath.lower() for df in detected_files_lower):
                prior_score += 0.4

            # Category-specific heuristics
            if category == TaskCategory.CODE_REVIEW:
                # Security keywords
                sec_kw = ("auth", "token", "password", "hash", "secret", "validate", "sanitize", "sql", "query", "jwt", "crypto", "permission")
                if any(kw in sym.full_code.lower() for kw in sec_kw):
                    prior_score += 0.5

            elif category == TaskCategory.TEST_GENERATION:
                # Public functions or API routes
                if sym.kind in (SymbolKind.ROUTE, SymbolKind.FUNCTION) and not sym.name.startswith("_"):
                    prior_score += 0.4

            elif category == TaskCategory.DEBUGGING:
                # If error traces mention the function or file
                if any(err_log in sym.full_code for err_log in decomposed.log_blocks):
                    prior_score += 0.6

            # Cap prior at 1.0
            prior_score = min(1.0, prior_score)

            # Direct seed / target override
            if short_name.lower() in detected_symbols_lower:
                total_relevance = max(0.95, round(w_sem * sem_score + w_dep * dep_score + w_prior * prior_score, 4))
            else:
                total_relevance = round(w_sem * sem_score + w_dep * dep_score + w_prior * prior_score, 4)

            # Initial recommended action
            if total_relevance >= 0.70:
                action = "PRESERVE"
            elif total_relevance >= 0.25 or dep_score > 0.0:
                action = "SUMMARIZE"
            else:
                action = "OMIT"

            results.append(ScoredSymbol(
                symbol=sym,
                semantic_score=round(sem_score, 3),
                dependency_score=round(dep_score, 3),
                task_prior_score=round(prior_score, 3),
                total_relevance=round(total_relevance, 3),
                recommended_action=action,
            ))

        # Sort by total relevance descending
        results.sort(key=lambda s: s.total_relevance, reverse=True)
        return results
