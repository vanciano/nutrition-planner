/* Meal detail — right-side panel (desktop) / bottom sheet (mobile). Shows the
   hero image, macros, key micronutrients vs daily targets (phase-focus ones
   highlighted), ingredients, a phase-mapping line, and a Swap action.
   Ported from the design's WMealDetail (logging dropped). */
import { useEffect } from "react";
import type { Phase } from "../data";
import type { MealDetail as MealDetailData } from "../api";
import { NPIcon } from "../icons";
import MealThumb from "./MealThumb";

const MICROS: { key: keyof MealDetailData["micros"]; token: string; label: string; unit: string; target: number }[] = [
  { key: "iron_mg", token: "iron", label: "Iron", unit: "mg", target: 18 },
  { key: "magnesium_mg", token: "magnesium", label: "Magnesium", unit: "mg", target: 320 },
  { key: "omega3_g", token: "omega3", label: "Omega-3", unit: "g", target: 1.6 },
  { key: "vitamin_b6_mg", token: "b6", label: "Vitamin B6", unit: "mg", target: 1.9 },
  { key: "vitamin_c_mg", token: "vitamin_c", label: "Vitamin C", unit: "mg", target: 75 },
  { key: "calcium_mg", token: "calcium", label: "Calcium", unit: "mg", target: 1000 },
];

const MACROS: { key: keyof MealDetailData["macros"]; label: string; unit: string; color: string }[] = [
  { key: "protein_g", label: "Protein", unit: "g", color: "#E2566F" },
  { key: "fiber_g", label: "Fibre", unit: "g", color: "#9267C8" },
  { key: "calories", label: "Calories", unit: "", color: "#1DA4A6" },
];

export default function MealDetail({
  meal,
  phase,
  slotLabel,
  slotTime,
  focusTokens,
  hasAlt,
  onSwap,
  onClose,
}: {
  meal: MealDetailData;
  phase: Phase;
  slotLabel: string;
  slotTime: string;
  focusTokens: string[];
  hasAlt: boolean;
  onSwap: () => void;
  onClose: () => void;
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const heroBg = `linear-gradient(150deg, ${phase.grad[1]}, ${phase.accent})`;

  return (
    <div className="w-detail-wrap">
      <div className="w-detail-scrim" onClick={onClose} />
      <div className="w-detail" role="dialog" aria-label={meal.name}>
        <div className="w-detail-hero" style={{ background: heroBg }}>
          <MealThumb
            key={meal.meal_id}
            src={meal.image_url}
            icon={meal.icon}
            imgClass="w-detail-img"
            emojiClass="w-detail-glyph"
            emojiStyle={{ fontSize: 76 }}
          />
          <button className="w-detail-close" onClick={onClose} type="button" aria-label="Close">
            {NPIcon.close("#fff")}
          </button>
          {meal.prep_time_min != null && (
            <div className="w-detail-time">{NPIcon.clock("#fff")}<span>{meal.prep_time_min} min</span></div>
          )}
          <div className="w-detail-slot">{slotLabel} · {slotTime}</div>
        </div>
        <div className="w-detail-body">
          {meal.tag_label && (
            <div className="w-meal-tag" style={{ color: phase.accent, background: phase.tint }}>{meal.tag_label}</div>
          )}
          <h2 className="w-detail-title">{meal.name}</h2>
          {meal.description && <p className="w-detail-blurb">{meal.description}</p>}

          {meal.phase_focus.length > 0 && (
            <div className="w-maps" style={{ background: phase.tint }}>
              {NPIcon.spark(phase.accent)}
              <span>
                Supports your <strong style={{ color: phase.accent }}>{phase.short.toLowerCase()} phase</strong>{" "}
                focus on {meal.phase_focus.join(" & ")}.
              </span>
            </div>
          )}

          <div className="w-sec-h">Macros <span className="w-illus">· per serving, illustrative</span></div>
          <div className="w-macrogrid" style={{ gridTemplateColumns: "repeat(3, 1fr)" }}>
            {MACROS.map((m) => (
              <div className="w-macrostat" key={m.key}>
                <span className="w-macrostat-bar" style={{ background: m.color }} />
                <span className="w-macrostat-val">
                  {meal.macros[m.key]}{m.unit && <small>{m.unit}</small>}
                </span>
                <span className="w-macrostat-label">{m.label}</span>
              </div>
            ))}
          </div>

          <div className="w-sec-h">Key micronutrients <span className="w-illus">· share of daily target</span></div>
          <div className="w-bd">
            {MICROS.map((r) => {
              const amt = meal.micros[r.key];
              const pct = Math.min(amt / r.target, 1);
              const sup = focusTokens.includes(r.token);
              return (
                <div className="w-bd-row" key={r.key}>
                  <div className="w-bd-top">
                    <span className="w-bd-label">
                      {r.label}
                      {sup && <span className="w-bd-dot" style={{ background: phase.accent }} />}
                    </span>
                    <span className="w-bd-amt">
                      {amt}{r.unit} <span className="w-bd-of">· {Math.round(pct * 100)}% of target</span>
                    </span>
                  </div>
                  <div className="w-bd-track">
                    <div
                      className="w-bd-fill"
                      style={{ width: `${pct * 100}%`, background: sup ? phase.accent : "var(--core-gray-300)" }}
                    />
                  </div>
                </div>
              );
            })}
          </div>

          {meal.ingredients.length > 0 && (
            <>
              <div className="w-sec-h">What's in it</div>
              <div className="w-ings">
                {meal.ingredients.map((ing, i) => (
                  <span className="w-ing" key={i}>{ing.food_name}</span>
                ))}
              </div>
            </>
          )}

          <div className="w-detail-actions">
            <button
              className="w-add w-add-ghost"
              type="button"
              onClick={onSwap}
              disabled={!hasAlt}
              style={{
                color: hasAlt ? phase.accent : "var(--color-foreground-minor)",
                borderColor: hasAlt ? phase.accent + "66" : "var(--color-stroke-primary)",
              }}
            >
              {NPIcon.swap(hasAlt ? phase.accent : "var(--color-foreground-minor)")} Swap this meal
            </button>
          </div>
          {!hasAlt && <p className="w-swap-note">No alternative for this slot right now.</p>}
        </div>
      </div>
    </div>
  );
}
