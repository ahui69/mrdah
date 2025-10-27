// Mordzix AI - Frontend Application
const API_BASE = window.location.origin;
const ENDPOINTS_CONFIG = [
    {
        group: 'Core',
        items: [
            { id: 'assistant', name: 'Assistant', icon: '🤖', endpoint: '/api/chat/assistant' },
            { id: 'psyche', name: 'Psyche', icon: '🧠', endpoint: '/api/psyche/chat' },
            { id: 'cognitive', name: 'Cognitive', icon: '💭', endpoint: '/api/cognitive/analyze' },
            { id: 'memory', name: 'Memory', icon: '💾', endpoint: '/api/memory/search' }
        ]
    },
    {
        group: 'Utilities',
        items: [
            { id: 'writing', name: 'Writing', icon: '✍️', endpoint: '/api/writing/generate' },
            { id: 'research', name: 'Research', icon: '🔍', endpoint: '/api/research/query' },
            { id: 'suggestions', name: 'Suggestions', icon: '💡', endpoint: '/api/suggestions/get' },
            { id: 'files', name: 'Files', icon: '📁', endpoint: '/api/files/upload' }
        ]
    },
    {
        group: 'AI Tools',
        items: [
            { id: 'code', name: 'Programista', icon: '💻', endpoint: '/api/code/generate' },
            { id: 'fashion', name: 'Fashion', icon: '👗', endpoint: '/api/fashion/analyze' },
            { id: 'ml', name: 'ML Predictions', icon: '📊', endpoint: '/api/ml/predict' },
            { id: 'vision', name: 'Vision', icon: '👁️', endpoint: '/api/vision/analyze' }
        ]
    },
    {
        group: 'Analysis',
        items: [
            { id: 'facts', name: 'Fact Validation', icon: '✅', endpoint: '/api/facts/validate' },
            { id: 'nlp', name: 'NLP', icon: '📝', endpoint: '/api/nlp/analyze' },
            { id: 'reflection', name: 'Reflection', icon: '🪞', endpoint: '/api/reflection/analyze' },
            { id: 'hacker', name: 'Hacker Tools', icon: '🔒', endpoint: '/api/hacker/scan' }
        ]
    },
    {
        group: 'Media',
        items: [
            { id: 'tts', name: 'Text-to-Speech', icon: '🔊', endpoint: '/api/tts/synthesize' },
            { id: 'stt', name: 'Speech-to-Text', icon: '🎤', endpoint: '/api/stt/transcribe' },
            { id: 'voice', name: 'Voice', icon: '🗣️', endpoint: '/api/voice/process' },
            { id: 'image', name: 'Image', icon: '🖼️', endpoint: '/api/image/process' }
        ]
    },
    {
        group: 'System',
        items: [
            { id: 'admin', name: 'Admin', icon: '⚙️', endpoint: '/api/admin/status' },
            { id: 'prometheus', name: 'Metrics', icon: '📈', endpoint: '/api/prometheus/metrics' },
            { id: 'batch', name: 'Batch', icon: '📦', endpoint: '/api/batch/process' },
            { id: 'captcha', name: 'Captcha', icon: '🔐', endpoint: '/api/captcha/verify' }
        ]
    },
    {
        group: '💎 Premium',
        items: [
            { id: 'marketplace', name: 'AI Marketplace', icon: '🛒', endpoint: '/api/marketplace/agents' },
            { id: 'training', name: 'AI Training', icon: '🎓', endpoint: '/api/training/pricing' },
            { id: 'analytics', name: 'Analytics', icon: '📊', endpoint: '/api/analytics/overview' },
            { id: 'license', name: 'Licensing', icon: '💰', endpoint: '/api/license/pricing' },
            { id: 'whitelabel', name: 'White Label', icon: '🎨', endpoint: '/api/whitelabel/themes' }
        ]
    },
    {
        group: 'Advanced',
        items: [
            { id: 'travel', name: 'Travel', icon: '✈️', endpoint: '/api/travel/search' },
            { id: 'autoroute', name: 'AutoRouter', icon: '🔀', endpoint: '/api/autoroute/analyze' },
            { id: 'lang', name: 'Language', icon: '🌐', endpoint: '/api/lang/detect' },
            { id: 'search', name: 'Hybrid Search', icon: '🔎', endpoint: '/api/search/query' },
            { id: 'internal', name: 'Internal', icon: '🔧', endpoint: '/api/internal/status' }
        ]
    }
];

