// PromptLens Chrome Extension Popup Handler (Synchronous 0ms + Live Proxy Sync Edition)

(function () {
  const tokensSavedEl = document.getElementById('tokens-saved');
  const costSavedEl = document.getElementById('cost-saved');
  const lastVaultIdEl = document.getElementById('last-vault-id');
  const btnOpenDashboard = document.getElementById('btn-open-dashboard');

  const btnManual = document.getElementById('mode-manual');
  const btnAuto = document.getElementById('mode-auto');
  const modeHintEl = document.getElementById('mode-hint');

  function setModeUI(mode) {
    if (mode === 'manual') {
      btnManual.classList.add('active');
      btnAuto.classList.remove('active');
      modeHintEl.innerHTML = '🔘 <b>Manual Mode:</b> Click button or press <b>Alt+C</b> to compress.';
    } else {
      btnAuto.classList.add('active');
      btnManual.classList.remove('active');
      modeHintEl.innerHTML = '⚡ <b>Auto Mode (Default):</b> Prompts >300B auto-compress on Enter/Send.';
    }
  }

  // 1. Instant 0ms Local Storage Read for zero-delay UI render
  chrome.storage.local.get(['compression_mode', 'last_vault_id', 'cached_stats', 'tokens_saved'], (store) => {
    const currentMode = store.compression_mode || 'auto';
    setModeUI(currentMode);

    if (store.last_vault_id) {
      lastVaultIdEl.textContent = store.last_vault_id;
    }

    const cached = store.cached_stats || {};
    const savedTokens = cached.total_tokens_saved ?? store.tokens_saved ?? 0;
    const usdSaved = cached.estimated_usd_saved ?? ((savedTokens / 1000000) * 3.0);

    tokensSavedEl.textContent = Number(savedTokens).toLocaleString();
    costSavedEl.textContent = `$${Number(usdSaved).toFixed(4)}`;
  });

  // 2. Background async fetch from proxy stats endpoint to sync live numbers
  fetch('http://localhost:8000/api/stats')
    .then((res) => (res.ok ? res.json() : null))
    .then((data) => {
      if (data) {
        tokensSavedEl.textContent = Number(data.total_tokens_saved).toLocaleString();
        costSavedEl.textContent = `$${Number(data.estimated_usd_saved).toFixed(4)}`;
        chrome.storage.local.set({
          tokens_saved: data.total_tokens_saved,
          cached_stats: {
            total_tokens_saved: data.total_tokens_saved,
            estimated_usd_saved: data.estimated_usd_saved
          }
        });
      }
    })
    .catch(() => {});

  // Event Listeners
  btnManual.addEventListener('click', () => {
    chrome.storage.local.set({ compression_mode: 'manual' }, () => {
      setModeUI('manual');
    });
  });

  btnAuto.addEventListener('click', () => {
    chrome.storage.local.set({ compression_mode: 'auto' }, () => {
      setModeUI('auto');
    });
  });

  btnOpenDashboard.addEventListener('click', () => {
    chrome.tabs.create({ url: 'http://localhost:3000' });
  });
})();
