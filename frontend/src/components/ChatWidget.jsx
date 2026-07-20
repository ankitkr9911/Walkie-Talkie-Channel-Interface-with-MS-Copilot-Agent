/**
 * ChatWidget — Walkie Talkie Inventory Assistant UI
 * ==================================================
 * Full-page layout: left sidebar + main chat panel.
 *
 * Sidebar (3 buttons):
 *   • Voice (Hold-To-Talk, TOGGLE: click=start, click=stop+send)
 *   • Chat  (text input)
 *   • Player (audio player panel with progress bar + replay)
 *
 * Chat panel:
 *   • Bot messages rendered as Markdown (tables, bold, lists)
 *   • User messages as plain text
 *   • Auto-scroll on new messages
 */

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Mic, Square, MessageSquare, Volume2,
  Send, Loader2, Bot, User, Play, Pause
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import useAudioRecorder from '../hooks/useAudioRecorder';

const API = '';   // Proxied by Vite in dev; Render URL in production

// ── Markdown component map ──────────────────────────────────────────────────
const MD = {
  table:    ({ node, ...p }) => <div className="md-table-wrap"><table className="md-table" {...p} /></div>,
  thead:    ({ node, ...p }) => <thead className="md-thead" {...p} />,
  tbody:    ({ node, ...p }) => <tbody className="md-tbody" {...p} />,
  tr:       ({ node, ...p }) => <tr className="md-tr" {...p} />,
  th:       ({ node, ...p }) => <th className="md-th" {...p} />,
  td:       ({ node, ...p }) => <td className="md-td" {...p} />,
  p:        ({ node, ...p }) => <p className="md-p" {...p} />,
  ul:       ({ node, ...p }) => <ul className="md-ul" {...p} />,
  ol:       ({ node, ...p }) => <ol className="md-ol" {...p} />,
  li:       ({ node, ...p }) => <li className="md-li" {...p} />,
  strong:   ({ node, ...p }) => <strong className="md-strong" {...p} />,
  em:       ({ node, ...p }) => <em className="md-em" {...p} />,
  h1:       ({ node, ...p }) => <h1 className="md-h1" {...p} />,
  h2:       ({ node, ...p }) => <h2 className="md-h2" {...p} />,
  h3:       ({ node, ...p }) => <h3 className="md-h3" {...p} />,
  code:     ({ node, inline, ...p }) =>
    inline
      ? <code className="md-code-inline" {...p} />
      : <pre className="md-pre"><code className="md-code-block" {...p} /></pre>,
  blockquote: ({ node, ...p }) => <blockquote className="md-blockquote" {...p} />,
};

