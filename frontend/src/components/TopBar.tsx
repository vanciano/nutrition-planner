import type { Phase } from "../data";
import { FloMark } from "../icons";

export default function TopBar({ phase }: { phase: Phase }) {
  return (
    <header className="w-top">
      <div className="w-top-inner">
        <div className="w-brand">
          <FloMark size={26} />
          <span className="w-brand-word">Flo</span>
          <span className="w-brand-div" />
          <span className="w-brand-sec">Nutrition</span>
        </div>
        <div className="w-top-phase" style={{ background: phase.tint, color: phase.accent }}>
          <span className="w-top-dot" style={{ background: phase.accent }} />
          {phase.short} · Day {phase.day}
        </div>
      </div>
    </header>
  );
}
