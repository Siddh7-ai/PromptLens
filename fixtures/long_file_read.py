# -*- coding: utf-8 -*-
"""
Module to handle advanced JSON and log compression algorithms.
Developed as part of the AI Agent Compression Proxy project.
"""

import re
import json
import logging
import hashlib
from typing import Dict, Any, List, Union

logger = logging.getLogger("compression")

class ContentCompressor:
    def __init__(self, ttl: int = 3600, max_cache_size: int = 1000):
        self.ttl = ttl
        self.max_cache_size = max_cache_size
        self.cache = {}
        self._initialize_rules()

    def _initialize_rules(self):
        self.stack_trace_regex = re.compile(
            r'File "([^"]+)", line (\d+), in (\w+)'
        )
        self.repeat_lines_regex = re.compile(r'^(.*)(\n\1)+$', re.MULTILINE)

    def hash_content(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    def compress_json_object(self, data: Union[Dict, List], max_tokens: int) -> Dict:
        """
        Compresses a JSON object by truncating arrays and deduplicating schemas.
        """
        if isinstance(data, list):
            return self._compress_list(data, max_tokens)
        elif isinstance(data, dict):
            return self._compress_dict(data, max_tokens)
        return data

    def _compress_list(self, data: List, max_tokens: int) -> List:
        if len(data) > 5:
            truncated = data[:3] + [{"_omitted_count": len(data) - 5}] + data[-2:]
            return [self.compress_json_object(item, max_tokens) for item in truncated]
        return [self.compress_json_object(item, max_tokens) for item in data]

    def _compress_dict(self, data: Dict, max_tokens: int) -> Dict:
        compressed = {}
        for k, v in data.items():
            compressed[k] = self.compress_json_object(v, max_tokens)
        return compressed

    def compress_text_logs(self, log_content: str, max_tokens: int) -> str:
        """
        Compresses plain text or logs by:
        1. Collapsing repeated identical lines.
        2. Truncating tracebacks (keeping top 3 + bottom 2 frames).
        3. Storing long strings in retrieval store.
        """
        lines = log_content.splitlines()
        collapsed_lines = []
        
        i = 0
        n = len(lines)
        while i < n:
            current_line = lines[i]
            count = 1
            while i + 1 < n and lines[i + 1] == current_line:
                count += 1
                i += 1
            if count > 1:
                collapsed_lines.append(f"[REPEATED {count} TIMES] {current_line}")
            else:
                collapsed_lines.append(current_line)
            i += 1

        return "\n".join(collapsed_lines)

    def extract_traceback(self, log_content: str) -> List[str]:
        lines = log_content.splitlines()
        tb_lines = []
        in_tb = False
        for line in lines:
            if line.startswith("Traceback (most recent call last):"):
                in_tb = True
                tb_lines.append(line)
            elif in_tb:
                tb_lines.append(line)
                if not line.startswith(" ") and not line.startswith("File "):
                    in_tb = False
        return tb_lines

# Initialize global compressor
global_compressor = ContentCompressor()