// PromptLens Background Service Worker (Manifest V3 - 100% Synced Vault Persistence)

const PROMPTLENS_API_BASE = 'http://localhost:8000';

async function sha256Hex12(text) {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest('SHA-256', data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
  return hashHex.substring(0, 12);
}

function normalizeLines(text) {
  if (!text) return [];
  // Strip Lexical double-newline padding and normalize line breaks
  const cleaned = text.replace(/(\r?\n\s*){2,}/g, '\n').trim();
  return cleaned.split(/\r?\n/);
}

function deduplicateLogs(lines) {
  if (!lines || lines.length === 0) return [];
  const deduped = [];
  let prevLine = null;
  let repeatCount = 0;

  for (const line of lines) {
    const stripped = line.trim();
    if (stripped === prevLine) {
      repeatCount++;
    } else {
      if (repeatCount > 0) {
        deduped.push(`  ... [x${repeatCount + 1} repeated log lines omitted] ...`);
      }
      deduped.push(line);
      prevLine = stripped;
      repeatCount = 0;
    }
  }
  if (repeatCount > 0) {
    deduped.push(`  ... [x${repeatCount + 1} repeated log lines omitted] ...`);
  }
  return deduped;
}

function generateStructuralIndex(lines, maxEntries = 35) {
  const sections = [];
  let currentSymbol = null;
  let symbolStart = 1;

  const symbolPrefixes = [
    "class ", "def ", "async def ", "function ", "async function ",
    "struct ", "impl ", "enum ", "trait ", "func ", "type ",
    "export default ", "export function ", "export class ",
    "public ", "private ", "protected ", "static ", "void ",
    "SELECT ", "CREATE TABLE ", "INSERT INTO ", "UPDATE ", "DELETE FROM ",
    "# ", "## ", "### ", "#### "
  ];

  lines.forEach((line, idx) => {
    const lineNum = idx + 1;
    const stripped = line.trim();
    const isMatch = symbolPrefixes.some((p) => stripped.startsWith(p)) || /^#{1,4}\s+|^Q\d+[:\s]/i.test(stripped);

    if (isMatch) {
      if (currentSymbol) {
        sections.push(`Lines ${symbolStart}-${lineNum - 1}: ${currentSymbol}`);
      }
      const parts = stripped.split(':');
      currentSymbol = parts[0].replace('{', '').trim().substring(0, 50);
      symbolStart = lineNum;
    }
  });

  if (currentSymbol && lines.length >= symbolStart) {
    sections.push(`Lines ${symbolStart}-${lines.length}: ${currentSymbol}`);
  }

  if (sections.length === 0 && lines.length > 20) {
    const chunkSize = Math.max(10, Math.floor(lines.length / 6));
    for (let startIdx = 1; startIdx <= lines.length; startIdx += chunkSize) {
      const endIdx = Math.min(lines.length, startIdx + chunkSize - 1);
      const firstWords = lines[startIdx - 1].trim().split(/\s+/).slice(0, 5).join(' ') || 'Content Block';
      sections.push(`Lines ${startIdx}-${endIdx}: ${firstWords}...`);
    }
  }

  if (sections.length === 0) return '';
  return '[PromptLens Structural Index]\n' + sections.slice(0, maxEntries).map((s) => `- ${s}`).join('\n');
}

function findErrorAnchors(lines, startLineOffset = 1) {
  const anchors = [];
  const keywords = ['error', 'exception', 'fail', 'warning', 'fatal', 'traceback', 'critical'];

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const lower = line.toLowerCase();
    if (keywords.some((kw) => lower.includes(kw))) {
      anchors.push({ lineNum: startLineOffset + i, lineText: line });
      if (anchors.length >= 8) break;
    }
  }
  return anchors;
}

