export interface Message {
  role: string;
  content: string;
  attachments?: Array<Record<string, any>>;
}

export interface Conversation {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
}

export interface ChatRequest {
  messages: Message[];
  user_id?: string;
  use_memory?: boolean;
  use_research?: boolean;
  internet_allowed?: boolean;
  auto_learn?: boolean;
  use_batch_processing?: boolean;
}

export interface ChatResponse {
  ok: boolean;
  answer: string;
  sources?: Array<Record<string, any>>;
  metadata?: Record<string, any>;
}

export interface PsycheState {
  mood: number;
  energy: number;
  focus: number;
  style: string;
}

export interface Settings {
  theme: 'light' | 'dark';
  temperature?: number;
  maxTokens?: number;
  model?: string;
  authToken?: string;
  userId?: string;
  useMemory: boolean;
  useResearch: boolean;
  autoLearn: boolean;
  internetAccess?: boolean;
  useBatchProcessing?: boolean;
}
