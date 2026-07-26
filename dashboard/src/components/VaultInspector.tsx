import React, { useState, useEffect } from 'react';
import { VaultItem } from '../types';
import { Search, Copy, Check, FileText, Clock, HardDrive, RefreshCw } from 'lucide-react';

export const VaultInspector: React.FC = () => {
  const [items, setItems] = useState<VaultItem[]>([]);
  const [selectedItem, setSelectedItem] = useState<VaultItem | null>(null);
  const [search, setSearch] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const fetchVault = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/vault');
      if (resp.ok) {
        const data = await resp.json();
        setItems(data.items || []);
        if (data.items && data.items.length > 0 && !selectedItem) {
          setSelectedItem(data.items[0]);
        }
      }
    } catch (err) {
      console.error('Failed to fetch vault items:', err);
    } finally {
      setLoading(false);
    }
  };

  const textAreaRef = React.useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetchVault();
  }, []);

  useEffect(() => {
    if (selectedItem && textAreaRef.current) {
      textAreaRef.current.scrollTop = 0;
    }
  }, [selectedItem]);

  const filteredItems = items.filter(
    (item) =>
      item.retrieval_id.toLowerCase().includes(search.toLowerCase()) ||
      item.preview.toLowerCase().includes(search.toLowerCase()) ||
      item.full_content.toLowerCase().includes(search.toLowerCase())
  );

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white">Reversible Vault Inspector</h1>
          <p className="text-sm text-[#888888] mt-1">
            Browse, search, and inspect raw uncompressed tool outputs stored in the hash-keyed memory vault.
          </p>
        </div>
        <button
          onClick={fetchVault}
          disabled={loading}
          className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-[#141414] hover:bg-[#1a1a1a] text-white border border-[#262626] transition flex items-center space-x-2 self-start"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>Refresh Vault</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Left Item List */}
        <div className="headroom-card p-4 space-y-4">
          <div className="relative">
            <Search className="w-3.5 h-3.5 text-[#666666] absolute left-3 top-3" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search by Vault ID or content..."
              className="w-full bg-[#050505] text-xs text-[#cccccc] placeholder-[#555555] border border-[#1f1f1f] rounded-lg pl-8 pr-3 py-2 focus:outline-none focus:border-[#444444] transition"
            />
          </div>

          <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
            {filteredItems.length === 0 ? (
              <div className="p-6 text-center text-xs text-[#666666]">
                {items.length === 0
                  ? 'No uncompressed payloads currently stored in vault.'
                  : 'No items match your search filter.'}
              </div>
            ) : (
              filteredItems.map((item) => (
                <div
                  key={item.retrieval_id}
                  onClick={() => setSelectedItem(item)}
                  className={`p-3 rounded-lg border text-xs cursor-pointer transition space-y-1.5 ${
                    selectedItem?.retrieval_id === item.retrieval_id
                      ? 'bg-[#1a1a1a] border-[#333333] text-white'
                      : 'bg-[#090909] border-[#181818] text-[#888888] hover:bg-[#111111] hover:text-[#cccccc]'
                  }`}
                >
                  <div className="flex items-center justify-between font-mono">
                    <span className="font-semibold text-white">{item.retrieval_id}</span>
                    <span className="text-[10px] text-[#666666]">{item.size_bytes.toLocaleString()} B</span>
                  </div>
                  <p className="line-clamp-2 text-[11px] font-mono text-[#777777]">{item.preview}</p>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right Detail Preview */}
        <div className="lg:col-span-2 headroom-card p-6 space-y-4 min-h-[500px] flex flex-col justify-between">
          {selectedItem ? (
            <>
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#1f1f1f]">
                  <div>
                    <div className="flex items-center space-x-2">
                      <FileText className="w-4 h-4 text-white" />
                      <span className="font-mono font-bold text-base text-white">{selectedItem.retrieval_id}</span>
                    </div>
                    <div className="flex items-center space-x-4 text-xs text-[#666666] mt-1 font-mono">
                      <span className="flex items-center space-x-1">
                        <HardDrive className="w-3 h-3" />
                        <span>{selectedItem.size_bytes.toLocaleString()} bytes</span>
                      </span>
                      <span className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(selectedItem.created_at * 1000).toLocaleTimeString()}</span>
                      </span>
                    </div>
                  </div>

                  <button
                    onClick={() => handleCopy(selectedItem.full_content)}
                    className="px-3 py-1.5 rounded-md text-xs font-medium bg-white hover:bg-[#e0e0e0] text-black transition flex items-center space-x-1.5"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied Original!' : 'Copy Original'}</span>
                  </button>
                </div>

                <div className="space-y-1">
                  <label className="text-xs font-semibold text-[#888888] uppercase tracking-wider block">
                    Full Uncompressed Raw Payload
                  </label>
                  <textarea
                    ref={textAreaRef}
                    value={selectedItem.full_content}
                    readOnly
                    rows={18}
                    className="w-full bg-[#050505] text-[#cccccc] border border-[#1f1f1f] rounded-xl p-3 text-xs font-mono focus:outline-none resize-none whitespace-pre overflow-x-auto"
                  />
                </div>
              </div>

              <div className="text-xs text-[#666666] pt-2 border-t border-[#1a1a1a]">
                💡 AI agents invoke <code className="text-[#aaaaaa]">retrieve_original(id=&quot;{selectedItem.retrieval_id}&quot;)</code> to pull this exact raw content on demand.
              </div>
            </>
          ) : (
            <div className="flex flex-col items-center justify-center h-full py-20 text-center text-[#555555]">
              <FileText className="w-8 h-8 mb-2" />
              <p className="text-xs">Select a vault payload from the list to view its uncompressed content.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