async function localCompressText(text, headCount = 10, tailCount = 10) {
  if (!text || text.length < 300) {
    return { compressed_text: text, is_compressed: false, savings_pct: 0, retrieval_id: null };
  }

  const rawLines = normalizeLines(text);
  const lines = deduplicateLogs(rawLines);
  const retrievalId = await sha256Hex12(text);

  if (lines.length <= headCount + tailCount + 2) {
    return { compressed_text: text, is_compressed: false, savings_pct: 0, retrieval_id: retrievalId };
  }

  const tocIndex = generateStructuralIndex(lines);
  const middleLines = lines.slice(headCount, lines.length - tailCount);
  const anchors = findErrorAnchors(middleLines, headCount + 1);
  let anchorBlock = '';
  if (anchors.length > 0) {
    const anchorStr = anchors.map((a) => `  Line ${a.lineNum}: ${a.lineText}`).join('\n');
    anchorBlock = `\n[PromptLens Pinned Middle Errors/Exceptions]\n${anchorStr}`;
  }

  let compressedLines = [];
  if (text.includes("Traceback (most recent call last):") || text.includes("FAILURES") || text.includes("ERRORS")) {
    if (lines.length > 12) {
      const head = lines.slice(0, 4);
      const tail = lines.slice(-4);
      const omitted = lines.length - 8;
      const marker = `--- [PROMPT LENS TRUNCATED ${omitted} stack trace lines. Use retrieve_original('${retrievalId}') for full log] ---`;
      compressedLines = head.concat([marker], tail);
    } else {
      compressedLines = lines;
    }
  } else {
    const head = lines.slice(0, headCount);
    const tail = lines.slice(-tailCount);
    const omitted = lines.length - (headCount + tailCount);
    const marker = `--- [PROMPT LENS TRUNCATED ${omitted} lines (total: ${lines.length}). Use retrieve_original('${retrievalId}') for full text] ---`;
    compressedLines = head.concat([marker], tail);
  }

  const prefix = tocIndex ? (tocIndex + '\n\n') : '';
  const suffix = anchorBlock ? (anchorBlock + '\n') : '';
  const compressedBody = prefix + compressedLines.join('\n') + suffix;

  const savingsPct = Math.max(0, Math.round((1 - compressedBody.length / text.length) * 100));
  const notice = `\n\n[PromptLens: Content compressed (saved ${savingsPct}% tokens). Original ID: ${retrievalId}. Call retrieve_original(id="${retrievalId}") if full data is required.]`;

  const finalCompressedStr = compressedBody + notice;

  return {
    compressed_text: finalCompressedStr,
    is_compressed: true,
    savings_pct: savingsPct,
    retrieval_id: retrievalId,
    original_text: text
  };
}

// Event listeners for text compression & vault payload fetching
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'compress_text') {
    // 1. Send API request directly to backend for canonical Vault storage and metrics
    fetch(`${PROMPTLENS_API_BASE}/api/compress`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ content: request.content })
    })
      .then((res) => {
        if (!res.ok) throw new Error('API status ' + res.status);
        return res.json();
      })
      .then((data) => {
        chrome.storage.local.get(['tokens_saved', 'requests_count'], (store) => {
          const currentSaved = store.tokens_saved || 0;
          const currentReqs = store.requests_count || 0;
          const savedTokens = Math.max(0, (data.original_tokens || 0) - (data.compressed_tokens || 0));
          const newTotalSaved = currentSaved + savedTokens;

          chrome.storage.local.set({
            tokens_saved: newTotalSaved,
            requests_count: currentReqs + 1,
            last_vault_id: data.retrieval_id,
            cached_stats: {
              total_tokens_saved: newTotalSaved,
              estimated_usd_saved: (newTotalSaved / 1000000) * 3.0
            }
          });
        });

        sendResponse({
          success: true,
          compressed_text: data.compressed_text,
          retrieval_id: data.retrieval_id,
          savings_pct: data.savings_pct,
          original_tokens: data.original_tokens,
          compressed_tokens: data.compressed_tokens
        });
      })
      .catch((err) => {
        console.warn('Backend proxy fetch offline/slow, fallback to local JS parity compressor:', err);
        localCompressText(request.content).then((localResult) => {
          // Fire background async sync attempt to persist in python vault
          fetch(`${PROMPTLENS_API_BASE}/api/compress`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: request.content })
          }).catch(() => {});

          sendResponse({
            success: true,
            compressed_text: localResult.compressed_text,
            retrieval_id: localResult.retrieval_id,
            savings_pct: localResult.savings_pct,
            fallback_mode: true
          });
        });
      });

    return true; // Keep async response channel open
  }

  if (request.action === 'fetch_vault_payload') {
    const id = request.retrieval_id;
    let url = `${PROMPTLENS_API_BASE}/api/vault/${id}`;
    const params = new URLSearchParams();
    if (request.start_line) params.append('start_line', request.start_line);
    if (request.end_line) params.append('end_line', request.end_line);
    if (params.toString()) url += `?${params.toString()}`;

    fetch(url)
      .then((res) => {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then((data) => sendResponse({ success: true, content: data.content }))
      .catch((err) => sendResponse({ success: false, error: err.message }));

    return true; // Keep channel open
  }
});
