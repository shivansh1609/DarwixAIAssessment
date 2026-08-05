/**
 * TalentBridge Voice Agent — Web Client
 * ======================================
 * Uses browser-native Web Speech API (free) for STT
 * and edge-tts via backend API (free) for TTS.
 *
 * No API keys needed on the client side.
 */

const API_BASE = window.location.origin;
let sessionId = crypto.randomUUID();
let isCallActive = false;
let recognition = null;
let isListening = false;
let isSpeaking = false;
let callStartTime = null;
let transcriptData = [];

// ─── Initialize ────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    checkBrowserSupport();
    checkBackendHealth();
    setMicButtonState('idle');
});

function checkBrowserSupport() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        updateStatus('Browser not supported — use Chrome', 'error');
        setMicButtonState('error');
        document.getElementById('btnCall').disabled = true;
        document.getElementById('callHint').textContent =
            'Web Speech API requires Google Chrome. Please open this page in Chrome.';
        return false;
    }
    return true;
}

async function checkBackendHealth() {
    try {
        const resp = await fetch(`${API_BASE}/api/health`);
        const data = await resp.json();
        document.getElementById('kbStatus').textContent =
            `${data.kb_stats?.total_records || 0} records indexed`;
    } catch (e) {
        document.getElementById('kbStatus').textContent = 'Offline';
    }
}

function setMicButtonState(state) {
    const btn = document.getElementById('btnCall');
    btn.classList.remove('active', 'listening', 'speaking', 'disconnected', 'error');

    if (!state || state === 'idle') {
        document.body.classList.remove('is-recording', 'is-speaking');
        return;
    }

    btn.classList.add(state);
    document.body.classList.toggle('is-recording', state === 'active' || state === 'listening');
    document.body.classList.toggle('is-speaking', state === 'speaking');
}

// ─── Call Control ──────────────────────────────────────────────

async function toggleCall() {
    if (isCallActive) {
        endCall();
    } else {
        startCall();
    }
}

async function startCall() {
    if (!checkBrowserSupport()) return;

    isCallActive = true;
    callStartTime = new Date();
    sessionId = crypto.randomUUID();
    transcriptData = [];

    const btn = document.getElementById('btnCall');
    setMicButtonState('active');
    btn.classList.add('active');
    document.getElementById('btnText').textContent = 'End Call';
    document.getElementById('callHint').textContent = 'Call in progress...';
    document.getElementById('agentAvatar').closest('.call-panel').classList.add('active');
    document.getElementById('waveform').classList.add('active');
    updateStatus('Connected', 'active');

    clearTranscriptUI();

    const greeting = "Hello! Thank you for reaching out to TalentBridge. I'm Sarah, your screening coordinator. I'd love to learn a bit about your background and answer any questions you have about the position you applied for. Could you start by confirming your name and which role you're interested in?";
    addMessage('bot', greeting);

    await speakText(greeting);
    startListening();
}

function endCall() {
    isCallActive = false;
    stopListening();

    const btn = document.getElementById('btnCall');
    btn.classList.remove('active');
    setMicButtonState('idle');
    document.getElementById('btnText').textContent = 'Start Screening Call';
    document.getElementById('callHint').textContent = 'Call ended. Click to start a new conversation.';
    document.getElementById('agentAvatar').closest('.call-panel').classList.remove('active');
    document.getElementById('waveform').classList.remove('active');
    updateStatus('Ready', '');

    addMessage('system', '— Call ended —');
}

// ─── Speech Recognition (FREE — Web Speech API) ───────────────

function startListening() {
    if (!isCallActive || isSpeaking) return;

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognition.maxAlternatives = 1;

    let finalTranscript = '';
    let interimDiv = null;

    recognition.onstart = () => {
        isListening = true;
        setMicButtonState('listening');
        updateStatus('Listening...', 'listening');
    };

    recognition.onresult = (event) => {
        let interim = '';
        finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
            const transcript = event.results[i][0].transcript;
            if (event.results[i].isFinal) {
                finalTranscript += transcript;
            } else {
                interim += transcript;
            }
        }

        if (interim && !interimDiv) {
            interimDiv = addMessage('user', interim, true);
        } else if (interim && interimDiv) {
            interimDiv.querySelector('.message-text').textContent = interim;
        }
    };

    recognition.onend = () => {
        isListening = false;

        if (finalTranscript.trim()) {
            if (interimDiv) {
                interimDiv.remove();
                interimDiv = null;
            }

            addMessage('user', finalTranscript.trim());
            sendToAgent(finalTranscript.trim());
        } else if (isCallActive && !isSpeaking) {
            setTimeout(() => startListening(), 500);
        }
    };

    recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        isListening = false;

        if (event.error === 'no-speech' && isCallActive) {
            setTimeout(() => startListening(), 1000);
        } else if (event.error === 'aborted') {
            // Intentional stop — do nothing
        } else {
            setMicButtonState('error');
            updateStatus(`STT Error: ${event.error}`, 'error');
            setTimeout(() => startListening(), 2000);
        }
    };

    recognition.start();
}

