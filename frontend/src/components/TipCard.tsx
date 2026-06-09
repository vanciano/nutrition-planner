/* Expandable "Tip for today" card. Ported from the design's WTipCard. */
import type { Phase } from "../data";
import { NPIcon } from "../icons";

export default function TipCard({
  phase,
  tip,
  expanded,
  onToggle,
}: {
  phase: Phase;
  tip: { short: string; long: string };
  expanded: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      className="w-tip"
      type="button"
      onClick={onToggle}
      style={{ background: phase.tint, borderColor: phase.accent + "33" }}
    >
      <span className="w-tip-ic" style={{ color: "#fff", background: phase.accent }}>
        {NPIcon.spark("#fff")}
      </span>
      <div className="w-tip-main">
        <div className="w-tip-head">
          <span className="w-tip-eyebrow" style={{ color: phase.accent }}>Tip for today</span>
          <span className="w-tip-toggle" style={{ color: phase.accent }}>
            {expanded ? "Show less" : "Read more"}
          </span>
        </div>
        <p className="w-tip-text">{expanded ? tip.long : tip.short}</p>
      </div>
    </button>
  );
}
