/* Compact macro strip: protein / fibre / calories (what np_meal_nutrition gives).
   Adapted from the design's WMacroStrip. */
import type { Macros } from "../api";

export default function MacroStrip({ macros }: { macros: Macros }) {
  const items = [
    { dot: "#E2566F", value: `${macros.protein_g}g`, label: "Protein" },
    { dot: "#9267C8", value: `${macros.fiber_g}g`, label: "Fibre" },
    { dot: "#1DA4A6", value: `${macros.calories}`, label: "kcal" },
  ];
  return (
    <div className="w-macros">
      {items.map((m) => (
        <span className="w-macro" key={m.label}>
          <i className="w-macro-dot" style={{ background: m.dot }} />
          <b>{m.value}</b> {m.label}
        </span>
      ))}
    </div>
  );
}
