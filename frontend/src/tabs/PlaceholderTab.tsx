import { WTabIcon } from "../icons";

export default function PlaceholderTab({
  which,
  accent,
}: {
  which: "plan" | "dashboard";
  accent: string;
}) {
  const copy = {
    plan: { title: "Your plan", body: "Your cycle-aware meal plan lands here next — recommended meals, this week's focus, and your daily tip." },
    dashboard: { title: "Dashboard", body: "Nutrient targets, meal variety, and your weekly progress will show up here soon." },
  }[which];

  return (
    <div className="w-screen w-screen-light">
      <div className="w-placeholder">
        <div className="w-placeholder-ic">{WTabIcon[which](accent)}</div>
        <h2>{copy.title}</h2>
        <p>{copy.body}</p>
      </div>
    </div>
  );
}
