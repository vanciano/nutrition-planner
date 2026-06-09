/* Plan tab — the cycle-phase day plan. Hero (cycle arc + phase selector) drives
   the phase app-wide; below it: today's tip, this week's focus (with evidence
   badges), the recommended meals (swap / rebuild), a tailored-to-you strip, and
   the meal-detail panel. All meal data is warehouse-backed via /api/plan. */
import { useCallback, useEffect, useState } from "react";
import { PHASES, type PhaseKey } from "../data";
import { getPlan, getMeal, type PlanResponse, type MealDetail as MealDetailData, type Profile } from "../api";
import { NPIcon } from "../icons";
import CycleArc from "../components/CycleArc";
import PhaseSelector from "../components/PhaseSelector";
import TipCard from "../components/TipCard";
import FocusCard from "../components/FocusCard";
import MealItem from "../components/MealItem";
import TailoredBar from "../components/TailoredBar";
import MealDetail from "../components/MealDetail";

export default function PlanTab({
  phaseKey,
  setPhaseKey,
  profile,
  onEditPrefs,
}: {
  phaseKey: PhaseKey;
  setPhaseKey: (k: PhaseKey) => void;
  profile: Profile;
  onEditPrefs: () => void;
}) {
  const phase = PHASES[phaseKey];
  const [plan, setPlan] = useState<PlanResponse | null>(null);
  const [error, setError] = useState(false);
  const [sel, setSel] = useState<Record<string, number>>({});
  const [tipExpanded, setTipExpanded] = useState(false);
  const [openSlot, setOpenSlot] = useState<string | null>(null);
  const [detail, setDetail] = useState<MealDetailData | null>(null);

  // Stable key so the effect fires once per real prefs change, not on every
  // new array reference (e.g. the initial profile load).
  const prefsKey = JSON.stringify([profile.diets, profile.allergies]);
  // (Re)load the plan whenever the phase changes; reset transient UI state.
  // Re-runs when profile diets/allergies change so the meals respect prefs.
  useEffect(() => {
    let live = true;
    setError(false);
    getPlan(phaseKey)
      .then((p) => {
        if (!live) return;
        setPlan(p);
        setSel({});
        setTipExpanded(false);
        setOpenSlot(null);
        setDetail(null);
      })
      .catch((e) => {
        console.error("failed to load plan", e);
        if (live) setError(true);
      });
    return () => { live = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phaseKey, prefsKey]);

  const ready = plan && plan.phase === phaseKey;
  const focusTokens = ready ? plan.focus.map((l) => l.token).filter((t): t is string => !!t) : [];
  const idxOf = (slot: string) => sel[slot] ?? 0;

  const swap = useCallback((slot: string, poolLen: number) => {
    setSel((s) => ({ ...s, [slot]: ((s[slot] ?? 0) + 1) % poolLen }));
  }, []);

  const rebuild = useCallback(() => {
    if (!plan) return;
    const next: Record<string, number> = {};
    for (const s of plan.slots) {
      const n = s.pool.length;
      if (n <= 1) { next[s.slot] = 0; continue; }
      const cur = sel[s.slot] ?? 0;
      let pick = cur;
      while (pick === cur) pick = Math.floor(Math.random() * n);
      next[s.slot] = pick;
    }
    setSel(next);
  }, [plan, sel]);

  const openMeal = useCallback(
    (slot: string, mealId: string) => {
      setOpenSlot(slot);
      setDetail(null);
      getMeal(mealId, phaseKey)
        .then((d) => setDetail(d))
        .catch((e) => console.error("failed to load meal", e));
    },
    [phaseKey],
  );

  const closeDetail = useCallback(() => { setOpenSlot(null); setDetail(null); }, []);

  return (
    <>
      <section
        className="w-hero"
        style={{ ["--np-g0" as string]: phase.grad[0], ["--np-g1" as string]: phase.grad[1], ["--np-g2" as string]: phase.grad[2] }}
      >
        <div className="w-hero-inner">
          <div className="w-eyebrow">Your cycle · {phase.range}</div>
          <div className="w-arc"><CycleArc phaseKey={phaseKey} /></div>
          <h1 className="w-phase-name">{phase.name}</h1>
          <div className="w-phase-goal">{ready ? plan.goal : phase.note}</div>
          <div className="w-seg-wrap"><PhaseSelector phaseKey={phaseKey} onSelect={setPhaseKey} /></div>
        </div>
      </section>

      <main className="w-main">
        {error && (
          <div className="w-disclaimer" style={{ margin: "8px auto 20px" }}>
            Couldn't load your plan right now. Try again in a moment.
          </div>
        )}

        {ready && (
          <>
            <TipCard phase={phase} tip={plan.tip} expanded={tipExpanded} onToggle={() => setTipExpanded((v) => !v)} />

            <section className="w-focus-sec">
              <div className="w-sec">
                <h2 className="w-sec-title">This week's focus</h2>
                <span className="w-sec-side">what we emphasize now</span>
              </div>
              <div className="w-focus-grid">
                {plan.focus.map((lv) => <FocusCard key={lv.nutrient} lever={lv} accent={phase.accent} />)}
              </div>
            </section>

            <section className="w-plan">
              <div className="w-sec">
                <h2 className="w-sec-title">Recommended meals</h2>
                <button
                  className="w-rebuild"
                  type="button"
                  onClick={rebuild}
                  style={{ color: phase.accent, borderColor: phase.accent + "55" }}
                >
                  {NPIcon.swap(phase.accent)} Rebuild plan
                </button>
              </div>
              <div className="w-plan-grid">
                {plan.slots.map((s) => {
                  const meal = s.pool[idxOf(s.slot)];
                  return (
                    <MealItem
                      key={s.slot}
                      meal={meal}
                      slotLabel={s.label}
                      slotTime={s.time}
                      phase={phase}
                      onOpen={() => openMeal(s.slot, meal.meal_id)}
                      onSwap={() => swap(s.slot, s.pool.length)}
                      hasAlt={s.pool.length > 1}
                    />
                  );
                })}
              </div>
              <TailoredBar profile={profile} accent={phase.accent} onEdit={onEditPrefs} />
            </section>

            <div className="w-disclaimer">
              Gentle guidance, not medical advice. Your nutrient targets are general daily reference
              points — guides to nourish you, never limits to stay under.
            </div>
          </>
        )}
      </main>

      {openSlot && detail && (() => {
        const slot = plan!.slots.find((s) => s.slot === openSlot);
        return (
          <MealDetail
            meal={detail}
            phase={phase}
            slotLabel={slot?.label ?? ""}
            slotTime={slot?.time ?? ""}
            focusTokens={focusTokens}
            hasAlt={(slot?.pool.length ?? 1) > 1}
            onSwap={() => { if (slot) swap(slot.slot, slot.pool.length); closeDetail(); }}
            onClose={closeDetail}
          />
        );
      })()}
    </>
  );
}
