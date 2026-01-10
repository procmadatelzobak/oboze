/**
 * Ó bože - Chat Interface
 * Handles WebSocket communication and chat UI
 */

class ChatInterface {
    constructor(messagesId, inputId, sendBtnId, simulateBtnId, statusBarId, gameEngine) {
        this.messagesContainer = document.getElementById(messagesId);
        this.inputField = document.getElementById(inputId);
        this.sendBtn = document.getElementById(sendBtnId);
        this.simulateBtn = document.getElementById(simulateBtnId);
        this.statusBar = document.getElementById(statusBarId);
        this.game = gameEngine;

        // Current scenario ID
        this.currentScenarioId = 'default';

        // Pending animation data
        this.pendingAnimation = null;
        this.pendingNarrative = null;

        // Connect WebSocket
        this.connect();

        // Event listeners
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.simulateBtn.addEventListener('click', () => this.startSimulation());
        this.inputField.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
    }

    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

        this.ws.onopen = () => {
            this.setStatus('Připojeno');
        };

        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.ws.onclose = () => {
            this.setStatus('Odpojeno - obnovuji...');
            setTimeout(() => this.connect(), 3000);
        };

        this.ws.onerror = (error) => {
            this.setStatus('Chyba připojení');
            console.error('WebSocket error:', error);
        };
    }

    handleMessage(data) {
        switch (data.type) {
            case 'scenario':
                this.loadScenario(data.data);
                break;

            case 'status':
                if (data.status === 'thinking') {
                    this.setStatus('Bože přemýšlí...');
                    this.addMessage('Bože přemýšlí...', 'system', true);
                }
                break;

            case 'response':
                this.handleResponse(data);
                break;

            case 'error':
                this.setStatus('Chyba');
                this.addMessage('Chyba: ' + data.errors.join(', '), 'system');
                this.sendBtn.disabled = false;
                break;
        }
    }

    loadScenario(scenario) {
        // Clear previous messages
        this.messagesContainer.innerHTML = '';

        // Reset game
        this.game.reset();

        // Load entities into game
        this.game.loadEntities(scenario.entities);

        // Show scenario description
        this.addMessage(scenario.description, 'agent');
        this.setStatus('Scénář načten: ' + scenario.name);

        // Enable input
        this.sendBtn.disabled = false;
        this.simulateBtn.disabled = true;
        this.pendingAnimation = null;
        this.pendingNarrative = null;
    }

    loadScenarioById(scenarioId) {
        this.currentScenarioId = scenarioId;
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({
                type: 'load_scenario',
                scenario_id: scenarioId
            }));
        }
    }

    restart() {
        this.loadScenarioById(this.currentScenarioId);
    }

    handleResponse(data) {
        // Remove thinking message
        const thinkingMsg = this.messagesContainer.querySelector('.thinking');
        if (thinkingMsg) {
            thinkingMsg.remove();
        }

        // Store pending data
        this.pendingAnimation = data.animation;
        this.pendingNarrative = data.narrative;

        // Enable simulation button
        this.simulateBtn.disabled = false;
        this.setStatus('Připraveno ke spuštění simulace');

        // Add hint message
        this.addMessage('Simulace připravena. Klikni na "Spustit simulaci".', 'system');
    }

    sendMessage() {
        const text = this.inputField.value.trim();
        if (!text || this.sendBtn.disabled) return;

        // Add user message to chat
        this.addMessage(text, 'user');

        // Send to server
        this.ws.send(JSON.stringify({
            type: 'user_input',
            text: text
        }));

        // Clear input and disable send
        this.inputField.value = '';
        this.sendBtn.disabled = true;
    }

    startSimulation() {
        if (!this.pendingAnimation) return;

        this.simulateBtn.disabled = true;
        this.setStatus('Simulace běží...');

        // Remove hint message
        const hintMsgs = this.messagesContainer.querySelectorAll('.message.system');
        hintMsgs.forEach(msg => {
            if (msg.textContent.includes('Simulace připravena')) {
                msg.remove();
            }
        });

        // Start animation
        this.game.startAnimation(this.pendingAnimation, () => {
            // Animation complete - show narrative
            this.setStatus('Simulace dokončena');
            this.addMessage(this.pendingNarrative, 'agent');

            // Reset state
            this.pendingAnimation = null;
            this.pendingNarrative = null;
            this.sendBtn.disabled = false;

            // Add end message
            this.addMessage('Scénář skončil. Klikni na "Restart scénáře" nebo vyber nový v menu.', 'system');
        });
    }

    addMessage(text, type, isThinking = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        if (isThinking) {
            messageDiv.classList.add('thinking');
        }

        const labelDiv = document.createElement('div');
        labelDiv.className = 'message-label';
        labelDiv.textContent = type === 'user' ? 'Ty' : type === 'agent' ? 'Bože' : 'Systém';

        const textDiv = document.createElement('div');
        textDiv.textContent = text;

        messageDiv.appendChild(labelDiv);
        messageDiv.appendChild(textDiv);

        this.messagesContainer.appendChild(messageDiv);
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    setStatus(status) {
        this.statusBar.textContent = status;
    }
}
