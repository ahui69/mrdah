import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Conversation, Message, Settings } from '../types';

interface ChatState {
  conversations: Conversation[];
  currentConversationId: string | null;
  settings: Settings;
  addConversation: (conversation: Conversation) => void;
  deleteConversation: (id: string) => void;
  setCurrentConversation: (id: string) => void;
  addMessage: (conversationId: string, message: Message) => void;
  updateSettings: (settings: Partial<Settings>) => void;
  exportConversations: () => string;
  importConversations: (data: string) => void;
  clearAll: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set, get) => ({
      conversations: [],
      currentConversationId: null,
      settings: {
        theme: typeof window !== 'undefined' && window.matchMedia 
          ? (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
          : 'dark',
        temperature: 0.7,
        maxTokens: 2000,
        model: 'gpt-4-turbo-preview',
        useMemory: true,
        useResearch: true,
        autoLearn: true,
      },
      addConversation: (conversation) =>
        set((state) => ({
          conversations: [conversation, ...state.conversations],
          currentConversationId: conversation.id,
        })),
      deleteConversation: (id) =>
        set((state) => ({
          conversations: state.conversations.filter((c) => c.id !== id),
          currentConversationId:
            state.currentConversationId === id ? state.conversations[0]?.id || null : state.currentConversationId,
        })),
      setCurrentConversation: (id) => set({ currentConversationId: id }),
      addMessage: (conversationId, message) =>
        set((state) => ({
          conversations: state.conversations.map((c) =>
            c.id === conversationId
              ? { ...c, messages: [...c.messages, message], updatedAt: Date.now(), title: c.messages.length === 0 ? message.content.slice(0, 50) : c.title }
              : c
          ),
        })),
      updateSettings: (newSettings) =>
        set((state) => {
          const updated = { ...state.settings, ...newSettings };
          // Persist theme to localStorage separately for instant load
          if (newSettings.theme && typeof window !== 'undefined') {
            localStorage.setItem('mordzix-theme', newSettings.theme);
            document.documentElement.classList.toggle('dark', newSettings.theme === 'dark');
          }
          return { settings: updated };
        }),
      exportConversations: () => JSON.stringify({ conversations: get().conversations, settings: get().settings, exportedAt: Date.now() }),
      importConversations: (data) => {
        try {
          const parsed = JSON.parse(data);
          set({ conversations: parsed.conversations || [], settings: parsed.settings || get().settings });
        } catch (error) {
          console.error('Import failed:', error);
        }
      },
      clearAll: () => set({ conversations: [], currentConversationId: null }),
    }),
    { name: 'mordzix-chat-storage' }
  )
);
