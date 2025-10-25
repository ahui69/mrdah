import { useEffect } from 'react';
import { useChatStore } from './store/chatStore';
import Sidebar from './components/Sidebar';
import ChatArea from './components/ChatArea';
import SettingsPanel from './components/SettingsPanel';

export default function App() {
  const { settings, currentConversationId, addConversation } = useChatStore();

  useEffect(() => {
    if (settings.theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [settings.theme]);

  // Auto-create first conversation if none exists
  useEffect(() => {
    if (!currentConversationId) {
      addConversation({
        id: Date.now().toString(),
        title: 'New Chat',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      });
    }
  }, []);

  return (
    <div className="flex h-screen bg-white dark:bg-gray-900 text-gray-900 dark:text-gray-100 overflow-hidden">
      <Sidebar />
      <ChatArea />
      <SettingsPanel />
    </div>
  );
}