// ── Helper ──────────────────────────────────────────────────────────────────
function fmtTime(secs) {
  if (!secs || isNaN(secs)) return '0:00';
  const m = Math.floor(secs / 60);
  const s = Math.floor(secs % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

// ── Component ───────────────────────────────────────────────────────────────
export default function ChatWidget() {
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      text: "Hello! I'm your **Inventory Assistant**.\n\nAsk me anything about stock levels, products, or warehouses. You can **type** or use the **Voice** button on the left.",
    },
  ]);
  const [inputText, setInputText]   = useState('');
  const [isLoading, setIsLoading]   = useState(false);
  const [activeMode, setActiveMode] = useState('voice');   // 'voice' | 'chat' | 'player'
  const [currentAudio, setCurrentAudio] = useState(null); // base64 WAV string
  const [isPlaying, setIsPlaying]   = useState(false);
  const [audioProgress, setAudioProgress] = useState(0);
  const [audioDuration, setAudioDuration] = useState(0);
  const [lastResponseText, setLastResponseText] = useState('');

  const chatEndRef = useRef(null);
  const audioRef   = useRef(new Audio());
  const { isRecording, startRecording, stopRecording } = useAudioRecorder();

  // ── Auto-scroll ────────────────────────────────────────────────────────────
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // ── Audio event listeners ──────────────────────────────────────────────────
  useEffect(() => {
    const a = audioRef.current;
    const onTime     = () => setAudioProgress(a.currentTime);
    const onDuration = () => setAudioDuration(a.duration);
    const onPlay     = () => setIsPlaying(true);
    const onPause    = () => setIsPlaying(false);
    const onEnded    = () => { setIsPlaying(false); setAudioProgress(0); };
    const onError    = () => setIsPlaying(false);

    a.addEventListener('timeupdate',      onTime);
    a.addEventListener('durationchange',  onDuration);
    a.addEventListener('play',            onPlay);
    a.addEventListener('pause',           onPause);
    a.addEventListener('ended',           onEnded);
    a.addEventListener('error',           onError);

    return () => {
      a.removeEventListener('timeupdate',      onTime);
      a.removeEventListener('durationchange',  onDuration);
      a.removeEventListener('play',            onPlay);
      a.removeEventListener('pause',           onPause);
      a.removeEventListener('ended',           onEnded);
      a.removeEventListener('error',           onError);
    };
  }, []);

  // ── Audio helpers ──────────────────────────────────────────────────────────
  const loadAndPlay = useCallback((base64) => {
    if (!base64) return;
    const a = audioRef.current;
    a.src = `data:audio/wav;base64,${base64}`;
    setCurrentAudio(base64);
    setAudioProgress(0);
    setAudioDuration(0);
    a.play().catch(() => {});
  }, []);

  const togglePlayPause = useCallback(() => {
    const a = audioRef.current;
    if (!currentAudio) return;
    if (isPlaying) { a.pause(); }
    else           { a.play().catch(() => {}); }
  }, [isPlaying, currentAudio]);

  const handleSeek = useCallback((e) => {
    if (!audioDuration) return;
    const rect  = e.currentTarget.getBoundingClientRect();
    const ratio = (e.clientX - rect.left) / rect.width;
    audioRef.current.currentTime = Math.max(0, Math.min(ratio * audioDuration, audioDuration));
  }, [audioDuration]);

  // ── Toggle-based PTT ───────────────────────────────────────────────────────
  // Click once → start recording (mic opens, button turns red)
  // Click again → stop recording → sends audio to backend
  const handlePttToggle = useCallback(async () => {
    if (isRecording) {
      // ── STOP + SEND ──
      const blob = await stopRecording();
      if (!blob || blob.size < 500) return;   // Ignore accidental double-clicks

      setIsLoading(true);
      setMessages((prev) => [...prev, { role: 'user', text: '🎤 Sending recording...' }]);

      try {
        const fd = new FormData();
        fd.append('audio', blob, 'recording.webm');
        fd.append('session_id', 'default');

        const res  = await fetch(`${API}/api/voice`, { method: 'POST', body: fd });
        const data = await res.json();

        // Replace placeholder with actual transcript
        setMessages((prev) => {
          const copy = [...prev];
          copy[copy.length - 1] = {
            role: 'user',
            text: data.transcript || '(could not transcribe)',
          };
          return copy;
        });

        // Bot reply
        const reply = data.response || 'No response received.';
        setMessages((prev) => [...prev, { role: 'bot', text: reply }]);
        setLastResponseText(reply);
        if (data.audio) loadAndPlay(data.audio);
      } catch {
        setMessages((prev) => [
          ...prev,
          { role: 'bot', text: 'Sorry, something went wrong. Please try again.' },
        ]);
      } finally {
        setIsLoading(false);
      }
    } else {
      // ── START ──
      startRecording();
    }
  }, [isRecording, startRecording, stopRecording, loadAndPlay]);

  // ── Text chat ──────────────────────────────────────────────────────────────
  const handleSendText = useCallback(async () => {
    const text = inputText.trim();
    if (!text || isLoading) return;
    setInputText('');
    setIsLoading(true);
    setMessages((prev) => [...prev, { role: 'user', text }]);

    try {
      const res  = await fetch(`${API}/api/chat`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({ message: text, session_id: 'default' }),
      });
      const data = await res.json();
      const reply = data.response || 'No response received.';
      setMessages((prev) => [...prev, { role: 'bot', text: reply }]);
      setLastResponseText(reply);
      if (data.audio) loadAndPlay(data.audio);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: 'bot', text: 'Sorry, something went wrong. Please try again.' },
      ]);
    } finally {
      setIsLoading(false);
    }
  }, [inputText, isLoading, loadAndPlay]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSendText(); }
  };

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="app-root">

      {/* ── Sidebar ── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <Bot size={26} color="#60a5fa" />
        </div>

        <nav className="sidebar-nav">
          {/* Voice / PTT */}
          <button
            className={`sidebar-btn ${activeMode === 'voice' ? 'active' : ''}`}
            onClick={() => setActiveMode('voice')}
            title="Hold-To-Talk"
            id="btn-voice-mode"
          >
            <Mic size={22} className={isRecording ? 'rec-icon' : ''} />
            <span>Voice</span>
            {isRecording && <span className="rec-dot" />}
          </button>

          {/* Chat */}
          <button
            className={`sidebar-btn ${activeMode === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveMode('chat')}
            title="Chat UI"
            id="btn-chat-mode"
          >
            <MessageSquare size={22} />
            <span>Chat</span>
          </button>

          {/* Audio Player */}
          <button
            className={`sidebar-btn ${activeMode === 'player' ? 'active' : ''}`}
            onClick={() => setActiveMode('player')}
            title="Audio Player"
            id="btn-player-mode"
          >
            <Volume2 size={22} className={isPlaying ? 'pulse' : ''} />
            <span>Player</span>
            {isPlaying && <span className="playing-dot" />}
          </button>
        </nav>

        <div className="sidebar-footer">
          <div className={`conn-badge ${isLoading ? 'loading' : 'online'}`}>
            {isLoading
              ? <Loader2 size={12} className="spin" />
              : <span className="conn-dot" />
            }
          </div>
        </div>
      </aside>

      {/* ── Main Panel ── */}
      <main className="main-panel">

        {/* Header */}
        <header className="main-header">
          <div className="header-left">
            <h1 className="main-title">Walkie Talkie — Inventory Assistant</h1>
            <span className="header-sub">AI-powered inventory management</span>
          </div>
          <div className={`status-badge ${isLoading ? 'processing' : 'online'}`}>
            {isLoading
              ? <><Loader2 size={13} className="spin" /> Processing…</>
              : <><span className="status-dot" /> Online</>
            }
          </div>
        </header>

        {/* Chat Messages */}
        <section className="message-list" id="message-list">
          {messages.map((msg, i) => (
            <div key={i} className={`message-row ${msg.role}`}>
              {msg.role === 'bot' && (
                <div className="msg-avatar bot-icon">
                  <Bot size={15} color="#fff" />
                </div>
              )}

              <div className={`message-bubble ${msg.role}`}>
                {msg.role === 'bot' ? (
                  <ReactMarkdown remarkPlugins={[remarkGfm]} components={MD}>
                    {msg.text}
                  </ReactMarkdown>
                ) : (
                  msg.text
                )}
              </div>

              {msg.role === 'user' && (
                <div className="msg-avatar user-icon">
                  <User size={15} color="#fff" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="message-row bot">
              <div className="msg-avatar bot-icon"><Bot size={15} color="#fff" /></div>
              <div className="message-bubble bot typing">
                <span className="typing-dot" /><span className="typing-dot" /><span className="typing-dot" />
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </section>

        {/* ── Input / Player Area ── */}
        <footer className="input-area">

          {/* Voice Mode — Toggle PTT */}
          {activeMode === 'voice' && (
            <div className="ptt-container">
              <button
                className={`ptt-button ${isRecording ? 'recording' : ''}`}
                onClick={handlePttToggle}
                disabled={isLoading}
                id="ptt-button"
              >
                {isRecording
                  ? <><Square size={20} /><span>Release to Send</span></>
                  : <><Mic size={20} /><span>{isLoading ? 'Processing…' : 'Hold to Talk'}</span></>
                }
                {isRecording && <span className="rec-ring" />}
              </button>
              <p className="ptt-hint">
                {isRecording
                  ? '🔴 Recording… click again to send'
                  : 'Click to start recording, click again to send'}
              </p>
            </div>
          )}

          {/* Chat Mode — Text Input */}
          {activeMode === 'chat' && (
            <div className="text-input-row">
              <input
                type="text"
                className="text-input"
                placeholder="Type your question here…"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
                id="text-input"
                autoFocus
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

          {/* Player Mode — Audio Player */}
          {activeMode === 'player' && (
            <div className="audio-player-card">
              {currentAudio ? (
                <>
                  <div className="player-top">
                    <div className="player-icon-wrap">
                      <Volume2 size={20} color="#2F6FED" />
                    </div>
                    <div className="player-info">
                      <span className="player-title">Last Voice Response</span>
                      <span className="player-sub">Click to replay anytime</span>
                    </div>
                  </div>

                  <div className="player-controls">
                    <button
                      className="play-pause-btn"
                      onClick={togglePlayPause}
                      id="play-pause-btn"
                    >
                      {isPlaying ? <Pause size={20} /> : <Play size={20} />}
                    </button>

                    <div className="progress-outer" onClick={handleSeek} id="progress-track" title="Click to seek">
                      <div
                        className="progress-inner"
                        style={{
                          width: audioDuration ? `${(audioProgress / audioDuration) * 100}%` : '0%',
                        }}
                      />
                      {audioDuration > 0 && (
                        <div
                          className="progress-thumb"
                          style={{
                            left: `${(audioProgress / audioDuration) * 100}%`,
                          }}
                        />
                      )}
                    </div>

                    <span className="time-display">
                      {fmtTime(audioProgress)} / {fmtTime(audioDuration)}
                    </span>
                  </div>

                  {lastResponseText && (
                    <p className="player-transcript" title="Response text">
                      {lastResponseText.slice(0, 120)}{lastResponseText.length > 120 ? '…' : ''}
                    </p>
                  )}
                </>
              ) : (
                <div className="player-empty">
                  <Volume2 size={36} color="#d1d5db" />
                  <p>No audio yet</p>
                  <span>Ask a question via Voice or Chat to get a voice response</span>
                </div>
              )}
            </div>
          )}
        </footer>
      </main>
    </div>
  );
}
