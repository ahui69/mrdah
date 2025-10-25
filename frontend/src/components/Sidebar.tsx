import { Plus, MessageSquare, Trash2, Download, Upload } from 'lucide-react';
import { useChatStore } from '../store/chatStore';
import type { Conversation } from '../types';

export default function Sidebar() {
  const { conversations, currentConversationId, addConversation, deleteConversation, setCurrentConversation, exportConversations, importConversations } = useChatStore();

  const handleNewChat = () => {
    const newConv: Conversation = {
      id: Date.now().toString(),
      title: 'New Chat',
      messages: [],
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    addConversation(newConv);
  };

  const handleExport = () => {
    const data = exportConversations();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `mordzix-export-${Date.now()}.json`;
    a.click();
  };

  const handleImport = () => {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'application/json';
    input.onchange = (e: any) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = (event) => {
          importConversations(event.target?.result as string);
        };
        reader.readAsText(file);
      }
    };
    input.click();
  };

  return (
    <div className="w-64 bg-gray-100 dark:bg-gray-800 flex flex-col border-r border-gray-200 dark:border-gray-700">
      <div className="p-4">
        <button
          onClick={handleNewChat}
          className="w-full flex items-center gap-2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
        >
          <Plus size={20} />
          <span>New Chat</span>
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {conversations.map((conv) => (
          <div
            key={conv.id}
            onClick={() => setCurrentConversation(conv.id)}
            className={`group flex items-center justify-between p-3 mb-1 rounded-lg cursor-pointer transition-colors ${
              currentConversationId === conv.id
                ? 'bg-gray-200 dark:bg-gray-700'
                : 'hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <div className="flex items-center gap-2 flex-1 min-w-0">
              <MessageSquare size={16} />
              <span className="truncate text-sm">{conv.title}</span>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                deleteConversation(conv.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500 hover:text-white rounded transition"
            >
              <Trash2 size={14} />
            </button>
          </div>
        ))}
      </div>

      <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
        <button
          onClick={handleExport}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition"
        >
          <Download size={16} />
          <span>Export</span>
        </button>
        <button
          onClick={handleImport}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition"
        >
          <Upload size={16} />
          <span>Import</span>
        </button>
      </div>
    </div>
  );
}
