import axios from 'axios';
import type { ChatRequest, ChatResponse, PsycheState } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token');
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

// ============================================================================
// 1. CHAT & ASSISTANT (3 endpoints)
// ============================================================================

export const chatAPI = {
  sendMessage: async (request: ChatRequest): Promise<ChatResponse> => {
    const { data } = await api.post<ChatResponse>('/chat/assistant', request);
    return data;
  },

  streamMessage: (request: ChatRequest): EventSource => {
    const params = new URLSearchParams({
      messages: JSON.stringify(request.messages),
      user_id: request.user_id || 'guest',
      use_memory: request.use_memory?.toString() || 'true',
      use_research: request.use_research?.toString() || 'true',
      internet_allowed: request.internet_allowed?.toString() || 'true',
      auto_learn: request.auto_learn?.toString() || 'true',
      use_batch_processing: request.use_batch_processing?.toString() || 'true',
    });
    const url = `${API_BASE}/chat/assistant/stream?${params}`;
    return new EventSource(url, { withCredentials: true });
  },

  autoLearn: async (topic: string, depth: 'shallow' | 'medium' | 'deep' = 'medium') => {
    const { data } = await api.post('/chat/auto', { topic, depth });
    return data;
  },
};

// ============================================================================
// 2. PSYCHE (10 endpoints)
// ============================================================================

export const psycheAPI = {
  getStatus: async (): Promise<PsycheState> => {
    const { data } = await api.get<PsycheState>('/psyche/status');
    return data;
  },

  updatePsyche: async (state: Partial<PsycheState>): Promise<void> => {
    await api.post('/psyche/save', state);
  },

  loadPsyche: async () => {
    const { data } = await api.get('/psyche/load');
    return data;
  },

  observeText: async (text: string) => {
    const { data } = await api.post('/psyche/observe', { text });
    return data;
  },

  addEpisode: async (episode: any) => {
    const { data } = await api.post('/psyche/episode', episode);
    return data;
  },

  reflect: async () => {
    const { data } = await api.get('/psyche/reflect');
    return data;
  },

  autoTune: async () => {
    const { data } = await api.get('/psyche/tune');
    return data;
  },

  reset: async () => {
    const { data } = await api.post('/psyche/reset');
    return data;
  },

  analyzeMessage: async (message: string) => {
    const { data } = await api.post('/psyche/analyze', { message });
    return data;
  },

  setMode: async (mode: string) => {
    const { data } = await api.post('/psyche/set-mode', { mode });
    return data;
  },

  enhancePrompt: async (prompt: string) => {
    const { data } = await api.post('/psyche/enhance-prompt', { prompt });
    return data;
  },
};

// ============================================================================
// 3. CODE EXECUTOR (13 endpoints)
// ============================================================================

export const codeAPI = {
  executeCode: async (code: string, language: string = 'python') => {
    const { data } = await api.post('/code/execute', { code, language });
    return data;
  },

  writeCode: async (filepath: string, content: string) => {
    const { data } = await api.post('/code/write', { filepath, content });
    return data;
  },

  readCode: async (filepath: string) => {
    const { data } = await api.post('/code/read', { filepath });
    return data;
  },

  runCommand: async (command: string, cwd?: string) => {
    const { data } = await api.post('/code/run', { command, cwd });
    return data;
  },

  installDeps: async (packages: string[]) => {
    const { data } = await api.post('/code/deps/install', { packages });
    return data;
  },

  listDeps: async () => {
    const { data } = await api.get('/code/deps/list');
    return data;
  },

  gitStatus: async () => {
    const { data } = await api.get('/code/git/status');
    return data;
  },

  gitCommit: async (message: string, files?: string[]) => {
    const { data } = await api.post('/code/git/commit', { message, files });
    return data;
  },

  gitPush: async (branch: string = 'main') => {
    const { data } = await api.post('/code/git/push', { branch });
    return data;
  },

  createProject: async (name: string, template: string) => {
    const { data } = await api.post('/code/project/create', { name, template });
    return data;
  },

  searchCode: async (query: string) => {
    const { data } = await api.post('/code/search', { query });
    return data;
  },

  analyzeCode: async (filepath: string) => {
    const { data } = await api.post('/code/analyze', { filepath });
    return data;
  },

  refactorCode: async (filepath: string, instructions: string) => {
    const { data } = await api.post('/code/refactor', { filepath, instructions });
    return data;
  },
};

// ============================================================================
// 4. FILES (8 endpoints)
// ============================================================================

