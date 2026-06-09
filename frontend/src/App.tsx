import { useEffect, useState } from "react";
import { getPhases, sendChat, type ChatMessage, type Phase } from "./api";

const NUTRIENT_KEYS = [
  "calories",
  "protein_g",
  "iron_mg",
  "magnesium_mg",
  "omega3_g",
  "vitamin_c_mg",
];

function PhaseCard({ phase }: { phase: Phase }) {
  return (
    <div className="card">
      <h3>{String(phase.cycle_phase)}</h3>
      <ul>
        {NUTRIENT_KEYS.filter((k) => phase[k] != null).map((k) => (
          <li key={k}>
            <span className="nutrient">{k}</span>
            <span className="value">{String(phase[k])}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default function App() {
  const [phases, setPhases] = useState<Phase[]>([]);
  const [error, setError] = useState<string | null>(null);

  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    getPhases()
      .then(setPhases)
      .catch((e) => setError(String(e)));
  }, []);

  async function onSend() {
    const text = input.trim();
    if (!text || busy) return;
    const next: ChatMessage[] = [...messages, { role: "user", content: text }];
    setMessages(next);
    setInput("");
    setBusy(true);
    try {
      const reply = await sendChat(next);
      setMessages([...next, { role: "assistant", content: reply }]);
    } catch (e) {
      setMessages([...next, { role: "assistant", content: `Error: ${e}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header>
        <h1>🥗 Nutrition Planner</h1>
        <p className="subtitle">Cycle-phase aware nutrition · Team 7</p>
      </header>

      <section>
        <h2>Phase nutrient targets</h2>
        {error && <p className="error">Failed to load phases: {error}</p>}
        <div className="cards">
          {phases.map((p) => (
            <PhaseCard key={String(p.cycle_phase)} phase={p} />
          ))}
        </div>
      </section>

      <section>
        <h2>Ask the assistant</h2>
        <div className="chat">
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <strong>{m.role === "user" ? "You" : "Assistant"}:</strong> {m.content}
            </div>
          ))}
          {busy && <div className="msg assistant">Assistant is thinking…</div>}
        </div>
        <div className="composer">
          <textarea
            value={input}
            placeholder="e.g. What should I eat during my luteal phase?"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                onSend();
              }
            }}
          />
          <button onClick={onSend} disabled={busy}>
            Send
          </button>
        </div>
      </section>
    </div>
  );
}
