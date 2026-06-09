/* "This week's focus" lever card with an evidence-quality badge. Ported from
   the design's WFocusCard + WEvidenceBadge, driven by focus_nutrients_by_phase. */
import type { FocusLever } from "../api";

function EvidenceBadge({ evidence }: { evidence: FocusLever["evidence"] }) {
  return (
    <span className="w-evbadge" style={{ color: evidence.color, background: evidence.tint }}>
      <i className="w-evdot" style={{ background: evidence.color }} />
      {evidence.label}
    </span>
  );
}

export default function FocusCard({ lever, accent }: { lever: FocusLever; accent: string }) {
  return (
    <div className="w-focus-card" style={{ borderColor: accent + "33" }}>
      <div className="w-focus-top">
        <span className="w-focus-label">{lever.nutrient}</span>
        <EvidenceBadge evidence={lever.evidence} />
      </div>
      <div className="w-focus-why">{lever.tagline}</div>
    </div>
  );
}
