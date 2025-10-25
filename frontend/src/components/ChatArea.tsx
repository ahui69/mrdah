import React, { useState, useEffect, useRef } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import { Send, Paperclip } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import { chatAPI } from '../services/api';
import type { Message, ChatRequest } from '../types';

export const ChatArea: React.FC = () => {
  const {
    currentConversationId,
    conversations,
    addMessage,
    settings,
  } = useChatStore();

  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const activeConversation = conversations.find(c => c.id === currentConversationId);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [activeConversation?.messages]);

  const handleSend = async () => {
    if (!input.trim() || !currentConversationId || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      attachments: [],
    };

    addMessage(currentConversationId, userMessage);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      const request: ChatRequest = {
        messages: [...(activeConversation?.messages || []), userMessage],
        user_id: settings.userId || 'default',
        use_memory: settings.useMemory,
        use_research: settings.useResearch,
        internet_allowed: settings.internetAccess,
        auto_learn: settings.autoLearn,
        use_batch_processing: settings.useBatchProcessing,
      };

      const response = await chatAPI.sendMessage(request);

      if (!response.ok) {
        throw new Error('Backend returned ok=false');
      }

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
        attachments: response.sources || [],
      };

      addMessage(currentConversationId, assistantMessage);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Network error';
      setError(errorMsg);
      console.error('Chat error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const renderMessage = (msg: Message) => {
    const html = DOMPurify.sanitize(marked.parse(msg.content) as string);
    const isUser = msg.role === 'user';
    
    return (
      <div className={`flex gap-4 px-4 py-6 ${
        isUser ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-900'
      }`}>
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-sm">
          {isUser ? '👤' : '🤖'}
        </div>
        <div className="flex-1 prose dark:prose-invert max-w-none" dangerouslySetInnerHTML={{ __html: html }} />
      </div>
    );
  };

  if (!currentConversationId) {
    return (
      <div className="flex-1 flex items-center justify-center bg-white dark:bg-gray-800">
        <p className="text-gray-500 dark:text-gray-400 text-lg">Select a conversation or create a new one</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white dark:bg-gray-800">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {activeConversation?.messages.map((msg, idx) => (
          <div key={idx}>{renderMessage(msg)}</div>
        ))}
        {isLoading && (
          <div className="flex gap-4 px-4 py-6 bg-gray-50 dark:bg-gray-900">
            <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center text-sm">🤖</div>
            <div className="flex-1 text-gray-600 dark:text-gray-400 italic">Thinking...</div>
          </div>
        )}
        {error && (
          <div className="mx-4 my-2 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-800 dark:text-red-200">
            {error}
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-2 items-end">
            <button className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors" title="Upload file">
              <Paperclip size={20} className="text-gray-500 dark:text-gray-400" />
            </button>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Type your message... (Shift+Enter for new line)"
              disabled={isLoading}
              rows={1}
              className="flex-1 resize-none rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-900 px-4 py-3 focus:outline-none focus:ring-2 focus:ring-gray-400 dark:focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
              style={{ minHeight: '44px', maxHeight: '200px' }}
            />
            <button 
              onClick={handleSend} 
              disabled={isLoading || !input.trim()}
              className="p-3 rounded-lg bg-gray-800 hover:bg-gray-700 disabled:bg-gray-300 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors"
              title="Send message"
            >
              <Send size={20} className="text-white" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default ChatArea;
