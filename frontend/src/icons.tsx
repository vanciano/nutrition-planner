/* Nutrition Planner — icons (Flo spec: 24×24, ~1.6–2px rounded stroke,
   currentColor, mono). Typed port of the design's icons.jsx subset used
   by the app shell + Profile tab. */
import type { ReactElement } from "react";

type Icon = (color?: string) => ReactElement;

export const NPIcon: Record<"info" | "check" | "plus" | "minus" | "chevron" | "chevronDown", Icon> = {
  info: (c = "currentColor") => (
    <svg width="18" height="18" viewBox="0 0 20 20" fill="none"><circle cx="10" cy="10" r="8" stroke={c} strokeWidth="1.6" /><path d="M10 9v4.5" stroke={c} strokeWidth="1.7" strokeLinecap="round" /><circle cx="10" cy="6.4" r="1" fill={c} /></svg>
  ),
  check: (c = "currentColor") => (
    <svg width="14" height="14" viewBox="0 0 16 16" fill="none"><path d="M3 8.5l3.2 3.2L13 4.5" stroke={c} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" /></svg>
  ),
  plus: (c = "currentColor") => (
    <svg width="16" height="16" viewBox="0 0 18 18" fill="none"><path d="M9 3.5v11M3.5 9h11" stroke={c} strokeWidth="2" strokeLinecap="round" /></svg>
  ),
  minus: (c = "currentColor") => (
    <svg width="16" height="16" viewBox="0 0 18 18" fill="none"><path d="M3.5 9h11" stroke={c} strokeWidth="2" strokeLinecap="round" /></svg>
  ),
  chevron: (c = "currentColor") => (
    <svg width="9" height="14" viewBox="0 0 9 14" fill="none"><path d="M1.5 1.5L7 7l-5.5 5.5" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
  ),
  chevronDown: (c = "currentColor") => (
    <svg width="14" height="9" viewBox="0 0 14 9" fill="none"><path d="M1.5 1.5L7 7l5.5-5.5" stroke={c} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
  ),
};

/* bottom-nav tab glyphs */
export const WTabIcon: Record<"plan" | "dashboard" | "profile", Icon> = {
  plan: (c = "currentColor") => (
    <svg width="23" height="23" viewBox="0 0 24 24" fill="none"><path d="M6 4h9l4 4v12a1 1 0 01-1 1H6a1 1 0 01-1-1V5a1 1 0 011-1z" stroke={c} strokeWidth="1.8" strokeLinejoin="round" /><path d="M9 11h6M9 15h4" stroke={c} strokeWidth="1.8" strokeLinecap="round" /></svg>
  ),
  dashboard: (c = "currentColor") => (
    <svg width="23" height="23" viewBox="0 0 24 24" fill="none"><path d="M5 19V11M12 19V5M19 19v-6" stroke={c} strokeWidth="2" strokeLinecap="round" /></svg>
  ),
  profile: (c = "currentColor") => (
    <svg width="23" height="23" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="8.5" r="3.6" stroke={c} strokeWidth="1.8" /><path d="M5.5 19.5c0-3.4 2.9-6 6.5-6s6.5 2.6 6.5 6" stroke={c} strokeWidth="1.8" strokeLinecap="round" /></svg>
  ),
};

/* Flo feather logo mark */
export function FloMark({ size = 26, color = "var(--core-pink-500)" }: { size?: number; color?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 687.079 677.72" style={{ color, display: "block" }}>
      <path fill="currentColor" d="M 6.535 601.7 C 51.335 599.1 130.335 588 212.135 551.3 C 341.435 493.3 408.235 408.7 409.235 409.5 C 412.435 412 366.235 478.4 279.335 536.9 C 217.135 578.7 164.435 600.4 111.135 616.4 C 77.635 626.4 129.135 608.5 177.235 642.3 C 210.235 665.5 211.635 690.7 212.935 670.1 C 213.535 660.6 213.135 647 212.235 636.8 C 242.635 645.4 286.035 653.4 340.335 647.4 C 399.535 640.8 454.135 618.8 502.635 582.4 C 519.635 569.6 504.635 573.4 495.935 575.1 C 474.735 579.2 435.935 583.4 392.835 573.1 C 421.935 573.1 610.135 559.5 667.535 394.3 C 728.535 218.4 645.135 0 439.835 0 C 234.435 0 206.735 305.1 210.335 361.6 C 199.935 331.1 195.635 286.2 202.735 247.3 C 205.435 232.6 209.035 215.8 190.835 237.4 C 155.935 278.9 110.135 359 123.435 466.7 C 107.235 453.3 92.635 444 79.035 437 C 63.735 429.1 57.135 426 74.235 447.4 C 87.735 464.3 104.135 502.9 83.535 543.1 C 67.735 573.9 40.535 589.1 11.535 592.3 C -2.265 593.5 -3.365 602.3 6.535 601.7 Z" />
    </svg>
  );
}