export const filesAPI = {
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/files/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  downloadFile: async (filename: string) => {
    const { data } = await api.get(`/files/download/${filename}`, {
      responseType: 'blob',
    });
    return data;
  },

  listFiles: async () => {
    const { data } = await api.get('/files/list');
    return data;
  },

  deleteFile: async (filename: string) => {
    const { data } = await api.delete(`/files/delete/${filename}`);
    return data;
  },

  readFile: async (filepath: string) => {
    const { data } = await api.post('/files/read', { filepath });
    return data;
  },

  writeFile: async (filepath: string, content: string) => {
    const { data } = await api.post('/files/write', { filepath, content });
    return data;
  },

  searchFiles: async (query: string) => {
    const { data } = await api.post('/files/search', { query });
    return data;
  },

  getMetadata: async (filename: string) => {
    const { data } = await api.get(`/files/metadata/${filename}`);
    return data;
  },
};

// ============================================================================
// 5. TRAVEL (6 endpoints)
// ============================================================================

export const travelAPI = {
  searchFlights: async (from: string, to: string, date: string) => {
    const { data } = await api.post('/travel/flights/search', { from, to, date });
    return data;
  },

  searchHotels: async (city: string, checkIn: string, checkOut: string) => {
    const { data } = await api.post('/travel/hotels/search', { city, checkIn, checkOut });
    return data;
  },

  getWeather: async (city: string) => {
    const { data } = await api.get(`/travel/weather/${city}`);
    return data;
  },

  getAttractions: async (city: string) => {
    const { data } = await api.get(`/travel/attractions/${city}`);
    return data;
  },

  planItinerary: async (destination: string, days: number) => {
    const { data } = await api.post('/travel/itinerary/plan', { destination, days });
    return data;
  },

  getCurrencyRate: async (from: string, to: string) => {
    const { data } = await api.get(`/travel/currency/${from}/${to}`);
    return data;
  },
};

// ============================================================================
// 6. RESEARCH (4 endpoints) - core/research_endpoint.py
// ============================================================================

export const researchAPI = {
  // POST /api/research/search - ogólne wyszukiwanie w internecie
  search: async (query: string, topk: number = 5, mode: string = 'full') => {
    const { data } = await api.post('/research/search', { query, topk, mode });
    return data;
  },

  // POST /api/research/autonauka - auto-learning z web research
  autonauka: async (query: string, topk: number = 5, user_id: string = 'guest', save_to_ltm: boolean = true) => {
    const { data } = await api.post('/research/autonauka', { query, topk, user_id, save_to_ltm });
    return data;
  },

  // GET /api/research/sources - lista źródeł
  getSources: async () => {
    const { data } = await api.get('/research/sources');
    return data;
  },

  // GET /api/research/test - test endpointu
  test: async () => {
    const { data } = await api.get('/research/test');
    return data;
  },
};

// ============================================================================
// 7. NLP (8 endpoints)
// ============================================================================

export const nlpAPI = {
  analyzeText: async (text: string) => {
    const { data } = await api.post('/nlp/analyze', { text });
    return data;
  },

  extractEntities: async (text: string) => {
    const { data } = await api.post('/nlp/entities', { text });
    return data;
  },

  sentiment: async (text: string) => {
    const { data } = await api.post('/nlp/sentiment', { text });
    return data;
  },

  summarize: async (text: string, maxLength: number = 100) => {
    const { data } = await api.post('/nlp/summarize', { text, maxLength });
    return data;
  },

  translate: async (text: string, targetLang: string) => {
    const { data } = await api.post('/nlp/translate', { text, targetLang });
    return data;
  },

  keywords: async (text: string) => {
    const { data } = await api.post('/nlp/keywords', { text });
    return data;
  },

  classify: async (text: string, categories: string[]) => {
    const { data } = await api.post('/nlp/classify', { text, categories });
    return data;
  },

  similarity: async (text1: string, text2: string) => {
    const { data } = await api.post('/nlp/similarity', { text1, text2 });
    return data;
  },
};

// ============================================================================
// 8. WRITING (12 endpoints)
// ============================================================================

