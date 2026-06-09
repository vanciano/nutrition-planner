/* Nutrition Planner — data model (typed port of the design's data.js).
   This iteration ships only the slice the shell + Profile tab need:
   the three cycle phases, energy-target bounds, and the diet/allergy
   option lists. Meal / nutrient / dashboard data is deferred. */

export type PhaseKey = "menstrual" | "follicular" | "luteal";

export interface Phase {
  key: PhaseKey;
  name: string;
  short: string;
  day: number;
  note: string;
  range: string;
  accent: string;
  tint: string;
  grad: [string, string, string];
}

export const PHASES: Record<PhaseKey, Phase> = {
  menstrual: {
    key: "menstrual", name: "Menstrual phase", short: "Menstrual", day: 2,
    range: "Days 1–5", note: "Day 2 of your period",
    accent: "#D24365", tint: "#FBE7EC", grad: ["#FBDDE4", "#F29DB0", "#D24365"],
  },
  follicular: {
    key: "follicular", name: "Follicular phase", short: "Follicular", day: 9,
    range: "Days 6–16", note: "Day 9 · energy on the rise",
    accent: "#1DA4A6", tint: "#E2F4F2", grad: ["#DAF3F1", "#90DAD5", "#1DA4A6"],
  },
  luteal: {
    key: "luteal", name: "Luteal phase", short: "Luteal", day: 24,
    range: "Days 17–28", note: "Day 24 · ~4 days until your period",
    accent: "#CC7A1F", tint: "#FFF4EA", grad: ["#FFF4EA", "#FFD9A8", "#FFAF60"],
  },
};

// PHASE_ORDER + each phase's `grad` triplet feed the deferred Plan-tab hero
// (cycle arc + phase selector + gradient band); unused by the shell/Profile today.
export const PHASE_ORDER: PhaseKey[] = ["menstrual", "follicular", "luteal"];

/* User-set daily energy target — a guide for scaling portions, never a limit. */
export const DEFAULT_CALORIE_TARGET = 2000;
export const CAL_MIN = 1400;
export const CAL_MAX = 3200;
export const CAL_STEP = 50;

export const DIETS = ["Vegetarian", "Vegan", "Pescatarian", "Dairy-free", "Gluten-free"];
export const ALLERGIES = ["Nuts", "Dairy", "Gluten", "Shellfish", "Eggs", "Soy", "Sesame"];
