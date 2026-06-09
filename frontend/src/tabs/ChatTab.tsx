/* Coach tab — an AI assistant that recommends meals grounded in the same
   selection the Plan uses (current phase + profile), and answers phase-aware
   movement questions. Talks to /api/chat via sendChat; grounding is server-side
   (phase + profile), so the client only sends the phase + message history. */
import { useEffect, useRef, useState } from "react";
import { PHASES, type PhaseKey } from "../data";
import { sendCoach, type ChatMessage, type Profile } from "../api";
import { NPIcon } from "../icons";

const STARTERS = [
  "What should I eat today?",
  "Swap my lunch for something lighter",
  "Best workout for my phase?",
];

export default function ChatTab({ phaseKey }: { phaseKey: PhaseKey; profile: Profile }) {
  const phase = PHASES[phaseKey];
  const accent = phase.accent;
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const threadRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, loading]);

  const send = (text: string) => {
    const content = text.trim();
    if (!content || loading) return;
    const next: ChatMessage[] = [...messages, { role: "user", content }];
    setMessages(next);
    setInput("");
    setLoading(true);
    sendCoach(next, phaseKey)
      .then((reply) => setMessages([...next, { role: "assistant", content: reply }]))
      .catch((e) => {
        console.error("chat failed", e);
        setMessages([...next, { role: "assistant", content: "Sorry — I couldn't answer just now. Try again in a moment." }]);
      })
      .finally(() => setLoading(false));
  };

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    send(input);
  };

  return (
    <div className="w-screen w-screen-light">
      <div className="w-shead">
        <h1 className="w-shead-title">Coach</h1>
        <p className="w-shead-sub">
          Meal ideas tailored to your <strong style={{ color: accent }}>{phase.short.toLowerCase()} phase</strong> — ask
          about food, swaps, or what movement suits you now.
        </p>
      </div>

      <div className="w-chat">
        <div className="w-chat-thread" ref={threadRef}>
          {messages.length === 0 && !loading && (
            <div className="w-chat-empty">
              <div className="w-chat-avatar" style={{ background: `linear-gradient(135deg, ${accent}, #9267C8)` }}>
                {NPIcon.spark("#fff")}
              </div>
              <p className="w-chat-empty-text">Ask me anything about eating for your cycle.</p>
              <div className="w-chat-starters">
                {STARTERS.map((s) => (
                  <button key={s} type="button" className="w-chat-starter" onClick={() => send(s)}
                    style={{ borderColor: accent + "55", color: accent }}>
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, i) => (
            <div key={i} className={"w-chat-row " + m.role}>
              <div className="w-chat-msg" style={m.role === "user" ? { background: accent, color: "#fff" } : undefined}>
                {m.content}
              </div>
            </div>
          ))}

          {loading && (
            <div className="w-chat-row assistant">
              <div className="w-chat-msg w-chat-typing"><span /><span /><span /></div>
            </div>
          )}
        </div>

        <form className="w-chat-input" onSubmit={onSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about meals or movement…"
            aria-label="Message"
          />
          <button type="submit" className="w-chat-send" disabled={!input.trim() || loading}
            style={{ background: accent }} aria-label="Send">
            {NPIcon.chevron("#fff")}
          </button>
        </form>
      </div>
    </div>
  );
}
