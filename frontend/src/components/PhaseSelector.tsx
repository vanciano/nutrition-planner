/* Segmented phase pill (Menstrual / Follicular / Luteal) with phase colour dots
   and a sliding thumb. Ported from the design's WPhaseSelector. */
import { PHASES, PHASE_ORDER, type PhaseKey } from "../data";

export default function PhaseSelector({
  phaseKey,
  onSelect,
}: {
  phaseKey: PhaseKey;
  onSelect: (k: PhaseKey) => void;
}) {
  const idx = PHASE_ORDER.indexOf(phaseKey);
  return (
    <div className="w-seg">
      <div
        className="w-seg-thumb"
        style={{ transform: `translateX(${idx * 100}%)`, width: "calc((100% - 8px) / 3)" }}
      />
      {PHASE_ORDER.map((k) => (
        <button
          key={k}
          className={"w-seg-opt" + (k === phaseKey ? " on" : "")}
          onClick={() => onSelect(k)}
          type="button"
        >
          <span className="w-seg-dot" style={{ background: PHASES[k].accent }} />
          {PHASES[k].short}
        </button>
      ))}
    </div>
  );
}
