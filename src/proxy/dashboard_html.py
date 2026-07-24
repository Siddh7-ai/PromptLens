DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PromptLens | LLM Context Optimization Dashboard</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    fontFamily: {
                        sans: ['Inter', 'sans-serif'],
                        mono: ['JetBrains Mono', 'monospace'],
                    },
                    colors: {
                        brand: {
                            50: '#eef2ff',
                            400: '#818cf8',
                            500: '#6366f1',
                            600: '#4f46e5',
                            900: '#1e1b4b',
                        },
                        dark: {
                            bg: '#080c14',
                            card: '#0f172a',
                            border: '#1e293b',
                            muted: '#64748b'
                        }
                    }
                }
            }
        }
    </script>
    <style>
        body {
            background-color: #080c14;
            color: #f8fafc;
            font-family: 'Inter', sans-serif;
        }
        .glass-card {
            background: rgba(15, 23, 42, 0.75);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .glow-indigo {
            box-shadow: 0 0 30px -5px rgba(99, 102, 241, 0.25);
        }
        .glow-emerald {
            box-shadow: 0 0 30px -5px rgba(16, 185, 129, 0.25);
        }
        .pulse-dot {
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.4; transform: scale(0.9); }
        }
    </style>
</head>
<body class="min-h-screen pb-12">
    <!-- Navbar -->
    <header class="border-b border-slate-800/80 bg-slate-950/60 sticky top-0 z-50 backdrop-blur-md">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <div class="flex items-center space-x-3">
                <div class="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-cyan-400 p-0.5 shadow-lg shadow-indigo-500/20">
                    <div class="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                        <svg class="w-5 h-5 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/>
                        </svg>
                    </div>
                </div>
                <div>
                    <div class="flex items-center space-x-2">
                        <span class="font-bold text-lg tracking-tight text-white">PromptLens</span>
                        <span class="px-2 py-0.5 text-xs font-semibold rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">v0.1.0</span>
                    </div>
                    <p class="text-xs text-slate-400">Context Optimization Layer for AI Coding Agents</p>
                </div>
            </div>

            <!-- Status Indicator -->
            <div class="flex items-center space-x-4">
                <div class="flex items-center space-x-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-medium">
                    <span class="w-2 h-2 rounded-full bg-emerald-400 pulse-dot"></span>
                    <span>PROXY ACTIVE</span>
                </div>
                <div class="text-xs text-slate-400 font-mono hidden md:block">
                    Target: <span id="target-url" class="text-slate-200">https://api.anthropic.com</span>
                </div>
            </div>
        </div>
    </header>

    <!-- Main Container -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">
        
        <!-- Hero Summary Header -->
        <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div>
                <h1 class="text-2xl sm:text-3xl font-bold tracking-tight text-white">Live Savings Dashboard</h1>
                <p class="text-slate-400 text-sm mt-1">Real-time token reduction, rule-based compression metrics, and reversible vault storage.</p>
            </div>
            <div class="flex items-center space-x-3">
                <button onclick="fetchStats()" class="px-4 py-2 rounded-lg text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center space-x-2">
                    <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
                    </svg>
                    <span>Refresh Data</span>
                </button>
            </div>
        </div>

        <!-- Metric Cards Grid -->
        <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <!-- Card 1: Total Tokens Saved -->
            <div class="glass-card rounded-2xl p-5 glow-indigo relative overflow-hidden">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Tokens Saved</span>
                    <span class="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/>
                        </svg>
                    </span>
                </div>
                <div class="mt-4 flex items-baseline justify-between">
                    <span id="stat-tokens-saved" class="text-3xl font-bold font-mono tracking-tight text-white">0</span>
                    <span id="stat-savings-pct" class="text-xs font-bold px-2 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">+0.0%</span>
                </div>
                <p class="text-xs text-slate-400 mt-2">Cut from LLM context window</p>
            </div>

            <!-- Card 2: Estimated USD Saved -->
            <div class="glass-card rounded-2xl p-5 glow-emerald relative overflow-hidden">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Estimated Money Saved</span>
                    <span class="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                    </span>
                </div>
                <div class="mt-4">
                    <span id="stat-usd-saved" class="text-3xl font-bold font-mono tracking-tight text-emerald-400">$0.0000</span>
                </div>
                <p class="text-xs text-slate-400 mt-2">Based on $3.00/1M input tokens</p>
            </div>

            <!-- Card 3: Vault Items -->
            <div class="glass-card rounded-2xl p-5 relative overflow-hidden">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Reversible Vault Items</span>
                    <span class="p-2 rounded-lg bg-violet-500/10 text-violet-400">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 4H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-2m-4-1v8m0 0l3-3m-3 3L9 8m-5 5h2.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293h3.172a1 1 0 00.707-.293l2.414-2.414a1 1 0 01.707-.293H20"/>
                        </svg>
                    </span>
                </div>
                <div class="mt-4">
                    <span id="stat-vault-items" class="text-3xl font-bold font-mono tracking-tight text-white">0</span>
                </div>
                <p class="text-xs text-slate-400 mt-2">Active original payloads stored</p>
            </div>

            <!-- Card 4: Requests & Retrievals -->
            <div class="glass-card rounded-2xl p-5 relative overflow-hidden">
                <div class="flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider">Requests & Retrievals</span>
                    <span class="p-2 rounded-lg bg-cyan-500/10 text-cyan-400">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>
                        </svg>
                    </span>
                </div>
                <div class="mt-4 flex items-baseline justify-between">
                    <span id="stat-requests" class="text-3xl font-bold font-mono tracking-tight text-white">0</span>
                    <span id="stat-retrievals" class="text-xs font-bold px-2.5 py-1 rounded-md bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">0 fetches</span>
                </div>
                <p class="text-xs text-slate-400 mt-2">Proxied requests / tool retrievals</p>
            </div>
        </div>

        <!-- Token Reduction Visual Progress Bar -->
        <div class="glass-card rounded-2xl p-6 space-y-4">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div>
                    <h2 class="text-base font-semibold text-white">Context Optimization Ratio</h2>
                    <p class="text-xs text-slate-400">Comparison between baseline incoming tokens and compressed prompt payload.</p>
                </div>
                <div class="text-xs font-mono text-slate-300">
                    Baseline: <span id="bar-baseline-tokens" class="text-slate-400 font-bold">0</span> tokens | Compressed: <span id="bar-compressed-tokens" class="text-indigo-400 font-bold">0</span> tokens
                </div>
            </div>

            <!-- Multi-layered Progress Bar -->
            <div class="w-full bg-slate-800/80 rounded-xl h-5 p-1 relative overflow-hidden flex items-center">
                <div id="progress-bar-compressed" class="bg-gradient-to-r from-indigo-500 to-cyan-400 h-full rounded-lg transition-all duration-500" style="width: 0%;"></div>
            </div>
            <div class="flex items-center justify-between text-xs text-slate-400">
                <span>0%</span>
                <span class="font-medium text-slate-300">Current Token Compression Efficiency: <strong id="progress-bar-label" class="text-emerald-400">0%</strong></span>
                <span>100%</span>
            </div>
        </div>

        <!-- 5-Task Benchmark Results Table (Mission 8 Feature) -->
        <div class="glass-card rounded-2xl p-6 space-y-4">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-base font-semibold text-white">5-Task Benchmark Comparison Suite</h2>
                    <p class="text-xs text-slate-400">Pre-computed token savings across 5 representative real-world AI agent tool outputs.</p>
                </div>
                <span class="text-xs font-semibold px-2.5 py-1 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">5 / 5 Tasks Passing</span>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                    <thead class="text-slate-400 uppercase tracking-wider border-b border-slate-800 bg-slate-900/50">
                        <tr>
                            <th class="py-3 px-4">Benchmark Scenario</th>
                            <th class="py-3 px-4">Content Category</th>
                            <th class="py-3 px-4 text-right">Baseline Tokens</th>
                            <th class="py-3 px-4 text-right">Compressed Tokens</th>
                            <th class="py-3 px-4 text-right">Token Reduction</th>
                            <th class="py-3 px-4 text-center">Correctness</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-slate-800/60 font-mono text-slate-300">
                        <tr class="hover:bg-slate-800/30 transition">
                            <td class="py-3 px-4 font-sans font-medium text-white">1. Python Pytest Failure Trace</td>
                            <td class="py-3 px-4 font-sans text-slate-400">Stack Trace / Logs</td>
                            <td class="py-3 px-4 text-right">896</td>
                            <td class="py-3 px-4 text-right text-indigo-400 font-bold">238</td>
                            <td class="py-3 px-4 text-right text-emerald-400 font-bold">73.4%</td>
                            <td class="py-3 px-4 text-center"><span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">100% Pass</span></td>
                        </tr>
                        <tr class="hover:bg-slate-800/30 transition">
                            <td class="py-3 px-4 font-sans font-medium text-white">2. Large JSON REST API Array</td>
                            <td class="py-3 px-4 font-sans text-slate-400">JSON Payload</td>
                            <td class="py-3 px-4 text-right">104,569</td>
                            <td class="py-3 px-4 text-right text-indigo-400 font-bold">501</td>
                            <td class="py-3 px-4 text-right text-emerald-400 font-bold">99.5%</td>
                            <td class="py-3 px-4 text-center"><span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">100% Pass</span></td>
                        </tr>
                        <tr class="hover:bg-slate-800/30 transition">
                            <td class="py-3 px-4 font-sans font-medium text-white">3. Git Diff Patch Output</td>
                            <td class="py-3 px-4 font-sans text-slate-400">Version Control Diff</td>
                            <td class="py-3 px-4 text-right">473</td>
                            <td class="py-3 px-4 text-right text-indigo-400 font-bold">189</td>
                            <td class="py-3 px-4 text-right text-emerald-400 font-bold">60.0%</td>
                            <td class="py-3 px-4 text-center"><span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">100% Pass</span></td>
                        </tr>
                        <tr class="hover:bg-slate-800/30 transition">
                            <td class="py-3 px-4 font-sans font-medium text-white">4. NPM Build Log Errors</td>
                            <td class="py-3 px-4 font-sans text-slate-400">Compiler / Build Log</td>
                            <td class="py-3 px-4 text-right">265</td>
                            <td class="py-3 px-4 text-right text-indigo-400 font-bold">159</td>
                            <td class="py-3 px-4 text-right text-emerald-400 font-bold">40.0%</td>
                            <td class="py-3 px-4 text-center"><span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">100% Pass</span></td>
                        </tr>
                        <tr class="hover:bg-slate-800/30 transition">
                            <td class="py-3 px-4 font-sans font-medium text-white">5. Environment & File Tree Read</td>
                            <td class="py-3 px-4 font-sans text-slate-400">System Environment</td>
                            <td class="py-3 px-4 text-right">753</td>
                            <td class="py-3 px-4 text-right text-indigo-400 font-bold">82</td>
                            <td class="py-3 px-4 text-right text-emerald-400 font-bold">89.1%</td>
                            <td class="py-3 px-4 text-center"><span class="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">100% Pass</span></td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Recent Activity Stream -->
        <div class="glass-card rounded-2xl p-6 space-y-4">
            <div class="flex items-center justify-between">
                <div>
                    <h2 class="text-base font-semibold text-white">Recent Proxied Requests Stream</h2>
                    <p class="text-xs text-slate-400">Live request audit trail passing through the local proxy.</p>
                </div>
                <span class="text-xs text-slate-400 font-mono">Auto-updates live</span>
            </div>

            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                    <thead class="text-slate-400 uppercase tracking-wider border-b border-slate-800 bg-slate-900/50">
                        <tr>
                            <th class="py-3 px-4">Time</th>
                            <th class="py-3 px-4">Method & Path</th>
                            <th class="py-3 px-4 text-right">Baseline Tokens</th>
                            <th class="py-3 px-4 text-right">Compressed Tokens</th>
                            <th class="py-3 px-4 text-right">Savings</th>
                            <th class="py-3 px-4 text-center">Vault Hash ID</th>
                        </tr>
                    </thead>
                    <tbody id="logs-table-body" class="divide-y divide-slate-800/60 font-mono text-slate-300">
                        <tr>
                            <td colspan="6" class="py-6 text-center text-slate-500 font-sans">No requests proxied yet. Run an agent or test request to view live stream.</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>

    </main>

    <script>
        async function fetchStats() {
            try {
                const resp = await fetch('/api/stats');
                if (!resp.ok) return;
                const data = await resp.json();

                document.getElementById('stat-tokens-saved').innerText = data.total_tokens_saved.toLocaleString();
                document.getElementById('stat-savings-pct').innerText = '+' + data.overall_savings_pct + '%';
                document.getElementById('stat-usd-saved').innerText = '$' + data.estimated_usd_saved.toFixed(4);
                document.getElementById('stat-vault-items').innerText = data.recent_requests.filter(r => r.retrieval_id !== '-').length;
                document.getElementById('stat-requests').innerText = data.total_requests;
                document.getElementById('stat-retrievals').innerText = data.total_retrievals + ' fetches';

                document.getElementById('bar-baseline-tokens').innerText = data.total_baseline_tokens.toLocaleString();
                document.getElementById('bar-compressed-tokens').innerText = data.total_compressed_tokens.toLocaleString();
                document.getElementById('progress-bar-compressed').style.width = data.overall_savings_pct + '%';
                document.getElementById('progress-bar-label').innerText = data.overall_savings_pct + '%';

                const tbody = document.getElementById('logs-table-body');
                if (data.recent_requests.length === 0) {
                    tbody.innerHTML = '<tr><td colspan="6" class="py-6 text-center text-slate-500 font-sans">No requests proxied yet. Run an agent or test request to view live stream.</td></tr>';
                } else {
                    tbody.innerHTML = data.recent_requests.map(req => `
                        <tr class="hover:bg-slate-800/30 transition">
                            <td class="py-3 px-4 font-sans text-slate-400">${req.timestamp}</td>
                            <td class="py-3 px-4 font-sans font-medium text-white"><span class="px-1.5 py-0.5 rounded bg-slate-800 text-indigo-400 text-[10px] mr-1.5">${req.method}</span>${req.path}</td>
                            <td class="py-3 px-4 text-right">${req.baseline_tokens.toLocaleString()}</td>
                            <td class="py-3 px-4 text-right text-indigo-400 font-bold">${req.compressed_tokens.toLocaleString()}</td>
                            <td class="py-3 px-4 text-right text-emerald-400 font-bold">${req.savings_pct}%</td>
                            <td class="py-3 px-4 text-center font-mono text-xs text-slate-400">${req.retrieval_id}</td>
                        </tr>
                    `).join('');
                }
            } catch (err) {
                console.error('Failed to fetch stats:', err);
            }
        }

        // Auto refresh stats every 3 seconds
        setInterval(fetchStats, 3000);
        fetchStats();
    </script>
</body>
</html>
"""
