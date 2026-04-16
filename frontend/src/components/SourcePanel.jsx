import React, { useState } from 'react';
import { FileText, ChevronDown, ChevronUp } from 'lucide-react';

function SourceCard({ source, index }) {
  const [open, setOpen] = useState(false);
  const score = source.rerank_score || 0;
  const pct   = Math.round(score * 100);
  const bar   = score >= 0.7 ? '#22c55e' : score >= 0.4 ? '#f59e0b' : '#ef4444';

  return (
    <div style={{
      border: '1px solid #1e2535', borderRadius: 8,
      background: '#0f1318', marginBottom: 8, overflow: 'hidden',
    }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: 10,
          padding: '10px 14px', background: 'transparent', border: 'none',
          cursor: 'pointer', textAlign: 'left',
        }}
      >
        <span style={{
          width: 22, height: 22, borderRadius: '50%', background: '#1a2030',
          border: '1px solid #252d3d', display: 'flex', alignItems: 'center',
          justifyContent: 'center', fontSize: 10, color: '#4f8ef7', flexShrink: 0,
          fontFamily: 'IBM Plex Mono,monospace',
        }}>
          {index + 1}
        </span>
        <FileText size={13} color="#4a5568" style={{ flexShrink:0 }}/>
        <span style={{ flex: 1, fontSize: 13, color: '#c8d3e8', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
          {source.source_name}
        </span>

        {/* Relevance bar */}
        <div style={{ display:'flex', alignItems:'center', gap:6, flexShrink:0 }}>
          <div style={{ width: 60, height: 4, background:'#1e2535', borderRadius:2, overflow:'hidden' }}>
            <div style={{ width:`${pct}%`, height:'100%', background:bar, borderRadius:2 }}/>
          </div>
          <span style={{ fontSize:11, color:bar, fontFamily:'IBM Plex Mono,monospace', minWidth:30 }}>
            {pct}%
          </span>
        </div>
        <span style={{ color:'#4a5568' }}>
          {open ? <ChevronUp size={13}/> : <ChevronDown size={13}/>}
        </span>
      </button>

      {open && (
        <div style={{ borderTop:'1px solid #1e2535', padding:'10px 14px 12px' }}>
          {source.sentences?.length > 0 ? (
            <div style={{ display:'flex', flexDirection:'column', gap:4 }}>
              {source.sentences.slice(0,6).map((s, i) => (
                <p key={i} style={{
                  fontSize:12, color:'#8a97b0', lineHeight:1.6, padding:'4px 8px',
                  borderLeft:'2px solid #252d3d', borderRadius:2,
                }}>
                  <span style={{ color:'#3a4560', fontFamily:'IBM Plex Mono,monospace', fontSize:10 }}>§{i+1} </span>
                  {s}
                </p>
              ))}
              {source.sentences.length > 6 &&
                <p style={{ fontSize:11, color:'#4a5568' }}>+{source.sentences.length - 6} more sentences</p>}
            </div>
          ) : (
            <p style={{ fontSize:12, color:'#8a97b0' }}>{source.text_snippet}</p>
          )}
          <p style={{ fontSize:11, color:'#3a4560', marginTop:8, fontFamily:'IBM Plex Mono,monospace' }}>
            doc_id: {source.doc_id?.substring(0, 12)}… · chunk #{source.chunk_index}
          </p>
        </div>
      )}
    </div>
  );
}

export default function SourcePanel({ sources = [] }) {
  if (!sources.length) return (
    <p style={{ color:'#4a5568', fontSize:13 }}>No sources retrieved.</p>
  );
  return (
    <div>
      {sources.map((s, i) => <SourceCard key={i} source={s} index={i}/>)}
    </div>
  );
}
