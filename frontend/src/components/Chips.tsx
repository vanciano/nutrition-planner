import { NPIcon } from "../icons";

export default function Chips({
  options,
  selected,
  onToggle,
  accent,
}: {
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
  accent: string;
}) {
  return (
    <div className="w-chips">
      {options.map((o) => {
        const on = selected.includes(o);
        return (
          <button
            key={o}
            type="button"
            className={"w-chip" + (on ? " on" : "")}
            onClick={() => onToggle(o)}
            style={on ? { borderColor: accent, background: accent + "16", color: accent } : undefined}
          >
            {on && <span className="w-chip-check">{NPIcon.check(accent)}</span>}
            {o}
          </button>
        );
      })}
    </div>
  );
}
