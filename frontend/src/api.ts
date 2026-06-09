export interface Phase {
  cycle_phase: string;
  [key: string]: string | number | null;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface Profile {
  energy_target: number;
  diets: string[];
  allergies: string[];
}

export async function getProfile(): Promise<Profile> {
  const res = await fetch("/api/profile");
  if (!res.ok) throw new Error(`GET /api/profile -> ${res.status}`);
  return res.json();
}

export async function saveProfile(profile: Profile): Promise<Profile> {
  const res = await fetch("/api/profile", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error(`PUT /api/profile -> ${res.status}`);
  return res.json();
}

export async function getPhases(): Promise<Phase[]> {
  const res = await fetch("/api/phases");
  if (!res.ok) throw new Error(`GET /api/phases -> ${res.status}`);
  const data = await res.json();
  return data.phases ?? [];
}

/* ── Plan tab ── */
export interface Macros {
  protein_g: number;
  fiber_g: number;
  calories: number;
}
export interface Micros {
  iron_mg: number;
  magnesium_mg: number;
  omega3_g: number;
  vitamin_c_mg: number;
  vitamin_b6_mg: number;
  calcium_mg: number;
}
export interface Meal {
  meal_id: string;
  name: string;
  slot: string;
  meal_type: string;
  description: string;
  benefit: string;
  key_nutrients: string[];
  tag: string | null;
  tag_label: string;
  macros: Macros;
  micros: Micros;
  image_url: string | null;
  icon: string;
  prep_time_min: number | null;
  dietary_tags: string[];
}
export interface MealDetail extends Meal {
  ingredients: { food_name: string; grams: number }[];
  phase_focus: string[];
  phase: string;
}
export interface Evidence {
  label: string;
  tier: "good" | "moderate" | "general";
  color: string;
  tint: string;
}
export interface FocusLever {
  nutrient: string;
  tagline: string;
  token: string | null;
  evidence: Evidence;
}
export interface PlanSlot {
  slot: string;
  label: string;
  time: string;
  pool: Meal[];
}
export interface PlanResponse {
  phase: string;
  goal: string;
  rationale: string;
  tip: { short: string; long: string };
  focus: FocusLever[];
  slots: PlanSlot[];
}

export async function getPlan(phase: string): Promise<PlanResponse> {
  const res = await fetch(`/api/plan?phase=${encodeURIComponent(phase)}`);
  if (!res.ok) throw new Error(`GET /api/plan -> ${res.status}`);
  return res.json();
}

export async function getMeal(id: string, phase: string): Promise<MealDetail> {
  const res = await fetch(`/api/meals/${encodeURIComponent(id)}?phase=${encodeURIComponent(phase)}`);
  if (!res.ok) throw new Error(`GET /api/meals/${id} -> ${res.status}`);
  return res.json();
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

/* AI Coach — follow-up Q&A about the recommended meals, grounded server-side
   in the user's current phase + profile + plan. */
export async function sendCoach(
  messages: ChatMessage[],
  phase?: string,
): Promise<string> {
  const res = await fetch("/api/coach", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, phase }),
  });
  if (!res.ok) throw new Error(`POST /api/coach -> ${res.status}`);
  const data = await res.json();
  return data.reply ?? "";
}
