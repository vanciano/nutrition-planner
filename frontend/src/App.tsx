import { useCallback, useEffect, useRef, useState } from "react";
import { getProfile, saveProfile, type Profile } from "./api";
import { PHASES, DEFAULT_CALORIE_TARGET, type PhaseKey } from "./data";
import TopBar from "./components/TopBar";
import BottomNav, { type TabKey } from "./components/BottomNav";
import ProfileTab from "./tabs/ProfileTab";
import PlanTab from "./tabs/PlanTab";
import ChatTab from "./tabs/ChatTab";

const DEFAULT_PROFILE: Profile = {
  energy_target: DEFAULT_CALORIE_TARGET,
  diets: [],
  allergies: [],
};

export default function App() {
  // The Plan tab's phase selector drives theming app-wide (TopBar + BottomNav accent).
  const [phaseKey, setPhaseKey] = useState<PhaseKey>("menstrual");
  const [tab, setTab] = useState<TabKey>("plan");
  const [profile, setProfile] = useState<Profile>(DEFAULT_PROFILE);

  const dirtyRef = useRef(false);
  const saveTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Load the persisted profile once on mount (server-sourced, so not "dirty").
  useEffect(() => {
    getProfile()
      .then(setProfile)
      .catch((e) => console.error("failed to load profile", e));
  }, []);

  // Debounced persist — only after a user edit, so the initial load never re-saves.
  useEffect(() => {
    if (!dirtyRef.current) return;
    if (saveTimer.current) clearTimeout(saveTimer.current);
    saveTimer.current = setTimeout(() => {
      saveProfile(profile).catch((e) => console.error("failed to save profile", e));
    }, 600);
    return () => {
      if (saveTimer.current) clearTimeout(saveTimer.current);
    };
  }, [profile]);

  const updateProfile = useCallback((updater: (p: Profile) => Profile) => {
    dirtyRef.current = true;
    setProfile(updater);
  }, []);

  const phase = PHASES[phaseKey];

  return (
    <div className="w-app">
      <TopBar phase={phase} />

      {tab === "plan" && (
        <PlanTab
          phaseKey={phaseKey}
          setPhaseKey={setPhaseKey}
          profile={profile}
          onEditPrefs={() => setTab("profile")}
        />
      )}
      {tab === "coach" && <ChatTab phaseKey={phaseKey} profile={profile} />}
      {tab === "profile" && (
        <ProfileTab phaseKey={phaseKey} profile={profile} setProfile={updateProfile} />
      )}

      <BottomNav tab={tab} onTab={setTab} accent={phase.accent} />
    </div>
  );
}