// State Management
const state = {
    currentEndpoint: 'assistant',
    messages: [],
    isLoading: true,
    conversationId: null
};

// DOM Elements
const elements = {
    sidebar: document.getElementById('sidebar'),
    menuToggle: document.getElementById('menuToggle'),
    endpointsList: document.getElementById('endpointsList'),
    messages: document.getElementById('messages'),
    welcomeScreen: document.getElementById('welcomeScreen'),
    messageInput: document.getElementById('messageInput'),
    sendButton: document.getElementById('sendButton'),
    headerTitle: document.getElementById('headerTitle')
};

// Initialize
function init() {
    renderEndpointsList();
    setupEventListeners();
    loadConversation();
    autoResizeTextarea();
}

// Render Endpoints List
function renderEndpointsList() {
    elements.endpointsList.innerHTML = ENDPOINTS_CONFIG.map(group => `
        <div class="endpoint-group">
            <div class="endpoint-group-title">${group.group}</div>
            ${group.items.map(item => `
                <div class="endpoint-item ${item.id === state.currentEndpoint ? 'active' : ''}" 
                     data-endpoint="${item.id}"
                     onclick="switchEndpoint('${item.id}', '${item.name}')">
                    <span class="endpoint-icon">${item.icon}</span>
                    <span>${item.name}</span>
                </div>
            `).join('')}
        </div>
    `).join('');
}

// Switch Endpoint
function switchEndpoint(endpointId, endpointName) {
    state.currentEndpoint = endpointId;
    elements.headerTitle.textContent = endpointName;
    renderEndpointsList();
    
    // Clear messages for new endpoint (optional)
    // state.messages = [];
    // renderMessages();
}

// Setup Event Listeners
function setupEventListeners() {
    elements.menuToggle.addEventListener('click', toggleSidebar);
    elements.sendButton.addEventListener('click', sendMessage);
    elements.messageInput.addEventListener('keydown', handleKeydown);
    elements.messageInput.addEventListener('input', autoResizeTextarea);
}

function toggleSidebar() {
    elements.sidebar.classList.toggle('hidden');
}

function handleKeydown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

