import React, { useState, useEffect } from 'react';
import { CompressionSettings } from '../types';
import { Sliders, Save, RotateCcw, Check } from 'lucide-react';

export const SettingsPanel: React.FC = () => {
  const [settings, setSettings] = useState<CompressionSettings>({
    head_lines: 10,
    tail_lines: 10,
    max_json_array: 50,
    min_tokens_threshold: 100,
  });
  const [saving, setSaving] = useState<boolean>(false);
  const [savedSuccess, setSavedSuccess] = useState<boolean>(false);

  const fetchSettings = async () => {
    try {
      const resp = await fetch('http://localhost:8000/api/settings');
      if (resp.ok) {
        const data: CompressionSettings = await resp.json();
        setSettings(data);
      }
    } catch (err) {
      console.error('Failed to fetch settings:', err);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    try {
      const resp = await fetch('http://localhost:8000/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });
      if (resp.ok) {
        setSavedSuccess(true);
        setTimeout(() => setSavedSuccess(false), 2000);
      }
    } catch (err) {
      console.error('Failed to save settings:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleReset = () => {
    setSettings({
      head_lines: 10,
      tail_lines: 10,
      max_json_array: 50,
      min_tokens_threshold: 100,
    });
  };

  return (
    <div className="space-y-6 max-w-3xl">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Compression Rules & Settings</h1>
        <p className="text-sm text-[#888888] mt-1">
          Adjust live truncation limits and minimum compression thresholds applied by PromptLens proxy.
        </p>
      </div>

      <div className="headroom-card p-6 space-y-6">
        <div className="flex items-center space-x-2 pb-4 border-b border-[#1f1f1f]">
          <Sliders className="w-5 h-5 text-white" />
          <h2 className="text-base font-semibold text-white">Rule Threshold Controls</h2>
        </div>

        <div className="space-y-6 text-xs">
          {/* Head Lines Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-white">Head Lines Preserved</label>
              <span className="font-mono font-bold text-white bg-[#1a1a1a] px-2 py-0.5 rounded border border-[#2e2e2e]">
                {settings.head_lines} lines
              </span>
            </div>
            <input
              type="range"
              min="2"
              max="50"
              value={settings.head_lines}
              onChange={(e) => setSettings({ ...settings, head_lines: parseInt(e.target.value) })}
              className="w-full accent-white cursor-pointer"
            />
            <p className="text-[11px] text-[#666666]">Number of lines preserved from top of stack traces and logs.</p>
          </div>

          {/* Tail Lines Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-white">Tail Lines Preserved</label>
              <span className="font-mono font-bold text-white bg-[#1a1a1a] px-2 py-0.5 rounded border border-[#2e2e2e]">
                {settings.tail_lines} lines
              </span>
            </div>
            <input
              type="range"
              min="2"
              max="50"
              value={settings.tail_lines}
              onChange={(e) => setSettings({ ...settings, tail_lines: parseInt(e.target.value) })}
              className="w-full accent-white cursor-pointer"
            />
            <p className="text-[11px] text-[#666666]">Number of lines preserved from bottom of stack traces and logs.</p>
          </div>

          {/* Max JSON Array Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-white">Max JSON Array Items</label>
              <span className="font-mono font-bold text-white bg-[#1a1a1a] px-2 py-0.5 rounded border border-[#2e2e2e]">
                {settings.max_json_array} items
              </span>
            </div>
            <input
              type="range"
              min="5"
              max="200"
              step="5"
              value={settings.max_json_array}
              onChange={(e) => setSettings({ ...settings, max_json_array: parseInt(e.target.value) })}
              className="w-full accent-white cursor-pointer"
            />
            <p className="text-[11px] text-[#666666]">Maximum number of array elements kept in tool output JSON responses.</p>
          </div>

          {/* Minimum Token Threshold Slider */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label className="font-semibold text-white">Minimum Token Threshold</label>
              <span className="font-mono font-bold text-white bg-[#1a1a1a] px-2 py-0.5 rounded border border-[#2e2e2e]">
                {settings.min_tokens_threshold} tokens
              </span>
            </div>
            <input
              type="range"
              min="10"
              max="500"
              step="10"
              value={settings.min_tokens_threshold}
              onChange={(e) => setSettings({ ...settings, min_tokens_threshold: parseInt(e.target.value) })}
              className="w-full accent-white cursor-pointer"
            />
            <p className="text-[11px] text-[#666666]">Outputs smaller than this threshold pass through uncompressed.</p>
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-between pt-4 border-t border-[#1a1a1a]">
          <button
            onClick={handleReset}
            className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-[#141414] hover:bg-[#1a1a1a] text-[#888888] hover:text-white border border-[#262626] transition flex items-center space-x-1.5"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reset Defaults</span>
          </button>
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 rounded-lg text-xs font-semibold bg-white hover:bg-[#e0e0e0] text-black transition flex items-center space-x-1.5"
          >
            {savedSuccess ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Save className="w-3.5 h-3.5" />}
            <span>{savedSuccess ? 'Settings Applied!' : saving ? 'Saving...' : 'Apply Live Settings'}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