export const writingAPI = {
  generateText: async (prompt: string, style?: string) => {
    const { data } = await api.post('/writing/generate', { prompt, style });
    return data;
  },

  improveText: async (text: string) => {
    const { data } = await api.post('/writing/improve', { text });
    return data;
  },

  proofread: async (text: string) => {
    const { data } = await api.post('/writing/proofread', { text });
    return data;
  },

  paraphrase: async (text: string) => {
    const { data } = await api.post('/writing/paraphrase', { text });
    return data;
  },

  expandText: async (text: string, targetLength: number) => {
    const { data } = await api.post('/writing/expand', { text, targetLength });
    return data;
  },

  condenseText: async (text: string, targetLength: number) => {
    const { data } = await api.post('/writing/condense', { text, targetLength });
    return data;
  },

  writeEmail: async (subject: string, context: string) => {
    const { data } = await api.post('/writing/email', { subject, context });
    return data;
  },

  writeBlogPost: async (topic: string, keywords: string[]) => {
    const { data } = await api.post('/writing/blog', { topic, keywords });
    return data;
  },

  writeStory: async (genre: string, prompt: string) => {
    const { data } = await api.post('/writing/story', { genre, prompt });
    return data;
  },

  writeCode: async (description: string, language: string) => {
    const { data } = await api.post('/writing/code', { description, language });
    return data;
  },

  writePoem: async (theme: string, style?: string) => {
    const { data } = await api.post('/writing/poem', { theme, style });
    return data;
  },

  writeSummary: async (text: string, format: 'bullet' | 'paragraph' = 'paragraph') => {
    const { data } = await api.post('/writing/summary', { text, format });
    return data;
  },
};

// ============================================================================
// 9. TTS/STT (3 endpoints)
// ============================================================================

export const voiceAPI = {
  textToSpeech: async (text: string, voice?: string) => {
    const { data } = await api.post('/tts/speak', { text, voice }, {
      responseType: 'blob',
    });
    return data;
  },

  speechToText: async (audioFile: File) => {
    const formData = new FormData();
    formData.append('audio', audioFile);
    const { data } = await api.post('/stt/transcribe', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return data;
  },

  listVoices: async () => {
    const { data } = await api.get('/tts/voices');
    return data;
  },
};

// ============================================================================
// 10. BATCH PROCESSING (4 endpoints)
// ============================================================================

export const batchAPI = {
  submitBatch: async (tasks: any[]) => {
    const { data } = await api.post('/batch/submit', { tasks });
    return data;
  },

  getBatchStatus: async (batchId: string) => {
    const { data } = await api.get(`/batch/status/${batchId}`);
    return data;
  },

  cancelBatch: async (batchId: string) => {
    const { data } = await api.delete(`/batch/cancel/${batchId}`);
    return data;
  },

  listBatches: async () => {
    const { data } = await api.get('/batch/list');
    return data;
  },
};

// ============================================================================
// 11. SUGGESTIONS (4 endpoints)
// ============================================================================

export const suggestionsAPI = {
  getProactiveSuggestions: async () => {
    const { data } = await api.get('/suggestions/proactive');
    return data;
  },

  getContextualSuggestions: async (context: string) => {
    const { data } = await api.post('/suggestions/contextual', { context });
    return data;
  },

  rateSuggestion: async (suggestionId: string, rating: number) => {
    const { data } = await api.post('/suggestions/rate', { suggestionId, rating });
    return data;
  },

  dismissSuggestion: async (suggestionId: string) => {
    const { data } = await api.post('/suggestions/dismiss', { suggestionId });
    return data;
  },
};

// ============================================================================
// 12. ADMIN (4 endpoints)
// ============================================================================

export const adminAPI = {
  getSystemStats: async () => {
    const { data } = await api.get('/admin/stats');
    return data;
  },

  clearCache: async () => {
    const { data } = await api.post('/admin/cache/clear');
    return data;
  },

  exportData: async (format: 'json' | 'csv' = 'json') => {
    const { data } = await api.get(`/admin/export?format=${format}`);
    return data;
  },

  getLogs: async (lines: number = 100) => {
    const { data } = await api.get(`/admin/logs?lines=${lines}`);
    return data;
  },
};

// ============================================================================
// 13. CAPTCHA (2 endpoints)
// ============================================================================

export const captchaAPI = {
  solveCaptcha: async (imageUrl: string) => {
    const { data } = await api.post('/captcha/solve', { imageUrl });
    return data;
  },

  getCaptchaBalance: async () => {
    const { data } = await api.get('/captcha/balance');
    return data;
  },
};

// ============================================================================
// 14. PROMETHEUS (3 endpoints)
// ============================================================================

export const metricsAPI = {
  getMetrics: async () => {
    const { data } = await api.get('/metrics');
    return data;
  },

  getHealthCheck: async () => {
    const { data } = await api.get('/health');
    return data;
  },

  getReadiness: async () => {
    const { data } = await api.get('/ready');
    return data;
  },
};

// ============================================================================
// 15. INTERNAL (1 endpoint)
// ============================================================================

export const internalAPI = {
  getInternalUI: async () => {
    const { data } = await api.get('/internal/ui');
    return data;
  },
};

// ============================================================================
// HEALTH CHECK
// ============================================================================

export const healthCheck = async (): Promise<boolean> => {
  try {
    const { data } = await api.get('/health', { baseURL: '' });
    return data.status === 'healthy';
  } catch {
    return false;
  }
};