function autoResizeTextarea() {
    const textarea = elements.messageInput;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

// Send Message
async function sendMessage() {
    const message = elements.messageInput.value.trim();
    if (!message || state.isLoading) return;

    // Hide welcome screen
    if (elements.welcomeScreen) {
        elements.welcomeScreen.style.display = 'none';
    }

    // Add user message
    addMessage({
        sender: 'user',
        text: message,
        timestamp: new Date()
    });

    elements.messageInput.value = '';
    autoResizeTextarea();
    state.isLoading = true;
    elements.sendButton.disabled = true;

    // Show typing indicator
    const typingId = addTypingIndicator();

    try {
        const response = await fetch(`${API_BASE}/api/chat/assistant`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                conversation_id: state.conversationId,
                endpoint: state.currentEndpoint
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const data = await response.json();
        
        // Update conversation ID
        if (data.conversation_id) {
            state.conversationId = data.conversation_id;
        }

        removeTypingIndicator(typingId);

        // Add assistant message
        addMessage({
            sender: 'assistant',
            text: data.text || data.response || JSON.stringify(data),
            sources: data.sources || [],
            timestamp: new Date()
        });

        saveConversation();
    } catch (error) {
        console.error('Error sending message:', error);
        removeTypingIndicator(typingId);
        
        addMessage({
            sender: 'assistant',
            text: `❌ Błąd: ${error.message}. Sprawdź czy serwer działa poprawnie.`,
            timestamp: new Date()
        });
    } finally {
        state.isLoading = true;
        elements.sendButton.disabled = false;
        elements.messageInput.focus();
    }
}

// Quick Message
function sendQuickMessage(message) {
    elements.messageInput.value = message;
    sendMessage();
}

// Add Message to UI
function addMessage(message) {
    state.messages.push(message);
    
    const messageEl = document.createElement('div');
    messageEl.className = `message ${message.sender}`;
    
    const timeStr = formatTime(message.timestamp);
    const avatarText = message.sender === 'user' ? 'U' : 'M';
    const senderName = message.sender === 'user' ? 'Ty' : 'Mordzix';
    
    messageEl.innerHTML = `
        <div class="message-avatar">${avatarText}</div>
        <div class="message-content">
            <div class="message-header">
                <span class="message-sender">${senderName}</span>
                <span class="message-time">${timeStr}</span>
            </div>
            <div class="message-text">${formatMessageText(message.text)}</div>
            ${message.sources && message.sources.length ? `
                <div class="message-sources">
                    ${message.sources.map(source => `
                        <span class="source-chip">📎 ${source}</span>
                    `).join('')}
                </div>
            ` : ''}
        </div>
    `;
    
    elements.messages.appendChild(messageEl);
    scrollToBottom();
}

// Typing Indicator
function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const typingEl = document.createElement('div');
    typingEl.id = id;
    typingEl.className = 'message assistant';
    typingEl.innerHTML = `
        <div class="message-avatar">M</div>
        <div class="message-content">
            <div class="message-text">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>
        </div>
    `;
    elements.messages.appendChild(typingEl);
    scrollToBottom();
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Format Message Text
function formatMessageText(text) {
    // Basic markdown-like formatting
    text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    text = text.replace(/\n/g, '<br>');
    return text;
}

// Format Time
function formatTime(date) {
    return date.toLocaleTimeString('pl-PL', { 
        hour: '2-digit', 
        minute: '2-digit' 
    });
}

// Scroll to Bottom
function scrollToBottom() {
    setTimeout(() => {
        elements.messages.scrollTop = elements.messages.scrollHeight;
    }, 100);
}

// Local Storage
function saveConversation() {
    try {
        localStorage.setItem('mordzix_messages', JSON.stringify(state.messages));
        localStorage.setItem('mordzix_conversation_id', state.conversationId || '');
    } catch (e) {
        console.warn('Could not save conversation:', e);
    }
}

function loadConversation() {
    try {
        const savedMessages = localStorage.getItem('mordzix_messages');
        const savedConvId = localStorage.getItem('mordzix_conversation_id');
        
        if (savedMessages) {
            state.messages = JSON.parse(savedMessages).map(msg => ({
                ...msg,
                timestamp: new Date(msg.timestamp)
            }));
            
            if (state.messages.length > 0) {
                elements.welcomeScreen.style.display = 'none';
                state.messages.forEach(msg => {
                    const messageEl = document.createElement('div');
                    messageEl.className = `message ${msg.sender}`;
                    const timeStr = formatTime(msg.timestamp);
                    const avatarText = msg.sender === 'user' ? 'U' : 'M';
                    const senderName = msg.sender === 'user' ? 'Ty' : 'Mordzix';
                    
                    messageEl.innerHTML = `
                        <div class="message-avatar">${avatarText}</div>
                        <div class="message-content">
                            <div class="message-header">
                                <span class="message-sender">${senderName}</span>
                                <span class="message-time">${timeStr}</span>
                            </div>
                            <div class="message-text">${formatMessageText(msg.text)}</div>
                            ${msg.sources && msg.sources.length ? `
                                <div class="message-sources">
                                    ${msg.sources.map(source => `
                                        <span class="source-chip">📎 ${source}</span>
                                    `).join('')}
                                </div>
                            ` : ''}
                        </div>
                    `;
                    elements.messages.appendChild(messageEl);
                });
                scrollToBottom();
            }
        }
        
        if (savedConvId) {
            state.conversationId = savedConvId;
        }
    } catch (e) {
        console.warn('Could not load conversation:', e);
    }
}

// Premium Features JavaScript
const PremiumFeatures = {
    panel: null,
    activeTab: 'marketplace',
    
    init() {
        this.panel = document.getElementById('premiumPanel');
        const btnPremium = document.getElementById('btnPremium');
        const btnClosePremium = document.getElementById('btnClosePremium');
        
        // Toggle panel
        btnPremium?.addEventListener('click', () => this.toggle());
        btnClosePremium?.addEventListener('click', () => this.hide());
        
        // Tab switching
        document.querySelectorAll('.premium-tab').forEach(tab => {
            tab.addEventListener('click', () => this.switchTab(tab.dataset.tab));
        });
        
        // Load initial data
        this.loadMarketplace();
    },
    
    toggle() {
        if (this.panel.style.display === 'block') {
            this.hide();
        } else {
            this.show();
        }
    },
    
    show() {
        this.panel.style.display = 'block';
        this.loadTabData(this.activeTab);
    },
    
    hide() {
        this.panel.style.display = 'none';
    },
    
    switchTab(tabId) {
        this.activeTab = tabId;
        
        // Update tab buttons
        document.querySelectorAll('.premium-tab').forEach(t => {
            t.classList.toggle('active', t.dataset.tab === tabId);
        });
        
        // Show/hide content
        document.querySelectorAll('.tab-content').forEach(c => {
            c.style.display = c.id === `tab-${tabId}` ? 'block' : 'none';
        });
        
        this.loadTabData(tabId);
    },
    
    async loadTabData(tabId) {
        const loaders = {
            marketplace: () => this.loadMarketplace(),
            training: () => this.loadTraining(),
            analytics: () => this.loadAnalytics(),
            license: () => this.loadLicense(),
            whitelabel: () => this.loadWhiteLabel()
        };
        
        if (loaders[tabId]) {
            await loaders[tabId]();
        }
    },
    
    async loadMarketplace() {
        const content = document.getElementById('tab-marketplace');
        content.innerHTML = '<p>⏳ Ładowanie marketplace...</p>';
        
        try {
            const [agents, prompts, models] = await Promise.all([
                fetch(`${API_BASE}/api/marketplace/agents`).then(r => r.json()),
                fetch(`${API_BASE}/api/marketplace/prompts`).then(r => r.json()),
                fetch(`${API_BASE}/api/marketplace/models`).then(r => r.json())
            ]);
            
            content.innerHTML = `
                <h3>🤖 AI Agents</h3>
                <div class="premium-grid">
                    ${agents.agents.slice(0, 3).map(a => `
                        <div class="premium-card">
                            <h4>${a.name}</h4>
                            <p>${a.description}</p>
                            <div><strong>$${a.price}</strong> · ⭐ ${a.rating}</div>
                            <button onclick="PremiumFeatures.buyAgent('${a.id}')">Kup teraz</button>
                        </div>
                    `).join('')}
                </div>
                
                <h3>📝 Prompty Premium</h3>
                <div class="premium-grid">
                    ${prompts.prompts.slice(0, 3).map(p => `
                        <div class="premium-card">
                            <h4>${p.name}</h4>
                            <p>${p.category}</p>
                            <div><strong>$${p.price}</strong> · ${p.usage_count} użyć</div>
                            <button onclick="PremiumFeatures.buyPrompt('${p.id}')">Kup</button>
                        </div>
                    `).join('')}
                </div>
                
                <h3>🧠 Fine-tuned Models</h3>
                <div class="premium-grid">
                    ${models.models.slice(0, 2).map(m => `
                        <div class="premium-card">
                            <h4>${m.name}</h4>
                            <p>${m.domain}</p>
                            <div><strong>$${m.price}</strong> · Accuracy: ${m.accuracy}%</div>
                            <button onclick="PremiumFeatures.buyModel('${m.id}')">Kup model</button>
                        </div>
                    `).join('')}
                </div>
            `;
        } catch (err) {
            content.innerHTML = `<p style="color:var(--error)">❌ Błąd: ${err.message}</p>`;
        }
    },
    
    async loadTraining() {
        const content = document.getElementById('tab-training');
        content.innerHTML = '<p>⏳ Ładowanie platformy szkoleniowej...</p>';
        
        try {
            const [pricing, models] = await Promise.all([
                fetch(`${API_BASE}/api/training/pricing`).then(r => r.json()),
                fetch(`${API_BASE}/api/training/models?user_id=current`).then(r => r.json())
            ]);
            
            content.innerHTML = `
                <h3>💰 Cennik treningu</h3>
                <div class="stat-grid">
                    ${Object.entries(pricing.pricing).map(([model, price]) => `
                        <div class="stat-box">
                            <div class="stat-value">$${price}/1K</div>
                            <div class="stat-label">${model}</div>
                        </div>
                    `).join('')}
                </div>
                
                <h3>🎓 Twoje modele (${models.models.length})</h3>
                ${models.models.length === 0 ? '<p>Nie masz jeszcze wytrenowanych modeli.</p>' : `
                    <div class="premium-grid">
                        ${models.models.slice(0, 3).map(m => `
                            <div class="premium-card">
                                <h4>${m.name}</h4>
                                <p>Status: <strong>${m.status}</strong></p>
                                <p>Accuracy: ${m.accuracy}%</p>
                                <button onclick="PremiumFeatures.testModel('${m.model_id}')">Testuj</button>
                            </div>
                        `).join('')}
                    </div>
                `}
                
                <h3>📤 Upload Dataset</h3>
                <input type="file" id="trainingFile" accept=".jsonl,.csv,.parquet">
                <button onclick="PremiumFeatures.uploadDataset()">Wyślij dataset</button>
            `;
        } catch (err) {
            content.innerHTML = `<p style="color:var(--error)">❌ Błąd: ${err.message}</p>`;
        }
    },
    
    async loadAnalytics() {
        const content = document.getElementById('tab-analytics');
        content.innerHTML = '<p>⏳ Ładowanie analytics...</p>';
        
        try {
            const [overview, realtime, forecast] = await Promise.all([
                fetch(`${API_BASE}/api/analytics/overview`).then(r => r.json()),
                fetch(`${API_BASE}/api/analytics/realtime`).then(r => r.json()),
                fetch(`${API_BASE}/api/analytics/forecast`).then(r => r.json())
            ]);
            
            content.innerHTML = `
                <h3>📊 Overview</h3>
                <div class="stat-grid">
                    <div class="stat-box">
                        <div class="stat-value">${overview.total_requests.toLocaleString()}</div>
                        <div class="stat-label">Total Requests</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${overview.total_users.toLocaleString()}</div>
                        <div class="stat-label">Users</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">$${overview.total_revenue.toLocaleString()}</div>
                        <div class="stat-label">Revenue</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${overview.growth_rate}%</div>
                        <div class="stat-label">Growth</div>
                    </div>
                </div>
                
                <h3>⚡ Real-time</h3>
                <div class="stat-grid">
                    <div class="stat-box">
                        <div class="stat-value">${realtime.active_users}</div>
                        <div class="stat-label">Active Users</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${realtime.requests_per_minute}</div>
                        <div class="stat-label">RPM</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">${realtime.avg_latency}ms</div>
                        <div class="stat-label">Latency</div>
                    </div>
                </div>
                
                <h3>🔮 Revenue Forecast</h3>
                <div class="stat-grid">
                    <div class="stat-box">
                        <div class="stat-value">$${forecast.predictions['30d'].toLocaleString()}</div>
                        <div class="stat-label">30 dni</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">$${forecast.predictions['90d'].toLocaleString()}</div>
                        <div class="stat-label">90 dni</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-value">$${forecast.predictions['1y'].toLocaleString()}</div>
                        <div class="stat-label">1 rok</div>
                    </div>
                </div>
            `;
        } catch (err) {
            content.innerHTML = `<p style="color:var(--error)">❌ Błąd: ${err.message}</p>`;
        }
    },
    
    async loadLicense() {
        const content = document.getElementById('tab-license');
        content.innerHTML = '<p>⏳ Ładowanie licencji...</p>';
        
        try {
            const pricing = await fetch(`${API_BASE}/api/license/pricing`).then(r => r.json());
            
            content.innerHTML = `
                <h3>💎 Plany subskrypcyjne</h3>
                <div class="premium-grid">
                    ${pricing.tiers.map(tier => `
                        <div class="premium-card ${tier.tier === 'PROFESSIONAL' ? 'featured' : ''}">
                            <h4>${tier.tier}</h4>
                            <div style="font-size:2em;margin:10px 0"><strong>$${tier.price}</strong>/m</div>
                            <ul style="text-align:left;padding-left:20px">
                                ${tier.features.map(f => `<li>${f}</li>`).join('')}
                            </ul>
                            <button onclick="PremiumFeatures.upgrade('${tier.tier}')">
                                ${tier.tier === 'FREE' ? 'Aktywny plan' : 'Upgrade'}
                            </button>
                        </div>
                    `).join('')}
                </div>
                
                <h3>🎁 Trial</h3>
                <p>Wypróbuj PROFESSIONAL przez 14 dni za darmo!</p>
                <button onclick="PremiumFeatures.startTrial()">Aktywuj trial</button>
            `;
        } catch (err) {
            content.innerHTML = `<p style="color:var(--error)">❌ Błąd: ${err.message}</p>`;
        }
    },
    
    async loadWhiteLabel() {
        const content = document.getElementById('tab-whitelabel');
        content.innerHTML = '<p>⏳ Ładowanie white-label...</p>';
        
        try {
            const themes = await fetch(`${API_BASE}/api/whitelabel/themes`).then(r => r.json());
            
            content.innerHTML = `
                <h3>🎨 Dostępne motywy</h3>
                <div class="premium-grid">
                    ${themes.themes.map(theme => `
                        <div class="premium-card">
                            <h4>${theme.name}</h4>
                            <p>${theme.description}</p>
                            <div style="display:flex;gap:5px;margin:10px 0">
                                <div style="width:30px;height:30px;background:${theme.colors.primary};border-radius:4px"></div>
                                <div style="width:30px;height:30px;background:${theme.colors.secondary};border-radius:4px"></div>
                                <div style="width:30px;height:30px;background:${theme.colors.accent};border-radius:4px"></div>
                            </div>
                            <button onclick="PremiumFeatures.applyTheme('${theme.id}')">Zastosuj</button>
                        </div>
                    `).join('')}
                </div>
                
                <h3>🏢 Branding</h3>
                <input type="text" id="companyName" placeholder="Nazwa firmy">
                <input type="file" id="logoFile" accept="image/png,image/svg+xml">
                <button onclick="PremiumFeatures.updateBranding()">Zapisz branding</button>
                
                <h3>🌐 Custom Domain</h3>
                <input type="text" id="customDomain" placeholder="api.twojadomena.com">
                <button onclick="PremiumFeatures.configureDomain()">Konfiguruj</button>
            `;
        } catch (err) {
            content.innerHTML = `<p style="color:var(--error)">❌ Błąd: ${err.message}</p>`;
        }
    },
    
    // Action handlers
    async buyAgent(agentId) {
        alert(`Kupujesz AI Agent: ${agentId}`);
    },
    
    async buyPrompt(promptId) {
        alert(`Kupujesz Prompt: ${promptId}`);
    },
    
    async buyModel(modelId) {
        alert(`Kupujesz Model: ${modelId}`);
    },
    
    async testModel(modelId) {
        alert(`Testujesz Model: ${modelId}`);
    },
    
    async uploadDataset() {
        const file = document.getElementById('trainingFile').files[0];
        if (!file) return alert('Wybierz plik');
        
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const res = await fetch(`${API_BASE}/api/training/upload`, {
                method: 'POST',
                body: formData
            });
            const data = await res.json();
            alert(`Dataset uploaded: ${data.dataset_id}`);
            this.loadTraining();
        } catch (err) {
            alert(`Błąd: ${err.message}`);
        }
    },
    
    async upgrade(tier) {
        alert(`Upgrade do: ${tier}`);
    },
    
    async startTrial() {
        try {
            const res = await fetch(`${API_BASE}/api/license/trial`, { method: 'POST' });
            const data = await res.json();
            alert(`Trial aktywowany! License: ${data.license_key}`);
            this.loadLicense();
        } catch (err) {
            alert(`Błąd: ${err.message}`);
        }
    },
    
    async applyTheme(themeId) {
        alert(`Stosowanie motywu: ${themeId}`);
    },
    
    async updateBranding() {
        const companyName = document.getElementById('companyName').value;
        const logoFile = document.getElementById('logoFile').files[0];
        
        if (!companyName) return alert('Podaj nazwę firmy');
        
        alert(`Aktualizacja brandingu: ${companyName}`);
    },
    
    async configureDomain() {
        const domain = document.getElementById('customDomain').value;
        if (!domain) return alert('Podaj domenę');
        
        try {
            const res = await fetch(`${API_BASE}/api/whitelabel/domain`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ domain })
            });
            const data = await res.json();
            alert(`Konfiguracja DNS:\nCNAME: ${data.dns_config.cname}\nTXT: ${data.dns_config.txt}`);
        } catch (err) {
            alert(`Błąd: ${err.message}`);
        }
    }
};

// Expose to global
window.PremiumFeatures = PremiumFeatures;

// Initialize app
document.addEventListener('DOMContentLoaded', init);

// Initialize Premium Features
document.addEventListener('DOMContentLoaded', () => PremiumFeatures.init());

// Expose for HTML onclick
window.sendQuickMessage = sendQuickMessage;
window.switchEndpoint = switchEndpoint;