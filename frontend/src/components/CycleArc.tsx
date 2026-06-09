/* Hero cycle-progress arc — a legible 180° arc with elapsed-cycle fill, phase
   boundary ticks, a high-contrast today marker, and a focal day number.
   Ported from the design's redesigned WCycleArc. */
import { PHASES, type PhaseKey } from "../data";

export default function CycleArc({ phaseKey }: { phaseKey: PhaseKey }) {
  const W = 300, H = 168, cx = W / 2, cy = 150, R = 122, STROKE = 11;
  const phase = PHASES[phaseKey];
  const dayFrac = Math.min(phase.day / 28, 0.992);
  const pt = (t: number): [number, number] => {
    const a = ((180 - 180 * t) * Math.PI) / 180;
    return [cx + R * Math.cos(a), cy - R * Math.sin(a)];
  };
  const arcPath = (t0: number, t1: number) => {
    const [x0, y0] = pt(t0), [x1, y1] = pt(t1);
    return `M ${x0.toFixed(2)} ${y0.toFixed(2)} A ${R} ${R} 0 0 1 ${x1.toFixed(2)} ${y1.toFixed(2)}`;
  };
  const [mx, my] = pt(dayFrac);
  const boundaries = [0.179, 0.571]; // menstrual→follicular, follicular→luteal

  return (
    <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} style={{ overflow: "visible", maxWidth: "100%" }}>
      <defs>
        <filter id="w-arc-sh" x="-60%" y="-60%" width="220%" height="220%">
          <feDropShadow dx="0" dy="2" stdDeviation="3.5" floodColor="rgba(90,35,25,0.28)" />
        </filter>
      </defs>
      <path d={arcPath(0, 1)} stroke="rgba(255,255,255,0.34)" strokeWidth={STROKE} fill="none" strokeLinecap="round" />
      <path d={arcPath(0, dayFrac)} stroke="#fff" strokeWidth={STROKE} fill="none" strokeLinecap="round" />
      {boundaries.map((b, i) => {
        const [bx, by] = pt(b);
        return <circle key={i} cx={bx} cy={by} r="2.3" fill="rgba(120,60,40,0.32)" />;
      })}
      <circle cx={mx} cy={my} r="10.5" fill="#fff" filter="url(#w-arc-sh)" />
      <circle cx={mx} cy={my} r="4.6" fill={phase.accent} style={{ transition: "fill .4s ease" }} />
      <text x={cx} y={cy - 72} textAnchor="middle" className="w-arc-lbl">DAY</text>
      <text x={cx} y={cy - 28} textAnchor="middle" className="w-arc-num">{phase.day}</text>
      <text x={cx} y={cy - 6} textAnchor="middle" className="w-arc-sub">of 28</text>
    </svg>
  );
}
