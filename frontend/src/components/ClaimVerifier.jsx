import React, { useState } from 'react';
import { ChevronDown, ChevronUp, CheckCircle, AlertTriangle, XCircle, Quote } from 'lucide-react';

const ICONS = {
  Correct:   <CheckCircle size={14} color="#22c55e"/>,
  Ambiguous: <AlertTriangle size={14} color="#f59e0b"/>,
  Incorrect: <XCircle size={14} color="#ef4444"/>,
};

const COLORS = {
  Correct:   { bg:'rgba(34,197,94,0.07)',  border:'rgba(34,197,94,0.2)',  text:'#22c55e' },
  Ambiguous: { bg:'rgba(245,158,11,0.07)', border:'rgba(245,158,11,0.2)', text:'#f59e0b' },
  Incorrect: { bg:'rgba(239,68,68,0.07)',  border:'rgba(239,68,68,0.2)',  text:'#ef4444' },
};

function ClaimRow({ claim, index }) {
  const [open, setOpen] = useState(false);
  const label = claim.label || 'Ambiguous';
  const col   = COLORS[label];
  const pct   = Math.round((claim.confidence || 0) * 100);
  const cit   = claim.citation || {};

  return (
    <div style={{
      border: `1px solid ${col.border}`,
      borderRadius: 8,
      background: col.bg,
      overflow: 'hidden',
      marginBottom: 8,
    }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', display: 'flex', alignItems: 'flex-start', gap: 10,
          padding: '10px 14px', background: 'transparent', border: 'none',
          cursor: 'pointer', textAlign: 'left',
        }}
      >
        <span style={{ marginTop: 1, flexShrink: 0 }}>{ICONS[label]}</span>
        <span style={{ flex: 1, fontSize: 13, color: '#c8d3e8', lineHeight: 1.5 }}>
          {claim.claim}
        </span>
        <span style={{
          flexShrink: 0, fontSize: 11, fontFamily: 'IBM Plex Mono,monospace',
          color: col.text, background: col.bg, border: `1px solid ${col.border}`,
          borderRadius: 4, padding: '1px 7px',
        }}>
          {pct}%
        </span>
        <span style={{ color: col.text, flexShrink: 0 }}>
          {open ? <ChevronUp size={14}/> : <ChevronDown size={14}/>}
        </span>
      </button>

      {open && cit.sentence && (
        <div style={{
          borderTop: `1px solid ${col.border}`,
          padding: '10px 14px 12px 38px',
        }}>
          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
            <Quote size={12} color="#4a5568" style={{ marginTop: 3, flexShrink: 0 }}/>
            <p style={{ fontSize: 12, color: '#8a97b0', fontStyle: 'italic', lineHeight: 1.6 }}>
              {cit.sentence}
            </p>
          </div>
          <p style={{ fontSize: 11, color: '#4a5568', marginTop: 6, fontFamily:'IBM Plex Mono,monospace' }}>
            Source: {cit.source_name || 'Unknown'}
            {cit.grounding_score != null &&
              ` · Grounding: ${Math.round(cit.grounding_score * 100)}%`}
          </p>
        </div>
      )}
    </div>
  );
}

export default function ClaimVerifier({ claims = [] }) {
  if (!claims.length) return null;
  const correct   = claims.filter(c => c.label === 'Correct').length;
  const ambiguous = claims.filter(c => c.label === 'Ambiguous').length;
  const incorrect = claims.filter(c => c.label === 'Incorrect').length;

  return (
    <div>
      {/* Summary bar */}
      <div style={{
        display: 'flex', gap: 16, marginBottom: 14, padding: '8px 12px',
        background: '#0f1318', borderRadius: 6, border: '1px solid #1e2535',
        fontSize: 12, fontFamily: 'IBM Plex Mono,monospace',
      }}>
        <span style={{ color: '#22c55e' }}>✓ {correct} verified</span>
        <span style={{ color: '#f59e0b' }}>~ {ambiguous} uncertain</span>
        <span style={{ color: '#ef4444' }}>✗ {incorrect} unsupported</span>
        <span style={{ color: '#4a5568', marginLeft: 'auto' }}>{claims.length} claims total</span>
      </div>

      {/* Claims list */}
      {claims.map((c, i) => <ClaimRow key={i} claim={c} index={i}/>)}
    </div>
  );
}
