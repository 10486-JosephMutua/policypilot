import React, { useState, useRef, useCallback } from 'react';
import { Upload, FileText, CheckCircle, AlertCircle, X, Loader } from 'lucide-react';
import { docsAPI } from '../services/api';

const ACCEPT = '.pdf,.txt,.docx,.md';

export default function DocumentUploader({ onIngested }) {
  const [dragging, setDragging] = useState(false);
  const [files, setFiles]       = useState([]);
  const inputRef = useRef(null);

  const processFile = useCallback(async (file) => {
    const id = `${file.name}-${Date.now()}`;
    setFiles(prev => [...prev, { id, name: file.name, status: 'uploading' }]);
    try {
      const result = await docsAPI.uploadFile(file);
      setFiles(prev => prev.map(f => f.id === id ? { ...f, status: 'done', result } : f));
      onIngested?.(result);
    } catch (err) {
      const msg = err.response?.data?.error || err.message;
      setFiles(prev => prev.map(f => f.id === id ? { ...f, status: 'error', error: msg } : f));
    }
  }, [onIngested]);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragging(false);
    Array.from(e.dataTransfer.files).forEach(processFile);
  }, [processFile]);

  const handleChange = (e) => {
    Array.from(e.target.files || []).forEach(processFile);
    e.target.value = '';
  };

  return (
    <div>
      {/* Drop zone */}
      <div
        onDragOver={e => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        style={{
          border: `2px dashed ${dragging ? '#4f8ef7' : '#1e2535'}`,
          borderRadius: 10,
          padding: '28px 20px',
          textAlign: 'center',
          cursor: 'pointer',
          transition: 'all 0.2s',
          background: dragging ? 'rgba(79,142,247,0.06)' : 'transparent',
        }}
      >
        <Upload size={22} color={dragging ? '#4f8ef7' : '#4a5568'} style={{ margin:'0 auto 8px' }}/>
        <p style={{ color: '#8a97b0', fontSize: 13 }}>
          Drop files here or <span style={{ color:'#4f8ef7' }}>browse</span>
        </p>
        <p style={{ color: '#3a4560', fontSize: 11, marginTop: 4 }}>
          PDF · DOCX · TXT · Markdown — max 50 MB
        </p>
        <input ref={inputRef} type="file" accept={ACCEPT} multiple hidden onChange={handleChange}/>
      </div>

      {/* File list */}
      {files.length > 0 && (
        <div style={{ marginTop: 12, display:'flex', flexDirection:'column', gap:6 }}>
          {files.map(f => (
            <div key={f.id} style={{
              display:'flex', alignItems:'center', gap:8,
              padding:'8px 12px', background:'#0f1318',
              border:'1px solid #1e2535', borderRadius:6,
            }}>
              <FileText size={13} color="#4a5568"/>
              <span style={{ flex:1, fontSize:12, color:'#8a97b0', overflow:'hidden', textOverflow:'ellipsis', whiteSpace:'nowrap' }}>
                {f.name}
              </span>
              {f.status === 'uploading' && <Loader size={13} color="#4f8ef7" style={{ animation:'spin 1s linear infinite' }}/>}
              {f.status === 'done'      && <CheckCircle size={13} color="#22c55e"/>}
              {f.status === 'error'     && (
                <span style={{ fontSize:11, color:'#ef4444', display:'flex', alignItems:'center', gap:4 }}>
                  <AlertCircle size={11}/>
                  {f.error?.substring(0,30)}
                </span>
              )}
              <button onClick={() => setFiles(prev => prev.filter(x => x.id !== f.id))}
                      style={{ background:'none', border:'none', cursor:'pointer', color:'#3a4560', padding:0 }}>
                <X size={12}/>
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
