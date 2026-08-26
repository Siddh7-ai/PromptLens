from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Optional

from ..parser.ast_parser import CodeSymbol, ParsedCodeFile


@dataclass
class DependencyNode:
    symbol_name: str
    symbol: Optional[CodeSymbol] = None
    filepath: Optional[str] = None
    callees: list[str] = field(default_factory=list)  # Symbols this node calls
    callers: list[str] = field(default_factory=list)  # Symbols that call this node
    imported_modules: list[str] = field(default_factory=list)


@dataclass
class ExpandedNeighborhood:
    seed_symbols: list[str]
    expanded_symbols: dict[str, float]  # symbol_name -> proximity_score (1.0 = seed, 0.7 = 1-hop, etc.)
    included_files: set[str] = field(default_factory=set)


class DependencyGraph:
    """
    Constructs static call-graphs and import-graphs across parsed files
    and performs dependency expansion for task-aware context preservation.
    """

    def __init__(self):
        self.nodes: dict[str, DependencyNode] = {}
        self.symbol_lookup: dict[str, CodeSymbol] = {}
        self.file_to_symbols: dict[str, list[str]] = defaultdict(list)

    def build_from_files(self, parsed_files: list[ParsedCodeFile]) -> None:
        """Populates the dependency graph from parsed files and their AST symbols."""
        self.nodes.clear()
        self.symbol_lookup.clear()
        self.file_to_symbols.clear()

        # Step 1: Register all symbols
        for pf in parsed_files:
            for sym in pf.symbols:
                self.symbol_lookup[sym.name] = sym
                self.file_to_symbols[pf.filepath].append(sym.name)
                
                # Base function name (e.g. without class prefix)
                short_name = sym.name.split(".")[-1]
                if short_name not in self.symbol_lookup:
                    self.symbol_lookup[short_name] = sym

                if sym.name not in self.nodes:
                    self.nodes[sym.name] = DependencyNode(
                        symbol_name=sym.name,
                        symbol=sym,
                        filepath=pf.filepath,
                        imported_modules=list(pf.imports),
                    )

        # Step 2: Wire caller -> callee edges
        for pf in parsed_files:
            for sym in pf.symbols:
                node = self.nodes.get(sym.name)
                if not node:
                    continue

                for dep in sym.dependencies:
                    # Match against registered symbols
                    target_sym = self.symbol_lookup.get(dep)
                    target_name = target_sym.name if target_sym else dep

                    if target_name not in node.callees:
                        node.callees.append(target_name)

                    # Wire reverse edge (caller)
                    if target_name in self.nodes:
                        if sym.name not in self.nodes[target_name].callers:
                            self.nodes[target_name].callers.append(sym.name)

    def expand_neighborhood(
        self,
        seed_symbols: list[str],
        max_hops: int = 2,
        hop_decay: float = 0.7
    ) -> ExpandedNeighborhood:
        """
        Expands around seed symbols up to max_hops in the dependency graph.
        Returns a map of symbol_name -> proximity score (1.0 down to decay^hops).
        """
        proximity: dict[str, float] = {}
        included_files: set[str] = set()
        queue: deque[tuple[str, int, float]] = deque()

        resolved_seeds = []
        for seed in seed_symbols:
            # Check direct match or short name match
            matched_sym = self.symbol_lookup.get(seed)
            name = matched_sym.name if matched_sym else seed
            resolved_seeds.append(name)
            queue.append((name, 0, 1.0))
            proximity[name] = 1.0
            if matched_sym and matched_sym.filepath:
                included_files.add(matched_sym.filepath)

        visited = set(resolved_seeds)

        while queue:
            curr_sym, hops, curr_score = queue.popleft()

            if hops >= max_hops:
                continue

            node = self.nodes.get(curr_sym)
            if not node:
                continue

            next_score = curr_score * hop_decay

            # 1. Expand downstream callees (what this symbol depends on)
            for callee in node.callees:
                if callee not in visited:
                    visited.add(callee)
                    proximity[callee] = max(proximity.get(callee, 0.0), next_score)
                    queue.append((callee, hops + 1, next_score))
                    
                    callee_sym = self.symbol_lookup.get(callee)
                    if callee_sym and callee_sym.filepath:
                        included_files.add(callee_sym.filepath)

            # 2. Expand upstream callers (what calls this symbol) with a lower weight
            caller_score = next_score * 0.8
            for caller in node.callers:
                if caller not in visited:
                    visited.add(caller)
                    proximity[caller] = max(proximity.get(caller, 0.0), caller_score)
                    queue.append((caller, hops + 1, caller_score))
                    
                    caller_sym = self.symbol_lookup.get(caller)
                    if caller_sym and caller_sym.filepath:
                        included_files.add(caller_sym.filepath)

        return ExpandedNeighborhood(
            seed_symbols=resolved_seeds,
            expanded_symbols=proximity,
            included_files=included_files,
        )
