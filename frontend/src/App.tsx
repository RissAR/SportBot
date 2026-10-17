import React, { useEffect, useState } from "react";
import { api, triggerHaptic } from "./api";
import { CalendarTab } from "./components/CalendarTab";
import { GuideTab } from "./components/GuideTab";
import { Navigation, TabType } from "./components/Navigation";
import { ProgressTab } from "./components/ProgressTab";
import { RestTimerHUD } from "./components/RestTimerHUD";
import { WorkoutTab } from "./components/WorkoutTab";
import { TodayWorkout, UserProfile } from "./types";

export const App: React.FC = () => {
  // Rules of Hooks: All hooks called at top level
  const [activeTab, setActiveTab] = useState<TabType>("workout");
  const [user, setUser] = useState<UserProfile | null>(null);
  const [todayWorkout, setTodayWorkout] = useState<TodayWorkout | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [restTargetTimestamp, setRestTargetTimestamp] = useState<number | null>(null);

  // Initialize Telegram WebApp SDK
  useEffect(() => {
    if (typeof window !== "undefined" && window.Telegram?.WebApp) {
      window.Telegram.WebApp.ready();
      window.Telegram.WebApp.expand();
    }
  }, []);

  // Fetch initial profile & today's workout
  const loadInitialData = async () => {
    setLoading(true);
    try {
      const profile = await api.fetchUserProfile();
      setUser(profile);
      const workout = await api.fetchTodayWorkout();
      setTodayWorkout(workout);
    } catch (err) {
      console.error("Failed to load initial SportBot state:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  const handleDifficultyChange = async (mode: "light" | "medium" | "hard") => {
    triggerHaptic("medium");
    try {
      await api.updateDifficulty(mode);
      setUser((prev) => (prev ? { ...prev, difficulty_mode: mode } : null));
      const workout = await api.fetchTodayWorkout();
      setTodayWorkout(workout);
    } catch (err) {
      console.error("Failed to update difficulty mode:", err);
    }
  };

  // Handlers for Rest Timer HUD
  const handleStartRest = (seconds: number) => {
    setRestTargetTimestamp(Date.now() + seconds * 1000);
  };

  const handleCloseRestTimer = () => {
    setRestTargetTimestamp(null);
  };

  const handleAdjustRestTimer = (secondsDelta: number) => {
    if (!restTargetTimestamp) return;
    const newTarget = restTargetTimestamp + secondsDelta * 1000;
    // Don't adjust below current time
    if (newTarget > Date.now()) {
      setRestTargetTimestamp(newTarget);
    } else {
      setRestTargetTimestamp(null);
    }
  };

  const defaultUser: UserProfile = {
    telegram_id: 123456789,
    username: "Athlete",
    current_day: 1,
    current_cycle: 1,
    difficulty_mode: "medium",
    total_workouts_completed: 0,
    latest_weight: null,
  };

  const activeUser = user || defaultUser;

  return (
    <div className="min-h-screen w-full bg-[#0c0d12] text-white flex flex-col justify-between selection:bg-red-500 selection:text-white">
      {/* Minimal Status Header (Stealth Dark / Apple Fitness style) */}
      <header className="sticky top-0 z-30 bg-[#0c0d12]/90 backdrop-blur-md border-b border-[#222533] px-4 py-2.5 max-w-md mx-auto w-full flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-white">Cycle {activeUser.current_cycle}</span>
          <span className="text-xs text-zinc-600">•</span>
          <span className="text-xs font-medium text-zinc-400">Day {activeUser.current_day} of 30</span>
        </div>

        {/* Compact difficulty switcher */}
        <div className="flex items-center bg-[#151720] border border-[#222533] rounded-lg p-0.5 text-xs">
          {(["Light", "Medium", "Hard"] as const).map((mode) => {
            const modeLower = mode.toLowerCase() as "light" | "medium" | "hard";
            const isActive = activeUser.difficulty_mode.toLowerCase() === modeLower;
            return (
              <button
                key={mode}
                type="button"
                onClick={() => handleDifficultyChange(modeLower)}
                className={`px-2 py-1 rounded-md text-[11px] font-medium transition-all ${
                  isActive
                    ? "bg-[#272b3b] text-white shadow-sm"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {mode}
              </button>
            );
          })}
        </div>
      </header>

      {/* Main Tab Content Container */}
      <main className="flex-1 max-w-md mx-auto w-full px-4 pt-3 pb-28">
        {activeTab === "workout" && (
          <WorkoutTab
            user={activeUser}
            workout={todayWorkout}
            loading={loading}
            onRefresh={loadInitialData}
            onStartRest={handleStartRest}
          />
        )}

        {activeTab === "calendar" && <CalendarTab user={activeUser} />}

        {activeTab === "progress" && (
          <ProgressTab user={activeUser} onRefreshUser={loadInitialData} />
        )}

        {activeTab === "guide" && <GuideTab />}
      </main>

      {/* Floating Rest Timer HUD */}
      <RestTimerHUD
        targetTimestamp={restTargetTimestamp}
        onClose={handleCloseRestTimer}
        onAdjust={handleAdjustRestTimer}
      />

      {/* Bottom Navigation */}
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />
    </div>
  );
};

export default App;
