import React, { useState } from 'react';
import Sidebar      from './components/Sidebar';
import QueryPanel   from './components/QueryPanel';
import ResultPanel  from './components/ResultPanel';
import './styles/globals.css';

function LoadingSkeleton() {
  return (
    <div style={{ display:'flex', flexDirection:'column', gap:16, marginTop:20 }}>
      <div style={{ display:'grid', gridTemplateColumns:'160px 1fr', gap:16 }}>
        <div className="skeleton" style={{ height:140, borderRadius:10 }}/>
        <div className="skeleton" style={{ height:140, borderRadius:10 }}/>
      </div>
      <div className="skeleton" style={{ height:40, borderRadius:8 }}/>
      <div className="skeleton" style={{ height:160, borderRadius:10 }}/>
      <div style={{ display:'flex', flexDirection:'column', gap:8 }}>
        {[...Array(3)].map((_,i) => (
          <div key={i} className="skeleton" style={{ height:52, borderRadius:8 }}/>
        ))}
      </div>
    </div>
  );
}

export default function App() {
  const [result,  setResult]  = useState(null);
  const [loading, setLoading] = useState(false);

  return (
    <div style={{ display:'flex', minHeight:'100vh' }}>
      <Sidebar/>

      <main style={{ flex:1, overflowY:'auto', padding:'32px 36px 60px' }}>
        {/* Page header */}
        <div style={{ marginBottom:28 }}>
          <h1 style={{ fontSize:28, color:'#e8edf5', marginBottom:6 }}>
            Legal &amp; Compliance Research
          </h1>
          <p style={{ color:'#4a5568', fontSize:13, fontFamily:'IBM Plex Mono,monospace' }}>
            Every answer is grounded, cited, and verified against your policy corpus.
          </p>
        </div>

        {/* Divider label */}
        <div style={{
          display:'flex', alignItems:'center', gap:10, marginBottom:20,
        }}>
          <div style={{ flex:1, height:1, background:'#1e2535' }}/>
          <span style={{
            fontSize:10, color:'#3a4560', fontFamily:'IBM Plex Mono,monospace',
            letterSpacing:1, textTransform:'uppercase',
          }}>
            Query Interface
          </span>
          <div style={{ flex:1, height:1, background:'#1e2535' }}/>
        </div>

        {/* Query */}
        <div style={{
          background:'#10141a', border:'1px solid #1e2535', borderRadius:12,
          padding:'20px 22px', marginBottom:24,
        }}>
          <QueryPanel onResult={setResult} onLoading={setLoading}/>
        </div>

        {/* Output */}
        {loading && <LoadingSkeleton/>}
        {!loading && result && (
          <div>
            <div style={{
              display:'flex', alignItems:'center', gap:10, marginBottom:16,
            }}>
              <div style={{ flex:1, height:1, background:'#1e2535' }}/>
              <span style={{
                fontSize:10, color:'#3a4560', fontFamily:'IBM Plex Mono,monospace',
                letterSpacing:1, textTransform:'uppercase',
              }}>
                Analysis Results
              </span>
              <div style={{ flex:1, height:1, background:'#1e2535' }}/>
            </div>
            <ResultPanel result={result}/>
          </div>
        )}

        {!loading && !result && (
          <div style={{
            textAlign:'center', padding:'60px 20px',
            color:'#3a4560', fontFamily:'IBM Plex Mono,monospace', fontSize:12,
          }}>
            <div style={{
              width:48, height:48, borderRadius:'50%', background:'#10141a',
              border:'1px solid #1e2535', display:'flex', alignItems:'center',
              justifyContent:'center', margin:'0 auto 16px',
            }}>
              <span style={{ fontSize:20 }}>⚖</span>
            </div>
            <p style={{ lineHeight:1.8 }}>
              Upload your policy corpus using the sidebar,<br/>
              then run a legal or compliance query above.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}
