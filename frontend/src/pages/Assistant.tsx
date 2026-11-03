import { useCallback, useEffect, useRef, useState } from 'react';
import {
  AlertCircle,
  Bot,
  Loader2,
  Mic,
  MicOff,
  Plus,
  Send,
  Sparkles,
  Trash2,
  Volume2,
  VolumeX,
} from 'lucide-react';
import { useAsync } from '../hooks/useAsync';
import { apiError, assistantApi, voiceApi } from '../services/api';
import type { AssistantAvailability, VoiceConfig } from '../types';
import { Card, ErrorBox, Heading, Notice, Spinner, Tag, fmtDateTime } from '../components/ui';

// ── Minimal Web Speech API typings (not in lib.dom for all TS versions) ────────
interface SpeechRecognitionResultLike {
  isFinal: boolean;
  0: { transcript: string };
}
interface SpeechRecognitionEventLike {
  resultIndex: number;
  results: { length: number; [index: number]: SpeechRecognitionResultLike };
}
interface SpeechRecognitionLike {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  start: () => void;
  stop: () => void;
  abort: () => void;
  onresult: ((event: SpeechRecognitionEventLike) => void) | null;
  onerror: ((event: { error?: string }) => void) | null;
  onend: (() => void) | null;
}
type SpeechRecognitionCtor = new () => SpeechRecognitionLike;

function getRecognitionCtor(): SpeechRecognitionCtor | null {
  const w = window as unknown as {
    SpeechRecognition?: SpeechRecognitionCtor;
    webkitSpeechRecognition?: SpeechRecognitionCtor;
  };
  return w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null;
}

interface Bubble {
  role: 'user' | 'assistant';
  content: string;
  mode?: string;
  at?: string;
  notice?: string;
}

const SUGGESTIONS = [
  'Explain my latest report in plain language',
  'What does a high LDL cholesterol mean?',
  'How can I improve my sleep quality?',
  'Which vitals should I track for hypertension?',
];

