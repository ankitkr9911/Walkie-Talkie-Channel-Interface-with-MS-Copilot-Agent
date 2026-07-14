/**
 * ChatWidget — Main UI Component
 * ================================
 * Matches the design reference: rounded card with sky-blue border,
 * browser chrome mockup, 4-icon toolbar, chat bubbles, voice response footer.
 *
 * Structure:
 *   Header → BrowserChrome → AgentAvatar → Toolbar → ChatPanel → VoiceFooter
 *
 * No business logic here — just records audio, sends to backend, displays responses.
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import { Mic, AudioLines, MessageSquare, Volume2, Send, Loader2, Bot, User } from 'lucide-react';
import useAudioRecorder from '../hooks/useAudioRecorder';

// Backend API base URL (proxied via Vite in dev)
const API = '';

export default function ChatWidget() {
  // --- State ---
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Hello! I\'m your Inventory Assistant. Ask me anything about stock, products, or warehouses. You can type or use Hold-To-Talk.' },
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeMode, setActiveMode] = useState('voice'); // voice | chat
  const [currentAudio, setCurrentAudio] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const chatEndRef = useRef(null);
  const audioRef = useRef(new Audio());
  const { isRecording, startRecording, stopRecording } = useAudioRecorder();

  // Auto-scroll chat to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // --- Audio Playback ---
  const playAudio = useCallback((base64Audio) => {
    if (!base64Audio) return;
    const audio = audioRef.current;
    audio.src = `data:audio/mp3;base64,${base64Audio}`;
    audio.onplay = () => setIsPlaying(true);
    audio.onended = () => setIsPlaying(false);
    audio.onerror = () => setIsPlaying(false);
    audio.play().catch(() => setIsPlaying(false));
    setCurrentAudio(base64Audio);
  }, []);

  // --- Send Voice (Hold-To-Talk release) ---
  const handleVoiceStop = useCallback(async () => {
    const blob = await stopRecording();
    if (!blob || blob.size < 1000) return; // Ignore very short recordings (clicks)

    setIsLoading(true);
    setMessages((prev) => [...prev, { role: 'user', text: '🎤 Recording sent...' }]);

    try {
      const formData = new FormData();
      formData.append('audio', blob, 'recording.webm');
      formData.append('session_id', 'default');

      const res = await fetch(`${API}/api/voice`, { method: 'POST', body: formData });
      const data = await res.json();

      // Update user message with transcript
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: 'user', text: data.transcript || '(could not transcribe)' };
        return updated;
      });

      // Add bot response
      setMessages((prev) => [...prev, { role: 'bot', text: data.response }]);

      // Play audio response
      if (data.audio) playAudio(data.audio);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'bot', text: 'Sorry, something went wrong. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  }, [stopRecording, playAudio]);

  // --- Send Text Message ---
  const handleSendText = useCallback(async () => {
    const text = inputText.trim();
    if (!text || isLoading) return;

    setInputText('');
    setIsLoading(true);
    setMessages((prev) => [...prev, { role: 'user', text }]);

    try {
      const res = await fetch(`${API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: 'default' }),
      });
      const data = await res.json();

      setMessages((prev) => [...prev, { role: 'bot', text: data.response }]);
      if (data.audio) playAudio(data.audio);
    } catch (err) {
      setMessages((prev) => [...prev, { role: 'bot', text: 'Sorry, something went wrong. Please try again.' }]);
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isLoading, playAudio]);

  // Handle Enter key in text input
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  };

  // --- Render ---
  return (
    <div className="widget-card">
      {/* Header */}
      <div className="widget-header">
        <h1 className="widget-title">Walkie Talkie — Inventory Assistant</h1>
      </div>

      {/* Browser Chrome Mockup */}
      <div className="browser-chrome">
        <div className="chrome-dots">
          <span className="dot dot-red" />
          <span className="dot dot-yellow" />
          <span className="dot dot-green" />
        </div>
        <div className="chrome-bar">
          <span className="chrome-nav">&lt; &gt;</span>
          <span className="chrome-url">walkie-talkie.app</span>
        </div>
      </div>

      {/* Agent Avatar */}
      <div className="agent-row">
        <div className="agent-avatar" id="agent-avatar">
          <MessageSquare size={20} color="#fff" />
          <div className="avatar-badge">
            <User size={10} color="#fff" />
          </div>
        </div>
      </div>

      {/* Icon Toolbar */}
      <div className="toolbar" id="toolbar">
        <button
          className={`toolbar-btn ${activeMode === 'voice' ? 'active' : ''}`}
          onClick={() => setActiveMode('voice')}
          id="btn-hold-to-talk"
        >
          <Mic size={22} />
          <span>Hold-To-Talk</span>
        </button>
        <button className="toolbar-btn" id="btn-audio-recorder">
          <AudioLines size={22} />
          <span>Audio Recorder</span>
        </button>
        <button
          className={`toolbar-btn ${activeMode === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveMode('chat')}
          id="btn-chat-ui"
        >
          <MessageSquare size={22} />
          <span>Chat UI</span>
        </button>
        <button
          className="toolbar-btn"
          onClick={() => currentAudio && playAudio(currentAudio)}
          id="btn-audio-player"
        >
          <Volume2 size={22} />
          <span>Audio Player</span>
        </button>
      </div>

      {/* Chat Conversation Panel */}
      <div className="chat-panel" id="chat-panel">
        <h2 className="chat-heading">Chat Conversation</h2>

        <div className="message-list" id="message-list">
          {messages.map((msg, i) => (
            <div key={i} className={`message-row ${msg.role}`}>
              {msg.role === 'bot' && (
                <div className="msg-avatar bot-icon">
                  <Bot size={16} color="#fff" />
                </div>
              )}
              <div className={`message-bubble ${msg.role}`}>
                {msg.text}
              </div>
              {msg.role === 'user' && (
                <div className="msg-avatar user-icon">
                  <User size={16} color="#fff" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="message-row bot">
              <div className="msg-avatar bot-icon">
                <Bot size={16} color="#fff" />
              </div>
              <div className="message-bubble bot typing">
                <Loader2 size={16} className="spin" />
                <span>Thinking...</span>
              </div>
            </div>
          )}

          <div ref={chatEndRef} />
        </div>
      </div>

      {/* Input Area — Voice or Text depending on mode */}
      <div className="input-area" id="input-area">
        {activeMode === 'voice' ? (
          <button
            className={`ptt-button ${isRecording ? 'recording' : ''}`}
            onMouseDown={startRecording}
            onMouseUp={handleVoiceStop}
            onMouseLeave={isRecording ? handleVoiceStop : undefined}
            onTouchStart={startRecording}
            onTouchEnd={handleVoiceStop}
            disabled={isLoading}
            id="ptt-button"
          >
            <Mic size={24} />
            <span>{isRecording ? 'Release to Send' : isLoading ? 'Processing...' : 'Hold to Talk'}</span>
          </button>
        ) : (
          <div className="text-input-row">
            <input
              type="text"
              className="text-input"
              placeholder="Type your question..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              id="text-input"
            />
            <button
              className="send-btn"
              onClick={handleSendText}
              disabled={isLoading || !inputText.trim()}
              id="send-button"
            >
              {isLoading ? <Loader2 size={18} className="spin" /> : <Send size={18} />}
            </button>
          </div>
        )}
      </div>

      {/* Voice Response Footer */}
      <div className="voice-footer" id="voice-footer">
        <Volume2 size={18} className={isPlaying ? 'pulse' : ''} />
        <span>{isPlaying ? 'Playing Voice Response...' : 'Voice Response'}</span>
      </div>
    </div>
  );
}
