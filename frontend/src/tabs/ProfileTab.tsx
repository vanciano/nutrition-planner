import { PHASES, DIETS, ALLERGIES, type PhaseKey } from "../data";
import type { Profile } from "../api";
import { NPIcon } from "../icons";
import CalorieInput from "../components/CalorieInput";
import Chips from "../components/Chips";

export default function ProfileTab({
  phaseKey,
  profile,
  setProfile,
}: {
  phaseKey: PhaseKey;
  profile: Profile;
  setProfile: (updater: (p: Profile) => Profile) => void;
}) {
  const phase = PHASES[phaseKey];
  const accent = phase.accent;

  const toggle = (key: "diets" | "allergies", val: string) =>
    setProfile((p) => {
      const has = p[key].includes(val);
      return { ...p, [key]: has ? p[key].filter((x) => x !== val) : [...p[key], val] };
    });

  return (
    <div className="w-screen w-screen-light">
      <div className="w-shead">
        <h1 className="w-shead-title">Profile</h1>
        <p className="w-shead-sub">Tune how your plan is built. These settings shape the meal suggestions we make for you.</p>
      </div>

      <div className="w-prof">
        <div className="w-prof-id">
          <div className="w-prof-av">
            <svg width="56" height="56" viewBox="0 0 56 56">
              <circle cx="28" cy="28" r="28" fill="var(--core-teal-700)" />
              <circle cx="21" cy="26" r="6.5" fill="#fff" />
              <circle cx="35" cy="26" r="6.5" fill="#fff" />
              <circle cx="21" cy="26" r="3" fill="#0A0A0A" />
              <circle cx="35" cy="26" r="3" fill="#0A0A0A" />
              <path d="M23 37c2.2 1.6 7 1.6 9 0" stroke="var(--core-peach-500)" strokeWidth="2.6" strokeLinecap="round" fill="none" />
            </svg>
          </div>
          <div className="w-prof-idmeta">
            <div className="w-prof-name">Sophie</div>
            <div className="w-prof-meta">{phase.name} · {phase.note}</div>
          </div>
        </div>

        <section className="w-card w-prof-sec">
          <h2 className="w-prof-h">Daily energy target</h2>
          <p className="w-prof-desc">Set a daily energy target and we'll scale your meal portions to match. It's a guide to keep you nourished — not a limit to stay under.</p>
          <CalorieInput
            value={profile.energy_target}
            onChange={(v) => setProfile((p) => ({ ...p, energy_target: v }))}
            accent={accent}
          />
        </section>

        <section className="w-card w-prof-sec">
          <h2 className="w-prof-h">Dietary preferences</h2>
          <p className="w-prof-desc">We'll lean your meal suggestions toward what you choose.</p>
          <Chips options={DIETS} selected={profile.diets} onToggle={(v) => toggle("diets", v)} accent={accent} />
        </section>

        <section className="w-card w-prof-sec">
          <h2 className="w-prof-h">Allergies</h2>
          <p className="w-prof-desc">We'll flag these in suggestions where we can.</p>
          <Chips options={ALLERGIES} selected={profile.allergies} onToggle={(v) => toggle("allergies", v)} accent={accent} />
          <div className="w-prof-disc">
            {NPIcon.info("var(--color-foreground-minor)")}
            <span>Noting an allergy helps us tailor ideas, but meals aren't guaranteed allergen-free. Always check ingredients and labels yourself.</span>
          </div>
        </section>
      </div>
    </div>
  );
}