export default function Assistant() {
  const availability = useAsync<AssistantAvailability>(
    () => assistantApi.availability().then((r) => r.data),
    []
  );
  const voiceCfg = useAsync<VoiceConfig>(() => voiceApi.config().then((r) => r.data), []);

  const [input, setInput] = useState('');
  const [bubbles, setBubbles] = useState<Bubble[]>([]);
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [sending, setSending] = useState(false);
  const [error, setError] = useState('');

  const [listening, setListening] = useState(false);
  const [interim, setInterim] = useState('');
  const [speakReplies, setSpeakReplies] = useState(false);
  const [voiceSupported, setVoiceSupported] = useState(false);
  const [voiceLanguage, setVoiceLanguage] = useState('en-US');

  const recogRef = useRef<SpeechRecognitionLike | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    setVoiceSupported(Boolean(getRecognitionCtor()));
  }, []);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [bubbles, sending]);

  const speak = useCallback((text: string, lang = 'en-US') => {
    if (!('speechSynthesis' in window) || !text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = lang;
    utterance.rate = 1;
    window.speechSynthesis.speak(utterance);
  }, []);

  const send = useCallback(
    async (message: string) => {
      const text = message.trim();
      if (!text || sending) return;

      setError('');
      setInput('');
      setInterim('');
      setBubbles((prev) => [...prev, { role: 'user', content: text, at: new Date().toISOString() }]);
      setSending(true);

      try {
        const { data } = await assistantApi.chat(text, conversationId);
        setConversationId(data.conversation_id);
        const reply: Bubble = {
          role: 'assistant',
          content: data.answer,
          mode: data.mode,
          at: new Date().toISOString(),
          notice: data.notice,
        };
        setBubbles((prev) => [...prev, reply]);
        if (speakReplies) speak(data.answer, voiceLanguage);
      } catch (err) {
        setError(apiError(err, 'The assistant could not answer right now.'));
        setBubbles((prev) => prev.slice(0, -1));
        setInput(text);
      } finally {
        setSending(false);
      }
    },
    [conversationId, sending, speakReplies, speak, voiceLanguage]
  );

  const startListening = useCallback(() => {
    const Ctor = getRecognitionCtor();
    if (!Ctor) return;

    const recog = new Ctor();
    recog.lang = voiceLanguage;
    recog.continuous = false;
    recog.interimResults = true;

    recog.onresult = (event) => {
      let finalText = '';
      let draft = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) finalText += result[0].transcript;
        else draft += result[0].transcript;
      }
      if (draft) setInterim(draft);
      if (finalText) {
        setInterim('');
        setInput(finalText.trim());
        void send(finalText);
      }
    };
    recog.onerror = (event) => {
      setListening(false);
      setInterim('');
      if (event.error === 'not-allowed') {
        setError('Microphone permission was blocked. Allow microphone access to use voice input.');
      } else if (event.error !== 'aborted' && event.error !== 'no-speech') {
        setError(`Voice input error: ${event.error ?? 'unknown'}`);
      }
    };
    recog.onend = () => {
      setListening(false);
      setInterim('');
    };

    recogRef.current = recog;
    try {
      recog.start();
      setListening(true);
      setError('');
    } catch {
      setListening(false);
      setError('Voice input is already running or unavailable in this browser.');
    }
  }, [send, voiceLanguage]);

  const stopListening = useCallback(() => {
    recogRef.current?.stop();
    setListening(false);
    setInterim('');
  }, []);

  const newConversation = () => {
    setConversationId(undefined);
    setBubbles([]);
    setError('');
    setInput('');
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
  };

  const ai = availability.data;
  const live = ai?.live ?? false;

  return (
    <>
      <Heading
        eyebrow="AI HEALTH ASSISTANT"
        title="Ask anything about your health"
        desc="Ask about a health term, lab value, or general wellness topic. Share only the report details you want explained."
        action={
          <button className="btn secondary" onClick={newConversation}>
            <Plus size={14} /> New conversation
          </button>
        }
      />

      {availability.loading && <Spinner label="Checking assistant status…" />}

      {ai && (
        <Notice tone={live ? 'teal' : 'amber'}>
          {live ? (
            <>
              Connected to a live <b>{ai.provider ?? ai.mode}</b> provider. Responses are generated by
              a large language model and may be incomplete or incorrect.
            </>
          ) : (
            <>
              <b>Demo mode.</b> No AI provider key is configured, so replies come from MediSense&apos;s
              built-in, topic-matched educational response library — this is not a live AI model.
              Add <code>GEMINI_API_KEY</code> or <code>OPENAI_API_KEY</code> on the server to enable one.
            </>
          )}
        </Notice>
      )}

      <div className="assistant-layout" style={{ marginTop: 16 }}>
        <Card className="chat-card">
          <div className="chat-head">
            <div className="assistant-avatar">
              <Bot size={17} />
            </div>
            <div>
              <b>MediSense Assistant</b>
              <small className="small-note">
                {ai ? (live ? `${ai.provider ?? ai.mode} · live` : 'Educational engine · demo mode') : 'Checking…'}
              </small>
            </div>
            <Tag tone={live ? 'green' : 'amber'}>{live ? 'LIVE' : 'DEMO'}</Tag>
            <button
              className="icon-btn"
              onClick={() => setSpeakReplies((s) => !s)}
              title={speakReplies ? 'Disable spoken replies' : 'Enable spoken replies'}
              aria-label={speakReplies ? 'Disable spoken replies' : 'Enable spoken replies'}
              style={{ marginLeft: 'auto' }}
            >
              {speakReplies ? <Volume2 size={17} /> : <VolumeX size={17} />}
            </button>
          </div>

          <div className="chat-messages" ref={scrollRef} aria-live="polite" aria-relevant="additions">
            {bubbles.length === 0 && (
              <div className="empty-state" style={{ padding: '34px 16px' }}>
                <div>
                  <Sparkles size={20} />
                </div>
                <b>Start a conversation</b>
                <p className="muted">
                  Ask about symptoms, lab values, medications or lifestyle. MediSense will not diagnose.
                </p>
                <div className="suggestions">
                  {SUGGESTIONS.map((s) => (
                    <button key={s} className="suggestion-chip" onClick={() => void send(s)}>
                      {s}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {bubbles.map((b, i) => (
              <div className={`message ${b.role === 'user' ? 'user' : ''}`} key={`${b.role}-${i}`}>
                {b.role === 'assistant' && (
                  <div className="message-avatar">
                    <Bot size={14} />
                  </div>
                )}
                <div className="bubble">
                  {b.content.split('\n').map((line, li) =>
                    line.trim() ? <p key={li}>{line}</p> : null
                  )}
                  {b.role === 'assistant' && (
                    <div className="bubble-meta">
                      <span>{b.mode ? b.mode.toUpperCase() : 'ASSISTANT'}</span>
                      <button className="text-btn" onClick={() => speak(b.content, voiceLanguage)} title="Read aloud">
                        <Volume2 size={12} /> Read
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {sending && (
              <div className="message">
                <div className="message-avatar">
                  <Bot size={14} />
                </div>
                <div className="bubble typing">
                  <Loader2 size={13} className="spin" />
                  <span>Thinking…</span>
                </div>
              </div>
            )}
          </div>

          {error && (
            <div style={{ padding: '0 18px' }}>
              <ErrorBox message={error} />
            </div>
          )}

          {interim && (
            <div className="interim-line">
              <Mic size={12} /> {interim}
            </div>
          )}

          <div className="chat-input chat-composer">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  void send(input);
                }
              }}
              placeholder={listening ? 'Listening… your words will appear here' : 'Type a question. Press Enter to send, Shift + Enter for a new line.'}
              aria-label="Message to MediSense Assistant"
              rows={2}
              disabled={sending}
            />
            <label className="voice-language-label" title="Choose the language for speech recognition">
              <span>Voice language</span>
              <select value={voiceLanguage} onChange={e => setVoiceLanguage(e.target.value)} aria-label="Voice language">
                {(voiceCfg.data?.languages?.length ? voiceCfg.data.languages : [{code:'en-US',label:'English (US)'},{code:'hi-IN',label:'Hindi'}]).map(language => <option key={language.code} value={language.code}>{language.label}</option>)}
              </select>
            </label>
            <button
              className={`icon-btn ${listening ? 'recording' : ''}`}
              onClick={listening ? stopListening : startListening}
              disabled={!voiceSupported || sending}
              title={
                voiceSupported
                  ? listening
                    ? 'Stop listening'
                    : `Speak your question in ${voiceCfg.data?.languages.find(l => l.code === voiceLanguage)?.label ?? 'the selected language'}`
                  : 'This browser does not support speech recognition'
              }
              aria-label="Voice input"
            >
              {listening ? <MicOff size={17} /> : <Mic size={17} />}
            </button>
            <button
              className="send-btn"
              onClick={() => void send(input)}
              disabled={sending || !input.trim()}
              aria-label="Send message"
            >
              {sending ? <Loader2 size={15} className="spin" /> : <Send size={15} />}
            </button>
          </div>
        </Card>

        <div>
          <Card>
            <div className="card-head">
              <b>Voice assistant</b>
              <Tag tone={voiceSupported ? 'green' : 'neutral'}>
                {voiceSupported ? 'Ready' : 'Unsupported'}
              </Tag>
            </div>

            {!voiceSupported && (
              <p className="small-note">
                This browser does not expose the Web Speech API. Voice input works in Chrome, Edge and
                recent Safari — typing always works everywhere.
              </p>
            )}

            {voiceSupported && (
              <div className="insight">
                <div className="insight-icon">
                  <Mic size={15} />
                </div>
                <div>
                  <b>Speech-to-text</b>
                  <small>
                    Runs in your browser via the Web Speech API. Audio is transcribed by the browser
                    vendor&apos;s speech service; MediSense itself never receives audio.
                  </small>
                </div>
              </div>
            )}

            <div className="insight">
              <div className="insight-icon violet">
                <Volume2 size={15} />
              </div>
              <div>
                <b>Text-to-speech</b>
                <small>
                  {voiceCfg.data?.synthesis === 'browser_speech_synthesis'
                    ? 'Replies are read aloud with the browser synthesiser — no server TTS is configured.'
                    : 'Server-side speech synthesis is available.'}
                </small>
              </div>
            </div>

            {voiceCfg.data && (
              <>
                <div className="divider" />
                <small className="small-note">Recognition languages</small>
                <div className="lang-chips">
                  {voiceCfg.data.languages.map((l) => (
                    <span className="chip-static" key={l.code}>
                      {l.label}
                    </span>
                  ))}
                </div>
                <p className="small-note" style={{ marginTop: 10 }}>
                  Privacy: <b>{voiceCfg.data.privacy}</b> — {voiceCfg.data.notes}
                </p>
              </>
            )}
          </Card>

          <Card style={{ marginTop: 15 }}>
            <div className="card-head">
              <b>Conversation</b>
              <button className="text-btn" onClick={newConversation}>
                <Trash2 size={12} /> Clear
              </button>
            </div>
            <div className="metric-line">
              <span>Messages</span>
              <b>{bubbles.length}</b>
            </div>
            <div className="metric-line">
              <span>Conversation ID</span>
              <b>{conversationId ?? 'new'}</b>
            </div>
            <div className="metric-line">
              <span>Started</span>
              <b>{bubbles[0]?.at ? fmtDateTime(bubbles[0].at) : '—'}</b>
            </div>
            <p className="small-note" style={{ marginTop: 12, display: 'flex', gap: 6 }}>
              <AlertCircle size={12} style={{ flexShrink: 0, marginTop: 2 }} />
              Conversations are stored against your account so you can return to them. MediSense does
              not provide diagnosis or emergency care.
            </p>
          </Card>
        </div>
      </div>
    </>
  );
}
