import React, { useEffect, useState } from 'react';
import { Shield, Database, Upload, ChevronRight, FileText } from 'lucide-react';
import DocumentUploader from './DocumentUploader';
import { docsAPI } from '../services/api';

export default function Sidebar() {
  const [open, setOpen]   = useState(false);
  const [docs, setDocs]   = useState([]);
  const [count, setCount] = useState(0);

  const refresh = async () => {
    try {
      const [d, c] = await Promise.all([docsAPI.listDocuments(), docsAPI.getCount()]);
      setDocs(d.documents || []);
      setCount(c.count || 0);
    } catch {}
  };

  useEffect(() => { refresh(); }, []);

  return (
    <aside style={{
      width: 260, flexShrink:0,
      background:'#10141a', borderRight:'1px solid #1e2535',
      display:'flex', flexDirection:'column', height:'100vh', position:'sticky', top:0,
    }}>
      {/* Logo */}
      <div style={{ padding:'22px 20px 16px', borderBottom:'1px solid #1e2535' }}>
        <div style={{ display:'flex', alignItems:'center', gap:9 }}>
          <Shield size={20} color="#4f8ef7"/>
          <span style={{ fontFamily:'DM Serif Display,serif', fontSize:18, color:'#e8edf5', letterSpacing:0.3 }}>
            PolicyPilot
          </span>
        </div>
        <p style={{ fontSize:11, color:'#3a4560', marginTop:5, fontFamily:'IBM Plex Mono,monospace', lineHeight:1.5 }}>
          Hallucination-proof RAG<br/>for legal &amp; compliance
        </p>
      </div>

      {/* Stats */}
      <div style={{
        display:'flex', gap:0, borderBottom:'1px solid #1e2535',
      }}>
        {[
          { label:'Documents', val:docs.length, icon:<FileText size={12}/> },
          { label:'Chunks',    val:count,        icon:<Database size={12}/> },
        ].map(s => (
          <div key={s.label} style={{
            flex:1, padding:'12px 16px', borderRight:'1px solid #1e2535',
            display:'flex', flexDirection:'column', gap:4,
          }}>
            <div style={{ display:'flex', alignItems:'center', gap:5, color:'#4a5568' }}>
              {s.icon}
              <span style={{ fontSize:10, fontFamily:'IBM Plex Mono,monospace', textTransform:'uppercase', letterSpacing:0.5 }}>
                {s.label}
              </span>
            </div>
            <span style={{ fontSize:20, fontFamily:'DM Serif Display,serif', color:'#4f8ef7' }}>{s.val}</span>
          </div>
        ))}
      </div>

      {/* Upload toggle */}
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          display:'flex', alignItems:'center', gap:8,
          padding:'12px 20px', background:'transparent', border:'none',
          borderBottom:'1px solid #1e2535', cursor:'pointer',
          color:'#8a97b0', fontSize:13, fontFamily:'Inter,sans-serif',
          textAlign:'left',
        }}
      >
        <Upload size={14} color="#4f8ef7"/>
        <span style={{ flex:1 }}>Upload Documents</span>
        <ChevronRight size={13} style={{ transform: open ? 'rotate(90deg)' : 'none', transition:'0.2s' }}/>
      </button>

      {open && (
        <div style={{ padding:'14px 16px', borderBottom:'1px solid #1e2535', animation:'fadeIn 0.2s ease' }}>
          <DocumentUploader onIngested={() => refresh()}/>
        </div>
      )}

      {/* Document list */}
      <div style={{ flex:1, overflowY:'auto', padding:'8px 0' }}>
        {docs.length === 0 ? (
          <p style={{ fontSize:12, color:'#3a4560', padding:'12px 20px', lineHeight:1.6 }}>
            No documents ingested yet.<br/>Upload PDFs or policy files above.
          </p>
        ) : (
          docs.map(d => (
            <div key={d.doc_id} style={{
              display:'flex', alignItems:'center', gap:8,
              padding:'7px 20px', borderBottom:'1px solid rgba(30,37,53,0.5)',
            }}>
              <FileText size={12} color="#4a5568" style={{ flexShrink:0 }}/>
              <div style={{ overflow:'hidden' }}>
                <p style={{
                  fontSize:12, color:'#8a97b0', overflow:'hidden',
                  textOverflow:'ellipsis', whiteSpace:'nowrap',
                }}>
                  {d.source_name}
                </p>
                <p style={{ fontSize:10, color:'#3a4560', fontFamily:'IBM Plex Mono,monospace' }}>
                  {d.doc_type}
                </p>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Bottom badge */}
      <div style={{ padding:'12px 20px', borderTop:'1px solid #1e2535' }}>
        <p style={{ fontSize:10, color:'#3a4560', fontFamily:'IBM Plex Mono,monospace', lineHeight:1.6 }}>
          Powered by Self-CRAG + tri-layer<br/>confidence scoring (2025)
        </p>
      </div>
    </aside>
  );
}
