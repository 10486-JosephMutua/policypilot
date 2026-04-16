import React, { useState } from 'react';
import { Search, RefreshCw, AlertTriangle } from 'lucide-react';
import { queryAPI } from '../services/api';

const EXAMPLES = [
  "What are the data retention requirements under GDPR Article 5?",
  "Summarise the whistleblower protections in the Sarbanes-Oxley Act.",
  "What constitutes a material breach under standard commercial contracts?",
  "Explain the CCPA opt-out obligations for third-party data sharing.",
];

export default function QueryPanel({ onResult, onLoading }) {
  const [query, setQuery]         = useState('');
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');
  const [challengeMode, setCM]    = useState(false);
  const [prevResult, setPrevResult] = useState(null);
  const [challengeReason, setCR]  = useState('');

  const submit = async (q = query, isChal = false) => {
    if (!q.trim()) return;
    setLoading(true); setError(''); onLoading?.(true);
    try {
      let result;
      if (isChal && prevResult) {
        result = await queryAPI.challenge(prevResult.query, challengeReason);
      } else {
        result = await queryAPI.runQuery(q.trim());
      }
      setPrevResult(result);
      onResult?.(result);
      setCM(false); setCR('');
    } catch (err) {
      setError(err.response?.data?.error || err.message || 'Request failed');
    } finally {
      setLoading(false); onLoading?.(false);
    }
  };

  return (
    <div style={{ display:'flex', flexDirection:'column', gap:14 }}>
      {/* Main search bar */}
      <div style={{
        display:'flex', alignItems:'flex-start', gap:10,
        background:'#0f1318', border:'1px solid #1e2535',
        borderRadius:10, padding:'10px 12px',
        transition:'border-color 0.2s',
      }}
        onFocus={() => {}}
      >
        <Search size={16} color="#4a5568" style={{ marginTop:3, flexShrink:0 }}/>
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) submit(); }}
          placeholder="Enter a legal or compliance question…"
          rows={3}
          style={{
            flex:1, background:'transparent', border:'none', outline:'none',
            color:'#e8edf5', fontSize:14, fontFamily:'Inter,sans-serif',
            resize:'vertical', lineHeight:1.6,
          }}
        />
      </div>

      {/* Example queries */}
      <div style={{ display:'flex', flexWrap:'wrap', gap:6 }}>
        {EXAMPLES.map((ex, i) => (
          <button key={i} onClick={() => { setQuery(ex); }}
            style={{
              fontSize:11, color:'#4a5568', background:'#0f1318',
              border:'1px solid #1a2030', borderRadius:20, padding:'3px 10px',
              cursor:'pointer', transition:'all 0.15s',
              fontFamily:'Inter,sans-serif',
            }}
            onMouseEnter={e => { e.target.style.color='#8a97b0'; e.target.style.borderColor='#252d3d'; }}
            onMouseLeave={e => { e.target.style.color='#4a5568'; e.target.style.borderColor='#1a2030'; }}
          >
            {ex.substring(0,42)}…
          </button>
        ))}
      </div>

      {/* Actions row */}
      <div style={{ display:'flex', gap:8, alignItems:'center' }}>
        <button
          onClick={() => submit()}
          disabled={loading || !query.trim()}
          style={{
            display:'flex', alignItems:'center', gap:7,
            background: loading || !query.trim() ? '#1a2030' : '#4f8ef7',
            color: loading || !query.trim() ? '#4a5568' : '#fff',
            border:'none', borderRadius:7, padding:'9px 20px',
            fontSize:13, fontWeight:500, cursor: loading ? 'wait' : 'pointer',
            transition:'all 0.15s', fontFamily:'Inter,sans-serif',
          }}
        >
          {loading
            ? <><RefreshCw size={14} style={{ animation:'spin 1s linear infinite' }}/> Researching…</>
            : <><Search size={14}/> Run Analysis</>
          }
        </button>

        {prevResult && !challengeMode && (
          <button onClick={() => setCM(true)}
            style={{
              display:'flex', alignItems:'center', gap:6,
              background:'rgba(245,158,11,0.1)', color:'#f59e0b',
              border:'1px solid rgba(245,158,11,0.2)', borderRadius:7,
              padding:'8px 16px', fontSize:13, cursor:'pointer', fontFamily:'Inter,sans-serif',
            }}
          >
            <AlertTriangle size={13}/> Challenge Answer
          </button>
        )}
        <span style={{ color:'#3a4560', fontSize:11, marginLeft:'auto', fontFamily:'IBM Plex Mono,monospace' }}>
          ⌘+Enter to run
        </span>
      </div>

      {/* Challenge panel */}
      {challengeMode && (
        <div style={{
          background:'rgba(245,158,11,0.05)', border:'1px solid rgba(245,158,11,0.2)',
          borderRadius:8, padding:'12px 14px',
          animation:'fadeIn 0.25s ease',
        }}>
          <p style={{ fontSize:12, color:'#f59e0b', marginBottom:8 }}>
            Challenge the previous answer. The pipeline will re-research with your context.
          </p>
          <textarea
            value={challengeReason}
            onChange={e => setCR(e.target.value)}
            placeholder="Provide a reason or counter-evidence…"
            rows={2}
            style={{
              width:'100%', background:'#0f1318', border:'1px solid rgba(245,158,11,0.2)',
              borderRadius:6, color:'#e8edf5', fontSize:13, padding:'8px 10px',
              outline:'none', fontFamily:'Inter,sans-serif', resize:'none',
            }}
          />
          <div style={{ display:'flex', gap:8, marginTop:8 }}>
            <button onClick={() => submit(prevResult.query, true)} disabled={loading}
              style={{
                background:'#f59e0b', color:'#0a0c0f', border:'none', borderRadius:6,
                padding:'7px 16px', fontSize:12, fontWeight:600, cursor:'pointer', fontFamily:'Inter,sans-serif',
              }}
            >
              {loading ? 'Re-researching…' : 'Re-Research'}
            </button>
            <button onClick={() => { setCM(false); setCR(''); }}
              style={{
                background:'transparent', color:'#8a97b0', border:'1px solid #1e2535',
                borderRadius:6, padding:'7px 14px', fontSize:12, cursor:'pointer', fontFamily:'Inter,sans-serif',
              }}
            >
              Cancel
            </button>
          </div>
        </div>
      )}

      {error && (
        <div style={{
          background:'rgba(239,68,68,0.08)', border:'1px solid rgba(239,68,68,0.2)',
          borderRadius:6, padding:'10px 12px', fontSize:13, color:'#ef4444',
        }}>
          {error}
        </div>
      )}
    </div>
  );
}
