import os
import sys
import time
from typing import Any

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.classifier.task_classifier import TaskClassifier
from src.compress.pipeline import PromptLensPipeline
from src.compress.text_compressor import compress_text
from src.utils.token_utils import get_token_count


BENCHMARK_PROMPTS = [
    {
        "id": "task_1_auth_mod",
        "title": "Code Modification: Add JWT Auth",
        "prompt": """
Add JWT authentication to the login and user routes.

```javascript
// filepath: routes/user.js
const express = require('express');
const router = express.Router();
const User = require('../models/user');

router.post('/login', async (req, res) => {
    const { email, password } = req.body;
    const user = await User.findOne({ email });
    if (!user || user.password !== password) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    return res.json({ success: true, user });
});

router.get('/profile', async (req, res) => {
    const user = await User.findById(req.query.id);
    res.json(user);
});

module.exports = router;
```

```javascript
// filepath: models/user.js
const mongoose = require('mongoose');

const UserSchema = new mongoose.Schema({
    email: { type: String, required: true },
    password: { type: String, required: true },
    name: String,
    role: { type: String, default: 'user' }
});

module.exports = mongoose.model('User', UserSchema);
```

```javascript
// filepath: utils/analytics.js
// 150 lines of background analytics tracking
function trackPageView(page, user) {
    console.log('page view tracked', page, user);
}
function trackEvent(evt, data) {
    console.log('event', evt, data);
}
module.exports = { trackPageView, trackEvent };
```
"""
    },
    {
        "id": "task_2_debug_err",
        "title": "Debugging: NullPointer Exception",
        "prompt": """
Why am I getting this TypeError: Cannot read property 'map' of undefined in StudentList?

```javascript
// filepath: components/StudentList.jsx
import React, { useEffect, useState } from 'react';
import { fetchStudents } from '../api/studentApi';

export function StudentList() {
    const [data, setData] = useState();

    useEffect(() => {
        fetchStudents().then(res => setData(res.data));
    }, []);

    return (
        <div className="student-list">
            <h2>Enrolled Students</h2>
            <ul>
                {data.items.map(s => (
                    <li key={s.id}>{s.name} - Grade: {s.grade}</li>
                ))}
            </ul>
        </div>
    );
}
```

```log
[ERROR] Uncaught TypeError: Cannot read properties of undefined (reading 'map')
    at StudentList (StudentList.jsx:14)
    at renderWithHooks (react-dom.development.js:14985)
    at mountIndeterminateComponent (react-dom.development.js:17811)
```
"""
    },
    {
        "id": "task_3_refactor_solid",
        "title": "Refactoring: SOLID Architecture",
        "prompt": """
Refactor this student management class to follow Single Responsibility and Open-Closed principles.

```python
# filepath: student_manager.py
class StudentManager:
    def __init__(self, db_conn):
        self.db = db_conn

    def register_student(self, name: str, email: str, major: str):
        # Validation logic
        if "@" not in email:
            raise ValueError("Invalid email format")
        
        # Persistence logic
        query = f"INSERT INTO students (name, email, major) VALUES ('{name}', '{email}', '{major}')"
        self.db.execute(query)

        # Email notification logic
        import smtplib
        server = smtplib.SMTP('smtp.school.edu')
        server.sendmail("admin@school.edu", email, f"Welcome {name}!")

        # Report generation logic
        with open("daily_report.txt", "a") as f:
            f.write(f"Registered {name} ({major})\n")
```
"""
    }
]


def run_head_tail_compression(prompt: str, lines_keep: int = 10) -> str:
    lines = prompt.splitlines()
    if len(lines) <= lines_keep * 2:
        return prompt
    head = "\n".join(lines[:lines_keep])
    tail = "\n".join(lines[-lines_keep:])
    return f"{head}\n\n... [TRUNCATED {len(lines) - lines_keep * 2} LINES] ...\n\n{tail}"


