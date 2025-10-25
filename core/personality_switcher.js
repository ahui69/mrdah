// Przyciski do wyboru osobowości
const personalityButtons = `
<div class="personality-buttons">
    <button id="normalPersonality" class="personality-btn active" onclick="setPersonality('normal')">
        <span class="dot normal"></span> Normalny
    </button>
    <button id="casualPersonality" class="personality-btn" onclick="setPersonality('luzniak')">
        <span class="dot casual"></span> Ziomek
    </button>
    <button id="creativePersonality" class="personality-btn" onclick="setPersonality('kreatywny')">
        <span class="dot creative"></span> Literat
    </button>
    <button id="auctionPersonality" class="personality-btn" onclick="setPersonality('aukcja')">
        <span class="dot auction"></span> Aukcja
    </button>
</div>
`;

// Style dla przycisków
const personalityStyles = `
.personality-buttons {
    display: flex;
    gap: 8px;
    margin: 12px 0;
    flex-wrap: wrap;
    justify-content: center;
}

.personality-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    border-radius: var(--border-radius-sm);
    background: var(--surface-lighter);
    border: 1px solid var(--surface-border);
    color: var(--text-secondary);
    font-size: 13px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
}

.personality-btn:hover {
    background: var(--surface-border);
    color: var(--text-primary);
}

.personality-btn.active {
    background: var(--surface-border);
    color: var(--text-primary);
    box-shadow: 0 0 0 1px var(--primary-color);
}

.personality-btn .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
}

.dot.normal {
    background: #4CAF50;
}

.dot.casual {
    background: var(--personality-casual);
}

.dot.creative {
    background: var(--personality-creative);
}

.dot.auction {
    background: #2196F3;
}
`;

// Funkcja do zmiany osobowości
function setPersonality(mode) {
    currentPersonality = mode;
    localStorage.setItem('currentPersonality', mode);
    
    // Aktualizacja wyglądu przycisków
    document.querySelectorAll('.personality-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    const btnId = {
        'normal': 'normalPersonality',
        'luzniak': 'casualPersonality',
        'kreatywny': 'creativePersonality',
        'aukcja': 'auctionPersonality'
    }[mode];
    
    if (btnId) {
        document.getElementById(btnId).classList.add('active');
    }
    
    // Opcjonalnie: pokaż informację o zmianie trybu
    const messageText = {
        'normal': 'Przełączono na tryb normalny - profesjonalny asystent.',
        'luzniak': 'Przełączono na tryb ziomka - luźny, bezpośredni styl.',
        'kreatywny': 'Przełączono na tryb literata - kreatywny, artystyczny styl.',
        'aukcja': 'Przełączono na tryb aukcji - opisy sprzedażowe w luźnym stylu.'
    }[mode];
    
    // Możesz dodać wizualny feedback o zmianie trybu
    const toastElem = document.createElement('div');
    toastElem.className = 'toast-notification';
    toastElem.innerHTML = messageText;
    document.body.appendChild(toastElem);
    
    setTimeout(() => {
        toastElem.classList.add('show');
        setTimeout(() => {
            toastElem.classList.remove('show');
            setTimeout(() => {
                document.body.removeChild(toastElem);
            }, 300);
        }, 3000);
    }, 10);
}

// Inicjalizacja przycisków osobowości
function initPersonalityButtons() {
    // Dodaj style do dokumentu
    const styleElem = document.createElement('style');
    styleElem.textContent = personalityStyles + `
        .toast-notification {
            position: fixed;
            top: 80px;
            left: 50%;
            transform: translateX(-50%) translateY(-20px);
            background: var(--surface-dark);
            border: 1px solid var(--surface-border);
            color: var(--text-primary);
            padding: 12px 16px;
            border-radius: var(--border-radius);
            z-index: 1000;
            box-shadow: var(--box-shadow);
            opacity: 0;
            transition: transform 0.3s ease, opacity 0.3s ease;
            font-size: 14px;
        }
        
        .toast-notification.show {
            transform: translateX(-50%) translateY(0);
            opacity: 1;
        }
    `;
    document.head.appendChild(styleElem);
    
    // Dodaj przyciski do dokumentu
    const controlsElem = document.querySelector('.input-controls') || document.querySelector('.input-container');
    if (controlsElem) {
        const buttonsContainer = document.createElement('div');
        buttonsContainer.innerHTML = personalityButtons;
        controlsElem.parentNode.insertBefore(buttonsContainer, controlsElem);
        
        // Ustaw aktywny przycisk
        const activeBtn = {
            'normal': 'normalPersonality',
            'luzniak': 'casualPersonality',
            'kreatywny': 'creativePersonality',
            'aukcja': 'auctionPersonality'
        }[currentPersonality] || 'normalPersonality';
        
        document.getElementById(activeBtn).classList.add('active');
    }
}

// Wywołaj funkcję po załadowaniu strony
window.addEventListener('load', initPersonalityButtons);