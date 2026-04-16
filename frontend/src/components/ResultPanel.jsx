import React, { useState } from 'react';
import { BookOpen, GitBranch, CheckSquare, Database, AlertOctagon, RotateCcw } from 'lucide-react';
import ConfidenceGauge from './ConfidenceGauge';
import ClaimVerifier   from './ClaimVerifier';
import CitationGraph   from './CitationGraph';
import SourcePanel     from './SourcePanel';

const TABS = [
  { id:'answer',   icon:<BookOpen size={14}/>,     label:'Answer'       },
  { id:'claims',   icon:<CheckSquare size={14}/>,   label:'Claim Audit'  },
  { id:'graph',    icon:<GitBranch size={14}/>,     label:'Citation Graph'},
  { id:'sources',  icon:<Database size={14}/>,      label:'Sources'      },
];

const RETRIEVAL_LABELS = {
  Correct:   { label:'High Confidence Retrieval', color:'#22c55e' },
  Ambiguous: { label:'Partial Retrieval',          color:'#f59e0b' },
  Incorrect: { label:'Reformulation Applied',      color:'#ef4444' },
};

export default function ResultPanel({ result }) {
  const [tab, setTab] = useState('answer');
  if (!result) return null;

  const conf    = result.confidence || {};
  const score   = conf.score || 0;
  const label   = conf.label || 'Ambiguous';
  const action  = result.retrieval_action || 'Ambiguous';
  const rl      = RETRIEVAL_LABELS[action] || RETRIEVAL_LABELS.Ambiguous;
  const details = conf.details || {};

  return (
    <div style={{ animation:'fadeIn 0.4s ease' }}>
      {/* Header metrics */}
      <div style={{
        display:'grid', gridTemplateColumns:'160px 1fr',
        gap:16, marginBottom:20, alignItems:'stretch',
      }}>
        {/* Gauge */}
        <div style={{
          background:'#10141a', border:'1px solid #1e2535',
          borderRadius:10, padding:'16px 10px',
          display:'flex', flexDirection:'column', alignItems:'center', gap:8,
        }}>
          <ConfidenceGauge score={score} label={label} size={130}/>
          <p style={{ fontSize:10, color:'#4a5568', textAlign:'center', fontFamily:'IBM Plex Mono,monospace' }}>
            ANSWER CONFIDENCE
          </p>
        </div>

        {/* Meta stats */}
        <div style={{
          background:'#10141a', border:'1px solid #1e2535', borderRadius:10, padding:'16px',
          display:'flex', flexDirection:'column', gap:12,
        }}>
          {/* Retrieval action badge */}
          <div style={{ display:'flex', alignItems:'center', gap:8 }}>
            <span style={{
              fontSize:11, fontFamily:'IBM Plex Mono,monospace',
              color:rl.color, background:`${rl.color}18`,
              border:`1px solid ${rl.color}33`, borderRadius:4, padding:'2px 8px',
            }}>
              {rl.label}
            </span>
            {result.loop_count > 0 && (
              <span style={{ fontSize:11, color:'#4a5568', display:'flex', alignItems:'center', gap:4 }}>
                <RotateCcw size={11}/> {result.loop_count} reformulation(s)
              </span>
            )}
            {result.challenged && (
              <span style={{ fontSize:11, color:'#f59e0b', background:'rgba(245,158,11,0.1)',
                             border:'1px solid rgba(245,158,11,0.2)', borderRadius:4, padding:'2px 8px' }}>
                Re-researched
              </span>
            )}
          </div>

          {/* Claim breakdown */}
          {details.total > 0 && (
            <div>
              <p style={{ fontSize:11, color:'#4a5568', marginBottom:6, fontFamily:'IBM Plex Mono,monospace', letterSpacing:0.5 }}>
                CLAIM VERIFICATION BREAKDOWN
              </p>
              <div style={{ display:'flex', gap:10, flexWrap:'wrap' }}>
                {[
                  { label:'Verified',    val:details.correct,   col:'#22c55e' },
                  { label:'Uncertain',   val:details.ambiguous, col:'#f59e0b' },
                  { label:'Unsupported', val:details.incorrect, col:'#ef4444' },
                  { label:'Total',       val:details.total,     col:'#4a5568' },
                ].map(s => (
                  <div key={s.label} style={{
                    background:'#0f1318', border:'1px solid #1a2030', borderRadius:6,
                    padding:'6px 12px', textAlign:'center',
                  }}>
                    <p style={{ fontSize:20, fontFamily:'DM Serif Display,serif', color:s.col }}>{s.val}</p>
                    <p style={{ fontSize:10, color:'#4a5568', fontFamily:'IBM Plex Mono,monospace' }}>{s.label}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Temporal warnings */}
          {result.temporal_flags?.length > 0 && (
            <div style={{
              background:'rgba(245,158,11,0.07)', border:'1px solid rgba(245,158,11,0.18)',
              borderRadius:6, padding:'8px 12px',
            }}>
              {result.temporal_flags.map((f,i) => (
                <p key={i} style={{ fontSize:12, color:'#f59e0b', display:'flex', alignItems:'flex-start', gap:6 }}>
                  <AlertOctagon size={12} style={{ marginTop:2, flexShrink:0 }}/> {f}
                </p>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display:'flex', gap:2, marginBottom:16,
        background:'#0f1318', borderRadius:8, padding:4,
        border:'1px solid #1e2535',
      }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            style={{
              flex:1, display:'flex', alignItems:'center', justifyContent:'center', gap:6,
              padding:'8px 10px', border:'none', borderRadius:6, cursor:'pointer',
              fontSize:12, fontFamily:'Inter,sans-serif', fontWeight:500,
              transition:'all 0.15s',
              background: tab === t.id ? '#1a2030' : 'transparent',
              color:       tab === t.id ? '#e8edf5' : '#4a5568',
            }}>
            {t.icon} <span style={{ display:'none' }}>{t.label}</span>
            <span>{t.label}</span>
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div key={tab} style={{ animation:'fadeIn 0.25s ease' }}>
        {tab === 'answer' && (
          <div style={{
            background:'#10141a', border:'1px solid #1e2535', borderRadius:10, padding:'20px 22px',
          }}>
            <p style={{
              fontSize:14, color:'#c8d3e8', lineHeight:1.8, whiteSpace:'pre-wrap',
              fontFamily:'Inter,sans-serif',
            }}>
              {result.answer}
            </p>
          </div>
        )}

        {tab === 'claims' && (
          <ClaimVerifier claims={result.verified_claims || []}/>
        )}

        {tab === 'graph' && (
          <div style={{ background:'#10141a', border:'1px solid #1e2535', borderRadius:10, padding:16 }}>
            <p style={{ fontSize:12, color:'#4a5568', marginBottom:12 }}>
              Interactive provenance graph — drag nodes to rearrange. Each claim is linked to its source sentence.
            </p>
            <CitationGraph graph={result.citation_graph}/>
          </div>
        )}

        {tab === 'sources' && (
          <SourcePanel sources={result.sources || []}/>
        )}
      </div>
    </div>
  );
}