def evaluate_all():
    pipeline = PromptLensPipeline(default_budget=2000)
    print("=" * 90)
    print(f"{'PROMPTLENS MULTI-STAGE COMPRESSION BENCHMARK':^90}")
    print("=" * 90)
    print(f"{'Task ID':<22} | {'Method / Stage':<28} | {'Orig Tok':<9} | {'Comp Tok':<9} | {'Savings %':<10} | {'Latency':<8}")
    print("-" * 90)

    summary_stats: dict[str, list[float]] = {
        "Baseline 0: No Compression": [],
        "Baseline 1: Head-Tail Slice": [],
        "PromptLens v1: Rule-Based": [],
        "PromptLens v2: AST Skeletons": [],
        "PromptLens v4: Task+Dep Aware": [],
        "PromptLens v5: Budget Knapsack": [],
    }

    for task in BENCHMARK_PROMPTS:
        raw = task["prompt"]
        orig_tokens = get_token_count(raw)

        # Baseline 0: No compression
        b0_toks = orig_tokens
        summary_stats["Baseline 0: No Compression"].append(0.0)
        print(f"{task['id']:<22} | {'Baseline 0 (No Comp)':<28} | {orig_tokens:<9} | {b0_toks:<9} | {'0.0%':<10} | {'0.0ms':<8}")

        # Baseline 1: Head/Tail slice
        t0 = time.perf_counter()
        ht_text = run_head_tail_compression(raw, lines_keep=8)
        ht_toks = get_token_count(ht_text)
        ht_lat = (time.perf_counter() - t0) * 1000
        ht_sav = (1.0 - (ht_toks / orig_tokens)) * 100
        summary_stats["Baseline 1: Head-Tail Slice"].append(ht_sav)
        print(f"{task['id']:<22} | {'Baseline 1 (Head-Tail)':<28} | {orig_tokens:<9} | {ht_toks:<9} | {f'{ht_sav:.1f}%':<10} | {f'{ht_lat:.1f}ms':<8}")

        # PromptLens v1: Rule-based
        t0 = time.perf_counter()
        v1_res = pipeline.compress(raw, mode="v1")
        v1_lat = (time.perf_counter() - t0) * 1000
        v1_sav = v1_res.total_savings_pct
        summary_stats["PromptLens v1: Rule-Based"].append(v1_sav)
        print(f"{task['id']:<22} | {'PromptLens v1 (Rule-Based)':<28} | {orig_tokens:<9} | {v1_res.compressed_tokens:<9} | {f'{v1_sav:.1f}%':<10} | {f'{v1_lat:.1f}ms':<8}")

        # PromptLens v2: AST Skeletons
        t0 = time.perf_counter()
        v2_res = pipeline.compress(raw, mode="v2")
        v2_lat = (time.perf_counter() - t0) * 1000
        v2_sav = v2_res.total_savings_pct
        summary_stats["PromptLens v2: AST Skeletons"].append(v2_sav)
        print(f"{task['id']:<22} | {'PromptLens v2 (AST Skeletons)':<28} | {orig_tokens:<9} | {v2_res.compressed_tokens:<9} | {f'{v2_sav:.1f}%':<10} | {f'{v2_lat:.1f}ms':<8}")

        # PromptLens v4: Task + Dependency-aware
        t0 = time.perf_counter()
        v4_res = pipeline.compress(raw, mode="v4")
        v4_lat = (time.perf_counter() - t0) * 1000
        v4_sav = v4_res.total_savings_pct
        summary_stats["PromptLens v4: Task+Dep Aware"].append(v4_sav)
        print(f"{task['id']:<22} | {'PromptLens v4 (Task+Dep)':<28} | {orig_tokens:<9} | {v4_res.compressed_tokens:<9} | {f'{v4_sav:.1f}%':<10} | {f'{v4_lat:.1f}ms':<8}")

        # PromptLens v5: Budget Knapsack
        t0 = time.perf_counter()
        v5_res = pipeline.compress(raw, mode="v5", budget=300)
        v5_lat = (time.perf_counter() - t0) * 1000
        v5_sav = v5_res.total_savings_pct
        summary_stats["PromptLens v5: Budget Knapsack"].append(v5_sav)
        print(f"{task['id']:<22} | {'PromptLens v5 (Budget Opt)':<28} | {orig_tokens:<9} | {v5_res.compressed_tokens:<9} | {f'{v5_sav:.1f}%':<10} | {f'{v5_lat:.1f}ms':<8}")
        print("-" * 90)

    print("\n" + "=" * 90)
    print(f"{'OVERALL AVERAGE SAVINGS ACROSS TASKS':^90}")
    print("=" * 90)
    for method, scores in summary_stats.items():
        avg = sum(scores) / len(scores)
        print(f"• {method:<35} : {avg:>6.2f}% average token reduction")
    print("=" * 90)


if __name__ == "__main__":
    evaluate_all()
