import { CAL_MIN, CAL_MAX, CAL_STEP } from "../data";
import { NPIcon } from "../icons";

export default function CalorieInput({
  value,
  onChange,
  accent,
}: {
  value: number;
  onChange: (v: number) => void;
  accent: string;
}) {
  const clamp = (n: number) => Math.max(CAL_MIN, Math.min(CAL_MAX, n));
  const dec = () => onChange(clamp(value - CAL_STEP));
  const inc = () => onChange(clamp(value + CAL_STEP));
  // Clamp so an out-of-range persisted value can't push the gradient stop past its track.
  const pct = Math.max(0, Math.min(100, ((value - CAL_MIN) / (CAL_MAX - CAL_MIN)) * 100));

  return (
    <div className="w-cal">
      <div className="w-cal-stepper">
        <button type="button" className="w-cal-btn" onClick={dec} disabled={value <= CAL_MIN} aria-label="Decrease">
          {NPIcon.minus("currentColor")}
        </button>
        <div className="w-cal-readout">
          <span className="w-cal-val" style={{ color: accent }}>{value.toLocaleString()}</span>
          <span className="w-cal-unit">kcal / day</span>
        </div>
        <button type="button" className="w-cal-btn" onClick={inc} disabled={value >= CAL_MAX} aria-label="Increase">
          {NPIcon.plus("currentColor")}
        </button>
      </div>
      <input
        type="range"
        className="w-cal-range"
        min={CAL_MIN}
        max={CAL_MAX}
        step={CAL_STEP}
        value={value}
        onChange={(e) => onChange(clamp(parseInt(e.target.value, 10)))}
        style={{ background: `linear-gradient(90deg, ${accent} ${pct}%, var(--core-gray-200) ${pct}%)` }}
      />
      <div className="w-cal-scale">
        <span>{CAL_MIN.toLocaleString()}</span>
        <span>{CAL_MAX.toLocaleString()}</span>
      </div>
    </div>
  );
}
