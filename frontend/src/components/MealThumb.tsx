/* Meal image with graceful fallback: shows the direct photo when available and
   it loads; on missing URL or load error, falls back to the emoji icon over the
   gradient tile. Keyed by src upstream so it resets when the meal changes. */
import { useState } from "react";

export default function MealThumb({
  src,
  icon,
  imgClass,
  emojiClass,
  emojiStyle,
}: {
  src: string | null;
  icon: string;
  imgClass: string;
  emojiClass: string;
  emojiStyle?: React.CSSProperties;
}) {
  const [failed, setFailed] = useState(false);
  if (src && !failed) {
    return <img className={imgClass} src={src} alt="" loading="lazy" onError={() => setFailed(true)} />;
  }
  return <span className={emojiClass} style={emojiStyle}>{icon}</span>;
}
