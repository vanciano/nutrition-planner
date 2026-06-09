/* Quiet "Tailored to your preferences" strip below the plan — Includes (✓ diets)
   and Avoiding (✕ allergies), with an Edit link to Profile. Ported from the
   design's WTailoredBar. */
import type { Profile } from "../api";
import { NPIcon } from "../icons";

export default function TailoredBar({
  profile,
  accent,
  onEdit,
}: {
  profile: Profile;
  accent: string;
  onEdit: () => void;
}) {
  const diets = profile.diets || [];
  const allergies = profile.allergies || [];
  const has = diets.length || allergies.length;
  return (
    <div className="w-tailored">
      <div className="w-tailored-head">
        <span className="w-tailored-label">
          {NPIcon.check("var(--color-foreground-minor)")}
          {has ? "Tailored to your preferences" : "No dietary preferences set"}
        </span>
        <button className="w-tailored-edit" type="button" onClick={onEdit} style={{ color: accent }}>
          {has ? "Edit" : "Add"}
          {NPIcon.chevron(accent)}
        </button>
      </div>
      {!!has && (
        <div className="w-tailored-groups">
          {diets.length > 0 && (
            <div className="w-tailored-group">
              <span className="w-tailored-gl">Includes</span>
              {diets.map((d) => (
                <span
                  className="w-tailored-chip pos"
                  key={d}
                  style={{ color: accent, borderColor: accent + "40", background: accent + "12" }}
                >
                  {NPIcon.check(accent)}
                  {d}
                </span>
              ))}
            </div>
          )}
          {allergies.length > 0 && (
            <div className="w-tailored-group">
              <span className="w-tailored-gl">Avoiding</span>
              {allergies.map((a) => (
                <span className="w-tailored-chip neg" key={a}>
                  {NPIcon.close("currentColor")}
                  {a.toLowerCase()}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
