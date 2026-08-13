// PromptLens Content Script - Universal Web AI Interceptor & Auto Vault Retriever (Official Transparent Eye Logo Parity)

(function () {
  console.log('⚡ PromptLens Web AI Context Optimizer Pro active.');

  let currentMode = 'auto';
  const processedMessageContainers = new Set();
  let isAutoRetrieving = false;
  let pillResetTimeout = null;

  const logoImgUrl = (typeof chrome !== 'undefined' && chrome.runtime && chrome.runtime.getURL)
    ? chrome.runtime.getURL('logo.png')
    : '';

  const INPUT_SELECTORS = [
    '#prompt-textarea',
    'textarea[placeholder*="Ask"]',
    'textarea[placeholder*="Message"]',
    'textarea[placeholder*="Send"]',
    'textarea',
    'div[contenteditable="true"]',
    'rich-textarea'
  ];

  function getActiveInput() {
    for (const selector of INPUT_SELECTORS) {
      const el = document.querySelector(selector);
      if (el && el.offsetWidth > 0 && el.offsetHeight > 0) {
        return el;
      }
    }
    return null;
  }

  function getInputValue(inputEl) {
    if (!inputEl) return '';
    let val = '';
    if (inputEl.isContentEditable) {
      val = inputEl.innerText || inputEl.textContent || '';
    } else {
      val = inputEl.value || '';
    }
    return val.replace(/(\r?\n\s*){2,}/g, '\n').trim();
  }

  function setInputValue(inputEl, text) {
    if (!inputEl) return;

    if (inputEl.isContentEditable) {
      inputEl.focus();

      // 1. Select all content in Lexical / ProseMirror editor
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(inputEl);
      selection.removeAllRanges();
      selection.addRange(range);

      // 2. Delete existing original text completely
      document.execCommand('delete', false);

      // 3. Insert pure compressed text ONCE
      const success = document.execCommand('insertText', false, text);
      if (!success || !inputEl.innerText.includes(text.substring(0, 15))) {
        inputEl.innerText = text;
      }

      // 4. Dispatch InputEvents for React state sync
      inputEl.dispatchEvent(new InputEvent('beforeinput', { bubbles: true, inputType: 'insertText', data: text }));
      inputEl.dispatchEvent(new InputEvent('input', { bubbles: true, inputType: 'insertText', data: text }));
      inputEl.dispatchEvent(new Event('change', { bubbles: true }));
      return;
    }

    inputEl.value = text;
    inputEl.dispatchEvent(new Event('input', { bubbles: true }));
    inputEl.dispatchEvent(new Event('change', { bubbles: true }));
  }

  async function sha256Hex12(text) {
    try {
      const encoder = new TextEncoder();
      const data = encoder.encode(text);
      const hashBuffer = await crypto.subtle.digest('SHA-256', data);
      const hashArray = Array.from(new Uint8Array(hashBuffer));
      const hashHex = hashArray.map((b) => b.toString(16).padStart(2, '0')).join('');
      return hashHex.substring(0, 12);
    } catch {
      let hash = 0;
      for (let i = 0; i < text.length; i++) {
        hash = ((hash << 5) - hash) + text.charCodeAt(i);
        hash |= 0;
      }
      return Math.abs(hash).toString(16).substring(0, 12);
    }
  }

  function normalizeLines(text) {
    if (!text) return [];
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

  async function fallbackLocalCompress(text, headCount = 10, tailCount = 10) {
    if (!text || text.length < 300) {
      return { compressed_text: text, savings_pct: 0, retrieval_id: 'local' };
    }
    const rawLines = normalizeLines(text);
    const lines = deduplicateLogs(rawLines);
    if (lines.length <= headCount + tailCount + 2) {
      return { compressed_text: text, savings_pct: 0, retrieval_id: 'local' };
    }

    const retrievalId = await sha256Hex12(text);

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

    return {
      compressed_text: compressedBody + notice,
      savings_pct: savingsPct,
      retrieval_id: retrievalId
    };
  }

  function showToast(message, isSuccess = true) {
    let toast = document.getElementById('promptlens-toast');
    if (!toast) {
      toast = document.createElement('div');
      toast.id = 'promptlens-toast';
      toast.className = 'promptlens-toast';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.style.borderColor = isSuccess ? '#00ff88' : '#ff4444';
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3500);
  }

  function showSideIndicator(title, message, vaultId = null) {
    let indicator = document.getElementById('promptlens-side-indicator');
    if (!indicator) {
      indicator = document.createElement('div');
      indicator.id = 'promptlens-side-indicator';
      indicator.className = 'promptlens-side-indicator';
      document.body.appendChild(indicator);
    }

    indicator.innerHTML = `
      <div class="promptlens-side-content">
        <img src="${logoImgUrl}" class="promptlens-flash-icon" alt="PromptLens Logo">
        <div>
          <div class="promptlens-side-title">${title}</div>
          <div class="promptlens-side-desc">${message}</div>
          ${vaultId ? `<div class="promptlens-side-vault">Vault SHA-256: <code>${vaultId}</code></div>` : ''}
        </div>
      </div>
    `;

    indicator.classList.add('show');
    setTimeout(() => indicator.classList.remove('show'), 5000);
  }

  function updatePillText() {
    if (pillResetTimeout) {
      clearTimeout(pillResetTimeout);
      pillResetTimeout = null;
    }

    const pill = document.getElementById('promptlens-pill');
    if (!pill) return;

    pill.className = 'promptlens-compress-pill';
    const span = pill.querySelector('span');
    if (!span) return;

    if (currentMode === 'manual') {
      pill.title = 'Manual Mode (Click or press Alt+C to compress)';
      span.textContent = 'PromptLens Compress (Alt+C)';
    } else {
      pill.title = 'Auto-Compress Mode active (compresses on Enter/Send)';
      span.textContent = 'PromptLens Auto-Compress Active';
    }
  }

  function triggerSendButtonClick() {
    const selectors = [
      'button[data-testid*="send-button"]',
      'button[data-testid*="send"]',
      'button[aria-label*="Send prompt"]',
      'button[aria-label*="Send"]',
      'button[aria-label*="send"]',
      'form button[type="submit"]',
      'form button:last-child'
    ];

    for (const selector of selectors) {
      const btn = document.querySelector(selector);
      if (btn) {
        btn.removeAttribute('disabled');
        btn.click();
        return true;
      }
    }
    return false;
  }

  function compressActiveInput(onComplete) {
    const inputEl = getActiveInput();
    if (!inputEl) {
      if (onComplete) onComplete();
      return;
    }

    const rawText = getInputValue(inputEl);
    if (!rawText || rawText.trim().length < 100 || rawText.includes('[PROMPT LENS TRUNCATED')) {
      if (onComplete) onComplete();
      return;
    }

    const pill = document.getElementById('promptlens-pill');
    if (pill) pill.querySelector('span').textContent = 'Compressing...';

    // 1. Instant 0ms local JavaScript compression for zero latency
    fallbackLocalCompress(rawText).then((instantRes) => {
      setInputValue(inputEl, instantRes.compressed_text);

      if (pill) {
        pill.className = 'promptlens-compress-pill promptlens-compressed';
        pill.querySelector('span').textContent = `✓ Cut ${instantRes.savings_pct || 0}% Tokens (ID: ${instantRes.retrieval_id || 'vault'})`;
      }
      if (currentMode === 'auto') {
        showSideIndicator('PromptLens Auto-Compressed', `Cut ${instantRes.savings_pct || 0}% tokens in background!`, instantRes.retrieval_id);
      } else {
        showToast(`⚡ Compressed! Cut ${instantRes.savings_pct || 0}% tokens (Vault ID: ${instantRes.retrieval_id || 'saved'})`);
      }

      if (pillResetTimeout) clearTimeout(pillResetTimeout);
      pillResetTimeout = setTimeout(() => {
        updatePillText();
      }, 3000);

      // 2. Fire-and-forget async background sync to Python vault (never blocks UI)
      try {
        if (chrome.runtime && chrome.runtime.id) {
          chrome.runtime.sendMessage(
            { action: 'compress_text', content: rawText, precomputed_id: instantRes.retrieval_id },
            () => {}
          );
        }
      } catch (err) {
        console.debug('PromptLens background sync skipped:', err);
      }

      if (onComplete) {
        onComplete();
      } else if (currentMode === 'auto') {
        setTimeout(triggerSendButtonClick, 50);
      }
    });
  }

  function getPromptContainer(inputEl) {
    const host = window.location.hostname;

    // 1. Claude.ai positioning target
    if (host.includes('claude.ai')) {
      const fieldset = inputEl.closest('fieldset');
      if (fieldset) return fieldset;

      const form = inputEl.closest('form');
      if (form) return form;

      const proseMirror = inputEl.closest('.ProseMirror') || inputEl.closest('[contenteditable="true"]');
      if (proseMirror) {
        let parent = proseMirror.parentElement;
        while (parent && parent.tagName !== 'BODY') {
          if (parent.tagName === 'FORM' || parent.tagName === 'FIELDSET' || parent.classList.contains('relative')) {
            return parent;
          }
          parent = parent.parentElement;
        }
      }
    }

    // 2. Gemini (gemini.google.com) positioning target
    if (host.includes('gemini.google.com')) {
      const richTextarea = inputEl.closest('rich-textarea');
      if (richTextarea) {
        const inputArea = richTextarea.closest('.input-area-container') || richTextarea.closest('.chat-input-container') || richTextarea.parentElement;
        if (inputArea) return inputArea;
      }
      const inputArea = inputEl.closest('.input-area-container') || inputEl.closest('.chat-input-container') || inputEl.closest('.input-area');
      if (inputArea) return inputArea;
    }

    // 3. ChatGPT / DeepSeek / OpenRouter positioning target
    const form = inputEl.closest('form');
    if (form) return form;

    return inputEl.closest('[class*="input-container"]') || inputEl.closest('[class*="textarea"]') || inputEl.parentElement;
  }

  function injectPromptLensPill() {
    const inputEl = getActiveInput();
    if (!inputEl || document.getElementById('promptlens-pill')) return;

    const pill = document.createElement('div');
    pill.id = 'promptlens-pill';
    pill.className = 'promptlens-compress-pill';
    pill.innerHTML = `
      <img src="${logoImgUrl}" class="promptlens-badge-icon" alt="PromptLens Logo">
      <span>PromptLens Compress (Alt+C)</span>
    `;

    pill.addEventListener('click', (e) => {
      e.preventDefault();
      e.stopPropagation();
      compressActiveInput();
    });

    // Reset pill state on typing new input
    inputEl.addEventListener('input', () => {
      const pillEl = document.getElementById('promptlens-pill');
      if (pillEl && pillEl.classList.contains('promptlens-compressed')) {
        updatePillText();
      }
    });

    const form = inputEl.closest('form');
    if (form && !form.dataset.promptlensHooked) {
      form.dataset.promptlensHooked = 'true';

      inputEl.addEventListener('keydown', (e) => {
        if (currentMode === 'auto' && e.key === 'Enter' && !e.shiftKey && !e.altKey && !e.ctrlKey) {
          const rawText = getInputValue(inputEl);
          if (rawText && rawText.length >= 300 && !rawText.includes('[PROMPT LENS TRUNCATED')) {
            e.preventDefault();
            e.stopPropagation();
            compressActiveInput(() => {
              setTimeout(triggerSendButtonClick, 150);
            });
          }
        }
      }, true);
    }

    const targetContainer = getPromptContainer(inputEl);
    if (targetContainer && targetContainer.parentElement) {
      targetContainer.parentElement.insertBefore(pill, targetContainer);
      updatePillText();
    } else if (inputEl.parentElement) {
      inputEl.parentElement.insertBefore(pill, inputEl);
      updatePillText();
    }
  }

  // --- IN-CHAT INTERACTIVE VAULT DRAWER (Clean Single-Injection) ---
  function scanAndEnhanceChatMessages() {
    const messageArticles = document.querySelectorAll('article');

    messageArticles.forEach((article) => {
      if (processedMessageContainers.has(article) || article.dataset.promptlensVaultInjected) return;
      if (article.querySelector('.promptlens-inline-vault-pill')) return;

      const txt = article.innerText || article.textContent || '';
      const match = txt.match(/retrieve_original\(['"]([a-f0-9]{12})['"]\)/i) || txt.match(/Original ID: ([a-f0-9]{12})/i);

      if (match && match[1]) {
        const vaultId = match[1];

        if (article.querySelector(`.promptlens-inline-vault-pill[data-vault-id="${vaultId}"]`)) return;

        article.dataset.promptlensVaultInjected = 'true';
        processedMessageContainers.add(article);

        const inlinePill = document.createElement('div');
        inlinePill.className = 'promptlens-inline-vault-pill';
        inlinePill.dataset.vaultId = vaultId;
        inlinePill.innerHTML = `⚡ Expand Vault Payload (ID: <code>${vaultId}</code>)`;

        let drawer = null;

        inlinePill.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();

          if (drawer) {
            drawer.style.display = drawer.style.display === 'none' ? 'block' : 'none';
            inlinePill.innerHTML = drawer.style.display === 'none' ? `⚡ Expand Vault Payload (ID: <code>${vaultId}</code>)` : `⚡ Hide Vault Payload (ID: <code>${vaultId}</code>)`;
            return;
          }

          inlinePill.textContent = '⚡ Loading Vault Payload...';

          try {
            chrome.runtime.sendMessage(
              { action: 'fetch_vault_payload', retrieval_id: vaultId },
              (res) => {
                if (res && res.success && res.content) {
                  inlinePill.innerHTML = `⚡ Hide Vault Payload (ID: <code>${vaultId}</code>)`;
                  drawer = document.createElement('div');
                  drawer.className = 'promptlens-vault-drawer';
                  drawer.innerHTML = `
                    <div class="promptlens-drawer-header">
                      <div class="promptlens-drawer-title">
                        <img src="${logoImgUrl}" class="promptlens-badge-icon" alt="PromptLens Logo">
                        PromptLens Reversible Vault Payload (${vaultId})
                      </div>
                      <span class="promptlens-drawer-close">✕</span>
                    </div>
                    <pre class="promptlens-drawer-code">${res.content}</pre>
                  `;

                  drawer.querySelector('.promptlens-drawer-close').addEventListener('click', () => {
                    drawer.style.display = 'none';
                    inlinePill.innerHTML = `⚡ Expand Vault Payload (ID: <code>${vaultId}</code>)`;
                  });

                  article.appendChild(drawer);
                } else {
                  inlinePill.textContent = '❌ Vault Payload Expired or Unavailable';
                }
              }
            );
          } catch {
            inlinePill.textContent = '❌ Refresh page to re-attach extension channel';
          }
        });

        article.appendChild(inlinePill);
      }
    });
  }

  // --- AUTOMATIC RESPONSE INTERCEPTOR ---
  function scanForAutoRetrievalRequests() {
    if (isAutoRetrieving) return;

    const bodyText = document.body.innerText || '';
    const retrievalMatch = bodyText.match(/retrieve_original\(['"]([a-f0-9]{12})['"]\)/i);

    if (retrievalMatch && retrievalMatch[1]) {
      const vaultId = retrievalMatch[1];
      const retrievalKey = `auto_retrieved_${vaultId}`;

      if (sessionStorage.getItem(retrievalKey)) return;
      sessionStorage.setItem(retrievalKey, 'true');

      isAutoRetrieving = true;
      showSideIndicator('PromptLens Auto-Retrieval', `Fetching lines from Vault (${vaultId})...`, vaultId);

      try {
        chrome.runtime.sendMessage(
          { action: 'fetch_vault_payload', retrieval_id: vaultId },
          (res) => {
            if (res && res.success && res.content) {
              const inputEl = getActiveInput();
              if (inputEl) {
                const snippet = res.content.length > 1500 ? res.content.substring(0, 1500) + '\n... [Vault Snippet Truncated]' : res.content;
                const replyText = `[PromptLens Automated Vault Payload - ID ${vaultId}]\nHere is the requested raw payload snippet from the Vault:\n\n\`\`\`\n${snippet}\n\`\`\``;
                
                setInputValue(inputEl, replyText);

                setTimeout(() => {
                  triggerSendButtonClick();
                  isAutoRetrieving = false;
                }, 600);
              } else {
                isAutoRetrieving = false;
              }
            } else {
              isAutoRetrieving = false;
            }
          }
        );
      } catch {
        isAutoRetrieving = false;
      }
    }
  }

  try {
    if (chrome.storage && chrome.storage.local) {
      chrome.storage.local.get(['compression_mode'], (store) => {
        currentMode = (store && store.compression_mode) || 'auto';
        updatePillText();
      });

      chrome.storage.onChanged.addListener((changes, area) => {
        if (area === 'local' && changes.compression_mode) {
          currentMode = changes.compression_mode.newValue || 'auto';
          updatePillText();
        }
      });
    }
  } catch {}

  // Global Capture-Phase Enter Key Interceptor for Web AI Platforms
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.altKey && !e.ctrlKey) {
      if (currentMode !== 'auto') return;

      const inputEl = getActiveInput();
      if (!inputEl) return;

      // Ensure cursor/focus is inside or targeting the active AI prompt input box
      const isFocused = document.activeElement === inputEl || inputEl.contains(document.activeElement);
      if (!isFocused && !inputEl.isContentEditable) return;

      const rawText = getInputValue(inputEl);
      if (rawText && rawText.length >= 150 && !rawText.includes('[PROMPT LENS TRUNCATED') && !rawText.includes('[PromptLens:')) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();

        compressActiveInput(() => {
          setTimeout(triggerSendButtonClick, 150);
        });
      }
    }
  }, true);

  document.addEventListener('keydown', (e) => {
    if (e.altKey && e.key.toLowerCase() === 'c') {
      e.preventDefault();
      compressActiveInput();
    }
  });

  const observer = new MutationObserver(() => {
    if (!document.getElementById('promptlens-pill')) {
      injectPromptLensPill();
    }
    scanAndEnhanceChatMessages();
    scanForAutoRetrievalRequests();
  });

  observer.observe(document.body, { childList: true, subtree: true });
  setTimeout(injectPromptLensPill, 500);
})();
