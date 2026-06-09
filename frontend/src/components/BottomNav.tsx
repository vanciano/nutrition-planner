import { WTabIcon } from "../icons";

export type TabKey = "plan" | "coach" | "profile";

const TABS: { k: TabKey; label: string; icon: (typeof WTabIcon)[keyof typeof WTabIcon] }[] = [
  { k: "plan", label: "Plan", icon: WTabIcon.plan },
  { k: "coach", label: "Coach", icon: WTabIcon.coach },
  { k: "profile", label: "Profile", icon: WTabIcon.profile },
];

export default function BottomNav({
  tab,
  onTab,
  accent,
}: {
  tab: TabKey;
  onTab: (t: TabKey) => void;
  accent: string;
}) {
  return (
    <nav className="w-bottomnav">
      {TABS.map((t) => {
        const on = t.k === tab;
        const c = on ? accent : "var(--color-foreground-minor)";
        return (
          <button
            key={t.k}
            className={"w-bn-tab" + (on ? " on" : "")}
            onClick={() => onTab(t.k)}
            type="button"
          >
            {t.icon(c)}
            <span style={{ color: c }}>{t.label}</span>
          </button>
        );
      })}
    </nav>
  );
}
