// PromptLens Chrome Extension Popup Handler (Instant 0ms + Live Proxy Sync Edition)

function initPopup() {
  const tokensSavedEl = document.getElementById('tokens-saved');
  const costSavedEl = document.getElementById('cost-saved');
  const lastVaultIdEl = document.getElementById('last-vault-id');
  const btnOpenDashboard = document.getElementById('btn-open-dashboard');

  const btnManual = document.getElementById('mode-manual');
  const btnAuto = document.getElementById('mode-auto');
  const modeHintEl = document.getElementById('mode-hint');

  function setModeUI(mode) {
    if (!btnManual || !btnAuto || !modeHintEl) return;
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
  if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(['compression_mode', 'last_vault_id', 'cached_stats', 'tokens_saved'], (store = {}) => {
      const s = store || {};
      const currentMode = s.compression_mode || 'auto';
      setModeUI(currentMode);

      if (s.last_vault_id && lastVaultIdEl) {
        lastVaultIdEl.textContent = s.last_vault_id;
      }

      const cached = s.cached_stats || {};
      const savedTokens = cached.total_tokens_saved ?? s.tokens_saved ?? 0;
      const usdSaved = cached.estimated_usd_saved ?? ((savedTokens / 1000000) * 3.0);

      if (tokensSavedEl) tokensSavedEl.textContent = Number(savedTokens).toLocaleString();
      if (costSavedEl) costSavedEl.textContent = `$${Number(usdSaved).toFixed(4)}`;
    });
  }

  // 2. Non-blocking background fetch with 800ms abort controller timeout
  const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timeoutId = setTimeout(() => controller?.abort(), 800);

  fetch('http://localhost:8000/api/stats', { signal: controller?.signal })
    .then((res) => (res.ok ? res.json() : null))
    .then((data) => {
      clearTimeout(timeoutId);
      if (data) {
        if (tokensSavedEl) tokensSavedEl.textContent = Number(data.total_tokens_saved).toLocaleString();
        if (costSavedEl) costSavedEl.textContent = `$${Number(data.estimated_usd_saved).toFixed(4)}`;
        if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
          chrome.storage.local.set({
            tokens_saved: data.total_tokens_saved,
            cached_stats: {
              total_tokens_saved: data.total_tokens_saved,
              estimated_usd_saved: data.estimated_usd_saved
            }
          });
        }
      }
    })
    .catch(() => {
      clearTimeout(timeoutId);
    });

  // Event Listeners
  if (btnManual) {
    btnManual.addEventListener('click', () => {
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ compression_mode: 'manual' }, () => {
          setModeUI('manual');
        });
      } else {
        setModeUI('manual');
      }
    });
  }

  if (btnAuto) {
    btnAuto.addEventListener('click', () => {
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ compression_mode: 'auto' }, () => {
          setModeUI('auto');
        });
      } else {
        setModeUI('auto');
      }
    });
  }

  if (btnOpenDashboard) {
    btnOpenDashboard.addEventListener('click', () => {
      if (typeof chrome !== 'undefined' && chrome.tabs && chrome.tabs.create) {
        chrome.tabs.create({ url: 'http://localhost:3000' });
      } else {
        window.open('http://localhost:3000', '_blank');
      }
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPopup);
} else {
  initPopup();
}


