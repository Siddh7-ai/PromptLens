// PromptLens Chrome Extension Popup Handler (Instant 0ms + Live Proxy Sync Edition)

const API_BASE = 'http://127.0.0.1:8000';

function updateUI(store = {}) {
  const tokensSavedEl = document.getElementById('tokens-saved');
  const costSavedEl = document.getElementById('cost-saved');
  const lastVaultIdEl = document.getElementById('last-vault-id');
  const btnManual = document.getElementById('mode-manual');
  const btnAuto = document.getElementById('mode-auto');
  const modeHintEl = document.getElementById('mode-hint');

  const currentMode = store.compression_mode || 'auto';
  if (btnManual && btnAuto && modeHintEl) {
    if (currentMode === 'manual') {
      btnManual.classList.add('active');
      btnAuto.classList.remove('active');
      modeHintEl.innerHTML = '🔘 <b>Manual Mode:</b> Click button or press <b>Alt+C</b> to compress.';
    } else {
      btnAuto.classList.add('active');
      btnManual.classList.remove('active');
      modeHintEl.innerHTML = '⚡ <b>Auto Mode (Default):</b> Prompts >300B auto-compress on Enter/Send.';
    }
  }

  if (store.last_vault_id && lastVaultIdEl) {
    lastVaultIdEl.textContent = store.last_vault_id;
  }

  const cached = store.cached_stats || {};
  const savedTokens = cached.total_tokens_saved ?? store.tokens_saved ?? 0;
  const usdSaved = cached.estimated_usd_saved ?? ((savedTokens / 1000000) * 3.0);

  if (tokensSavedEl) tokensSavedEl.textContent = Number(savedTokens).toLocaleString();
  if (costSavedEl) costSavedEl.textContent = `$${Number(usdSaved).toFixed(4)}`;
}

function initPopup() {
  const btnOpenDashboard = document.getElementById('btn-open-dashboard');
  const btnManual = document.getElementById('mode-manual');
  const btnAuto = document.getElementById('mode-auto');

  // 1. Instant 0ms Local Storage Read for zero-delay UI render
  if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(['compression_mode', 'last_vault_id', 'cached_stats', 'tokens_saved'], (store = {}) => {
      updateUI(store);
    });
  }

  // 2. Ultra-fast non-blocking background fetch (127.0.0.1 avoids Windows IPv6 delay)
  const controller = typeof AbortController !== 'undefined' ? new AbortController() : null;
  const timeoutId = setTimeout(() => controller?.abort(), 300);

  fetch(`${API_BASE}/api/stats`, { signal: controller?.signal })
    .then((res) => (res.ok ? res.json() : null))
    .then((data) => {
      clearTimeout(timeoutId);
      if (data) {
        const tokensSavedEl = document.getElementById('tokens-saved');
        const costSavedEl = document.getElementById('cost-saved');
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
      const modeHintEl = document.getElementById('mode-hint');
      btnManual.classList.add('active');
      if (btnAuto) btnAuto.classList.remove('active');
      if (modeHintEl) modeHintEl.innerHTML = '🔘 <b>Manual Mode:</b> Click button or press <b>Alt+C</b> to compress.';
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ compression_mode: 'manual' });
      }
    });
  }

  if (btnAuto) {
    btnAuto.addEventListener('click', () => {
      const modeHintEl = document.getElementById('mode-hint');
      btnAuto.classList.add('active');
      if (btnManual) btnManual.classList.remove('active');
      if (modeHintEl) modeHintEl.innerHTML = '⚡ <b>Auto Mode (Default):</b> Prompts >300B auto-compress on Enter/Send.';
      if (typeof chrome !== 'undefined' && chrome.storage && chrome.storage.local) {
        chrome.storage.local.set({ compression_mode: 'auto' });
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



