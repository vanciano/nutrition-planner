/* A slot card in the day plan: thumbnail, slot label + time, name, focus-nutrient
   tag, benefit line, macro strip, and a Swap action. Ported from the design's
   WPlanItem (logging dropped). */
import type { Phase } from "../data";
import type { Meal } from "../api";
import { NPIcon } from "../icons";
import MacroStrip from "./MacroStrip";
import MealThumb from "./MealThumb";

export default function MealItem({
  meal,
  slotLabel,
  slotTime,
  phase,
  onOpen,
  onSwap,
  hasAlt,
}: {
  meal: Meal;
  slotLabel: string;
  slotTime: string;
  phase: Phase;
  onOpen: () => void;
  onSwap: () => void;
  hasAlt: boolean;
}) {
  return (
    <div className="w-plan-item">
      <button className="w-plan-open" type="button" onClick={onOpen}>
        <div
          className="w-plan-thumb"
          style={{ background: `linear-gradient(150deg, ${phase.grad[1]}, ${phase.accent})` }}
        >
          <MealThumb
            key={meal.meal_id}
            src={meal.image_url}
            icon={meal.icon}
            imgClass="w-plan-img"
            emojiClass="w-plan-emoji"
          />
        </div>
        <div className="w-plan-main">
          <div className="w-plan-eyebrow">
            <span className="w-plan-slot" style={{ color: phase.accent }}>{slotLabel}</span>
            <span className="w-plan-time">{NPIcon.clock("currentColor")}{slotTime}</span>
          </div>
          <div className="w-plan-name">{meal.name}</div>
          <div className="w-plan-sub">
            {meal.tag_label && (
              <span className="w-plan-tag" style={{ color: phase.accent, background: phase.tint }}>
                {meal.tag_label}
              </span>
            )}
            <span className="w-plan-benefit">{meal.benefit}</span>
          </div>
          <MacroStrip macros={meal.macros} />
        </div>
        <span className="w-plan-chev">{NPIcon.chevron("var(--color-foreground-minor)")}</span>
      </button>
      <div className="w-plan-foot">
        <button
          className="w-log"
          type="button"
          onClick={onSwap}
          disabled={!hasAlt}
          style={{
            color: hasAlt ? phase.accent : "var(--color-foreground-minor)",
            borderColor: hasAlt ? phase.accent + "55" : "var(--color-stroke-primary)",
          }}
        >
          {NPIcon.swap(hasAlt ? phase.accent : "var(--color-foreground-minor)")} Swap
        </button>
      </div>
    </div>
  );
}
