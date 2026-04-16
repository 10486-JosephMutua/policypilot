import axios from 'axios';

const API = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  timeout: 120000,
});

API.interceptors.request.use(cfg => {
  console.log(`[API] ${cfg.method?.toUpperCase()} ${cfg.url}`);
  return cfg;
});

API.interceptors.response.use(
  r => r,
  err => {
    console.error('[API Error]', err.response?.data || err.message);
    return Promise.reject(err);
  }
);

export const queryAPI = {
  runQuery: (query) =>
    API.post('/api/query', { query }).then(r => r.data),

  challenge: (query, reason) =>
    API.post('/api/challenge', { query, reason }).then(r => r.data),
};

export const docsAPI = {
  uploadFile: (file, docType = 'policy') => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('doc_type', docType);
    return API.post('/api/documents/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then(r => r.data);
  },

  ingestText: (text, sourceName, docType = 'policy') =>
    API.post('/api/documents/ingest-text', {
      text,
      source_name: sourceName,
      doc_type: docType,
    }).then(r => r.data),

  listDocuments: () => API.get('/api/documents').then(r => r.data),
  getCount: () => API.get('/api/documents/count').then(r => r.data),
};

export const healthAPI = {
  check: () => API.get('/api/health').then(r => r.data),
};