function stopListening() {
    if (recognition) {
        try { recognition.abort(); } catch (e) {}
        recognition = null;
    }
    isListening = false;
}

// ─── Send to Agent Backend ─────────────────────────────────────

async function sendToAgent(message) {
    if (!isCallActive) return;

    updateStatus('Thinking...', 'active');
    const thinkingMsg = addMessage('bot', '...', false, true);

    try {
        const resp = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId }),
        });

        const data = await resp.json();
        const reply = data.response;

        if (thinkingMsg) thinkingMsg.remove();
        addMessage('bot', reply);
        await speakText(reply);

        if (isCallActive) {
            startListening();
        }

    } catch (error) {
        console.error('Chat API error:', error);
        if (thinkingMsg) thinkingMsg.remove();
        addMessage('bot', "I'm sorry, I'm having a brief connection issue. Could you please repeat that?");
        if (isCallActive) {
            setTimeout(() => startListening(), 2000);
        }
    }
}

// ─── TTS (FREE — edge-tts via backend) ─────────────────────────

async function speakText(text) {
    if (!isCallActive) return;

    isSpeaking = true;
    stopListening();
    setMicButtonState('speaking');
    updateStatus('Speaking...', 'active');
    document.getElementById('waveform').classList.add('active');

    try {
        const resp = await fetch(
            `${API_BASE}/api/tts?text=${encodeURIComponent(text)}&lang=en`
        );

        if (resp.ok) {
            const blob = await resp.blob();
            const audioUrl = URL.createObjectURL(blob);
            const audio = new Audio(audioUrl);

            await new Promise((resolve) => {
                audio.onended = resolve;
                audio.onerror = () => {
                    console.error('Audio playback error, falling back to browser TTS');
                    fallbackTTS(text).then(resolve);
                };
                audio.play().catch(() => {
                    fallbackTTS(text).then(resolve);
                });
            });

            URL.revokeObjectURL(audioUrl);
        } else {
            await fallbackTTS(text);
        }
    } catch (e) {
        console.error('TTS error:', e);
        await fallbackTTS(text);
    }

    isSpeaking = false;
    document.getElementById('waveform').classList.remove('active');
    if (isCallActive) {
        setMicButtonState('active');
    }
}

function fallbackTTS(text) {
    return new Promise((resolve) => {
        if ('speechSynthesis' in window) {
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.rate = 1.0;
            utterance.pitch = 1.0;
            utterance.onend = resolve;
            utterance.onerror = resolve;
            window.speechSynthesis.speak(utterance);
        } else {
            resolve();
        }
    });
}

// ─── Transcript Management ────────────────────────────────────

function addMessage(speaker, text, isInterim = false, isThinking = false) {
    const body = document.getElementById('transcriptBody');

    const empty = body.querySelector('.transcript-empty');
    if (empty) empty.remove();

    const div = document.createElement('div');
    div.className = `message ${speaker}`;
    if (isInterim) div.classList.add('interim');
    if (isThinking) div.classList.add('thinking');

    const now = new Date();
    const time = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    const elapsed = callStartTime
        ? Math.floor((now - callStartTime) / 1000)
        : 0;
    const mins = Math.floor(elapsed / 60);
    const secs = (elapsed % 60).toString().padStart(2, '0');

    const speakerLabel = speaker === 'user' ? 'You' : speaker === 'bot' ? 'Sarah (Agent)' : 'System';

    div.innerHTML = `
        <span class="message-speaker">${speakerLabel}</span>
        <span class="message-text">${text}</span>
        <span class="message-time">${time} · ${mins}:${secs}</span>
    `;

    body.appendChild(div);
    body.scrollTop = body.scrollHeight;

    if (!isInterim && !isThinking) {
        transcriptData.push({
            time: `${mins}:${secs}`,
            speaker: speakerLabel,
            text: text,
        });
    }

    return div;
}

function clearTranscript() {
    clearTranscriptUI();
    transcriptData = [];
}

function clearTranscriptUI() {
    const body = document.getElementById('transcriptBody');
    body.innerHTML = `
        <div class="transcript-empty">
            <div class="empty-icon">✦</div>
            <p>Transcript will appear here when the call starts.</p>
        </div>
    `;
}

function downloadTranscript() {
    if (transcriptData.length === 0) {
        alert('No transcript to download.');
        return;
    }

    let md = `# TalentBridge Screening Call Transcript\n`;
    md += `**Date**: ${new Date().toISOString().split('T')[0]}\n`;
    md += `**Session**: ${sessionId}\n\n`;
    md += `| Time | Speaker | Text |\n|------|---------|------|\n`;

    transcriptData.forEach(entry => {
        md += `| ${entry.time} | ${entry.speaker} | ${entry.text.replace(/\|/g, '\\|')} |\n`;
    });

    const blob = new Blob([md], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `screening_transcript_${new Date().toISOString().split('T')[0]}.md`;
    a.click();
    URL.revokeObjectURL(url);
}

function updateStatus(text, type) {
    const badge = document.getElementById('statusBadge');
    const statusText = document.getElementById('statusText');
    statusText.textContent = text;
    badge.className = 'status-badge';
    if (type) badge.classList.add(type);
}
