"""
Unit tests for CodeCompressor.
Covers: small code, large code, Python, JavaScript, TypeScript, Java, C++, invalid code.
"""
import pytest
from src.compress.code_compressor import CodeCompressor
from src.store.retrieval_store import RetrievalStore


@pytest.fixture
def store():
    return RetrievalStore(ttl_seconds=3600)


@pytest.fixture
def code_compressor(store):
    return CodeCompressor(min_lines_threshold=10, min_tokens_threshold=40, store=store)


def test_small_code_passes_intact(code_compressor):
    small_code = "def add(a, b):\n    return a + b\n"
    res = code_compressor.compress(small_code)
    assert not res.is_compressed
    assert res.compressed_code == small_code
    assert res.savings_pct == 0.0


def test_python_large_code_compression(code_compressor, store):
    python_code = """
import os
import sys

class DataPipeline:
    \"\"\"Processes user event streams.\"\"\"
    def __init__(self, config):
        self.config = config
        self.active = True

    def process_events(self, events):
        \"\"\"Batch event processor with validation.\"\"\"
        results = []
        for event in events:
            if not event.get("valid"):
                continue
            normalized = event.get("data", "").strip().lower()
            timestamp = event.get("ts", 0)
            status = "processed"
            results.append({"status": status, "payload": normalized})
        return results

    def shutdown(self):
        self.active = False
        return True
"""
    res = code_compressor.compress(python_code)
    assert res.is_compressed
    assert res.savings_pct > 0
    assert "class DataPipeline:" in res.compressed_code
    assert "def process_events" in res.compressed_code
    assert "Processes user event streams" in res.compressed_code
    assert res.retrieval_id is not None
    # Verify retrieval
    original = store.get(res.retrieval_id)
    assert original == python_code


def test_javascript_typescript_compression(code_compressor):
    ts_code = """
import { Request, Response } from 'express';

export interface UserPayload {
    id: string;
    email: string;
    role: string;
}

export class AuthController {
    public async login(req: Request, res: Response): Promise<void> {
        const { username, password } = req.body;
        if (!username || !password) {
            res.status(400).json({ error: 'Missing credentials' });
            return;
        }
        const user = await database.findUser(username);
        const valid = await bcrypt.compare(password, user.passwordHash);
        if (!valid) {
            res.status(401).json({ error: 'Unauthorized' });
            return;
        }
        res.json({ token: 'jwt-xyz' });
    }
}
"""
    res = code_compressor.compress(ts_code)
    assert res.is_compressed
    assert "AuthController" in res.compressed_code
    assert "login(" in res.compressed_code
    assert res.language_detected in ("typescript", "javascript")


def test_java_code_compression(code_compressor):
    java_code = """
package com.promptlens.service;

import java.util.List;
import java.util.ArrayList;

public class OrderService {
    private final String endpoint;

    public OrderService(String endpoint) {
        this.endpoint = endpoint;
    }

    public List<String> processOrders(List<String> rawOrders) {
        List<String> completed = new ArrayList<>();
        for (String order : rawOrders) {
            if (order != null && !order.isEmpty()) {
                String sanitized = order.trim();
                completed.add(sanitized);
            }
        }
        return completed;
    }
}
"""
    res = code_compressor.compress(java_code)
    assert res.is_compressed
    assert "public class OrderService" in res.compressed_code
    assert "processOrders" in res.compressed_code
    assert res.language_detected == "java"


def test_cpp_code_compression(code_compressor):
    cpp_code = """
#include <iostream>
#include <vector>
#include <string>

namespace promptlens {
    class MatrixEngine {
    public:
        void compute(const std::vector<int>& data) {
            int sum = 0;
            for (auto v : data) {
                sum += v * 2;
                if (sum > 1000) {
                    sum = 1000;
                }
            }
            std::cout << sum << std::endl;
        }
    };
}
"""
    res = code_compressor.compress(cpp_code)
    assert res.is_compressed
    assert "class MatrixEngine" in res.compressed_code
    assert res.language_detected == "cpp"


def test_invalid_syntax_code_fails_open(code_compressor):
    invalid_garbage = "def @@@ invalid !!! ((((())) {}{}{}:;:; class ????"
    res = code_compressor.compress(invalid_garbage)
    # Fails open: returns original without raising exception
    assert res.compressed_code == invalid_garbage
