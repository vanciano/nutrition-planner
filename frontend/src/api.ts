export interface Phase {
  cycle_phase: string;
  [key: string]: string | number | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export async function getPhases(): Promise<Phase[]> {
  const res = await fetch("/api/phases");
  if (!res.ok) throw new Error(`GET /api/phases -> ${res.status}`);
  const data = await res.json();
  return data.phases ?? [];
}

export async function sendChat(
  messages: ChatMessage[],
  phase?: string,
): Promise<string> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, phase }),
  });
  if (!res.ok) throw new Error(`POST /api/chat -> ${res.status}`);
  const data = await res.json();
  return data.reply ?? "";
}
